# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (subagent profile cost awareness — evitar subagent_explore)

- **MODEL-GUIDE.md: profiles built-in vs custom agents (custo)** —
  adicionada tabela comparando `subagent_general` (gratuito, herda
  GLM-5.2 High do parent), `subagent_explore` (PAGO, resolve para
  SWE-1.6 $0.5/$2.5 MTok), e custom agents (gratuito, `model: swe-1-7`).
  Aviso: **nunca usar `subagent_explore`** — usar custom `researcher`
  (gratuito, 262K vs 200K). Fonte: docs.devin.ai/cli/subagents.
- **AGENTS.md Rule 3 item 5**: atualizado para avisar que
  `subagent_explore` é pago e que `subagent_general` é gratuito (herda
  parent). Recomenda custom agents com `model: swe-1-7`.
- **SKILL-TIERS.md**: linha sobre `subagent_general` atualizada para
  explicitar que é gratuito e que `subagent_explore` deve ser evitado.

### Fixed (CRÍTICO — agents/ usando modelo PAGO em vez de gratuito)

- **BUG CRÍTICO DE CUSTO**: todos os 5 agents/ (architect, debugger,
  implementer, researcher, reviewer) usavam `model: swe` que é alias para
  `swe-1.7-lightning` (PAGO, $2.5/$12.5 MTok, 202K context). O modelo
  gratuito é `swe-1-7` (SWE-1.7 Max, 262K context, Free). Corrigido: todos
  os agents/ agora usam `model: swe-1-7`. Descoberto via `devin models list`.
- **Impacto**: cada subagent dispatch estava custando ~$2.5/$12.5 MTok
  desnecessariamente. O modelo gratuito tem MAIS contexto (262K vs 202K).
  Correção salva dinheiro E dá mais headroom de contexto.
- **MODEL-GUIDE.md**: seção SWE-1.7 reescrita com dados reais de
  `devin models list` (262K, não 256K). Tabela de variantes com preços
  reais. Aviso crítico sobre alias `swe` ser pago.
- **AGENTS.md Rule 20**: atualizada com `swe-1-7` (não `swe`), 262K (não
  256K), e aviso de que `swe` alias é pago.
- **SKILL-TIERS.md, TOOLS-MAP.md, README.md**: todas as referências a
  `model: swe` corrigidas para `model: swe-1-7`. 256K → 262K.
- **context-budget.py**: WINDOW_256K renomeado para WINDOW_262K (262_000).
- **skills/self-extend/SKILL.md**: exemplo de `model` atualizado para
  `swe-1-7` [free] em vez de `swe`.
- **Protocolo de escalada expandido**: 6 níveis (gratuito → GLM-5.2 Max →
  DeepSeek V4 Flash $0.14/$0.28 → Opus $5/$25 → GPT-5.4 $2.5/$15).
  DeepSeek V4 Flash adicionado como opção paga mais barata ($0.14/$0.28).

### Added (model cost awareness — gratuitos vs pagos)

- **MODEL-GUIDE.md: modelos pagos como fallback** — adicionada seção
  "Modelos frontier — fallback para casos extremos (custosos)" com lista
  explícita de gratuitos (GLM-5.2 High, SWE-1.7) vs pagos (GLM-5.2 Max,
  No Thinking, Opus, GPT, Sonnet, Codex, Gemini), tabela de quando usar
  cada modelo pago, e protocolo de escalada de 5 níveis:
  1. GLM-5.2 High (gratuito) → 2. SWE-1.7 fan-out (gratuito) →
  3. GLM-5.2 Max (pago) → 4. Opus (pago) → 5. GPT (pago).
  Regra: nunca usar modelos pagos sem esgotar os gratuitos primeiro.
- **AGENTS.md Rule 20: somente High e SWE-1.7 são gratuitos** — adicionado
  bullet point explicitando que todos os demais modelos são pagos (GLM-5.2
  Max, No Thinking, Opus, GPT, Sonnet, Codex, Gemini). Só usar como
  fallback após esgotar GLM-5.2 High + SWE-1.7 fan-out (3+ tentativas
  documentadas). Ver protocolo de escalada em `MODEL-GUIDE.md`.
- **Reasoning effort table corrigida** — `glm-5-2-max` marcado como
  **pago** (credit 3), não gratuito. Só `glm-5-2` (High) é gratuito.
  `glm-5-2-none` (No Thinking) também é pago.

### Added (MODEL-GUIDE.md — reasoning effort + subagent vs compaction)

- **Reasoning effort decision guide** — adicionada seção explicando que
  `reasoning_effort` no Devin CLI é controlado pelo `model_uid` (não por
  config separada). Tabela de decisão: quando usar off (glm-5-2-none),
  high (glm-5-2), max (glm-5-2-max). Mapeamento de valores documentado:
  `low`/`medium` mapeiam para `high` (não existem níveis intermediários).
  Fonte: glm52.ai/guides/glm-5-2-reasoning-effort, Z.ai docs, apidog.com.
- **Subagent vs compaction decision table** — adicionada seção com tabela
  comparando 3 respostas para context pressure: subagent (fresh window),
  compaction (summarize), context editing (evict tool results). Regra de
  composição: subagents para subtasks separáveis, compaction para thread
  contínua. Recomendações específicas para GLM-5.2 (200K) despachando
  SWE-1.7 (256K). Fonte: dreaming.press/posts/subagents-vs-compaction.

### Fixed (critical — validate-mermaid.py fail-closed + hooks sync)

- **`validate-mermaid.py` fail-closed on node unavailable (critical bug)** —
  when Node.js or mermaid was not installed (FileNotFoundError) or the
  subprocess timed out (TimeoutExpired), the hook returned `(False, ...)`
  which caused `block()` — blocking ALL writes/edits containing mermaid
  blocks. This is fail-closed: a validator unavailability blocks the user's
  workflow. Fixed: now returns `(True, "")` (fail-open) and logs to stderr.
  All other hooks in this bundle fail open on tool unavailability
  (destructive-gate, check-ai-signature, constraint-pinning, etc.) — this
  was the only exception. Verified with simulated FileNotFoundError and
  TimeoutExpired: both now allow the write.
- **`hooks.v1.json` missing `validate-mermaid.py`** — config.json had
  validate-mermaid.py on `^(write|edit)$` with timeout 60, but hooks.v1.json
  (legacy backup) only had check-ai-signature.py on that matcher. Synced.
- **`mermaid-parse-check.js` hardcoded paths** — only checked
  `C:\Users\Fingertech\scoop\...` (machine-specific Windows paths). Added
  portable lookup: (1) `require.resolve('mermaid')` first, (2) `npm root -g`
  fallback, (3) known paths including Linux (`/usr/local/lib`, `/usr/lib`,
  `~/.nvm/versions/node/...`), (4) original Windows scoop paths.

### Fixed (context budget estimates stale)

- **`TOOLS-MAP.md` context budget** — AGENTS.md estimate updated from
  ~5225 tok (2.61%) to ~5289 tok (2.64%). SKILL-TIERS, MODEL-GUIDE, TOOLS-MAP
  estimates updated to measured values. Total fixo corrected from ~6905 tok
  to ~5289 tok (AGENTS.md only); total with optional docs from ~10905 tok
  to ~11439 tok.
- **`MODEL-GUIDE.md` context budget** — same updates for 200K and 256K
  sections. AGENTS.md estimate from ~4900 tok (2.45%) to ~5289 tok (2.64%).
  256K share from 1.91% to 2.07%.

### Fixed (docs consistency — TOOLS-MAP.md pós iter 6.1-6.2)

- **`TOOLS-MAP.md` ferramentas table desatualizada** — tabela ainda marcava
  8 ferramentas excluídas (get_output, write_to_process, kill_shell,
  read_subagent, close_browser_preview, mcp_list_tools, mcp_list_servers,
  apply_patch, exit_plan_mode) com "✓" no hook matcher e validator, mas
  essas foram removidas do matcher na iteração 6.2. Atualizado para "—"
  com explicação. Cobertura corrigida de "27/27" para "19/27".
- **`TOOLS-MAP.md` hooks table desatualizada** — validate-tool-args.py
  matcher mostrava "todas 27 tools" em vez de "19 tool names";
  silent-error-review.py mostrava "todas" em vez de
  `^(exec|mcp_call_tool)$`. Ambos corrigidos.
- **`TOOLS-MAP.md` eventos count** — "8 eventos" corrigido para "6 eventos"
  (PreToolUse, PostToolUse, PostCompaction, UserPromptSubmit, SessionStart,
  Stop — SessionEnd e PermissionRequest não têm hooks configurados).

### Fixed (critical — constraint pinning + refine hook)

- **`constraint-pinning.py` marker not session-scoped (bug)** — `marker_path()`
  used a fixed filename (`devin-constraint-reinject.marker`) with no
  session_id, despite the comment claiming "Session-scoped marker path."
  Parallel sessions (parent + subagent) would overwrite each other's markers,
  causing one session's UserPromptSubmit to read the other's marker (or find
  none). Fixed: marker filename now includes session_id
  (`devin-constraint-reinject-{session_id}.marker`), sanitized and truncated.
  SessionStart clears all stale markers via glob (session_id is absent for
  SessionStart per Devin CLI docs). Verified against
  docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks: "every stdin payload
  includes a stable per-session session_id ... absent for events that fire
  before the first user prompt, e.g. SessionStart."
- **`constraint-pinning.py` dead code removed** — `inject("PostCompaction")`
  was called best-effort after writing the marker, but PostCompaction does NOT
  support `hookSpecificOutput.additionalContext` (per Devin CLI docs: only
  UserPromptSubmit, SessionStart, and PostToolUse support it). The JSON output
  was silently ignored by the CLI. Removed the call; the marker-based
  re-injection at UserPromptSubmit is the correct mechanism.
- **`refine-review-prompt.py` skill reference fixed** — the REMINDER told the
  agent to "run the `refine` skill" but no skill named `refine` exists in the
  bundle. The Refine mode lives inside the `primeagent-reference` skill.
  Updated to "run the `primeagent-reference` skill in Refine mode." Also
  updated the cross-reference in `primeagent-reference/SKILL.md` table row 2
  from "`refine` skill" to "`primeagent-reference` Refine mode."

### Changed

- **`silent-error-review.py` scope narrowed (noise reduction)** — PostToolUse
  matcher changed from `""` (all tools) to `^(exec|mcp_call_tool)$`. The ALTK
  Silent Error Review component is "best suited for tool responses that are
  verbose and/or based on tabular responses" (arXiv:2603.15473). The previous
  broad matcher fired on every `read`, `grep`, `glob`, `todo_write`,
  `ask_user_question`, etc., injecting `additionalContext` noise into the
  context window on every tool call. Empty-output checks for `read`/`webfetch`
  and no-match checks for `grep`/`glob`/`find_file_by_name` were removed —
  those conditions are already visible to the agent and are not in ALTK's
  scope. The `error` regex now requires a colon (`^\s*error\s*:`) to avoid
  false positives on "error handling"/"error recovery". The test-failure
  regex now requires a non-zero count (`[1-9]\d*`). At most one finding is
  emitted per call. The arXiv:2607.07405 citation is now characterized
  correctly as the *problem* (78% silent failures); the paper's *intervention*
  (pre-execution gates) is implemented separately as `destructive-gate.py`.
  Addresses PR #1 review comment on hook noise.
- **`validate-tool-args.py` matcher narrowed (latency reduction)** — PreToolUse
  matcher reduced from 28 to 19 tools. Removed 9 tools where validation is
  trivial or absent: `get_output`, `write_to_process`, `kill_shell` (only
  checked `shell_id` presence — the tool itself fails with a clear error),
  `read_subagent` (only checked `agent_id` presence — same),
  `close_browser_preview` (only checked `preview_id` presence — same),
  `mcp_list_tools` and `mcp_list_servers` (checks were literal `pass` no-ops),
  `apply_patch` (was `pass` fail-open), `exit_plan_mode` (was `pass` no-ops),
  yet all still spawned a Python process on every call. The 19 remaining
  tools have real validation value: path tools, search tools, network tools,
  delegation tools, MCP tools, control tools, and UI tools
  (`ask_user_question`, `browser_preview`, `todo_write`). Saves ~9 Python
  process spawns per session with zero loss of real validation.

## [2.5.1] - 2026-08-20

### Fixed

- **SWE-1.7 context window** — corrigido de "200K (user spec) / 256K (Kimi K2.7 base)"
  para definitivamente 256K. Verificado contra fontes primárias: benchlm.ai,
  tipjournal.com, awesomeagents.ai, cognition.com/blog/swe-1-7. O user spec
  de 200K era incorreto — SWE-1.7 herda 256K do Kimi K2.7 base.
- **Agent model pins** — adicionado `model: swe` em todos os 5 agent profiles
  (architect, debugger, implementer, researcher, reviewer). Sem pin, o default
  subagent router da Devin CLI resolve para SWE-1.6 (200K), não SWE-1.7 (256K).
  Verificado contra docs.devin.ai/cli/subagents: "With the default Subagent
  router setting it resolves to SWE-1.6." Pin `swe` (short name) resolve para
  o latest SWE (atualmente 1.7) e auto-updates para SWE-1.8 quando lançado.
- **Docs atualizados** — MODEL-GUIDE.md, AGENTS.md Rule 20, TOOLS-MAP.md,
  SKILL-TIERS.md, README.md, CHANGELOG.md agora refletem acuradamente:
  default subagent router = SWE-1.6; custom agents com `model: swe` = SWE-1.7.

### Verified

- Devin CLI subagents docs (docs.devin.ai/cli/subagents) — primary source
- Cognition SWE-1.7 blog (cognition.com/blog/swe-1-7) — primary source
- BenchLM SWE-1.7 specs (benchlm.ai/models/swe-1-7) — primary source
- GLM-5.2 docs (docs.z.ai/guides/llm/glm-5.2) — primary source, 1M raw context
  (200K in Devin CLI `glm-5-2` variant, 1M in `glm-5-2-max-1m` variant)

## [2.5.0] - 2026-08-20

### Added

- **Rule 20: Model-aware operation** — GLM-5.2 High (200K, thinking, tool-use
  during inference, cache $0.26/M) is primary; SWE-1.7 (200K/256K,
  self-compaction, 1000 TPS) is subagent default. Don't over-specify tool-use
  (GLM decides natively). Fan-out is cheap. Keep system prompt cache-stable.
  Non-pinned (model-specific, see MODEL-GUIDE.md). Pinned set unchanged
  (Rules 2, 5, 7, 12-19).
- **MODEL-GUIDE.md** — síntese de fontes primárias verificadas para GLM-5.2
  High + SWE-1.7. Linhagem GLM-4.5→4.6→5.2, specs SWE-1.7, estratégia de
  model pin em agents/, context budget, verificação de citações.
- **TOOLS-MAP.md** — mapeamento completo do runtime: 27 ferramentas, 7
  subagentes, 8 hooks, 11 scripts, configs, modos, modelos disponíveis.
- **4 validators faltantes** em `validate-tool-args.py`: `ask_user_question`,
  `browser_preview`, `close_browser_preview`, `todo_write`. + 2
  modo-dependentes: `apply_patch`, `exit_plan_mode`. Hook matcher atualizado
  em `config.json` e `hooks.v1.json` (22→28 tools).

### Changed

- **Agent model pins atualizados** — `architect.md`, `debugger.md`,
  `implementer.md`, `researcher.md`, `reviewer.md` agora têm `model: swe`
  (resolve para SWE-1.7, latest, 256K, 1000 TPS). Sem pin, o default subagent
  router da Devin CLI resolve para SWE-1.6 (200K), não SWE-1.7 — pin necessário.
  `subagent_general` herda GLM-5.2 do parent para trabalho complexo.
- **SKILL-TIERS.md reescrito** — custos de tokens medidos (bytes÷4 do
  SKILL.md, 2026-08-20) em vez de estimativas. Tabela de modelos alvo
  (GLM-5.2 + SWE-1.7). Linha lógica atualizada para 200K/256K. Anti-patterns
  expandidos (subagent general para pesquisa, model pin em read-only).
- **`context-budget.py`** — reporta share tanto de 200K (GLM-5.2) quanto de
  256K (SWE-1.7). JSON output inclui `window_256k_share_pct`.
- **`audit.py`** — `live_base` auto-detecta path (WSL `~/.config/devin`,
  Linux, Windows `%APPDATA%`) em vez de path stale `C:\Users\leand\...`.
  Rule count 18→19. README badge rules-18→rules-19.
- **`hooks.v1.json`** — `%APPDATA%` → `{{APPDATA}}` (Devin-native, expansível).
- **`agents/debugger.md`** — referência `systematic-debugging` →
  `diagnosing-bugs` (consolidado em v2.4.0).
- **`agents/implementer.md`** — referência `subagent-driven-development` →
  `dispatching-parallel-agents` (consolidado em v2.4.0).
- **README.md** — badge `rules-18` → `rules-19`.
- **manifest.json** — `rule_count` 18→19, adicionado `agent_count: 5`,
  `tool_count: 27`, `docs: [...]`.

### Verified

- Todas as 7 citações arXiv no AGENTS.md verificadas contra fontes primárias
  (2026-08-20): arXiv:2307.03172, 2606.22528v2, 2607.13083, 2606.30317,
  2607.25152, ICLR 2026 Workshop (Reward Hacking), Llama 4 Scout 10M.
- GLM-5.2 specs verificadas: docs.devin.ai/desktop/models (model_uid,
  pricing, credit multiplier), docs.z.ai/guides/llm/glm-4.6 (200K context,
  thinking mode, tool-use during inference).
- SWE-1.7 specs verificadas: cognition.com/blog/swe-1-7 (Kimi K2.7 base,
  self-compaction, 1000 TPS, alternating length penalty).

### Not repeated (from git history)

- v2.5.0 anterior (Rule 20 memory-hygiene + Rule 21 effort-calibration) foi
  REVERTIDO por over-engineering. Esta v2.5.0 é diferente: Rule 20 é
  model-aware (não memory-hygiene), sem Rule 21, sem skills extras.
- animation-physics removido (domain-specific) — não adicionar skills
  domain-specific.
- graphify removido (caro, sem uso) — não adicionar skills caras sem uso.
- .claude/ path leak corrigido — não vazar paths non-Devin.

## [2.4.0] - 2026-08-18

### Added

- **Rule 19: Never read secrets or sensitive env vars** — new pinned
  governance rule. Never `read`, `cat`, `echo`, `print`, or output API keys,
  tokens, passwords, private keys, or `.env` secret values. Use them (pass to
  commands, reference by variable name) but never display their contents. If
  a key/env var is missing, empty, or doesn't behave as expected, say so
  without exposing the value. Pinned into `constraint-pinning.py` (survives
  compaction). Pinned set is now Rules 2, 5, 7, 12-19.
- **`context-window-hygiene` skill** — clear vs compact, MCP paranoia,
  lost-in-the-middle (arXiv:2307.03172).
- **`mcp-context-audit` skill + `mcp-context-audit.py` script** — estimates
  per-server tool-definition token cost; flags >15 tools/server and >5%
  window share.
- **`context-budget.py` script** — SessionStart hook that reports AGENTS.md
  token cost to stderr. Transparency without context bloat.
- **`SKILL-TIERS.md`** — skills categorized by domain with token costs
  (~1700 tok vs ~2094 for `skill list`).

### Pruned (orphaned/duplicated — no consumers)

- **`graphify` skill** — 9659 tok (a mais cara), sem `graphify-out/` em
  nenhum projeto ativo. CLI `graphify.exe` instalado mas sem uso pelo agente.
  Rule 6 (graphify trigger) removida do AGENTS.md. 47 → 46 skills.
- **`post-compaction-reminder.py`** — órfão (0 hooks), duplicado por
  `constraint-pinning.py` (superior: dinâmico, 9 regras pinned, em 3 hooks).
- **MCP `arxiv`** — 0 consumidores (grep por `mcp__arxiv` em skills/ vazio).
  `observability-quality` cita `arxiv.org/abs/...` (URL de paper), não o MCP.
- **`heartbeat` skill** — emulação PrimeAgent que não fita Devin CLI
  (single-process, sem daemon). OS scheduler + script launches nova sessão
  não funciona no runtime atual.
- **`session-checkpoint` skill** — mesma razão. Emulação daemon-backed
  reattach não funciona em single-process.

### Consolidated (overlaps merged with mode selectors — content preserved)

- **`grilling`** ← `grill-me` + `grill-with-docs` (wrappers de 5-6 linhas
  que só redirecionavam). Modos: Default, Stateless, With-docs.
- **`diagnosing-bugs`** ← `systematic-debugging`. Pipeline unificado de
  6 fases. Arquivos de suporte (`root-cause-tracing.md`,
  `defense-in-depth.md`, `condition-based-waiting.md`) movidos para
  `diagnosing-bugs/`.
- **`tool-and-skill-discovery`** ← `find-skills`. Discovery + install/evaluate
  em uma skill.
- **`dispatching-parallel-agents`** ← `subagent-driven-development`. Dispatch
  geral + modo plan execution. Scripts e prompts de suporte movidos.
- **`planning-pipeline`** ← `to-spec` + `to-tickets` + `to-questionnaire`.
  Modos: Spec, Tickets, Questionnaire.
- **`obsidian-workflow`** ← `obsidian-project-docs` + `vault-organizer` +
  `wiki-audit` + `memory-bridge`. Modos: Build, Reorganize, Audit,
  Cross-session. Templates, references e scripts movidos.
- **`primeagent-reference`** ← `a2a-mailbox` + `refine` + `subagent-router`.
  Modos: Reference Card, A2A Messaging, Refine, Subagent Router.

### Fixed

- **`hooks.v1.json` leftover no global** — arquivo user-level com paths
  `%APPDATA%` literais não expandidos causava `validate-mermaid.py` e outros
  hooks a falhar com `[Errno 2] No such file or directory`. O Devin CLI lia
  o arquivo (não deveria — user-level hooks vão em `config.json` desde
  v2.2.1). Arquivo deletado do global.
- **`audit.py` rule detector false positive** — `6. **` era detectado como
  substring de `16. **`, inflando a contagem de regras. Ancorado com `\n`
  prefix para matching start-of-line.

### Changed

- **62 → 46 skills** (-16, 26% redução). Mesma cobertura funcional, menos
  namespace bloat, menos manutenção.
- **17 → 18 rules** (Rule 6 removida, Rule 19 adicionada). Regras pinned:
  2, 5, 7, 12-19.
- **12 → 11 scripts** (remoção de `post-compaction-reminder.py`).
- **2 → 1 MCP** (remoção de `arxiv`).
- **AGENTS.md enxugado**: 25KB → 18.5KB (~6263 → ~4614 tok). Non-pinned rules
  comprimidas para one-liners referenciando skills.
- **`constraint-pinning.py`** — Rule 19 adicionada ao `PINNED_CONSTRAINTS`
  e `key_phrases`.
- **`agents/researcher.md`** — removida referência a `graphify` (query mode).
- **`obsidian-workflow/SKILL.md`** — 9 referências a `graphify` substituídas
  por `ls`/`tree`/`git ls-files`.
- **Version 2.3.0 → 2.4.0** (manifest). README badges, counts, skill tables
  atualizados. SKILL-TIERS.md reescrito com 46 skills.
- **`audit.py`** — contagens e listas de sync atualizadas para 46 skills,
  11 scripts, 18 rules, v2.4.0.

## [2.3.0] - 2026-08-18

### Added (context window management — from "Context Windows Explained for Coding Agents", Matt Pocock)

- **Rule 18: Keep the context window lean** — new pinned governance rule.
  Context window = input + output tokens (hard-capped); lost-in-the-middle
  deprioritizes the middle of long chats; default to `clear` over `compact`;
  keep rules files small; audit MCP servers before adding; bigger window ≠
  better retrieval. Pinned into `constraint-pinning.py` (survives compaction).
- **`context-window-hygiene` skill** — practical user-facing hygiene: clear vs
  compact, lean rules, MCP paranoia, subagent context savings, model selection
  heuristic. Backed by lost-in-the-middle (arXiv:2307.03172).
- **`mcp-context-audit` skill + `mcp-context-audit.py` script** — estimates
  per-server tool-definition token cost; flags >15 tools/server (selection
  accuracy degrades, arXiv:2606.30317) and >5% window share. `--config` static
  mode + `--tools` measured mode (fed from `mcp_list_tools`).
- **`context-budget.py` script** — SessionStart hook that reports the AGENTS.md
  token cost to stderr. Transparency analogous to Claude Code's `/context`,
  without adding context bloat (stderr only). Warns at ≥10% of a 200k window.

### Changed

- **AGENTS.md enxugado: 25KB → 18KB (~6263 → ~4546 tokens).** Non-pinned rules
  compressed to terse one-liners referencing skills; pinned rules (2, 5, 7,
  12-18) keep full detail. Reduces lost-in-the-middle tax on every session.
- **`constraint-pinning.py`** — Rule 18 added to `PINNED_CONSTRAINTS` and
  `key_phrases`; pinned set is now Rules 2, 5, 7, 12-18.
- **`config.json` / `hooks.v1.json`** — `context-budget.py` added to
  SessionStart alongside `constraint-pinning.py`.
- **Version 2.2.5 → 2.3.0** (manifest). README badges, counts, rules table,
  hooks table, and skill listing updated (62 skills, 18 rules, 12 scripts).
- **`audit.py`** — hardcoded expectations updated to the true counts
  (62 skills, 18 rules, 12 scripts, version 2.3.0); new skills added to the
  live-vs-bundle sync list.
- **`SKILL-TIERS.md`** — novo arquivo de discovery rápido. Skills
  categorizadas por domínio de uso (núcleo, docs, programação, debug, git,
  jira, obsidian, planejamento, pesquisa, meta, setup, artefatos de pesquisa,
  outros) com custo em tokens e quando invocar. ~1500 tok vs ~2094 tok de
  `skill list`. Referenciado em AGENTS.md Rule 4 e README.

## [2.2.3] - 2026-08-15

### Fixed (coverage gaps vs official tool list)

- **validate-tool-args.py missing 7 tools** — the official docs list
  `get_output`, `write_to_process`, `kill_shell`, `skill`, `request_scope`,
  `mcp_list_tools`, `mcp_list_servers` as available tool names. The validator
  had no checks for them, so calls with missing required args (e.g. `get_output`
  without `shell_id`) passed silently. Added validators for all 7.
- **validate-tool-args.py early-exit on empty tool_input** — `if not tool_input`
  treated `{}` as falsy and exited before validating. Tools like `get_output`
  and `kill_shell` that require args but received `{}` were allowed. Fixed:
  only skip on non-dict input, not empty dict.
- **researcher.md model: swe** — `swe` is not a documented model value.
  Changed to `sonnet` (documented in the subagent profiles example).
- **researcher.md BOM** — UTF-8 BOM (EF BB BF) removed.
- **Matcher expanded** — config.json and hooks.v1.json matchers now include
  the 7 newly-validated tool names.

## [2.2.2] - 2026-08-15

### Fixed (critical — hook commands used %APPDATA% which is not expanded)

- **`%APPDATA%` is not expanded in hook commands** — the hook shell does not run
  through cmd.exe, so `%APPDATA%` stays literal and the path becomes
  `D:\...\%APPDATA%\devin\scripts\...` (No such file or directory). All hooks failed
  to find their scripts. Live config.json now uses absolute paths
  (`C:/Users/leand/AppData/Roaming/devin/scripts/...`).
- **Bundle uses `{{APPDATA}}` placeholder** — portable across users/machines.
  `install.ps1` expands `{{APPDATA}}` to `$env:APPDATA` (forward slashes) during
  merge. `export.ps1` normalizes absolute APPDATA paths back to `{{APPDATA}}`.
- **audit.py** — regex now matches `scripts/` and `scripts\`; warns on `%APPDATA%`;
  normalizes `{{APPDATA}}` vs absolute path before comparing live vs bundle hooks.

## [2.2.1] - 2026-08-15

### Fixed (critical — hooks at wrong location)

- **hooks.v1.json is not a valid user-level location** — the docs
  ([Where Hooks Live](https://docs.devin.ai/cli/extensibility/hooks/overview#where-hooks-live))
  list `hooks.v1.json` only under project-level (`.devin/hooks.v1.json`). At user-level,
  hooks must be in `config.json` under the `"hooks"` key. The standalone `hooks.v1.json`
  at `%APPDATA%\devin\` was silently ignored. Hooks are now merged into `config.json`.
- **mcp_config.json BOM** — file had UTF-8 BOM (EF BB BF), removed.
- **mcp_config.json undocumented fields** — `arxiv` server had `transport: stdio` (not
  documented for stdio servers; transport is inferred from `command`) and a `note` field
  (not in the schema). Both removed.
- **refine-review-prompt.py exit code** — printed `{"decision":"block"}` but exited with
  0 instead of 2. Changed to exit 2 for consistency with all other blocking scripts.
- **export.ps1 / install.ps1 / audit.py** — updated to read/write hooks from `config.json`
  instead of standalone `hooks.v1.json`. The bundle keeps `hooks.v1.json` for project-level
  use (`.devin/hooks.v1.json`).

## [2.2.0] - 2026-08-15

### Fixed (critical — hooks were non-functional)

Verified every hook script against the official Devin CLI hook contract
([Lifecycle Hooks](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks),
[Overview](https://docs.devin.ai/cli/extensibility/hooks/overview)). Nine defects
made the hooks silently no-op:

- **`tool` → `tool_name`** — every script read `data["tool"]`, which does not exist in the payload. All tool checks always saw an empty string and never fired. Affected all 9 scripts.
- **Exit code 1 → 2** — blocking requires exit code **2**; exit 1 is "error, logged but doesn't block". Every block was being ignored. Affected 7 scripts.
- **`tool_response` schema** — real shape is `{success, output, error}`, not `{exit_code, stderr, results, content, matches}`. `silent-error-review.py` never detected anything.
- **`Stop` payload** — has `stop_hook_active`, not `event`. `check-ai-signature.py` and `refine-review-prompt.py` exited early on every Stop event.
- **`PostCompaction` cannot inject context** — only `UserPromptSubmit`, `SessionStart`, and `PostToolUse` support `hookSpecificOutput.additionalContext`. Constraint Pinning was rewritten as a three-event flow: detect at PostCompaction → marker → re-inject at UserPromptSubmit.
- **Unanchored matchers** — `"read"` also matched `notebook_read`, `read_subagent`, and `mcp_read_resource`; `"write"` also matched `write_to_process`. Matchers are now anchored regexes (`^exec$`, `^(write|edit)$`, explicit tool list).
- **Missing `decision`/`reason` output** — blocks now return `{"decision":"block","reason":...}` so the agent receives an actionable explanation instead of a bare non-zero exit.
- **`hook_event_name` dispatch** — multi-event scripts now dispatch on `hook_event_name` instead of guessing from absent fields.
- **Stop-hook loop risk** — `refine-review-prompt.py` now honours `stop_hook_active` and consumes its marker before blocking, so it can block at most once.

Also fixed: `DEVIN_PROJECT_DIR` is now used for the project root; `rm -rf` target
parsing rewritten (whitelist by path prefix, handles multiple targets and shell
operators); `validate-skill-format.py` no longer false-positives on the prose word
"task (" and now joins folded multi-line YAML frontmatter values.

### Removed

- **`post-compaction-reminder.py`** — printed a reminder to stdout on `PostCompaction`, an event that cannot inject context, so it never reached the agent. Superseded by `constraint-pinning.py`.

### Added
- **Rule 14:** Constraint Pinning survives compaction — governance constraints re-injected after compaction with hash verification (arXiv:2606.22528v2)
- **Rule 15:** Refinement evidence must be reproducible — phantom guardrails occur in 25% of self-improvement runs (arXiv:2607.13083)
- **Rule 16:** Self-improvement loops produce 47-74% illusory gains — validate with held-out tests (ICLR 2026 Workshop)
- **5 new scripts:**
  - `destructive-gate.py` — PreToolUse hook blocking `rm -rf /`, `git push --force` without `--dry-run`, `DROP TABLE`, `chmod -R 777 /` (arXiv:2607.07405, KDD 2026 Workshop)
  - `silent-error-review.py` — PostToolUse hook flagging `success:true` responses that carry error indicators, empty reads, or no-match searches (ALTK, ACM CAIS 2026)
  - `constraint-pinning.py` — three-event Constraint Pinning across PostCompaction / UserPromptSubmit / SessionStart (arXiv:2606.22528v2)
  - `validate-tool-args.py` — PreToolUse hook validating paths, regexes, URLs, and subagent profiles for 15 tools (ALTK SPARC, ACM CAIS 2026)
  - `validate-refinement-evidence.py` — manual-run script checking `refinements.log.jsonl` for phantom guardrails
  - `validate-skill-format.py` — manual-run script scoring SKILL.md against the 8-point quality checklist
- **arxiv MCP server** — Domain-Specific Adapter pattern, 14 tools, for Rule 12 enforcement (arXiv:2606.30317 evaluation)
- **3 new hook events wired** — `PostToolUse` (silent error detection), `UserPromptSubmit` and `SessionStart` (Constraint Pinning re-injection and marker cleanup)
- **Held-out gap check** in `check-push-green.py` — blocks push when validation passes but held-out fails
- **MCP evaluation criteria** in Rule 13 — 5 patterns, 4 anti-patterns, tool count < 10-15 (arXiv:2606.30317)
- **Dynamic Subagent Construction (AOrchestra 4-tuple)** documented in `self-extend` skill (ICML 2026, arXiv:2602.03786)
- **Role Bottleneck Awareness (AgentCARD)** in `subagent-router` skill (arXiv:2606.20629)
- **Phantom Guardrail Check** in `refine` skill Step 1 (arXiv:2607.13083)
- **Elaborate Stagnation Check** in `refine` skill outcome tracking (arXiv:2607.25152)
- **Interaction-Centric Failure Dimension** in `diagnosing-bugs` skill (arXiv:2607.28802)
- **VRR-Stop stopping criterion** in `systematic-debugging` skill (arXiv:2607.17641)

### Changed
- `hooks.v1.json` — 3 to 6 events, 4 to 7 hook scripts, anchored regex matchers
- `AGENTS.md` — expanded from 13 to 16 rules, added MCP evaluation criteria to Rule 13
- `check-push-green.py` — added held-out gap measurement (Rule 16), skips `--dry-run` pushes
- `check-ai-signature.py` — Stop event now scans unstaged changes in addition to staged
- `README.md` — updated counts (16 rules, 6 events, 7 hook scripts, 2 manual-run scripts), added rules 14-16, documented the hook contract
- `audit.py` — expectations updated to 16 rules / 9 scripts / version 2.2.0

## [2.1.0] - 2026-08-15

### Added
- **Rule 13:** Devin CLI is not a security sandbox — guardrails for untrusted code, MCP servers, skills, and reward hacking
- **7 new skills** from verified PrimeAgent/RLM research:
  - `context-folding` — RLM-style context folding (arXiv:2512.24601), depth=1 only
  - `refine` — Continual Harness self-improvement (arXiv:2605.09998) with auto-trigger, outcome tracking, reward hacking guard
  - `autonomous-gates` — bounded autonomous mode with quality gates
  - `a2a-mailbox` — file-based A2A messaging emulating PrimeAgent's `agent_message.send()`
  - `session-checkpoint` — structured checkpoint for cross-session continuation
  - `heartbeat` — OS-scheduled re-entry via Task Scheduler/cron
  - `primeagent-reference` — reference card of 9/9 adapted features with verified sources
- **`refine-review-prompt.py`** Stop hook for auto-refinement prompts
- **LICENSE** (MIT)
- **SECURITY.md** — security policy documenting guardrails and limitations
- **CONTRIBUTING.md** — contribution guide with skill/rule/hook standards
- **CHANGELOG.md** — this file
- **.github/workflows/ci.yml** — CI: validate JSON + Python + skill frontmatter on push/PR
- **.github/ISSUE_TEMPLATE/** — bug report and feature request templates
- **.github/PULL_REQUEST_TEMPLATE.md** — PR template
- **Rule 12 clause:** "Don't trust ANY subagent return without verification" — subagent returns are leads, not answers

### Changed
- `post-compaction-reminder.py` — now re-primes rules 7-10 (verification, Rule 12, Rule 13) in addition to 1-6
- `check-push-green.py` — added .NET detection (`.sln`/`.csproj`) + `dotnet test`
- `manifest.json` — synced with disk (was missing 9 skills)
- `README.md` — major rewrite: badges, quick start, prerequisites, troubleshooting, bilingual sections, updated counts
- `.gitignore` — expanded with common temp files

### Fixed
- `post-compaction-reminder.py` was missing rules 10-13 — after compaction, verification and security rules were not re-primed
- `check-push-green.py` did not detect .NET projects — C#/F#/VB.NET pushes were not blocked by failing tests
- `manifest.json` was missing 9 skills (jira, observability-quality, context-folding, refine, autonomous-gates, primeagent-reference, a2a-mailbox, session-checkpoint, heartbeat)
- `refine` skill was not autonomous — added auto-trigger (Stop hook + `.refine-pending` marker), outcome tracking (`refinements.log.jsonl`), rollback by ID

### PrimeAgent/RLM Adaptation Status
- **9/9 features adapted** (3 direct, 3 emulated, 1 partial, 2 guardrails)
- All claims verified against primary sources (arXiv, GitHub, PrimeAgent blog, ARC Prize leaderboard)
- 2 errors in source video corrected (GPT-V → GPT-5, Opus-V → Opus 5)

## [2.0.0] - 2026-08-13

### Added
- Rule 12: Maximum precision, zero tolerance for partial verification
- Rule 11: Never fail from failures
- Cross-platform installer (Windows + Linux/macOS)
- Auto-discover skills export (not limited to manifest)
- Secrets masking in export (config.json, mcp_config.json, credentials.toml)
- 5 subagent profiles (architect, debugger, implementer, researcher, reviewer)
- Hooks: check-ai-signature, check-push-green, post-compaction-reminder
- 45 skills (unified, adapted, and original)

### Changed
- Rules framed as negative constraints (evidence: arXiv:2604.11088)
- Post-compaction re-priming (evidence: arXiv:2605.10039 — 5.6% compliance decay per step)

## [1.0.0] - 2026-08-11

### Added
- Initial bundle: AGENTS.md (10 rules), skills, config, hooks, scripts
- Windows installer (install.ps1) and exporter (export.ps1)
