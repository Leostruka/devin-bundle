"""dma ws_probe: testa handshake WebSocket sem auth (CSWSH / auth lead).

Faz SO o upgrade handshake (GET + cabecalhos WS). Se o endpoint
responde 101 sem credencial, auth do socket e' um lead. Com --origin
arbitrario + 101 = cross-site websocket hijacking candidato.

Requer --scope como todo tool que toca rede. ws(s) conta contra a
mesma allowlist do host http correspondente.

Uso:
  python ws_probe.py --scope scope.md --url ws://app/socket
  python ws_probe.py --scope scope.md --url wss://rt.x/socket \
      --origin https://evil.test --header-file headers.txt
"""
import argparse
import base64
import hashlib
import os
import socket
import ssl
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import allowed, load_scope, jwrite, die  # noqa: E402
from probe import load_extra_headers  # noqa: E402

WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def handshake(url, timeout, origin, extra_headers):
    p = urlparse(url)
    scheme = "https" if p.scheme in ("wss", "https") else "http"
    host, port = p.hostname, p.port or (443 if scheme == "https" else 80)
    path = (p.path or "/") + ("?" + p.query if p.query else "")
    key = base64.b64encode(os.urandom(16)).decode()
    lines = [f"GET {path} HTTP/1.1",
             f"Host: {host}:{port}",
             "Upgrade: websocket",
             "Connection: Upgrade",
             f"Sec-WebSocket-Key: {key}",
             "Sec-WebSocket-Version: 13"]
    if origin:
        lines.append(f"Origin: {origin}")
    for k, v in (extra_headers or {}).items():
        lines.append(f"{k}: {v}")
    raw = "\r\n".join(lines) + "\r\n\r\n"

    sock = socket.create_connection((host, port), timeout=timeout)
    if scheme == "https":
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(sock, server_hostname=host)
    sock.sendall(raw.encode())
    resp = b""
    while b"\r\n\r\n" not in resp and len(resp) < 8192:
        chunk = sock.recv(4096)
        if not chunk:
            break
        resp += chunk
    sock.close()
    head = resp.split(b"\r\n\r\n")[0].decode("utf-8", "replace")
    status = int(head.split()[1]) if head.split()[1:2] else 0
    hdrs = {}
    for l in head.split("\r\n")[1:]:
        if ":" in l:
            k, v = l.split(":", 1)
            hdrs[k.strip().lower()] = v.strip()
    expect = base64.b64encode(
        hashlib.sha1((key + WS_MAGIC).encode()).digest()).decode()
    return {"status": status, "headers": hdrs,
            "accept_valid": hdrs.get("sec-websocket-accept") == expect,
            "first_line": head.split("\r\n")[0]}


def main():
    ap = argparse.ArgumentParser(description="dma ws_probe (handshake only)")
    ap.add_argument("--scope", required=True)
    ap.add_argument("--url", required=True, help="ws:// ou wss://")
    ap.add_argument("--origin", help="Origin arbitrario (teste CSWSH)")
    ap.add_argument("--auth-env", metavar="VAR[:Header]",
                    help="header de auth via variavel de ambiente")
    ap.add_argument("--header-file", help="arquivo 'Nome: valor' por linha")
    ap.add_argument("--timeout", type=float, default=10)
    ap.add_argument("--out",
                    default=os.path.join(".devin/scratch", "dma", "ws.jsonl"))
    a = ap.parse_args()

    http_equiv = a.url.replace("wss://", "https://").replace("ws://", "http://")
    allow, deny = load_scope(a.scope)
    ok, why = allowed(http_equiv, allow, deny)
    if not ok:
        die(f"fora do escopo ({why}): {a.url}")

    extra = load_extra_headers(a.auth_env, a.header_file)
    try:
        r = handshake(a.url, a.timeout, a.origin, extra)
    except Exception as e:  # noqa: BLE001
        jwrite(a.out, {"url": a.url, "error": str(e)})
        die(f"handshake falhou: {e}")

    rec = {"url": a.url, "origin": a.origin, **r}
    jwrite(a.out, rec)
    if r["status"] == 101 and r["accept_valid"]:
        auth_note = "sem cookie/auth no handshake"
        if a.origin:
            auth_note += f" + Origin {a.origin} aceito = CSWSH candidato"
        print(f"[ws] 101 SWITCHING PROTOCOLS {a.url} | {auth_note}")
    else:
        print(f"[ws] {r['status']} {a.url} (handshake rejeitado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
