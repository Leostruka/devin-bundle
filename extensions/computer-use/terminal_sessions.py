#!/usr/bin/env python3
"""Terminal sessions daemon — holds spawned PTYs across CLI invocations.

Same shape as the browser_events daemon: loopback socket, one JSON line
per connection, session-tagged pidfile, idle TTL exit. Sessions are own
PTY processes (winpty backend) — never attached to user terminals.

Ops ({op, arg?}):
  status | list | spawn {shell,cols,rows} | send {sid,text} |
  recv {sid,tail?,wait?,timeout?} | close {sid} | kill {sid} | stop
"""
import json
import os
import socket
import sys
import tempfile
import time
import uuid

import cu_terminal

SESSIONS_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-tsdaemon.json")
IDLE_S = float(os.environ.get("CU_TSDAEMON_IDLE", "900"))


def _write_pidfile(port, session):
    data = {"pid": os.getpid(), "port": port, "session": session,
            "started": time.time()}
    tmp = SESSIONS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, SESSIONS_PATH)


def _op(env):
    op = env.get("op")
    arg = env.get("arg") or {}
    if op == "status":
        return {"ok": True, "sessions": cu_terminal.sessions()}
    if op == "list":
        return {"ok": True, "sessions": cu_terminal.sessions()}
    if op == "spawn":
        return cu_terminal.spawn(shell=arg.get("shell", "cmd"),
                                 cols=int(arg.get("cols", 120)),
                                 rows=int(arg.get("rows", 30)))
    if op == "send":
        return cu_terminal.send_to(arg["sid"], arg["text"])
    if op == "recv":
        return cu_terminal.recv_from(arg["sid"],
                                     tail=arg.get("tail"),
                                     wait=arg.get("wait"),
                                     timeout=float(arg.get("timeout", 10)))
    if op == "close":
        return cu_terminal.close_session(arg["sid"])
    if op == "kill":
        return cu_terminal.kill(arg["sid"])
    if op == "stop":
        return {"ok": True, "stopped": True}
    return {"ok": False, "error": f"unknown op {op!r}"}


def daemon_main():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    srv.settimeout(1.0)
    session = uuid.uuid4().hex[:12]
    _write_pidfile(srv.getsockname()[1], session)
    last = time.time()
    stopping = False
    try:
        while not stopping and time.time() - last < IDLE_S:
            try:
                c, _ = srv.accept()
            except socket.timeout:
                continue
            with c:
                try:
                    c.settimeout(60)
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = c.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    env = json.loads(data.decode("utf-8"))
                    if env.get("session") != session:
                        resp = {"ok": False, "error": "stale session"}
                    else:
                        resp = _op(env)
                        if env.get("op") == "stop":
                            stopping = True
                    c.sendall(json.dumps(resp).encode() + b"\n")
                    last = time.time()
                except Exception:
                    pass
    finally:
        srv.close()
        for sid in list(cu_terminal._SESSIONS):
            cu_terminal.close_session(sid)
        try:
            os.remove(SESSIONS_PATH)
        except OSError:
            pass


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        daemon_main()
