"""dma audit: transforma probes.jsonl em vereditos prontos p/ findings.

Le um ou mais probes.jsonl e emite tabela markdown + lista de leads:
headers de seguranca ausentes, cookies sem flags, CORS refletindo
origin arbitrario, servidor/tech exposto, redirects suspeitos.

Offline: nao toca rede. So le jsonl.

Uso:
  python audit.py .devin/scratch/dma/probes.jsonl
  python audit.py probes.jsonl cors.jsonl --out audit.md
"""
import argparse
import json
import sys
from urllib.parse import urlparse

SEC_NAMES = {
    "content-security-policy": "CSP",
    "x-frame-options": "XFO",
    "x-content-type-options": "XCTO",
    "strict-transport-security": "HSTS",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
}


def analyze(rec):
    leads = []
    url = rec.get("url", "?")
    if rec.get("skipped") or rec.get("error") or rec.get("stop"):
        return leads
    sec = rec.get("sec_headers") or {}
    missing = [SEC_NAMES[k] for k, v in sec.items() if not v]
    if missing:
        leads.append(("headers", url,
                      "faltam: " + ", ".join(missing)))
    for c in rec.get("cookies") or []:
        miss = []
        if not c.get("httponly"):
            miss.append("HttpOnly")
        if not c.get("secure"):
            miss.append("Secure")
        if not c.get("samesite"):
            miss.append("SameSite")
        if miss:
            leads.append(("cookie", url,
                          f"{c.get('name')} sem {'/'.join(miss)}"))
    cors = rec.get("cors")
    if cors and cors.get("reflected"):
        cred = " com credentials" if cors.get("acac") == "true" else ""
        leads.append(("CORS", url,
                      f"reflete Origin arbitrario{cred}"))
    if rec.get("server") or rec.get("x_powered_by"):
        leads.append(("fingerprint", url,
                      f"server={rec.get('server')}"
                      f" x-powered-by={rec.get('x_powered_by')}"))
    if rec.get("redirect_to"):
        leads.append(("redirect", url,
                      f"{rec['status']} -> {rec['redirect_to']}"))
    return leads


def main():
    ap = argparse.ArgumentParser(description="dma audit: jsonl -> vereditos")
    ap.add_argument("jsonl", nargs="+")
    ap.add_argument("--out", default=None, help="markdown (default stdout)")
    a = ap.parse_args()

    recs, leads, tech = [], [], {}
    for path in a.jsonl:
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"[audit] nao abre {path}: {e}", file=sys.stderr)
            continue
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("stop") or rec.get("oracle"):
                continue
            recs.append(rec)
            leads += analyze(rec)
            for k in ("server", "x_powered_by"):
                if rec.get(k):
                    tech.setdefault(rec[k], set()).add(
                        urlparse(rec.get("url", "")).hostname or "?")
        fh.close()

    ok = sum(1 for r in recs if r.get("status"))
    lines = [f"# audit dma — {len(recs)} registros, {ok} respostas",
             "",
             "## tech fingerprint",
             ""]
    if tech:
        for name, hosts in sorted(tech.items()):
            lines.append(f"- `{name}` ({', '.join(sorted(hosts))})")
    else:
        lines.append("- nada exposto")
    lines += ["", "## leads", ""]
    if leads:
        lines += ["| tipo | url | detalhe |", "|---|---|---|"]
        for t, u, d in leads:
            lines.append(f"| {t} | {u} | {d} |")
    else:
        lines.append("nenhum lead de header/cookie/cors")
    out = "\n".join(lines) + "\n"

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        print(f"[audit] {len(leads)} leads -> {a.out}")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
