# Adequacao Devin CLI 3000.11.92 -> 3000.11.228

Data: 2026-10-27. Instalado: `devin 3000.11.228 (053434014dbd)`.
Delta: `3000.11.205` + `3000.11.228` (changelog estavel).

## Escopo

- Bump `validated_cli_version` em `data/bundle-identity.json` e `README.md`.
- Nova secao de capacidades em `.devin/docs/DEVIN-CLI-COMPATIBILITY.md`.
- `TOOLS-MAP.md`: comandos novos, campos de hook novos, remocao `/loop`.
- `CHANGELOG.md` entrada Unreleased.

## Adotado (mudanca real)

- `fail_closed: true` nos dois matchers `PreToolUse` (`pre-exec-guard.py`,
  `pre-write-guard.py`). Verificado empiricamente: hook com exit 1 deixa
  `exec` passar sem a flag e bloqueia com ela ("Blocked: a required
  PreToolUse hook failed"). Guards quebrados agora falham fechado;
  hooks observadores seguem fail-open.
- `read_config_from.cloud: false`: mantem MCPs do Devin Cloud e plugins
  pessoais fora da superficie validada; consistente com as demais
  fontes (todas `false` exceto `agents_standard`). Plugins exigidos pela
  organizacao continuam carregando.

## Documentado (sem adocao)

- `stop: "<reason>"` em output de hook (qualquer evento), Claude-format
  `continue: false`/`stopReason`.
- `hookSpecificOutput.updatedToolOutput` (PostToolUse): reescrita do
  resultado da tool (redaction); sem consumidor atual.
- `DEVIN_SESSION_STORE=files` (experimental, NFS/SMB); `agent.verbosity`.
- `/rename`, `/pickup`, `/confetti`, `devin models`, `/hooks`.
- Permission UX (regra exata, duracao do grant, `e` p/ editar),
  transcript compacto + `Ctrl+O`, pickers/editor/`/context` novos,
  session picker instantaneo.
- Steering com interrupcao imediata preservando comando longo.
- Fixes: session DB migration repair, inline-image crash, `local_exec`
  credential path, matcher list-of-strings, MCP discover/connect.

## Removido pelo CLI

- `/loop` e `agent.model_mixture` (usar `/goal`). Bundle nao afetado.

## Gates

- `python audit.py`, `python -m pytest`, `devin doctor`,
  `devin rules list`, export dry-run (config.json e recurso exportavel).
- Empirico: teste controlado de `fail_closed` em projeto scratch
  (verificado).
