# Adequacao Devin CLI 3000.12.17 -> 3000.12.28

Data: 2026-11-08. Instalado: `devin 3000.12.28 (91c3aec41579)`.
Latest confirmado via `static.devin.ai/cli/current/manifest.json` (version
3000.12.28). O changelog publico encerra em 3000.12.17; o delta foi sondado
direto no binario.

## Escopo

- Bump `validated_cli_version` em `data/bundle-identity.json` e `README.md`.
- Nova secao `3000.12.28 capabilities` em `.devin/docs/DEVIN-CLI-COMPATIBILITY.md`.
- `CHANGELOG.md` entrada em `Unreleased`.

## Documentado (sem mudanca de config)

- `devin sandbox` virou subcomando (`sandbox setup` imprime prereqs); a flag
  `--sandbox`/`DEVIN_SANDBOX` segue. Windows ainda exige WSL 2 (verificado via
  `devin sandbox setup`).
- `--respect-workspace-trust [true|false]`: `-p` nao-interativo falha em
  diretorio nao-confiavel sem `false`; `--cloud` nunca checa trust.
- `devin update` no Windows continua manual (`irm ... install.ps1`).

## Gates

- `devin --version` (`3000.12.28`, hash 91c3aec41579)
- `devin doctor` (`3 passed, 0 warnings, 0 failures` c/ live bundle)
- `devin rules list` (regras do bundle resolvidas)
- `devin sandbox setup` (mensagem WSL-2 conforme documentado)
- `python -m pytest tests/validation/test_cli_3000_6_14_compatibility.py` (6/6)
- `python audit.py` (0 errors, 0 warnings)
