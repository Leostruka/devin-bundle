"""dma oracle: oraculo de existencia IDOR com veredito de diff.

Mesma URL, ids diferentes; compara status/len/body_sha256/tempo e diz
se existe oraculo ("resposta distingue valido de invalido"). GET only.

Uso:
  python oracle.py --scope scope.md --base https://app \
      --url "/api/users/{id}" --ids 42,999999,424242 --delay 2

Git Bash/MSYS converte argv que comeca com '/' em path do Windows —
passe URL absoluta ou MSYS_NO_PATHCONV=1.

O primeiro id e' a baseline (id valido/autorizado). Diffs grandes de
tempo sao ruido comum: so conta se > 2x baseline ou +300ms.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import allowed, load_scope, jwrite, die  # noqa: E402
from probe import one_request, probe  # noqa: E402


def diff_fields(base, rec):
    d = []
    if rec["status"] != base["status"]:
        d.append(f"status {base['status']}->{rec['status']}")
    if rec.get("body_sha256") != base.get("body_sha256"):
        d.append("body")
    if abs(rec["len"] - base["len"]) > 64:
        d.append(f"len {base['len']}->{rec['len']}")
    bt = base["time_ms"]
    if rec["time_ms"] > max(2 * bt, bt + 300):
        d.append(f"time {bt}ms->{rec['time_ms']}ms")
    return d


def main():
    ap = argparse.ArgumentParser(description="dma oracle (IDOR existence)")
    ap.add_argument("--scope", required=True)
    ap.add_argument("--url", required=True,
                    help="URL ou path com placeholder {id}")
    ap.add_argument("--ids", required=True,
                    help="csv; o primeiro e' a baseline (id valido)")
    ap.add_argument("--base", help="base p/ --url relativo")
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--timeout", type=float, default=10)
    ap.add_argument("--out",
                    default=os.path.join(".devin/scratch", "dma", "oracle.jsonl"))
    a = ap.parse_args()

    if "{id}" not in a.url and "{ID}" not in a.url:
        die("--url precisa de placeholder {id}")
    allow, deny = load_scope(a.scope)
    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    if len(ids) < 2:
        die("preciso de >= 2 ids (baseline + comparacao)")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    recs = []
    for idv in ids:
        url = a.url.replace("{id}", idv).replace("{ID}", idv)
        if "://" not in url:
            if not a.base:
                die("url relativa sem --base")
            base = a.base.rstrip("/")
            url = base + (url if url.startswith("/") else "/" + url)
        ok, why = allowed(url, allow, deny)
        if not ok:
            jwrite(a.out, {"url": url, "skipped": True, "reason": why})
            print(f"  SKIP {url} ({why})")
            continue
        try:
            rec = probe(url, "GET", a.timeout, None)
        except Exception as e:  # noqa: BLE001
            rec = {"url": url, "id": idv, "error": str(e)}
            jwrite(a.out, rec)
            print(f"  ERR  {url} -> {e}")
            continue
        rec["id"] = idv
        recs.append(rec)
        jwrite(a.out, rec)
        print(f"  {rec['status']:>3} id={idv} ({rec['len']}b"
              f" {rec['time_ms']}ms sha={rec.get('body_sha256')})")
        time.sleep(a.delay)

    if len(recs) < 2:
        die("menos de 2 respostas validas — oraculo inconclusivo")
    base = recs[0]
    verdict = {"baseline_id": base["id"], "comparisons": []}
    oracle = False
    for r in recs[1:]:
        d = diff_fields(base, r)
        verdict["comparisons"].append({"id": r["id"], "diffs": d})
        if any(x.startswith(("status", "body", "len")) for x in d):
            oracle = True
    verdict["oracle_exists"] = oracle
    jwrite(a.out, {"oracle": verdict})
    print(f"[oracle] {'EXISTE' if oracle else 'NAO detectado'}"
          f" (baseline id={base['id']}) -> {a.out}")
    return 0 if oracle else 1


if __name__ == "__main__":
    sys.exit(main())
