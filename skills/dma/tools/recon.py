"""dma recon: coleta passiva. Zero pacotes no alvo.

Fontes publicas apenas:
  - crt.sh        (CT logs -> subdominios)
  - Wayback CDX   (URLs historicas)
  - dns.google    (DoH JSON -> A/AAAA/CNAME/TXT/MX/NS)

Uso:
  python recon.py --domain example.com --out .devin/scratch/dma/recon/
  python recon.py --domain example.com --skip wayback
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse

UA = {"User-Agent": "dma-recon/1.0 (authorized pentest, passive)"}
RRTYPES = ["A", "AAAA", "CNAME", "TXT", "MX", "NS"]


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def crtsh(domain):
    q = urllib.parse.quote(f"%.{domain}")
    data = json.loads(fetch(f"https://crt.sh/?q={q}&output=json"))
    names = set()
    for row in data:
        for n in str(row.get("name_value", "")).splitlines():
            n = n.strip().lstrip("*.")
            if n and n.endswith(domain) and " " not in n and "@" not in n:
                names.add(n)
        cn = str(row.get("common_name", "")).strip().lstrip("*.")
        if cn.endswith(domain) and " " not in cn and "@" not in cn:
            names.add(cn)
    return sorted(names)


def wayback(domain, limit=2000):
    q = urllib.parse.quote(f"{domain}/*")
    url = (
        "https://web.archive.org/cdx/search/cdx?url=" + q +
        "&output=text&fl=original&collapse=urlkey"
        f"&filter=statuscode:200&limit={limit}"
    )
    raw = fetch(url, timeout=60).decode("utf-8", "replace")
    return sorted({l.strip() for l in raw.splitlines() if l.strip()})


def doh(domain):
    out = {}
    for rt in RRTYPES:
        try:
            data = json.loads(fetch(
                f"https://dns.google/resolve?name={domain}&type={rt}"))
            out[rt] = sorted({
                a.get("data", "").rstrip(".") for a in data.get("Answer", [])
            })
        except Exception as e:  # noqa: BLE001 - registrar e seguir
            out[rt] = [f"erro: {e}"]
    return out


def dangling_cnames(dns_map):
    """CNAMEs que apontam para fora do dominio = candidatos a takeover.
    Anotar apenas; verificacao real e gated (Passo 5)."""
    sus = []
    markers = ("amazonaws", "azurewebsites", "cloudapp", "github.io",
               "herokuapp", "herokudns", "netlify", "vercel", "fastly",
               "cloudfront", "wpengine", "shopify", "zendesk", "status.io",
               "surge.sh", "bitbucket.io", "pages.dev", "webflow")
    for cname in dns_map.get("CNAME", []):
        for m in markers:
            if m in cname:
                sus.append(cname)
                break
    return sus


def resolve_live(names, workers=8):
    """Resolve nomes via DoH em paralelo (passivo: queries vao ao
    dns.google, nao ao alvo). Retorna {host: [ips]} dos que respondem."""
    from concurrent.futures import ThreadPoolExecutor

    def one(n):
        try:
            data = json.loads(fetch(
                f"https://dns.google/resolve?name={n}&type=A"))
            ips = [a.get("data") for a in data.get("Answer", [])
                   if a.get("type") == 1]
            return (n, ips) if ips else (n, None)
        except Exception:  # noqa: BLE001
            return (n, None)

    live = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, (n, ips) in enumerate(ex.map(one, names)):
            if ips:
                live[n] = ips
            if i % 50 == 49:
                print(f"[recon] resolve: {i + 1}/{len(names)}"
                      f" ({len(live)} vivos)")
    return live


def main():
    ap = argparse.ArgumentParser(description="dma recon passivo (zero pacote no alvo)")
    ap.add_argument("--domain", required=True)
    ap.add_argument("--out", default=os.path.join(".devin/scratch", "dma", "recon"))
    ap.add_argument("--limit", type=int, default=2000, help="limite wayback")
    ap.add_argument("--resolve", action="store_true",
                    help="resolve subdominios via DoH -> live_hosts.txt")
    ap.add_argument("--skip", nargs="*", default=[],
                    choices=["crtsh", "wayback", "dns"])
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    errors = {}

    if "crtsh" not in a.skip:
        try:
            subs = crtsh(a.domain)
            p = os.path.join(a.out, "subdomains.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("\n".join(subs) + "\n")
            print(f"[recon] crt.sh: {len(subs)} subdominios -> {p}")
            if a.resolve:
                live = resolve_live(subs)
                lp = os.path.join(a.out, "live_hosts.txt")
                with open(lp, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(sorted(live)) + "\n")
                jp = os.path.join(a.out, "live_hosts.json")
                with open(jp, "w", encoding="utf-8") as fh:
                    json.dump(live, fh, indent=2)
                print(f"[recon] {len(live)}/{len(subs)} vivos -> {lp}")
        except Exception as e:  # noqa: BLE001
            errors["crtsh"] = str(e)
            print(f"[recon] crt.sh FALHOU: {e}", file=sys.stderr)

    if "wayback" not in a.skip:
        try:
            urls = wayback(a.domain, a.limit)
            p = os.path.join(a.out, "wayback_urls.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("\n".join(urls) + "\n")
            print(f"[recon] wayback: {len(urls)} urls -> {p}")
        except Exception as e:  # noqa: BLE001
            errors["wayback"] = str(e)
            print(f"[recon] wayback FALHOU: {e}", file=sys.stderr)

    if "dns" not in a.skip:
        dns = doh(a.domain)
        cnames = dangling_cnames(dns)
        dns["_takeover_candidates"] = cnames
        p = os.path.join(a.out, "dns.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(dns, fh, indent=2, ensure_ascii=False)
        print(f"[recon] dns -> {p}"
              + (f" | takeover candidates: {len(cnames)}" if cnames else ""))

    if errors:
        ep = os.path.join(a.out, "errors.json")
        with open(ep, "w", encoding="utf-8") as fh:
            json.dump(errors, fh, indent=2)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
