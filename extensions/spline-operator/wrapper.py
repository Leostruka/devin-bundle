#!/usr/bin/env python3
"""Spline desktop operator — launch, drive, and kill Spline via its embedded MCP bridge.

Spline (Electron) bundles `resources/spline-mcp.cjs`: a Node process that hosts a
WebSocket bridge on ws://127.0.0.1:19692 (env HANA_MCP_PORT overrides) and also
speaks MCP over stdio. The running Spline app connects to the bridge as "editor"
and pushes a manifest of tools; agent clients connect with
`{"type":"hello","role":"agent",...}` and dispatch `{"type":"call",...}` messages.

Stdlib only. The bridge dies when its stdin hits EOF, so `launch` spawns a
detached keeper daemon (`_daemon`) that holds the bridge's stdin pipe open.

Usage:
    wrapper.py launch [--file PATH] [--timeout SEC]
    wrapper.py status
    wrapper.py tools
    wrapper.py call NAME [JSON_ARGS]
    wrapper.py kill
    wrapper.py --self-test
"""

import argparse
import base64
import json
import os
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time

DEFAULT_PORT = 19692
AGENT_ORIGIN = "hana-mcp-agent"
CLIENT = {"name": "devin-spline-operator", "version": "1.0"}
STATE_FILE = os.path.join(tempfile.gettempdir(), "spline-operator-state.json")

DEFAULT_SPLINE_EXE = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\Spline\Spline.exe"
)
DEFAULT_MCP_CJS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\Spline\resources\spline-mcp.cjs"
)


# ---------- minimal websocket client (stdlib) ----------

def _ws_connect(host, port, origin, timeout):
    s = socket.create_connection((host, port), timeout=timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall(
        (
            f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\nOrigin: {origin}\r\n\r\n"
        ).encode()
    )
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = s.recv(4096)
        if not chunk:
            raise ConnectionError("bridge closed during handshake")
        resp += chunk
    status = resp.split(b"\r\n", 1)[0].decode()
    if "101" not in status:
        s.close()
        raise ConnectionError(f"handshake rejected: {status}")
    return s


def _ws_send_text(s, payload):
    data = payload.encode()
    mask = os.urandom(4)
    n = len(data)
    if n < 126:
        hdr = struct.pack("!BB", 0x81, 0x80 | n)
    elif n < 65536:
        hdr = struct.pack("!BBH", 0x81, 0x80 | 126, n)
    else:
        hdr = struct.pack("!BBQ", 0x81, 0x80 | 127, n)
    s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def _ws_recv_msg(s):
    buf = b""
    while True:
        hdr = s.recv(2)
        if len(hdr) < 2:
            return None
        fin, op = hdr[0] & 0x80, hdr[0] & 0x0F
        ln = hdr[1] & 0x7F
        if ln == 126:
            ln = struct.unpack("!H", s.recv(2))[0]
        elif ln == 127:
            ln = struct.unpack("!Q", s.recv(8))[0]
        payload = b""
        while len(payload) < ln:
            chunk = s.recv(ln - len(payload))
            if not chunk:
                return None
            payload += chunk
        if op == 8:
            return None
        if op in (1, 2):
            buf += payload
        if fin and buf:
            return buf.decode()


def _bridge_alive(port):
    try:
        socket.create_connection(("127.0.0.1", port), timeout=2).close()
        return True
    except OSError:
        return False


def _agent_session(port, timeout=15):
    """Connect, say hello, yield decoded messages until close."""
    s = _ws_connect("127.0.0.1", port, AGENT_ORIGIN, timeout)
    s.settimeout(timeout)
    _ws_send_text(s, json.dumps({"type": "hello", "role": "agent", "client": CLIENT}))
    return s


def _next_of_type(s, wanted, limit=50):
    for _ in range(limit):
        raw = _ws_recv_msg(s)
        if raw is None:
            return None
        msg = json.loads(raw)
        if msg.get("type") in wanted:
            return msg
    return None


# ---------- state file ----------

def _save_state(**kw):
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            state = json.load(open(STATE_FILE))
        except (OSError, json.JSONDecodeError):
            pass
    state.update(kw)
    json.dump(state, open(STATE_FILE, "w"), indent=1)


def _load_state():
    try:
        return json.load(open(STATE_FILE))
    except (OSError, json.JSONDecodeError):
        return {}


# ---------- process helpers ----------

def _find_pids(image=None, cmdline_contains=None):
    """Return matching PIDs via PowerShell CIM (Windows) or ps (POSIX)."""
    pids = []
    if os.name == "nt":
        q = "Get-CimInstance Win32_Process"
        if image:
            q += f" | Where-Object {{$_.Name -eq '{image}'"
            if cmdline_contains:
                q += f" -and $_.CommandLine -like '*{cmdline_contains}*'"
            q += "}"
        elif cmdline_contains:
            q += f" | Where-Object {{$_.CommandLine -like '*{cmdline_contains}*'}}"
        q += " | Select-Object -ExpandProperty ProcessId"
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", q],
            capture_output=True, text=True, timeout=15,
        ).stdout
        pids = [int(x) for x in out.split() if x.strip().isdigit()]
    else:
        out = subprocess.run(
            ["ps", "-axo", "pid,comm,args"], capture_output=True, text=True
        ).stdout
        for line in out.splitlines():
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            ok = (image and image in parts[1]) or (
                cmdline_contains and cmdline_contains in parts[2]
            )
            if ok and "wrapper.py" not in parts[2]:
                pids.append(int(parts[0]))
    return pids


def _kill_pid(pid):
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T"], capture_output=True, timeout=10
            )
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True, timeout=10,
            )
        else:
            os.kill(pid, signal.SIGTERM)
            for _ in range(20):
                try:
                    os.kill(pid, 0)
                except OSError:
                    return
                time.sleep(0.25)
            os.kill(pid, signal.SIGKILL)
    except (OSError, subprocess.TimeoutExpired):
        pass


# ---------- commands ----------

def cmd_daemon(args):
    """Keeper process: holds the bridge's stdin pipe open so it never sees EOF."""
    node = args.node or "node"
    proc = subprocess.Popen(
        [node, args.mcp],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _save_state(bridge_pid=proc.pid)
    proc.wait()


def cmd_launch(args):
    port = args.port
    exe, mcp = args.exe, args.mcp
    errors = []
    for p, what in ((exe, "Spline.exe"), (mcp, "spline-mcp.cjs")):
        if not os.path.exists(p):
            errors.append(f"{what} not found: {p}")
    if errors:
        return {"ok": False, "errors": errors}

    if not _bridge_alive(port):
        daemon_cmd = [
            sys.executable, os.path.abspath(__file__), "_daemon",
            "--mcp", mcp,
        ] + (["--node", args.node] if args.node else [])
        kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
              "stderr": subprocess.DEVNULL}
        if os.name == "nt":
            kw["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            kw["start_new_session"] = True
        subprocess.Popen(daemon_cmd, **kw)
        deadline = time.time() + 15
        while time.time() < deadline and not _bridge_alive(port):
            time.sleep(0.25)
        if not _bridge_alive(port):
            return {"ok": False, "error": "bridge failed to listen on %d" % port}

    spline_pids = _find_pids(image="Spline.exe")
    if not spline_pids:
        argv = [exe] + ([args.file] if args.file else [])
        subprocess.Popen(argv)
    deadline = time.time() + args.timeout
    tools = None
    while time.time() < deadline:
        try:
            s = _agent_session(port, timeout=8)
            msg = _next_of_type(s, {"manifest"}, limit=20)
            s.close()
            if msg and msg.get("tools"):
                tools = msg["tools"]
                break
        except (OSError, json.JSONDecodeError):
            pass
        time.sleep(1)
    if tools is None:
        return {"ok": False, "error": f"no manifest within {args.timeout}s",
                "hint": "Spline may still be starting; retry `status`"}
    _save_state(launched_at=time.time(), tool_count=len(tools))
    return {"ok": True, "tools": [t["name"] for t in tools],
            "spline_pids": _find_pids(image="Spline.exe")}


def cmd_status(args):
    port = args.port
    if not _bridge_alive(port):
        return {"ok": True, "bridge": "down", "editor": "disconnected",
                "spline_pids": _find_pids(image="Spline.exe")}
    try:
        s = _agent_session(port, timeout=8)
        msg = _next_of_type(s, {"manifest"}, limit=20)
        s.close()
        tools = msg.get("tools", []) if msg else []
        return {"ok": True, "bridge": "up", "port": port,
                "editor": "connected" if tools else "no-manifest",
                "tool_count": len(tools),
                "spline_pids": _find_pids(image="Spline.exe")}
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": True, "bridge": "up", "editor": f"error: {e}",
                "spline_pids": _find_pids(image="Spline.exe")}


def cmd_tools(args):
    s = _agent_session(args.port, timeout=10)
    msg = _next_of_type(s, {"manifest"}, limit=20)
    s.close()
    if not msg:
        return {"ok": False, "error": "no manifest received"}
    return {"ok": True, "tools": [
        {"name": t["name"],
         "description": t.get("description", "")[:120]}
        for t in msg["tools"]
    ]}


def cmd_call(args):
    try:
        call_args = json.loads(args.args) if args.args else {}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"invalid JSON args: {e}"}
    s = _agent_session(args.port, timeout=10)
    call_id = "w1"
    manifest = _next_of_type(s, {"manifest"}, limit=20)
    if not manifest:
        s.close()
        return {"ok": False, "error": "no manifest — is Spline running?"}
    names = {t["name"] for t in manifest["tools"]}
    if args.name not in names:
        s.close()
        return {"ok": False, "error": f"unknown tool '{args.name}'",
                "available": sorted(names)}
    _ws_send_text(s, json.dumps(
        {"type": "call", "id": call_id, "name": args.name, "args": call_args}))
    s.settimeout(args.timeout)
    msg = _next_of_type(s, {"result", "error"}, limit=10)
    s.close()
    if msg is None:
        return {"ok": False, "error": "no response / closed"}
    return {"ok": msg["type"] == "result", "response": msg}


def cmd_kill(args):
    state = _load_state()
    killed = []
    for pid in _find_pids(image="Spline.exe"):
        _kill_pid(pid)
        killed.append(pid)
    bridge_pids = set(_find_pids(cmdline_contains="spline-mcp.cjs"))
    if state.get("bridge_pid"):
        bridge_pids.add(state["bridge_pid"])
    for pid in _find_pids(cmdline_contains="_daemon --mcp"):
        if pid != os.getpid():
            _kill_pid(pid)
    for pid in bridge_pids:
        _kill_pid(pid)
        killed.append(pid)
    _save_state(bridge_pid=None)
    return {"ok": True, "killed_pids": killed,
            "remaining_spline": _find_pids(image="Spline.exe")}


def cmd_self_test(args):
    out = {"ok": True}
    p = _ws_send_text.__name__ and True
    out["checks"] = {
        "state_file": STATE_FILE,
        "default_exe_exists": os.path.exists(DEFAULT_SPLINE_EXE),
        "default_mcp_exists": os.path.exists(DEFAULT_MCP_CJS),
        "frame_encode": p,
    }
    return out


def main():
    ap = argparse.ArgumentParser(description="Spline desktop operator")
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("HANA_MCP_PORT", DEFAULT_PORT)))
    ap.add_argument("--exe", default=DEFAULT_SPLINE_EXE)
    ap.add_argument("--mcp", default=DEFAULT_MCP_CJS)
    ap.add_argument("--node", default=None, help="node binary override")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("launch")
    p.add_argument("--file", default=None, help="project file to open")
    p.add_argument("--timeout", type=int, default=45)
    p = sub.add_parser("status")
    p = sub.add_parser("tools")
    p = sub.add_parser("call")
    p.add_argument("name")
    p.add_argument("args", nargs="?", default=None)
    p.add_argument("--timeout", type=int, default=60)
    p = sub.add_parser("kill")
    p = sub.add_parser("_daemon")
    p.add_argument("--mcp", default=DEFAULT_MCP_CJS)
    p.add_argument("--node", default=None)

    args = ap.parse_args()
    if args.self_test:
        result = cmd_self_test(args)
    elif args.cmd == "launch":
        result = cmd_launch(args)
    elif args.cmd == "status":
        result = cmd_status(args)
    elif args.cmd == "tools":
        result = cmd_tools(args)
    elif args.cmd == "call":
        result = cmd_call(args)
    elif args.cmd == "kill":
        result = cmd_kill(args)
    elif args.cmd == "_daemon":
        cmd_daemon(args)
        return
    else:
        ap.print_help()
        sys.exit(2)
    print(json.dumps(result, indent=1))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
