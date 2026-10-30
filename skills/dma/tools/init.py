"""dma init: scaffold do Passo 0 + checagens de seguranca do artefato.

- cria .devin/scratch/dma/ (scope.md template, recon/)
- verifica se .devin/scratch/ esta gitignored (condicao de parada da skill)
- valida scope.md existente (allowlist vazia = contrato nao fechado)
- NUNCA sobrescreve scope.md existente

Uso:
  python init.py                    # no repo alvo
  python init.py --root /path/repo
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_scope  # noqa: E402

SCOPE_TEMPLATE = """# Contrato de escopo dma
# Preencher com o usuario ANTES de qualquer request no alvo.

## contrato
- modo: producao|staging|local
- janela:
- rate_max:
- duracao:
- contas autorizadas:

## allowlist
# host exato, *.dominio.com, host/path ou https://host/prefixo/
# (uma entrada por linha; deny vence allow)

## deny
# paths/hosts proibidos dentro do allowlist
"""


def git_ignored(root, path):
    """Retorna True/False; None se nao for repo git."""
    try:
        subprocess.run(
            ["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, check=True, timeout=10)
    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired):
        return None
    r = subprocess.run(
        ["git", "-C", root, "check-ignore", "-q", path],
        capture_output=True, timeout=10)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="dma init (scaffold Passo 0)")
    ap.add_argument("--root", default=".", help="raiz do projeto alvo")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    dma_dir = os.path.join(root, ".devin/scratch", "dma")
    os.makedirs(os.path.join(dma_dir, "recon"), exist_ok=True)
    print(f"[init] {dma_dir}")

    scope_path = os.path.join(dma_dir, "scope.md")
    if os.path.isfile(scope_path):
        print(f"[init] scope.md existe, nao sobrescrevo")
        try:
            allow, deny = load_scope(scope_path)
            print(f"[init] scope OK: {len(allow)} allow, {len(deny)} deny")
        except SystemExit as e:
            print(f"[init] scope INVALIDO: {e}")
    else:
        with open(scope_path, "w", encoding="utf-8") as fh:
            fh.write(SCOPE_TEMPLATE)
        print(f"[init] scope.md template criado — FECHE COM O USUARIO "
              "antes de request")

    ignored = git_ignored(root, ".devin/scratch")
    if ignored is None:
        print("[init] nao e repo git — sem risco de commitar artefato")
    elif ignored:
        print("[init] .devin/scratch/ gitignored — artefatos seguros")
    else:
        print("[init] !! .devin/scratch/ NAO esta gitignored.")
        print("       Artefato de pentest em repo rastreado vaza em commit.")
        print("       Adicione '.devin/scratch/' ao .gitignore ou mova para "
              "pasta temp fora do repo.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
