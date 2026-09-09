# Correções das issues menores do AUDIT_REPORT (lote 4)

## Input

- Restam 22 issues menores no `AUDIT_REPORT.md`.
- Lote 4 selecionado:
  - `1.3.1`: `install.ps1`/`install.sh` não validam checksum/hash.
  - `1.3.2`: flag `--restore-secrets` pode ser confusa.
  - `1.3.4`: placeholder `{{APPDATA}}/devin` adiciona complexidade.
  - `3.3.5`: `agent-cost-guard` não integra com `validate-tool-args.py`.
  - `4.3.4`: `validate-tool-args.py` não testa `max_parallel` não-inteiro.
  - `4.3.5`: `PermissionRequest` sem handler ativo.

## Authorized scope

- Corrigir as issues do lote 4.
- Atualizar `AUDIT_REPORT.md`.
- Rodar `python audit.py` e `python -m pytest`.

## Verification functions

VF1: install scripts registram/verificam hashes. ✅
VF2: README/helptext explicam `--restore-secrets` corretamente. ✅
VF3: placeholder documentado/auditado. ✅
VF4: `agent-cost-guard` menciona `validate-tool-args.py`. ✅
VF5: teste cobre `max_parallel` inválido. ✅
VF6: `PermissionRequest` documentado como intencional. ✅
VF7: `python audit.py` passa. ✅
VF8: `python -m pytest -q` passa. ✅

## Gates

- [x] Corrigir `1.3.1`.
- [x] Corrigir `1.3.2`.
- [x] Corrigir `1.3.4`.
- [x] Corrigir `3.3.5`.
- [x] Corrigir `4.3.4`.
- [x] Corrigir `4.3.5`.
- [x] Atualizar `AUDIT_REPORT.md`.
- [x] Rodar `audit.py`.
- [x] Rodar `pytest`.

## Evidence

- `install.ps1:92-104` e `install.sh:50-56`: funções de hash SHA-256.
- `README.md:433-501`, `install.ps1:34-36`, `install.sh:25`: documentação de `-RestoreSecrets`/`--restore-secrets`.
- `.devin/adr/001-apdata-placeholder.md`: ADR do placeholder.
- `skills/agent-cost-guard/SKILL.md:28`: referência a `validate-tool-args.py`.
- `tests/held-out/mutation/test_validate_tool_args_new.py:107-128`: testes de `max_parallel`.
- `README.md:189`, `docs/TOOLS-MAP.md:94`: documentação de `PermissionRequest` sem handler.
- `python audit.py`: 32/32 checks, 0 errors, 0 warnings.
- `python -m pytest -q`: 288 passed.
