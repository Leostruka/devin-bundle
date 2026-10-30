"""dma shared helpers: scope allowlist parsing, secret masking, jsonl io.

Todas as tools que tocam rede carregam o contrato daqui. scope.md ausente
ou alvo fora da allowlist = recusa. Nao existe flag para burlar.
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

ALLOW_SECTIONS = {"allowlist", "allow", "alvos"}
DENY_SECTIONS = {"deny", "exclusoes", "fora"}


def load_scope(path):
    """Le scope.md. Secoes '## allowlist' e '## deny'/'## exclusoes',
    uma entrada por linha (bullet '- ' opcional, '```' e vazias ignoradas).

    Entrada = host ('example.com', '*.example.com'), 'host/path' ou
    URL completa ('https://app.example.com/v1/') = prefixo de path.
    """
    if not os.path.isfile(path):
        raise SystemExit(
            f"[dma] scope ausente: {path}. Feche o Passo 0 antes de tocar rede."
        )
    allow, deny = [], []
    section = None
    in_fence = False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if line.startswith("#"):
                name = line.lstrip("#").strip().lower().rstrip(":")
                section = (
                    "allow" if name in ALLOW_SECTIONS
                    else "deny" if name in DENY_SECTIONS
                    else None
                )
                continue
            if not line or line.startswith("<!--"):
                continue
            if line.startswith("- "):
                line = line[2:].strip()
            if not line:
                continue
            if section == "allow":
                allow.append(line)
            elif section == "deny":
                deny.append(line)
    if not allow:
        raise SystemExit(
            f"[dma] {path}: nenhuma entrada em '## allowlist'. "
            "Contrato vazio = zero request."
        )
    return allow, deny


def _host(url):
    return (urlparse(url).hostname or "").lower()


def _host_match(host, entry_host):
    entry_host = entry_host.lower().lstrip("*.")
    return host == entry_host or host.endswith("." + entry_host)


def _path_match(path, ep):
    """ep com '/' final = subarvore (prefixo). Sem '/' = exato ou segmento."""
    path = path or "/"
    if not ep or ep == "/":
        return True
    if ep.endswith("/"):
        return path.startswith(ep)
    return path == ep or path.startswith(ep + "/")


def entry_match(url, entry):
    """Uma entrada cobre url? Host exato/subdominio; path veja _path_match."""
    p = urlparse(url)
    host = _host(url)
    if not host:
        return False
    entry = entry.strip()
    if "://" in entry:
        e = urlparse(entry)
        if not _host_match(host, e.hostname or ""):
            return False
        return _path_match(p.path, e.path or "/")
    if "/" in entry:
        eh, _, ep = entry.partition("/")
        if not _host_match(host, eh):
            return False
        return _path_match(p.path, "/" + ep)
    return _host_match(host, entry)


def allowed(url, allow, deny):
    """Deny vence allow. Retorna (bool, motivo)."""
    for d in deny:
        if entry_match(url, d):
            return False, f"deny: {d}"
    for a in allow:
        if entry_match(url, a):
            return True, f"allow: {a}"
    return False, "fora da allowlist"


def mask(value, keep=4):
    """Nunca retorna o segredo inteiro: prefixo + tamanho."""
    s = str(value)
    if len(s) <= keep:
        return "*" * len(s)
    return f"{s[:keep]}{'*' * 4}({len(s)}ch)"


SECRET_RES = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("slack_token", re.compile(r"xox[bapors]-[A-Za-z0-9-]{10,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("stripe_key", re.compile(r"[sr]k_(?:live|test)_[0-9a-zA-Z]{16,}")),
    ("generic_secret", re.compile(
        r"(?i)(?:api[_-]?key|secret|token|passwo?rd|passwd|pwd|auth)"
        r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
    )),
]


def mask_secrets(text):
    """Aplica masking em todo segredo reconhecido dentro de um trecho."""
    out = text
    for _, rx in SECRET_RES:
        def _sub(m):
            return m.group(0)[:0] + mask(m.group(1) if m.lastindex else m.group(0))
        out = rx.sub(_sub, out)
    return out


def jwrite(path, obj):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")


def die(msg, code=2):
    print(f"[dma] {msg}", file=sys.stderr)
    raise SystemExit(code)
