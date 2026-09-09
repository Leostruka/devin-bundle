# Correções das issues menores do AUDIT_REPORT (lote 1)

## Input

- `AUDIT_REPORT.md` identifica 39 issues menores.
- Lote 1 selecionado:
  - `5.3.3`: `mcp_config.json` não é validado por `audit.py`.
  - `7.3.2`: `config.json` não é validado por schema.
  - `8.3.3`: Não há testes para `config.json` schema ou hooks.
  - `10.3.2`: `README.md` não menciona agente `qa-ci`.
  - `10.3.3`: `CHANGELOG.md` não menciona as 6 novas skills da Fase 4/5.

## Authorized scope

- Corrigir as issues do lote 1.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: `audit.py` valida `mcp_config.json` (estrutura mínima, transporte, URL). ✅
VF2: `audit.py` valida `config.json` (schema, hooks, eventos). ✅
VF3: Testes cobrem `config.json` e `hooks.v1.json`. ✅
VF4: `README.md` menciona `qa-ci`. ✅
VF5: `CHANGELOG.md` detalha skills da v3.1.0. ✅
VF6: `python audit.py` passa. ✅
VF7: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `5.3.3`.
- [x] Corrigir `7.3.2`.
- [x] Corrigir `8.3.3`.
- [x] Corrigir `10.3.2`.
- [x] Corrigir `10.3.3`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `audit.py:328-352`: validação de `mcp_config.json`.
- `audit.py:187-229`: validação de schema de `config.json`.
- `tests/validation/test_config_schema.py`: 7 testes de schema.
- `README.md:162`: `qa-ci` listado na tabela de perfis.
- `CHANGELOG.md:12-18`: 6 novas skills listadas na v3.1.0.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 280 passed.
