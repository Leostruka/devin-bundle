#!/usr/bin/env python3
"""Bound-terminal read/control CLI. Prints one JSON object to stdout.

Works only against a terminal explicitly bound for this session
(`terminal.py bind`) — same contract as browser.py. `spawn`/`send-to`/
`recv`/`close`/`kill` manage in-process PTY sessions (never user
terminals); for cross-invocation sessions use the sessions daemon.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile

import cu_actions
import cu_terminal

DAEMON_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-tsdaemon.json")


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


# -- sessions daemon client ----------------------------------------------------

def _daemon_info():
    try:
        with open(DAEMON_PATH, encoding="utf-8") as f:
            d = json.load(f)
        if os.name == "nt":
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, d["pid"])
            if not h:
                return None
            ctypes.windll.kernel32.CloseHandle(h)
        return d
    except Exception:
        return None


def _daemon_call(op, arg=None):
    d = _daemon_info()
    if not d:
        return {"ok": False, "error": "sessions daemon not running "
                "(terminal.py sessions start)"}
    try:
        s = socket.create_connection(("127.0.0.1", d["port"]), timeout=60)
        with s:
            env = {"session": d["session"], "op": op}
            if arg is not None:
                env["arg"] = arg
            s.sendall(json.dumps(env).encode() + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                chunk = s.recv(1 << 20)
                if not chunk:
                    break
                data += chunk
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"sessions daemon: {e}"}


def _daemon_start():
    if _daemon_info():
        return {"ok": True, "started": False, "note": "already running"}
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "terminal_sessions.py")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | \
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
    kw = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              stdin=subprocess.DEVNULL, close_fds=True)
    if flags:
        kw["creationflags"] = flags
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable, script, "--daemon"], **kw)
    import time
    for _ in range(100):
        time.sleep(0.1)
        if _daemon_info():
            return {"ok": True, "started": True}
    return {"ok": False, "error": "daemon did not write pidfile"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bind")
    b.add_argument("--hwnd", type=int, required=True)
    b.add_argument("--pid", type=int, default=None)
    b.add_argument("--mode", default="auto",
                   choices=["auto", "wt", "conhost", "mintty"])

    sub.add_parser("unbind")
    sub.add_parser("status")
    sub.add_parser("info")

    r = sub.add_parser("read")
    r.add_argument("--tail", type=int, default=None)
    r.add_argument("--find", default=None)

    tp = sub.add_parser("type")
    tp.add_argument("text")

    k = sub.add_parser("key")
    k.add_argument("name",
                   choices=["enter", "tab", "esc", "up", "down", "left",
                            "right", "ctrl+c"])

    sc = sub.add_parser("scroll")
    sc.add_argument("direction", choices=["up", "down"])
    sc.add_argument("n", type=int, nargs="?", default=3)

    s = sub.add_parser("send")
    s.add_argument("text")
    s.add_argument("--shell", default=None)
    s.add_argument("--timeout", type=float, default=10.0)
    s.add_argument("--confirm", action="store_true")

    e = sub.add_parser("exec")
    e.add_argument("text")
    e.add_argument("--shell", default="cmd",
                   choices=["cmd", "powershell", "pwsh", "bash", "wsl"])
    e.add_argument("--wait", default=None, help="regex to wait for")
    e.add_argument("--timeout", type=float, default=10.0)

    sp = sub.add_parser("spawn")
    sp.add_argument("--shell", default="cmd")
    sp.add_argument("--cols", type=int, default=120)
    sp.add_argument("--rows", type=int, default=30)

    st = sub.add_parser("send-to")
    st.add_argument("session")
    st.add_argument("text")

    rv = sub.add_parser("recv")
    rv.add_argument("session")
    rv.add_argument("--tail", type=int, default=None)
    rv.add_argument("--wait", default=None)
    rv.add_argument("--timeout", type=float, default=10.0)

    cl = sub.add_parser("close")
    cl.add_argument("session")

    kl = sub.add_parser("kill")
    kl.add_argument("session")

    ss = sub.add_parser("sessions")
    ss.add_argument("op", choices=["start", "stop", "status", "list"])

    args = p.parse_args()

    if args.cmd == "bind":
        probe = None
        if args.pid:
            probe = {args.hwnd: {"class": "", "pid": args.pid}}
            probe = None  # class resolved by real probe
        print(json.dumps(cu_terminal.bind(args.hwnd, mode=args.mode)))
        return
    if args.cmd == "unbind":
        print(json.dumps(cu_terminal.unbind()))
        return
    if args.cmd == "status":
        b = cu_terminal.binding()
        out = {"ok": True, "bound": b is not None}
        if b:
            out["binding"] = {k: b[k] for k in
                              ("hwnd", "pid", "mode", "title") if k in b}
        print(json.dumps(out))
        return
    if args.cmd == "info":
        print(json.dumps(cu_terminal.info()))
        return
    if args.cmd == "read":
        print(json.dumps(cu_terminal.read(tail=args.tail, find=args.find)))
        return
    if args.cmd == "type":
        print(json.dumps(cu_terminal.type_text(args.text)))
        return
    if args.cmd == "key":
        print(json.dumps(cu_terminal.key(args.name)))
        return
    if args.cmd == "scroll":
        print(json.dumps(cu_terminal.scroll(args.direction, args.n)))
        return
    if args.cmd == "send":
        print(json.dumps(cu_terminal.send(args.text, shell=args.shell,
                                          timeout=args.timeout,
                                          confirm=args.confirm)))
        return
    if args.cmd == "exec":
        r = cu_terminal.spawn(shell=args.shell)
        if not r.get("ok"):
            print(json.dumps(r))
            return
        sid = r["session"]
        cu_terminal.send_to(sid, args.text + "\r\n")
        out = cu_terminal.recv_from(sid, wait=args.wait,
                                    timeout=args.timeout)
        cu_terminal.close_session(sid)
        print(json.dumps(out))
        return
    if args.cmd == "sessions":
        if args.op == "start":
            print(json.dumps(_daemon_start()))
        elif args.op == "stop":
            print(json.dumps(_daemon_call("stop")))
        else:
            print(json.dumps(_daemon_call(args.op)))
        return
    if args.cmd in ("spawn", "send-to", "recv", "close", "kill"):
        # persistent sessions live in the daemon — start on demand
        if not _daemon_info():
            r = _daemon_start()
            if not r.get("ok"):
                print(json.dumps(r))
                return
        if args.cmd == "spawn":
            out = _daemon_call("spawn", {"shell": args.shell,
                                         "cols": args.cols,
                                         "rows": args.rows})
        elif args.cmd == "send-to":
            out = _daemon_call("send", {"sid": args.session,
                                        "text": args.text})
        elif args.cmd == "recv":
            out = _daemon_call("recv", {"sid": args.session,
                                        "tail": args.tail,
                                        "wait": args.wait,
                                        "timeout": args.timeout})
        elif args.cmd == "close":
            out = _daemon_call("close", {"sid": args.session})
        else:
            out = _daemon_call("kill", {"sid": args.session})
        print(json.dumps(out))
        return
    fail(f"unknown cmd {args.cmd}")


if __name__ == "__main__":
    cu_actions.run_cli(main)
