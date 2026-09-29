#!/usr/bin/env python3
"""Blender operator: launch, drive, and kill headless Blender via a TCP
JSONL exec loop inside it (`blender_server.py`).

No MCP bridge, no addon install, no GUI. The wrapper spawns
`blender -b --factory-startup --python blender_server.py -- --port N`,
which opens a persistent 127.0.0.1:N server evaluating bpy code sent as
one-line JSON requests. Stdlib only.

Usage:
    wrapper.py launch [--blend FILE] [--port N] [--timeout S]
    wrapper.py status
    wrapper.py exec --code "bpy..." | --file script.py [--timeout S]
    wrapper.py exec-file script.py        (alias of exec --file)
    wrapper.py kill
    wrapper.py --self-test
"""
import argparse
import glob
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

DEFAULT_PORT = 19693
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "blender_server.py")
STATE_FILE = os.path.join(tempfile.gettempdir(), "blender-operator-state.json")
LOG_FILE = os.path.join(tempfile.gettempdir(), "blender-operator-server.log")


# ---------- blender discovery ----------

def find_blender(explicit=None):
    """Return path to blender executable or None."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("BLENDER_EXE")
    if env:
        candidates.append(env)
    on_path = shutil.which("blender")
    if on_path:
        candidates.append(on_path)
    if os.name == "nt":
        patterns = [
            r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Blender*\blender.exe"),
            os.path.expandvars(r"%ProgramFiles%\Blender*\blender.exe"),
        ]
    else:
        patterns = ["/usr/bin/blender", "/usr/local/bin/blender",
                    "/opt/blender*/blender",
                    "/Applications/Blender.app/Contents/MacOS/Blender"]
    for pat in patterns:
        hits = sorted(glob.glob(pat), reverse=True)
        candidates.extend(hits)
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
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


# ---------- protocol ----------

def _request(port, payload, timeout=30):
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
        f = s.makefile("rw", encoding="utf-8", newline="\n")
        f.write(json.dumps(payload) + "\n")
        f.flush()
        line = f.readline()
        if not line:
            return {"ok": False, "error": "server closed without reply"}
        return json.loads(line)


def _alive(port):
    try:
        r = _request(port, {"id": "ping", "op": "ping"}, timeout=3)
        return r.get("ok"), r
    except OSError:
        return False, {}


# ---------- process helpers ----------

def _find_pids(image=None, cmdline_contains=None):
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
                cmdline_contains and cmdline_contains in parts[2])
            if ok and "wrapper.py" not in parts[2]:
                pids.append(int(parts[0]))
    return pids


def _kill_pid(pid):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=10)
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

def cmd_launch(args):
    blender = find_blender(args.exe)
    if not blender:
        return {"ok": False,
                "error": "blender executable not found",
                "hint": "set BLENDER_EXE env var or --exe; install from blender.org (free, GPL)"}
    if not os.path.isfile(SERVER):
        return {"ok": False, "error": f"server script missing: {SERVER}"}
    alive, info = _alive(args.port)
    if alive:
        return {"ok": True, "already_running": True, "blender": info}
    argv = [blender, "-b", "--factory-startup",
            "--python", SERVER, "--", "--port", str(args.port)]
    if args.blend:
        argv.insert(4, args.blend)
    log = open(LOG_FILE, "ab")
    kw = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log}
    if os.name == "nt":
        kw["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                               | subprocess.DETACHED_PROCESS)
    else:
        kw["start_new_session"] = True
    proc = subprocess.Popen(argv, **kw)
    _save_state(pid=proc.pid, port=args.port, blender=blender)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        alive, info = _alive(args.port)
        if alive:
            _save_state(pid=proc.pid, port=args.port, blender=blender,
                        blender_version=info.get("blender"))
            return {"ok": True, "pid": proc.pid, "port": args.port,
                    "blender": info.get("blender"), "log": LOG_FILE}
        if proc.poll() is not None:
            return {"ok": False, "error": "blender exited during startup",
                    "exit_code": proc.returncode, "log": LOG_FILE}
        time.sleep(0.3)
    return {"ok": False,
            "error": f"server not ready within {args.timeout}s",
            "log": LOG_FILE}


def cmd_status(args):
    alive, info = _alive(args.port)
    state = _load_state()
    return {"ok": True,
            "server": "up" if alive else "down",
            "port": args.port,
            "blender": info.get("blender"),
            "scene": info.get("scene"),
            "pid": state.get("pid"),
            "exe": state.get("blender") or find_blender(args.exe),
            "blender_pids": _find_pids(image="blender.exe" if os.name == "nt"
                                       else "blender")}


def cmd_exec(args):
    if args.file:
        try:
            code = open(args.file, encoding="utf-8").read()
        except OSError as e:
            return {"ok": False, "error": f"cannot read {args.file}: {e}"}
    else:
        code = args.code
    if not code:
        return {"ok": False, "error": "no code given (--code or --file)"}
    r = _request(args.port,
                 {"id": "w1", "op": "exec", "code": code},
                 timeout=args.timeout)
    return r


def cmd_kill(args):
    out = {"ok": True}
    alive, _ = _alive(args.port)
    if alive:
        try:
            _request(args.port, {"id": "k", "op": "shutdown"}, timeout=5)
            out["shutdown_sent"] = True
        except OSError:
            out["shutdown_sent"] = False
        time.sleep(1)
    state = _load_state()
    killed = []
    pid = state.get("pid")
    if pid:
        try:
            os.kill(pid, 0)
        except OSError:
            pass
        else:
            _kill_pid(pid)
            killed.append(pid)
    image = "blender.exe" if os.name == "nt" else "blender"
    leftover = [p for p in _find_pids(
        cmdline_contains="blender_server.py")]
    for p in leftover:
        _kill_pid(p)
        killed.append(p)
    _save_state(pid=None)
    out["killed_pids"] = killed
    out["server"] = "down" if not _alive(args.port)[0] else "still-up"
    return out


def cmd_self_test(args):
    blender = find_blender(args.exe)
    out = {"ok": True, "checks": {
        "server_script": os.path.isfile(SERVER),
        "blender_found": blender,
        "state_file": STATE_FILE,
        "log_file": LOG_FILE,
        "port": args.port,
    }}
    if blender:
        try:
            v = subprocess.run([blender, "--version"], capture_output=True,
                               text=True, timeout=20).stdout.splitlines()
            out["checks"]["blender_version"] = v[0] if v else None
        except (OSError, subprocess.TimeoutExpired) as e:
            out["checks"]["blender_version_error"] = str(e)
    else:
        out["checks"]["blender_version"] = None
        out["ok"] = False
        out["error"] = "blender not installed; install from blender.org or set BLENDER_EXE"
    return out


def main():
    ap = argparse.ArgumentParser(description="Blender headless operator")
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("BLENDER_OPERATOR_PORT",
                                               DEFAULT_PORT)))
    ap.add_argument("--exe", default=None, help="blender.exe override")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("launch")
    p.add_argument("--blend", default=None, help=".blend file to open")
    p.add_argument("--timeout", type=int, default=60)
    sub.add_parser("status")
    p = sub.add_parser("exec")
    p.add_argument("--code", default=None)
    p.add_argument("--file", default=None)
    p.add_argument("--timeout", type=int, default=300)
    p = sub.add_parser("exec-file")
    p.add_argument("script")
    p.add_argument("--timeout", type=int, default=300)
    sub.add_parser("kill")

    args = ap.parse_args()
    if args.self_test:
        result = cmd_self_test(args)
    elif args.cmd == "launch":
        result = cmd_launch(args)
    elif args.cmd == "status":
        result = cmd_status(args)
    elif args.cmd == "exec":
        result = cmd_exec(args)
    elif args.cmd == "exec-file":
        args.file = args.script
        args.code = None
        result = cmd_exec(args)
    elif args.cmd == "kill":
        result = cmd_kill(args)
    else:
        ap.print_help()
        sys.exit(2)
    print(json.dumps(result, indent=1))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
