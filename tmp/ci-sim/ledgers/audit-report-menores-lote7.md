# Correções das issues menores do AUDIT_REPORT (lote 7 - final)

## Input

- Restam 4 issues menores no `AUDIT_REPORT.md`.
- Lote 7 selecionado:
  - `3.3.2`: `leo` skill mistura orquestração com descrições extensas.
  - `4.3.2`: `silent-error-review.py` pode gerar falsos positivos.
  - `6.3.4`: Regras 14-19 são extensas.
  - `9.3.4`: `scratch/` contém esforços antigos sem status claro.

## Authorized scope

- Corrigir as 4 issues restantes.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: `leo/SKILL.md` mais concisa ou modular. ✅
VF2: `silent-error-review.py` melhora detecção de warnings+error. ✅
VF3: Regras 14-19 resumidas ou justificadas. ✅
VF4: `scratch/` ganha README de arquivamento. ✅
VF5: `python audit.py` passa. ✅
VF6: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `3.3.2`.
- [x] Corrigir `4.3.2`.
- [x] Corrigir `6.3.4`.
- [x] Corrigir `9.3.4`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `skills/leo/SKILL.md:7-17`: TL;DR adicionado.
- `scripts/silent-error-review.py:87-117`: heurística de erro forte em linhas de warning.
- `AGENTS.md:97-133`: subtítulos resumo nas regras pinned 14-19.
- `.devin/scratch/README.md` e READMEs por stub: status ARCHIVED.
- `manifest.json` sincronizado; live reinstalado.
- `python audit.py`: 31/31 checks, 0 errors, 1 warning (`__pycache__` esperado).
- `python -m pytest -q`: 289 passed.
