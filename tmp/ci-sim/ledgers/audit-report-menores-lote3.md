# Correções das issues menores do AUDIT_REPORT (lote 3)

## Input

- Restam 28 issues menores no `AUDIT_REPORT.md`.
- Lote 3 selecionado:
  - `4.3.1`: `check-push-green.py` timeout de 60s pode ser curto.
  - `4.3.3`: `context-pressure.py` não tem teste de unidade.
  - `6.3.2`/`9.3.1`: `.devin/rules/` está vazio.
  - `6.3.3`/`9.3.2`: `.devin/adr/` contém apenas `README.md`.

## Authorized scope

- Corrigir as issues do lote 3.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: `check-push-green.py` timeout aumentado. ✅
VF2: `tests/` cobre `context-pressure.py`. ✅
VF3: `.devin/rules/` tem arquivo explicativo. ✅
VF4: `.devin/adr/` tem ADRs documentando decisões arquiteturais. ✅
VF5: `python audit.py` passa. ✅
VF6: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `4.3.1`.
- [x] Corrigir `4.3.3`.
- [x] Corrigir `6.3.2`/`9.3.1`.
- [x] Corrigir `6.3.3`/`9.3.2`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `scripts/check-push-green.py:24`: `TEST_TIMEOUT` aumentado para 120.
- `tests/validation/test_context_pressure.py`: 4 testes de unidade.
- `.devin/rules/README.md`: explica uso vazio intencional.
- `.devin/adr/001-apdata-placeholder.md` e `002-subagent-model-swe-1-7.md`: ADRs.
- `manifest.json`: hashes de scripts/atualizados.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 284 passed.
