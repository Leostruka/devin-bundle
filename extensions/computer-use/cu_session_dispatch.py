#!/usr/bin/env python3
"""$CU_SESSION=1 routing: send the CLI's op to the persistent loopback
daemon (cu_session.py --daemon) and print its JSON stdout verbatim.

Daemon is spawned on demand; its pidfile lives in the system temp dir.
Loopback only — 127.0.0.1 is never a public surface.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

DAEMON_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-daemon.json")


def _daemon_info():
    try:
        with open(DAEMON_PATH, encoding="utf-8") as f:
            d = json.load(f)
        # stale pidfile: process gone?
        if os.name == "nt":
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, d["pid"])
            if not h:
                return None
            ctypes.windll.kernel32.CloseHandle(h)
        return d
    except Exception:
        return None


def _spawn_daemon(timeout=10.0):
    cu_session = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "cu_session.py")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | \
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen([sys.executable, cu_session, "--daemon"],
                     creationflags=flags, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < timeout:
        d = _daemon_info()
        if d:
            return d
        time.sleep(0.1)
    return None


def _request(d, cmd, timeout=30.0):
    with socket.create_connection(("127.0.0.1", d["port"]),
                                  timeout=timeout) as s:
        s.sendall(json.dumps(
            {"session": d["session"], "cmd": cmd}).encode() + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    return json.loads(data.decode("utf-8"))


def run_via_daemon(script, argv):
    """Used by frontends under $CU_SESSION=1. Prints the op's JSON to
    stdout and exits with its implied status."""
    d = _daemon_info() or _spawn_daemon()
    if d is None:
        print(json.dumps({"ok": False, "error": "cu daemon unavailable"}))
        sys.exit(1)
    try:
        r = _request(d, {"script": script, "argv": argv})
    except Exception as e:
        print(json.dumps({"ok": False,
                          "error": f"daemon request failed: {e}"}))
        sys.exit(1)
    out = r.get("output")
    if out:
        print(out)
        try:
            sys.exit(0 if json.loads(out).get("ok") else 1)
        except Exception:
            sys.exit(0)
    print(json.dumps({"ok": False,
                      "error": r.get("error", "empty daemon response")}))
    sys.exit(1)
