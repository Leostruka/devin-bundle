#!/usr/bin/env python3
"""selftest - smoke test for agent-rts (GDD section 11).

Boots server.py on an ephemeral port against a throwaway --root, then
asserts: /health, /snapshot schema, /telemetry sections, WS upgrade with
hello+snapshot frames, static index.html, /intent file creation, /cmd
refresh_repo, /decisions 404, /event append, /score.

  selftest.py [--keep]
"""
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "server.py")
PASS, FAIL = "PASS", "FAIL"
_results = []


def check(name, cond, extra=""):
    _results.append((name, bool(cond), extra))
    print("%s %s%s" % (PASS if cond else FAIL, name,
                       " - " + str(extra)[:120] if extra and not cond
                       else ""))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def get(port, path, timeout=10):
    try:
        with urllib.request.urlopen(
                "http://127.0.0.1:%d%s" % (port, path),
                timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}
    except Exception as e:
        return None, {"error": str(e)}


def post(port, path, body, timeout=30):
    req = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (port, path),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}


def ws_client(port):
    """Minimal WS client: handshake, then read text frames."""
    import base64
    key = base64.b64encode(os.urandom(16)).decode()
    s = socket.create_connection(("127.0.0.1", port), timeout=10)
    req = ("GET /ws HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\n"
           "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
           "Sec-WebSocket-Version: 13\r\n\r\n" % key)
    s.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)
    head, _, rest = buf.partition(b"\r\n\r\n")
    if b"101" not in head.split(b"\r\n")[0]:
        s.close()
        return None, []
    s.settimeout(10)

    def read(n):
        b = rest[:0]
        while len(b) < n:
            chunk = s.recv(n - len(b))
            if not chunk:
                return None
            b += chunk
        return b

    frames = []
    pending = bytearray(rest)

    def next_frame():
        while True:
            if len(pending) >= 2:
                ln = pending[1] & 0x7F
                need = 2 + (2 if ln == 126 else 8 if ln == 127 else 0)
                if len(pending) >= need:
                    if ln == 126:
                        ln = struct.unpack("!H", pending[2:4])[0]
                    elif ln == 127:
                        ln = struct.unpack("!Q", pending[2:10])[0]
                    if len(pending) >= need + ln:
                        data = bytes(pending[need:need + ln])
                        del pending[:need + ln]
                        return data
            chunk = s.recv(65536)
            if not chunk:
                return None
            pending.extend(chunk)

    for _ in range(4):
        f = next_frame()
        if f is None:
            break
        try:
            frames.append(json.loads(f.decode("utf-8")))
        except Exception:
            pass
        if len(frames) >= 2:
            break
    return s, frames


def main():
    keep = "--keep" in sys.argv
    port = free_port()
    root = tempfile.mkdtemp(prefix="agent-rts-test-")
    os.makedirs(os.path.join(root, ".devin", "rts"), exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--port", str(port),
         "--root", root, "--no-browser"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        ok = False
        for _ in range(60):
            code, body = get(port, "/health", timeout=2)
            if code == 200 and body.get("ok"):
                ok = True
                break
            time.sleep(0.25)
        check("server boots + /health", ok)

        code, snap = get(port, "/snapshot")
        check("/snapshot schema", code == 200 and all(
            k in snap for k in ("ts", "world", "repo", "decisions",
                                "intents")), code)

        code, tel = get(port, "/telemetry")
        check("/telemetry sections", code == 200 and all(
            k in tel for k in ("git", "issues", "forge", "ledgers",
                               "gas", "supply")), code)

        sock, frames = ws_client(port)
        types = [f.get("type") for f in frames]
        check("WS hello+snapshot", sock is not None and
              "hello" in types and "snapshot" in types, types)
        snapf = next((f for f in frames
                      if f.get("type") == "snapshot"), {})
        check("WS snapshot has world+repo",
              "world" in snapf and "repo" in snapf,
              list(snapf.keys())[:8])

        code, raw = get(port, "/")
        check("index.html served", code == 200 and
              "agent-rts" in str(raw), code)

        code, raw = get(port, "/js/main.js")
        check("js module served", code == 200 and
              "Scene3D" in str(raw), code)
        vcode, _v = get(port, "/vendor/three.module.js")
        check("vendor three.js (bootstrap-run dependent)",
              vcode in (200, 404), vcode)

        code, res = post(port, "/intent",
                         {"kind": "order", "to": "all", "order": "move",
                          "x": 10, "y": 10})
        idir = os.path.join(root, ".devin", "rts", "intents")
        wrote = os.path.isdir(idir) and any(
            fn.endswith(".json") for fn in os.listdir(idir))
        check("POST /intent writes file", code == 200 and wrote,
              (code, res))

        code, res = post(port, "/cmd", {"cmd": "refresh_repo"})
        check("POST /cmd refresh_repo", code == 200 and res.get("ok")
              and "repo" in res, (code, str(res)[:80]))

        code, _res = post(port, "/decisions/nope/answer", {"choice": 0})
        check("decision answer 404", code == 404, code)

        evp = os.path.join(root, ".devin", "rts", "events.jsonl")
        before = os.path.getsize(evp) if os.path.isfile(evp) else 0
        code, _res = post(port, "/event", {"type": "test.ping"})
        after = os.path.getsize(evp) if os.path.isfile(evp) else 0
        check("POST /event appends log", code == 200 and after > before,
              code)

        code, res = get(port, "/score")
        check("/score", code == 200 and isinstance(res, dict), code)
    finally:
        proc.terminate()
        try:
            out = proc.communicate(timeout=5)[0] or ""
        except Exception:
            proc.kill()
            out = ""
        tb = "Traceback" in out
        check("no server tracebacks", not tb,
              out[-300:] if tb else "")
        if keep:
            print(out)
    n_fail = sum(1 for _n, ok, _e in _results if not ok)
    print("\n%d checks, %d failed" % (len(_results), n_fail))
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
