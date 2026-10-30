"""dma gql_probe: sonda GraphQL com o minimo de trafego.

Dois probes GET (read-only) por endpoint:
  1. introspection minima: ?query={__schema{queryType{name}}}
     200 com data = introspection LIGADA (lead direto)
  2. suggestion oracle: ?query={campoInexistente}
     resposta com "Did you mean" = field suggestion ativa

Nada de POST, nada de query de mutacao, nada de dump de schema.
Dump completo e batching sao Passo 5 (gated).

Uso:
  python gql_probe.py --scope scope.md --url https://app/graphql
"""
import argparse
import json
import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import allowed, load_scope, jwrite, mask_secrets, die  # noqa: E402
from probe import one_request  # noqa: E402


def gql_get(url, query, timeout):
    sep = "&" if "?" in url else "?"
    full = f"{url}{sep}query={quote(query)}"
    return full, one_request(full, "GET", timeout)


def main():
    ap = argparse.ArgumentParser(description="dma gql_probe (GET read-only)")
    ap.add_argument("--scope", required=True)
    ap.add_argument("--url", required=True, help="endpoint graphql")
    ap.add_argument("--timeout", type=float, default=10)
    ap.add_argument("--out",
                    default=os.path.join(".devin/scratch", "dma", "gql.jsonl"))
    a = ap.parse_args()

    allow, deny = load_scope(a.scope)
    ok, why = allowed(a.url, allow, deny)
    if not ok:
        die(f"fora do escopo ({why}): {a.url}")

    findings = []
    full, r = gql_get(a.url, "{__schema{queryType{name}}}", a.timeout)
    body = r["body"][:2000].decode("utf-8", "replace")
    intro = r["status"] == 200 and '"__schema"' in body
    rec = {"probe": "introspection", "url": full, "status": r["status"],
           "introspection_on": intro,
           "snippet": mask_secrets(body[:400])}
    jwrite(a.out, rec)
    print(f"[gql] introspection: {'LIGADA' if intro else 'off/erro'}"
          f" ({r['status']})")
    if intro:
        findings.append("introspection habilitada")

    full, r = gql_get(a.url, "{dmaCampoInexistenteXyz}", a.timeout)
    body = r["body"][:2000].decode("utf-8", "replace")
    suggest = "did you mean" in body.lower() or "did you mean" in body
    rec = {"probe": "field_suggestion", "url": full, "status": r["status"],
           "suggestion_on": suggest,
           "snippet": mask_secrets(body[:400])}
    jwrite(a.out, rec)
    print(f"[gql] field suggestion: {'ATIVA' if suggest else 'off'}")
    if suggest:
        findings.append("field suggestion ativa (enum schema via typo)")

    if not findings:
        print("[gql] nenhum lead — introspection e suggestion fechadas")
    else:
        print(f"[gql] leads: {', '.join(findings)} — dump/schema e "
              "batching sao Passo 5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
