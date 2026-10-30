"""dma probe: probes minimos read-only com allowlist enforced.

Contrato duro:
  - exige --scope apontando para scope.md com '## allowlist' preenchida
  - TODO request e validado contra allow/deny antes de sair
  - redirect NAO e seguido: Location fora do escopo = grava flag e PARA
    o batch (condicao de parada da skill)
  - metodos permitidos: GET, HEAD, OPTIONS. Nada de POST.
  - segredos em body snippet sao mascarados antes de gravar

Uso:
  python probe.py candidates.txt --scope .devin/scratch/dma/scope.md \
      --base https://app.example.com --delay 2 --out .devin/scratch/dma/probes.jsonl
  python probe.py paths.txt --scope scope.md --base https://x --origin https://evil.test
"""
import argparse
import hashlib
import http.client
import json
import os
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import allowed, load_scope, mask, mask_secrets, jwrite, die  # noqa: E402

UA = "dma-probe/1.0 (authorized, read-only)"
METHODS = {"GET", "HEAD", "OPTIONS"}
MAX_BODY = 512 * 1024
SNIPPET = 400
SEC_HEADERS = ["content-security-policy", "x-frame-options",
               "x-content-type-options", "strict-transport-security",
               "referrer-policy", "permissions-policy"]

_DNS_CACHE = {}
_CONN_POOL = {}

SKELETON_PATHS = [
    "/.git/HEAD", "/.git/config", "/.env", "/.env.local",
    "/.env.production", "/.aws/credentials", "/.npmrc", "/.htpasswd",
    "/web.config", "/backup.zip", "/dump.sql", "/phpinfo.php",
    "/server-status", "/actuator", "/actuator/env", "/metrics",
    "/swagger.json", "/swagger-ui.html", "/openapi.json",
    "/api-docs", "/v2/api-docs", "/graphql", "/graphiql",
    "/crossdomain.xml", "/elmah.axd", "/trace.axd", "/debug/",
    "/_profiler/", "/adminer.php", "/phpmyadmin/", "/robots.txt",
    "/sitemap.xml", "/package.json", "/composer.json",
]


def resolve_host(host):
    """Resolve uma vez por host e cacheia. localhost no Windows resolve
    lento (::1 primeiro); usar IP direto corta ~2s por request."""
    if host not in _DNS_CACHE:
        try:
            infos = socket.getaddrinfo(host, None, socket.AF_INET)
            _DNS_CACHE[host] = infos[0][4][0] if infos else host
        except OSError:
            _DNS_CACHE[host] = host
    return _DNS_CACHE[host]


def get_conn(p, timeout):
    """Pool de conexoes por (scheme, host, port). HTTP conecta no IP
    resolvido com Host original; HTTPS mantem hostname (SNI/cert)."""
    key = (p.scheme, p.hostname, p.port)
    conn = _CONN_POOL.get(key)
    if conn is not None:
        return conn
    port = p.port or (443 if p.scheme == "https" else 80)
    if p.scheme == "https":
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(p.hostname, port,
                                           timeout=timeout, context=ctx)
    else:
        conn = http.client.HTTPConnection(resolve_host(p.hostname), port,
                                          timeout=timeout)
    _CONN_POOL[key] = conn
    return conn


def normalize(cand, base):
    cand = cand.strip()
    if not cand or cand.startswith("#"):
        return None
    if cand.startswith("://"):
        cand = "http" + cand
    if "://" not in cand:
        if not base:
            die(f"candidato relativo sem --base: {cand}")
        cand = urljoin(base.rstrip("/") + "/", cand.lstrip("/"))
    return cand


def one_request(url, method, timeout, origin=None, extra_headers=None):
    """Um request, sem seguir redirect. Retorna dict de resultado."""
    p = urlparse(url)
    path = (p.path or "/") + ("?" + p.query if p.query else "")
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if p.scheme == "http":
        host_hdr = p.hostname + (f":{p.port}" if p.port and p.port != 80 else "")
        headers["Host"] = host_hdr
    if origin:
        headers["Origin"] = origin
    if extra_headers:
        headers.update(extra_headers)
    conn = get_conn(p, timeout)
    t0 = time.time()
    try:
        conn.request(method, path, headers=headers)
        r = conn.getresponse()
        body = r.read(MAX_BODY) if method != "HEAD" else b""
    except (http.client.HTTPException, OSError) as e:
        # conexao morta no pool: fecha e tenta uma vez com conexao nova
        key = (p.scheme, p.hostname, p.port)
        try:
            _CONN_POOL.pop(key).close()
        except (KeyError, OSError):
            pass
        conn = get_conn(p, timeout)
        conn.request(method, path, headers=headers)
        r = conn.getresponse()
        body = r.read(MAX_BODY) if method != "HEAD" else b""
    dt = int((time.time() - t0) * 1000)
    hdrs = {}
    cookies = []
    for k, v in r.getheaders():
        k = k.lower()
        if k == "set-cookie":
            cookies.append(v)
        hdrs[k] = v
    if r.will_close:
        try:
            _CONN_POOL.pop((p.scheme, p.hostname, p.port)).close()
        except (KeyError, OSError):
            pass
    return {
        "status": r.status, "reason": r.reason, "time_ms": dt,
        "len": len(body), "body": body, "headers": hdrs,
        "set_cookies": cookies,
    }


def cookie_flags(raw):
    parts = [x.strip() for x in raw.split(";")]
    name = parts[0].split("=", 1)[0] if parts else "?"
    low = raw.lower()
    return {
        "name": name,
        "secure": "secure" in low,
        "httponly": "httponly" in low,
        "samesite": ("samesite=" in low and
                     low.split("samesite=", 1)[1].split(";")[0].strip() or None),
    }


def load_extra_headers(auth_env, header_file):
    """Segredos NUNCA via argv: --auth-env le variavel de ambiente,
    --header-file le 'Nome: valor' por linha de um arquivo (gitignored)."""
    out = {}
    if auth_env:
        name, _, hdr = auth_env.partition(":")
        hdr = hdr or "Authorization"
        val = os.environ.get(name)
        if val is None:
            die(f"--auth-env: variavel '{name}' nao definida")
        out[hdr] = val
    if header_file:
        if not os.path.isfile(header_file):
            die(f"--header-file ausente: {header_file}")
        with open(header_file, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if ":" not in line:
                    die(f"--header-file linha {i} sem 'Nome: valor': "
                        "formato invalido")
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def probe(url, method, timeout, origin, extra_headers=None):
    res = one_request(url, method, timeout, origin, extra_headers)
    sent_secret_vals = [v for v in (extra_headers or {}).values()
                        if len(v) >= 8]
    h = res["headers"]
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": url, "method": method, "status": res["status"],
        "time_ms": res["time_ms"], "len": res["len"],
        "content_type": h.get("content-type"),
        "server": h.get("server"), "x_powered_by": h.get("x-powered-by"),
        "sec_headers": {k: (k in h) for k in SEC_HEADERS},
        "cookies": [cookie_flags(c) for c in res["set_cookies"]],
        "headers": h,
    }
    if origin:
        rec["cors"] = {
            "acao": h.get("access-control-allow-origin"),
            "acac": h.get("access-control-allow-credentials"),
            "reflected": h.get("access-control-allow-origin") == origin,
        }
    if res["status"] in (301, 302, 303, 307, 308):
        loc = h.get("location", "")
        rec["redirect_to"] = urljoin(url, loc) if loc else None
    if method == "GET" and res["body"]:
        rec["body_sha256"] = hashlib.sha256(res["body"]).hexdigest()[:16]
        snippet = res["body"][:SNIPPET].decode("utf-8", "replace")
        snippet = mask_secrets(snippet)
        for v in sent_secret_vals:
            snippet = snippet.replace(v, mask(v))
        rec["body_snippet"] = snippet
    return rec


def main():
    ap = argparse.ArgumentParser(description="dma probe (read-only, allowlist)")
    ap.add_argument("candidates", nargs="?", default=None,
                    help="arquivo com uma url/path por linha")
    ap.add_argument("--skeleton", action="store_true",
                    help="usa a lista embutida de arquivos/paineis sensiveis "
                         "como candidatos (precisa de --base)")
    ap.add_argument("--scope", required=True, help="scope.md (obrigatorio)")
    ap.add_argument("--base", help="base p/ paths relativos (https://host)")
    ap.add_argument("--method", default="GET", choices=sorted(METHODS))
    ap.add_argument("--delay", type=float, default=2.0,
                    help="segundos entre requests (default 2)")
    ap.add_argument("--timeout", type=float, default=10)
    ap.add_argument("--origin", help="envia Origin arbitrario (teste CORS)")
    ap.add_argument("--auth-env", metavar="VAR[:Header]",
                    help="header de auth vindo de variavel de ambiente "
                         "(default do header: Authorization)")
    ap.add_argument("--header-file", help="arquivo 'Nome: valor' por linha")
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--out",
                    default=os.path.join(".devin/scratch", "dma", "probes.jsonl"))
    a = ap.parse_args()

    allow, deny = load_scope(a.scope)
    extra_headers = load_extra_headers(a.auth_env, a.header_file)
    if a.base:
        ok, why = allowed(a.base, allow, deny)
        if not ok:
            die(f"--base fora do escopo ({why}): {a.base}")

    if a.skeleton:
        if not a.base:
            die("--skeleton precisa de --base")
        cands = list(SKELETON_PATHS)
        if a.candidates:
            with open(a.candidates, encoding="utf-8",
                      errors="replace") as fh:
                cands += [l for l in fh]
    else:
        if not a.candidates:
            die("informe candidates ou use --skeleton")
        with open(a.candidates, encoding="utf-8",
                  errors="replace") as fh:
            cands = [l for l in fh]
    print(f"[probe] {len(cands)} candidatos | scope: {len(allow)} allow"
          f" {len(deny)} deny | delay {a.delay}s")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    n_ok = n_skip = 0
    consecutive_5xx = 0
    for i, raw in enumerate(cands):
        if n_ok >= a.max:
            print(f"[probe] --max {a.max} atingido, parando")
            break
        url = normalize(raw, a.base)
        if not url:
            continue
        ok, why = allowed(url, allow, deny)
        if not ok:
            rec = {"url": url, "skipped": True, "reason": why}
            jwrite(a.out, rec)
            print(f"  SKIP {url} ({why})")
            n_skip += 1
            continue
        try:
            rec = probe(url, a.method, a.timeout, a.origin, extra_headers)
        except Exception as e:  # noqa: BLE001
            rec = {"url": url, "error": str(e)}
            jwrite(a.out, rec)
            print(f"  ERR  {url} -> {e}")
            consecutive_5xx = 0
            time.sleep(a.delay)
            continue
        jwrite(a.out, rec)
        n_ok += 1
        cors = ""
        if rec.get("cors") and rec["cors"]["reflected"]:
            cors = " | CORS REFLETE ORIGIN ARBITRARIO"
        print(f"  {rec['status']:>3} {url} ({rec['len']}b"
              f" {rec['time_ms']}ms){cors}")
        if rec.get("redirect_to"):
            ok2, why2 = allowed(rec["redirect_to"], allow, deny)
            if not ok2:
                jwrite(a.out, {"stop": True, "reason":
                               "redirect para fora do escopo",
                               "url": url, "to": rec["redirect_to"]})
                print(f"[probe] PARADA: {url} -> {rec['redirect_to']}"
                      f" ({why2}). Pergunte ao usuario.")
                return 3
        if rec["status"] == 429 or rec["status"] >= 500:
            consecutive_5xx += 1
            if consecutive_5xx >= 3:
                jwrite(a.out, {"stop": True, "reason":
                               "alvo degradando (429/5xx em cadeia)"})
                print("[probe] PARADA: alvo degradando (429/5xx x3)")
                return 3
        else:
            consecutive_5xx = 0
        if i < len(cands) - 1:
            time.sleep(a.delay)
    print(f"[probe] ok={n_ok} skip={n_skip} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
