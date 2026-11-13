# Correções das issues menores do AUDIT_REPORT (lote 6)

## Input

- Restam 11 issues menores no `AUDIT_REPORT.md`.
- Lote 6 selecionado:
  - `3.3.1`: Várias skills não têm `triggers` no frontmatter.
  - `3.3.3`: Habilidades similares podem confundir.
  - `4.3.6`: `SessionEnd` e `Stop` compartilham `memory-stop.py`.
  - `8.3.4`: `tests/` não cobrem todos os 82 skills.
  - `9.3.3`: `refinements.log.jsonl` sem verificação de conteúdo.
  - `9.3.5`: `__pycache__` existe em `.devin/`.

## Authorized scope

- Corrigir as issues do lote 6.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: Skills sem triggers recebem triggers mínimos. ✅
VF2: SKILL-TIERS clarifica diferenças entre cost skills. ✅
VF3: `SessionEnd`/`Stop` memory-stop documentado como intencional. ✅
VF4: Teste verifica conteúdo mínimo das skills. ✅
VF5: `refinements.log.jsonl` valida conteúdo além de ID. ✅
VF6: Audit detecta `__pycache__` em `.devin/`. ✅
VF7: `python audit.py` passa. ✅
VF8: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `3.3.1`.
- [x] Corrigir `3.3.3`.
- [x] Corrigir `4.3.6`.
- [x] Corrigir `8.3.4`.
- [x] Corrigir `8.3.5`.
- [x] Corrigir `9.3.3`.
- [x] Corrigir `9.3.5`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- 66 skills adicionaram `triggers: [user, model]`.
- `docs/SKILL-TIERS.md` com nota de skills de custo.
- `README.md:187-188` detalhando `Stop` e `SessionEnd`.
- `tests/validation/test_skill_format_passes.py:26-36` testa conteúdo mínimo.
- `audit.py:407-418` verifica `__pycache__`.
- `audit.py:720-756` valida campos do `refinements.log.jsonl`.
- `manifest.json` sincronizado.
- `python audit.py`: 31/31 checks, 0 errors, 1 warning (`__pycache__` normal).
- `python -m pytest -q`: 289 passed.
