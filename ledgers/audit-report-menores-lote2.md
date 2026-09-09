# Correções das issues menores do AUDIT_REPORT (lote 2)

## Input

- Restam 34 issues menores no `AUDIT_REPORT.md`.
- Lote 2 selecionado:
  - `5.3.2`: Documentar número de tools do `atlassian` no bundle.
  - `5.3.4`: Não há mecanismo de fallback se `atlassian` não estiver autenticado.
  - `7.3.3`: `manifest.json` não versiona scripts nem agentes por hash.
  - `7.3.4`: `config.json` `attribution: false` sem explicar o impacto.
  - `10.3.4`: `docs/TOOLS-MAP.md` não atualiza tool count do MCP `atlassian`.
  - `10.3.5`: `CONTRIBUTING.md` e `SECURITY.md` não são citados no audit.

## Authorized scope

- Corrigir as issues do lote 2.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: `docs/TOOLS-MAP.md` documenta tool count do atlassian. ✅
VF2: `manifest.json` inclui hashes de scripts e agentes (ou audit valida drift). ✅
VF3: `config.json` explica `attribution: false` ou README/SECURITY documenta. ✅
VF4: `audit.py` verifica conteúdo de `CONTRIBUTING.md` e `SECURITY.md`. ✅
VF5: `python audit.py` passa. ✅
VF6: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `5.3.2`.
- [x] Corrigir `5.3.4`.
- [x] Corrigir `7.3.3`.
- [x] Corrigir `7.3.4`.
- [x] Corrigir `10.3.4`.
- [x] Corrigir `10.3.5`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `docs/TOOLS-MAP.md:129`: nota sobre tool count do atlassian.
- `manifest.json`: `export_hash`/`exported_at` adicionados a scripts e agents.
- `audit.py:288-329`: validação de hashes de scripts e agents.
- `README.md:455`: documentação de `attribution: false`.
- `audit.py:443-457`: verificação de conteúdo mínimo de docs.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 280 passed.
