# Correções das issues críticas do AUDIT_REPORT

## Input

- `AUDIT_REPORT.md` (`.devin/notes/audit-report/AUDIT_REPORT.md`) identificou 2 issues críticas:
  - `1.3.3`: `export` com `-NoMask`/`--no-mask` pode commitar/pushar secrets.
  - `5.3.1`: MCP `atlassian` usa `transport: http` com URL `https://`.

## Authorized scope

- Corrigir `1.3.3` e `5.3.1` no branch `3-news`.
- Não modificar outros arquivos além do necessário.
- Atualizar `AUDIT_REPORT.md` para refletir as correções.
- Rodar `python audit.py` e `python -m pytest` antes de commit.

## Verification functions

VF1: `export.ps1 -NoMask -Push` é bloqueado antes do push. ✅
VF2: `export.sh --no-mask --push` é bloqueado antes do push. ✅
VF3: `mcp_config.json` tem `transport: https` consistente com a URL. ✅
VF4: `python audit.py` passa. ✅
VF5: `python -m pytest -q` passa. ✅

## Gates

- [x] Implementar bloqueio em `export.ps1`.
- [x] Implementar bloqueio em `export.sh`.
- [x] Corrigir `mcp_config.json`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `export.ps1:252-258` bloqueia `-Push` com `-NoMask`.
- `export.sh:423-429` bloqueia `--push` com `--no-mask`.
- `scripts/check-push-green.py:76-101` adiciona `check_unmasked_secrets` no PreToolUse de `git push`.
- `mcp_config.json:5` alterado de `http` para `https`.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 264 passed.
- Live installation sincronizada via `install.ps1 -Force -Backup`.
