# Correções das issues importantes do AUDIT_REPORT

## Input

- `AUDIT_REPORT.md` identificou 5 issues importantes:
  - `1.3.5`: Não há testes automatizados para `install.ps1`/`install.sh`.
  - `1.3.6`: `export.ps1 -Push` faz git push sem re-validar o estado local.
  - `6.3.1`: `AGENTS.md` é longo (~250 linhas) e carrega em toda sessão.
  - `8.3.1`: `audit.py` não valida `install.ps1`/`install.sh`/`export.ps1`/`export.sh`.
  - `8.3.2`: `audit.py` não valida conteúdo de `AGENTS.md` contra número de regras.

## Authorized scope

- Corrigir as 5 issues importantes no branch `3-news`.
- Atualizar `AUDIT_REPORT.md` para refletir as correções.
- Rodar `python audit.py` e `python -m pytest` antes de commit.

## Verification functions

VF1: `audit.py` valida estrutura/sintaxe dos scripts install/export. ✅
VF2: `audit.py` detecta se uma regra está ausente ou mal formatada em `AGENTS.md`. ✅
VF3: `export.ps1 -Push` e `export.sh --push` executam `audit.py` e `pytest` antes do push. ✅
VF4: `install.ps1`/`install.sh` têm testes de sintaxe/estrutura. ✅
VF5: `AGENTS.md` é menor ou está modularizado sem perda de conteúdo. ✅
VF6: `python audit.py` passa. ✅
VF7: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `8.3.2` (validação de regras no audit.py).
- [x] Corrigir `8.3.1` (validação de install/export no audit.py).
- [x] Corrigir `1.3.6` (export re-executa audit + pytest).
- [x] Corrigir `1.3.5` (testes para install/export).
- [x] Corrigir `6.3.1` (modularizar `AGENTS.md`).
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `audit.py:109-154`: validação de regras e budget de tokens do `AGENTS.md`.
- `audit.py:499-548`: validação estrutural de `install.ps1`, `install.sh`, `export.ps1`, `export.sh`.
- `export.ps1:482-505`: execução de `audit.py` e `pytest` no pre-push.
- `export.sh:477-497`: execução de `audit.py` e `pytest` no pre-push.
- `tests/validation/test_install_export_scripts.py`: 9 testes de estrutura e sintaxe.
- `AGENTS.md`: regras 14-19 condensadas; ~24K chars / ~6K tokens.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 273 passed.
- Live installation sincronizada via `install.ps1 -Force -Backup`.
