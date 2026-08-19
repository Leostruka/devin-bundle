# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-08-19

### Added

- **Rule 20: Prefer explicit over auto-saved memory** — new non-pinned
  governance rule. Prefer user-authored preferences (AGENTS.md, skills,
  repo docs) over agent-auto-saved cross-session memory (MEMORY.md,
  `.claude/memory`, etc.). Auto-memory permitted only with selective
  management (add+delete), never naive growth. Backed by arXiv:2605.07313
  (16-20pp reliability loss from accumulation), arXiv:2605.17830 (temporal
  contamination), arXiv:2505.16067 (error propagation, +10% with managed),
  arXiv:2607.02374 (reasoning drift), arXiv:2502.09597 (preference
  following <10%), arXiv:2404.15269 (CIPHER, user-editable preferences),
  arXiv:2310.08560 (MemGPT, managed memory helps).
- **Rule 21: Calibrate effort to task difficulty** — new non-pinned
  governance rule. Default to lowest reasoning effort that still uses
  chain-of-thought; raise only when verification fails or the task is
  genuinely hard. Improve task specification before raising effort —
  information quality substitutes for reasoning budget. Backed by
  arXiv:2412.21187 (overthinking: 1,953% more tokens on "2+3=?", 13
  redundant solutions, 48.6% reduction without accuracy loss),
  arXiv:2408.03314 (compute-optimal 4× more efficient than best-of-N,
  ICLR 2025), arXiv:2608.01347 (prompt-induced waste: "multiple
  approaches" 2.4-7.4× reasoning without success, "max certainty" 18×
  cost loops), arXiv:2607.13034 (E3: 85% cost / 91% token cut at 100%
  success), arXiv:2607.02436 (counterpoint: effort High→xHigh lifts
  perfect runs 28%→89% on hard tasks).
- **`memory-hygiene` skill** — decision framework (stateless vs managed
  vs naive), 6 rules, 5 anti-patterns, 8 academic sources. Distilled
  from "Kill your MEMORY.md" (Matt Pocock), claims verified against
  primary sources.
- **`effort-calibration` skill** — effort tier table (Minimum/Medium/
  High), 7 rules, 7 anti-patterns, 5 academic sources. Distilled from
  "Your effort level is TOO DAMN HIGH" (Matt Pocock), claims verified
  against primary sources.

### Changed

- **46 → 48 skills** (+2: memory-hygiene, effort-calibration).
- **18 → 20 rules** (Rule 20 + Rule 21 added; Rule 6 still removed).
  Pinned set unchanged: 2, 5, 7, 12-19.
- **AGENTS.md**: 18.5KB → 25.4KB (~4614 → ~6328 tok, 3.16% of 200k
  window). Still lean; both new rules are non-pinned one-liners in the
  summary with detail sections at the bottom.
- **`manifest.json`**: version 2.4.0 → 2.5.0, skill_count 46 → 48,
  rule_count 18 → 20.
- **`README.md`**: badges updated (skills-48, rules-20, version-2.5.0).
- **`SKILL-TIERS.md`**: 2 skills added to "Meta (gestão de sessão)";
  AGENTS.md cost updated (~6300 tok).
- **`audit.py`**: rule range 1→22, expected counts 48 skills / 20 rules,
  version checks 2.5.0, badge checks skills-48 / rules-20 / version-2.5.0.

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
