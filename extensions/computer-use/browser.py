#!/usr/bin/env python3
"""Bound-browser observation + control CLI. Prints one JSON object to stdout.

Works only against a browser explicitly bound for this session
(`browser.py bind`) — same contract as --via browser in mouse/type_text.
The `events` subcommands front the persistent browser_events daemon
(WS held open, real CDP/BiDi event streams); everything else is one-shot
via the JS collector + evaluate.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile

import cu_actions
import cu_browser

EVENTS_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-bevents.json")


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def _client():
    cli = cu_browser._cdp_client()
    if cli is None:
        fail("browser_unavailable — bind first "
             "(browser.py bind --endpoint http://127.0.0.1:9222 --pid N)")
    return cli


def _ensure_collector(cli):
    if not cli.evaluate("!!window.__cu_collector"):
        cli.install_collector()


# -- events daemon client ------------------------------------------------------

def _events_info():
    try:
        with open(EVENTS_PATH, encoding="utf-8") as f:
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


def _events_call(op):
    d = _events_info()
    if not d:
        return {"ok": False, "error": "events daemon not running "
                "(browser.py events start)"}
    try:
        s = socket.create_connection(("127.0.0.1", d["port"]), timeout=30)
        with s:
            s.sendall(json.dumps(
                {"session": d["session"], "op": op}).encode() + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                chunk = s.recv(1 << 20)
                if not chunk:
                    break
                data += chunk
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"events daemon: {e}"}


def _events_start(args):
    if _events_info():
        return {"ok": True, "started": False, "note": "already running"}
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "browser_events.py")
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
        if _events_info():
            return {"ok": True, "started": True}
    return {"ok": False, "error": "daemon did not write pidfile"}


def _events_stop(_args):
    r = _events_call({"op": "stop"})
    if not r.get("ok"):
        # dead daemon — stale pidfile cleanup is still our job
        try:
            os.remove(EVENTS_PATH)
        except OSError:
            pass
        return {"ok": True, "stopped": True, "note": "stale pidfile removed"}
    return r


# -- command handlers ------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bind")
    b.add_argument("--endpoint", required=True)
    b.add_argument("--pid", type=int, required=True)

    sub.add_parser("unbind")
    sub.add_parser("status")

    e = sub.add_parser("eval")
    e.add_argument("js")
    e.add_argument("--boundaries", action="store_true",
                   help="wrap string results as untrusted content")

    sub.add_parser("collect", help="install the JS collector now")

    for name in ("console", "errors", "requests"):
        c = sub.add_parser(name)
        c.add_argument("--clear", action="store_true")
        c.add_argument("--substr", default=None)

    w = sub.add_parser("wait")
    g = w.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--url")
    g.add_argument("--fn")
    g.add_argument("--selector")
    w.add_argument("--state", choices=["visible", "hidden"],
                   default="visible")
    w.add_argument("--timeout", type=float, default=10.0)
    w.add_argument("--interval", type=float, default=0.25)

    sub.add_parser("cookies")

    s = sub.add_parser("storage")
    s.add_argument("area", choices=["local", "session"])
    s.add_argument("op", nargs="?", default="all",
                   choices=["all", "get", "set", "remove", "keys", "clear"])
    s.add_argument("key", nargs="?")
    s.add_argument("value", nargs="?")

    f = sub.add_parser("find")
    f.add_argument("kind", choices=["role", "text", "label", "placeholder",
                                    "alt", "testid", "title"])
    f.add_argument("value")
    f.add_argument("--name", default=None)

    sub.add_parser("tabs")

    pi = sub.add_parser("pin")
    pi.add_argument("target", nargs="?",
                    help="target/context id; omit or 'off' to unpin")

    n = sub.add_parser("navigate")
    n.add_argument("url")

    ev = sub.add_parser("events")
    ev.add_argument("op", choices=["start", "stop", "status", "drain",
                                   "console", "errors", "requests",
                                   "dialogs", "respond", "tabs", "pin",
                                   "har"])
    ev.add_argument("arg", nargs="?", default=None,
                    help="respond: accept|dismiss; pin: targetId; "
                         "har: output path")

    args = p.parse_args()

    if args.cmd == "bind":
        print(json.dumps(cu_browser.bind(args.endpoint, args.pid)))
        return
    if args.cmd == "unbind":
        print(json.dumps(cu_browser.unbind()))
        return
    if args.cmd == "status":
        b = cu_browser.binding()
        out = {"ok": True, "bound": b is not None}
        if b:
            out["binding"] = {k: b[k] for k in
                              ("endpoint", "pid", "target_id") if k in b}
            cli = cu_browser._cdp_client()
            out["reachable"] = cli is not None
            if cli:
                out["dialect"] = cli.dialect
                cli.close()
        print(json.dumps(out))
        return
    if args.cmd == "pin":
        t = None if args.target in (None, "off") else args.target
        print(json.dumps(cu_browser.pin_target(t)))
        return
    if args.cmd == "events":
        if args.op == "start":
            print(json.dumps(_events_start(args)))
        elif args.op == "stop":
            print(json.dumps(_events_stop(args)))
        else:
            op = {"op": args.op}
            if args.arg is not None:
                op["arg"] = args.arg
            print(json.dumps(_events_call(op)))
        return

    cli = _client()
    try:
        if args.cmd == "eval":
            r = cli.evaluate(args.js)
            out = {"ok": True, "result": r}
            if args.boundaries and isinstance(r, str):
                out["result"] = cu_browser.boundaries(r)
                out["bounded"] = True
        elif args.cmd == "collect":
            out = cli.install_collector()
        elif args.cmd in ("console", "errors", "requests"):
            _ensure_collector(cli)
            kind = {"console": "log", "errors": "errors",
                    "requests": "net"}[args.cmd]
            items = cli.collector(kind, clear=args.clear)
            if args.substr:
                items = [i for i in items
                         if args.substr.lower() in json.dumps(i).lower()]
            out = {"ok": True, "count": len(items), "items": items,
                   "source": "js_collector",
                   "note": "app-level only — subresources/navigation need "
                           "the events daemon"}
        elif args.cmd == "wait":
            out = cli.wait(fn=args.fn, text=args.text, url=args.url,
                           selector=args.selector, state=args.state,
                           timeout=args.timeout, interval=args.interval)
        elif args.cmd == "cookies":
            out = {"ok": True, "cookies": cli.cookies()}
        elif args.cmd == "storage":
            out = {"ok": True,
                   "result": cli.storage(args.area, args.op,
                                         args.key, args.value)}
        elif args.cmd == "find":
            out = {"ok": True,
                   "elements": cli.find(args.kind, args.value, args.name)}
        elif args.cmd == "tabs":
            out = {"ok": True, "tabs": cli.tabs()}
        elif args.cmd == "navigate":
            out = {"ok": True, "result": cli.navigate(args.url)}
        else:
            out = {"ok": False, "error": f"unknown cmd {args.cmd}"}
        print(json.dumps(out))
    except Exception as ex:
        fail(f"{type(ex).__name__}: {ex}")
    finally:
        cli.close()


if __name__ == "__main__":
    cu_actions.run_cli(main)
