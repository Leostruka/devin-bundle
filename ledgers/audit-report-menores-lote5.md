# Correções das issues menores do AUDIT_REPORT (lote 5)

## Input

- Restam 16 issues menores no `AUDIT_REPORT.md`.
- Lote 5 selecionado:
  - `2.3.1`: `qa-ci` tem `exec`/`get_output`; risco de poluição verificar/modificar.
  - `2.3.2`: `reviewer` tem `exec`/`get_output`; idealmente não escrever.
  - `2.3.4`: `.devin/agents/` sem agente `reviewer` de projeto.
  - `3.3.4`: `ontology-validator`, `task-sizer`, `secure-defaults-check` sem scripts.

## Authorized scope

- Corrigir as issues do lote 5.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: `agents/qa-ci.md` reforça read-only/exec controlado. ✅
VF2: `agents/reviewer.md` reforça write-free. ✅
VF3: `.devin/agents/reviewer.md` existe. ✅
VF4: 3 skills ganham scripts executáveis mínimos. ✅
VF5: `python audit.py` passa. ✅
VF6: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `2.3.1`.
- [x] Corrigir `2.3.2`.
- [x] Corrigir `2.3.4`.
- [x] Corrigir `3.3.4`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `agents/qa-ci.md:10-11`: comentários de exec/get_output.
- `agents/reviewer.md:10-13`: comentários e ausência de write/edit.
- `.devin/agents/reviewer.md`: agente local adicionado.
- `skills/ontology-validator/scripts/validate.py`, `skills/task-sizer/scripts/estimate.py`, `skills/secure-defaults-check/scripts/check.py`: scripts adicionados.
- `manifest.json`: hashes atualizados.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 288 passed.
