"""Internal-protocol recon proxy.

Run:  python recon/forward.py --port 8642
Then: WINDSURF_API_SERVER_URL=http://127.0.0.1:8642 devin -p "hi"

Forwards every request to https://server.codeium.com verbatim, logs
method/path/headers/body for both directions to forward-<ts>.jsonl.
Auth headers are redacted in the log; bodies are base64 (protobuf).
"""

import base64
import http.client
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UPSTREAM_HOST = "server.codeium.com"
OUT = Path(__file__).resolve().parent / f"forward-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
PORT = 8642
_lock = threading.Lock()

REDACT = {"authorization", "x-api-key", "cookie"}


def _emit(rec: dict) -> None:
    with _lock:
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _relay(self, method: str) -> None:
        n = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(n) if n else b""
        rid = f"{int(time.time()*1000)}"
        auth = self.headers.get("authorization", "")
        auth_shape = None
        if auth.startswith("Basic "):
            try:
                raw = base64.b64decode(auth[6:] + "==").decode("utf-8", "replace")
                parts = raw.split(":")
                auth_shape = {"scheme": "Basic", "nparts": len(parts),
                              "p0len": len(parts[0]), "p0head": parts[0][:12],
                              "p1len": len(parts[1]) if len(parts) > 1 else 0}
            except Exception:
                auth_shape = {"scheme": "Basic", "decode": "fail"}
        elif auth:
            auth_shape = {"scheme": auth.split(" ")[0], "len": len(auth)}
        _emit({
            "ts": time.time(), "dir": "req", "rid": rid,
            "method": method, "path": self.path,
            "headers": {k: ("<REDACTED>" if k.lower() in REDACT else v)
                        for k, v in self.headers.items()},
            "auth_shape": auth_shape,
            "body_b64": base64.b64encode(body).decode(), "body_len": n,
        })
        print(f"[fwd] -> {method} {self.path} len={n}", flush=True)

        hdrs = {k: v for k, v in self.headers.items()
                if k.lower() not in ("host", "content-length", "accept-encoding")}
        conn = http.client.HTTPSConnection(UPSTREAM_HOST, 443, timeout=120)
        try:
            conn.request(method, self.path, body=body, headers=hdrs)
            resp = conn.getresponse()
            status = resp.status
            rh = dict(resp.getheaders())
            data = resp.read()
        except Exception as e:  # noqa: BLE001 - recon tool
            _emit({"ts": time.time(), "dir": "err", "rid": rid, "error": str(e)})
            self.send_error(502, str(e))
            return
        finally:
            conn.close()

        _emit({
            "ts": time.time(), "dir": "resp", "rid": rid,
            "status": status,
            "headers": {k: v for k, v in rh.items() if k.lower() not in REDACT},
            "body_b64": base64.b64encode(data).decode(), "body_len": len(data),
        })
        print(f"[fwd] <- {status} {self.path} len={len(data)}", flush=True)

        self.send_response(status)
        for k, v in rh.items():
            if k.lower() in ("transfer-encoding", "connection", "content-length"):
                continue
            self.send_header(k, v)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_GET = lambda s: H._relay(s, "GET")
    do_POST = lambda s: H._relay(s, "POST")
    do_PUT = lambda s: H._relay(s, "PUT")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else PORT
    print(f"[fwd] :{port} -> https://{UPSTREAM_HOST} log={OUT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
