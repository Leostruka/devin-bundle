"""dma mine: mineracao de superficie sobre dumps coletados.

Le arquivos (dir recursivo ou lista) e extrai:
  endpoints   - paths /api/*, /vN/*, rotas SPA, action=, baseURL, ws(s)://
  urls        - URLs absolutas (agrupadas por host)
  hosts       - hosts internos/terceiros vistos
  secrets     - padroes trufflehog, SEMPRE mascarados (localizacao + prefixo)
  dom_sinks   - innerHTML, eval, v-html, postMessage sem origin, etc
  deser       - marcadores de desserializacao (rO0AB, __VIEWSTATE, O:)
  skeleton    - candidatos a arquivo/painel exposto (.git, .env, swagger...)

Saida: leads.json (linhas nao: um objeto com vetores) + resumo no stdout.
Offline: nao toca rede.

Uso:
  python mine.py .devin/scratch/dma/recon/ dump.js mirror/ --out .devin/scratch/dma/mine.json
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SECRET_RES, mask  # noqa: E402

TEXT_EXT = {
    ".js", ".mjs", ".ts", ".jsx", ".tsx", ".json", ".map", ".html", ".htm",
    ".txt", ".xml", ".conf", ".cfg", ".ini", ".env", ".yaml", ".yml",
    ".php", ".py", ".rb", ".java", ".go", ".cs", ".vue", ".svelte", "",
}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2",
            ".ttf", ".eot", ".pdf", ".zip", ".gz", ".mp4", ".webp"}

RX_ABS_URL = re.compile(r"https?://[^\s\"'<>)\]]{4,}")
RX_WS = re.compile(r"wss?://[^\s\"'<>)\]]{4,}")
RX_PATH = re.compile(r"[\"'](/(?:api|v\d+|rest|graphql|gql|auth|oauth|admin"
                     r"|internal|private|user|account|pay|billing|webhook"
                     r"|callback|upload|download|file|export|import|debug"
                     r"|actuator|metrics|health|status|config)"
                     r"[A-Za-z0-9_./{}?=&%:-]*)[\"']")
RX_GENERIC_PATH = re.compile(r"[\"'](/[A-Za-z0-9_][A-Za-z0-9_./-]{1,120})[\"']")
RX_BASEURL = re.compile(r"(?i)(?:baseurl|base_url|api_?url|endpoint)"
                        r"\s*[:=]\s*[\"']([^\"']+)[\"']")
RX_ACTION = re.compile(r"[?&]action=([A-Za-z0-9_-]+)")
RX_PARAM = re.compile(r"[?&]([A-Za-z_][A-Za-z0-9_]*)=")
RX_DOM_SINK = re.compile(
    r"(?i)(innerHTML|outerHTML|document\.write|insertAdjacentHTML|\beval\("
    r"|new Function|setTimeout\s*\(\s*[\"']|v-html|dangerouslySetInnerHTML"
    r"|\$\(.*\)\.html\(|postMessage\s*\(|location\.hash|location\.search"
    r"|document\.URL|window\.name)")
RX_POSTMSG_NOORIGIN = re.compile(r"postMessage\s*\([^,]+,\s*[\"']\*[\"']")
RX_DESER = re.compile(r"(rO0AB[A-Za-z0-9+/=]{6,}|__VIEWSTATE|__EVENTVALIDATION"
                      r"|O:\d+:\"[^\"]+\":\d+:|YTowOnt|\.deserialize\(|"
                      r"pickle\.loads|unserialize\s*\(|ObjectInputStream)")
RX_PROTOTYPE = re.compile(r"(__proto__|constructor\[|prototype\[|"
                          r"\[constructor\])")
RX_GRAPHQL = re.compile(r"(?i)(graphql|__schema|__type|query\s+\w+\s*\()")
RX_IDOR = re.compile(r"(/\d{1,12}([/?\"']|$)|[?&](id|uid|user|user_id|"
                     r"account|acct|doc|file|order|invoice|record|obj)"
                     r"[A-Za-z_]*=\w+|/\{?(id|uid|[A-Za-z_]+_id)\}?[/?\"'])")

SKELETON_PATHS = [
    "/.git/HEAD", "/.git/config", "/.env", "/.env.local", "/.env.production",
    "/env", "/.aws/credentials", "/.npmrc", "/.htpasswd", "/.htaccess",
    "/web.config", "/wp-config.php.bak", "/config.php.bak", "/backup.zip",
    "/backup.tar.gz", "/db.sql", "/dump.sql", "/phpinfo.php", "/info.php",
    "/server-status", "/server-info", "/actuator", "/actuator/health",
    "/actuator/env", "/actuator/heapdump", "/metrics", "/swagger.json",
    "/swagger-ui.html", "/swagger/", "/openapi.json", "/api-docs",
    "/v2/api-docs", "/graphql", "/graphiql", "/playground",
    "/.well-known/security.txt", "/crossdomain.xml", "/clientaccesspolicy.xml",
    "/elmah.axd", "/trace.axd", "/debug/", "/console/", "/_profiler/",
    "/telescope/", "/horizon/", "/__debug__/", "/admin/", "/adminer.php",
    "/phpmyadmin/", "/wp-admin/", "/wp-json/wp/v2/users", "/.DS_Store",
    "/sitemap.xml", "/robots.txt", "/security.txt", "/package.json",
    "/composer.json", "/yarn.lock", "/Dockerfile", "/docker-compose.yml",
]

MAX_FILE = 4 * 1024 * 1024


def iter_files(roots):
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for dp, _, fns in os.walk(root):
            for fn in fns:
                yield os.path.join(dp, fn)


def scan_file(path, acc):
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXT:
        return
    try:
        if os.path.getsize(path) > MAX_FILE:
            return
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return

    for m in RX_ABS_URL.finditer(text):
        u = m.group(0).rstrip(".,;'\"")
        acc["urls"].add(u)
        h = urlparse(u).hostname
        if h:
            acc["hosts"].add(h.lower())
    for m in RX_WS.finditer(text):
        acc["endpoints"].add(m.group(0).rstrip(".,;'\""))
        acc["ws"] = True
    for rx in (RX_PATH, RX_GENERIC_PATH):
        for m in rx.finditer(text):
            acc["endpoints"].add(m.group(1))
    for m in RX_BASEURL.finditer(text):
        acc["endpoints"].add(m.group(1))
    for m in RX_ACTION.finditer(text):
        acc["actions"].add(m.group(1))
    for m in RX_PARAM.finditer(text):
        acc["params"].add(m.group(1))
    for m in RX_GRAPHQL.finditer(text):
        acc["graphql_seen"] = True
        break

    for name, rx in SECRET_RES:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            acc["secrets"].append({
                "type": name, "file": path, "line": line,
                "value": mask(m.group(1) if m.lastindex else m.group(0)),
            })
    for m in RX_DOM_SINK.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        acc["dom_sinks"].append({
            "sink": m.group(1), "file": path, "line": line,
        })
    for m in RX_POSTMSG_NOORIGIN.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        acc["dom_sinks"].append({
            "sink": "postMessage('*') sem origin check", "file": path,
            "line": line,
        })
    for m in RX_DESER.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        acc["deser"].append({
            "marker": m.group(0)[:40], "file": path, "line": line,
        })
    for m in RX_PROTOTYPE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        acc["proto"].append({"file": path, "line": line})

    low = text.lower()
    for cand in SKELETON_PATHS:
        if cand.lower() in low:
            acc["skeleton_refs"].append({"path": cand, "file": path})


def main():
    ap = argparse.ArgumentParser(description="dma mine: mineracao offline de dumps")
    ap.add_argument("roots", nargs="+", help="arquivos/dirs a minerar")
    ap.add_argument("--out", default=os.path.join(".devin/scratch", "dma", "mine.json"))
    a = ap.parse_args()

    acc = {"urls": set(), "hosts": set(), "endpoints": set(),
           "actions": set(), "params": set(),
           "secrets": [], "dom_sinks": [], "deser": [], "proto": [],
           "skeleton_refs": [], "ws": False, "graphql_seen": False}
    n = 0
    for f in iter_files(a.roots):
        if os.path.splitext(f)[1].lower() in TEXT_EXT or True:
            scan_file(f, acc)
            n += 1

    # endpoints vindos de urls absolutas tambem entram como path
    for u in list(acc["urls"]):
        p = urlparse(u)
        if p.path and p.path != "/":
            acc["endpoints"].add(p.path)

    # candidatos a IDOR: endpoint com segmento numerico ou param de id
    idor = [e for e in acc["endpoints"] if RX_IDOR.search(e)]
    idor += [u for u in acc["urls"] if RX_IDOR.search(u)]

    out = {
        "files_scanned": n,
        "hosts": sorted(acc["hosts"]),
        "urls": sorted(acc["urls"]),
        "endpoints": sorted(acc["endpoints"]),
        "actions": sorted(acc["actions"]),
        "params": sorted(acc["params"]),
        "secrets": acc["secrets"],
        "dom_sinks": acc["dom_sinks"],
        "deserialization_markers": acc["deser"],
        "prototype_pollution_hints": acc["proto"],
        "skeleton_refs_seen_in_dumps": acc["skeleton_refs"],
        "websocket_seen": acc["ws"],
        "graphql_seen": acc["graphql_seen"],
        "idor_candidates": sorted(set(idor)),
        "skeleton_candidates": SKELETON_PATHS,
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print(f"[mine] {n} arquivos -> {a.out}")
    print(f"  endpoints: {len(out['endpoints'])} | urls: {len(out['urls'])}"
          f" | hosts: {len(out['hosts'])} | params: {len(out['params'])}")
    print(f"  secrets (mascarados): {len(out['secrets'])}"
          f" | dom_sinks: {len(out['dom_sinks'])}"
          f" | deser: {len(out['deserialization_markers'])}"
          f" | proto: {len(out['prototype_pollution_hints'])}")
    if acc["ws"]:
        print("  websocket endpoint detectado")
    if acc["graphql_seen"]:
        print("  graphql detectado (introspection/suggest/depth = Passo 5)")
    if out["idor_candidates"]:
        print(f"  idor_candidates: {len(out['idor_candidates'])}"
              " (alimentam oracle.py)")
    if out["secrets"]:
        print("  !! segredos: valores NUNCA gravados em claro, so localizacao")
    return 0


if __name__ == "__main__":
    sys.exit(main())
