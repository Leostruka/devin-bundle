# Adequacao Devin CLI 3000.11.228 -> 3000.11.234

Data: 2026-10-30. Instalado: `devin 3000.11.234 (92c83011d113)`.

## Escopo

- Bump `validated_cli_version` em `data/bundle-identity.json` e `README.md`.
- Nova secao `3000.11.234 capabilities` em `.devin/docs/DEVIN-CLI-COMPATIBILITY.md`.
- Sincronizacao de `.devin/docs/TOOLS-MAP.md` (`--verbosity` / `DEVIN_VERBOSITY`, `session_id` + `prompt_id` nos payloads de hook, `PreToolUse` `hookSpecificOutput.updatedInput`, `devin desktop`, e correcao da nota de `agent.verbosity: 3`).
- `CHANGELOG.md` entrada em `Unreleased`.

## Adotado / Alinhado

- `keymap` com especificacao separada por `-` (`"queue_message": "ctrl-4"` em `config.json`, validado sem warnings no startup).
- `agent.verbosity: 3` mantido em `config.json`; documentada a flag de sessao `--verbosity <0..3>` / `DEVIN_VERBOSITY`.
- IDs de correlacao `session_id` e `prompt_id` no stdin de todos os eventos de hook (adotado passivamente).

## Documentado (sem mudanca de config)

- `PreToolUse` `hookSpecificOutput.updatedInput` (reescrita de argumentos antes da execucao).
- `devin desktop [ARGS]...` e argumento posicional `[PATH]...`.
- `devin acp --agent-type <summarizer|review>` e `--refusal-fallback <MODEL>`.

## Gates

- `devin --version` (`3000.11.234`)
- `devin doctor --json` (`ok: true`)
- `devin rules list`
- `python audit.py` (`0 errors, 0 warnings`)
- `python -m pytest`
- `./export.ps1 -DryRun` (`8 / 8`)
