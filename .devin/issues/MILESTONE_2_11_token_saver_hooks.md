# MILESTONE 2 / ISSUE 11: token-saver hooks - output-mode injector + quiet tools + RL auto-resume

Status: resolved · Source: github.com/aicodeking/pandacode (MIT+attribution; via YT cCFAIrbt_s8 + goremy.ai coverage) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#10/D.3 · Blocked-by: none · Blocks: none

## Contexto & Valor

- PandaCode economiza ~650 tok/msg movendo instrucoes fixas para system-prompt cacheado e enviando estilo SO na mudanca de modo. Nosso equivalente deterministico: hook `UserPromptSubmit` injeta fragmento de preset apenas quando o modo muda (state file), mais compressao de tool output no lado do musculo.
- Valor: 3 presets acionaveis (caveman/lean/quiet) sem editar AGENTS.md; quiet-tools corta ruido de exec; auto-resume pos rate-limit vira intent agendada, nao memoria fraca.

## Brain (Skill)

- Fragmentos de preset (curtos, versionados em `data/output-modes.json` junto do hook):
  - `caveman`: respostas ultra-telegraficas, bullets only, sem preambulo (extende Rule 8).
  - `lean`: minimal-diff, zero prosa em volta de codigo, nada alem do pedido.
  - `quiet`: sem narracao de tool calls; colapsar saida verbosa.
- Doc no `context-hygiene`: tabela modo->efeito + como setar (`devin mode caveman` ou escrever `.devin/output-mode.json`).

## Muscle (Hooks + Scripts)

- `scripts/token-saver.py` (UserPromptSubmit): le `.devin/output-mode.json` (`{"mode":"off|caveman|lean|quiet"}`); injeta fragmento SO quando mode != ultimo injetado (`state` no mesmo json); combos `lean+quiet` permitidos.
- `scripts/post-exec.py` += quiet-mode: colapsa linhas repetidas, tail-N em logs de teste, dedupe de stack traces (bounded, so quando mode=quiet).
- `scripts/stop-guard.py` += detectar assinatura de rate-limit no tail da sessao -> escreve `.devin/rts/intents/i<ms>.json` `{"kind":"resume_at","when":<reset_ts>}` + instrui `scheduled-turns` (opt-in, nunca auto).
- `scripts/post-exec.py` footer opcional: `git diff --stat` 1-linha quando cwd e repo e mode!=off.
- `hooks.v1.json`: adicionar `token-saver.py` em UserPromptSubmit.

## Step-by-step

0. `token-saver.py` + `output-modes.json` + teste de injecao-on-change.
1. quiet-mode em post-exec + footer diff (flags no mode file).
2. RL-detect em stop-guard + intent writer; testar com transcript forjado.
3. Registrar em hooks.v1.json + manifest; `render-user-hooks.py` dry-run.
4. Gate: `pytest` (injecao so-on-change; quiet colapsa fixture; intent escrito em RL forjado); `audit.py` 0 errors.

## Non-goals

Sem modificar AGENTS.md; sem auto-resume real (so agenda); sem filtrar tool output do usuario, so compressao opt-in; sem GUI/approval bar (canon Devin CLI ja tem permissoes proprias).

## Answer

Implemented as consolidated-hook modules (not a new hooks.v1.json entry,
matching the in-process `_hookrun` architecture):

- `scripts/token-saver.py` (user-prompt.py): reads `.devin/output-mode.json`,
  injects preset fragment only when mode != state.last; "off" emits a
  restore notice once; combos `lean+quiet` join fragments from
  `data/output-modes.json`.
- `scripts/git-diff-stat.py` (post-exec.py): `diff-stat: N files (+a/-b)`
  footer after exec when the active preset sets `flags.diff_footer`
  (caveman, lean), cwd is a repo, and diff is non-empty.
- `scripts/rl-resume-detect.py` (stop-guard.py): rate-limit signature in
  `last_assistant_message` writes `.devin/rts/intents/i<ms>.json`
  `{"kind":"resume_at","when":<ts>,"auto":false}` with parsed retry-after /
  reset times bounded to 24h.
- `data/output-modes.json`: caveman/lean/quiet presets + flags.
- Docs: HOOKS-PIPELINE module lists, context-hygiene "Output modes" table,
  README/TOOLS-MAP counts (37 scripts, 24 internal modules).

Quiet output compression at the hook layer is impossible (PostToolUse
hooks emit context, they cannot rewrite tool output) — the quiet preset
achieves the same effect through the injected style contract; documented
as such.

Tests: 13 new (test_hook_token_saver/rl_resume_detect/git_diff_stat).
Gate: pytest green, audit 0 errors.
