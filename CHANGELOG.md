# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-09-06

### Added

- Validated task-adaptive harness recipes, durable session logging, MCP code-mode routing, model-interface preflight, bidirectional patch verification, temporal regression checks, and prompt-bloat quality gates.
- Validation coverage for Leo's orchestration contract.

### Changed

- **`leo` skill**: promoted from session-start router to the bundle's universal orchestrator, with direct routing to `wayfinder` and specialist domains, multi-skill composition, and control returning to Leo until verified completion.
- Live bundle installation and audit now validate all 32 checks with no warnings.

## [2.9.0] - 2026-09-01

### Added

- **7 Matt Pocock AI Coding workshop plans**: skills, plans and ledgers for context-workflow, grill-me, prd-to-issues, afk-loop, tdd-feedback, deep-modules, and push-pull-review.
  - `context-window-hygiene` + `scripts/context-budget.py`: added `SMART_ZONE_TOKENS` (100k), `--simulate`, and explicit `clear` over `compact` nudge.
  - `grilling`: assertive questions, one recommendation alongside every question, and `shared design concept` PRD export.
  - `planning-pipeline` and `writing-plans`: PRD as destination document, declared modules and interfaces, tracer-bullet vertical slices, and prototype/disposable asset lifecycle.
  - `afk-loop`: new skill for unattended TDD over local Markdown issues in isolated worktrees.
  - `tdd`: RED→verify RED→GREEN→verify GREEN→REFLECT→REFACTOR contract, anti-cheat reflection, and `Feedback Loops Are the Quality Ceiling`.
  - `improve-codebase-architecture`: Ousterhout deep vs shallow module heuristics and five deepening refactor moves.
  - `code-review`, `receiving-code-review`, `impeccable`: push/pull pattern distinction with Sand Castle as mental model, no Docker dependency.
- **`afk-loop` skill** — Prompt/workflow for an unattended agent that consumes local Markdown issue files under `.devin/scratch/<feature>/issues/*.md`, uses TDD in an isolated git worktree, and picks the next ready issue autonomously from a DAG of blocking relationships. Stops when no ready issues remain or on blockers; does not commit/push to `main` without human confirmation and does not require Docker.
- **`youtube-fetcher` skill** — Devin-native, stdlib-first, network-free adapter for turning a YouTube URL and provider/fixture caption/metadata JSON into raw, timestamped transcript + metadata Markdown under `.devin/notes/youtube/`. Strict host allowlist for URL validation, input/output size limits, symlink containment, duplicate preservation, and handoff to `structured-knowledge-extraction`. Conceptually adapted from JimmySadek/youtube-fetcher-to-markdown (MIT); no code copied.
- **`leo` skill** — `/leo` session-start skill that injects bundle operating rules, skill discovery, tool verification, telegraphic output, subagent/model routing, and a clear priority hierarchy. Replaces the playbook experiment.

### Changed

- **README.md**: complete rewrite explaining the full ecosystem (rules, skills, agents, tools, hooks, context, memory) and operational flows (idea → ship, AFK loop, deep modules, push/pull review). Updated counts and badges.
- **manifest.json**: version `2.8.1` → `2.9.0`, skill count `75` → `76` with `afk-loop`.
- **docs/TOOLS-MAP.md**, **docs/DEVIN-CLI-COMPATIBILITY.md**: skill count updated to `76`.

## [2.8.1] - 2026-08-29

### Fixed

- **README.md**: corrected rule count (19 → 20), script count in Mermaid (13 → 17), added `context-pressure.py` and `SessionEnd`/`memory-stop.py` rows, clarified `credentials.toml` as generated.
- **docs/TOOLS-MAP.md**: added `context-pressure.py` (PostToolUse) and `SessionEnd`/`memory-stop.py` rows; updated rule count (19 → 20); corrected claim that `SessionEnd` was unused.
- **docs/SKILL-TIERS.md**: added `youtube-fetcher` to Data tier.
- **CONTRIBUTING.md**: corrected hook exit code (1 → 2) for block.
- **SECURITY.md**: updated `post-compaction-reminder.py` → `constraint-pinning.py` and `refine` skill → `primeagent-reference` Refine mode.
- **hooks.v1.json** (root + `.devin/`): synchronized with `config.json` hooks; uses `python scripts/*.py` paths and lists all 8 lifecycle events.
- **manifest.json**: synchronized `impeccable` purpose with `SKILL.md` description.

### Changed

- **12 skills**: removed YAML quote wrapping from `description` frontmatter so `validate-skill-format.py` scores 100 (`a11y-audit`, `api-design`, `cost-optimization`, `database`, `deploy`, `docker`, `e2e-testing`, `i18n`, `impeccable`, `legacy-refactor`, `performance`, `security-audit`).

## [2.8.0] - 2026-08-28

### Added

- **11 new skills for modern agent coverage**:
  - `deploy` — deploy, release, rollback, and smoke-test workflows.
  - `security-audit` — defensive SAST, dependency CVE, and secret-leak scanning.
  - `performance` — profiling, benchmarking, and bottleneck optimization.
  - `a11y-audit` — WCAG, keyboard, screen-reader, and contrast checks.
  - `api-design` — REST/OpenAPI design and contract testing.
  - `database` — schema design, migrations, query review, and indexing.
  - `e2e-testing` — Playwright/Selenium/Cypress critical-journey tests.
  - `cost-optimization` — token, cache, model routing, and MCP cost reduction.
  - `docker` — container build, run, compose, and image scanning.
  - `i18n` — internationalization, pluralization, LTR/RTL, and formatting.
  - `legacy-refactor` — strangler-fig, seams, and incremental modernization.

### Changed

- **manifest.json**: version 2.7.0 → 2.8.0, 71 skill entries.
- **README.md**: skills badge 60 → 71, version badge 2.7.0 → 2.8.0, summary and Mermaid diagram updated.
- **docs/TOOLS-MAP.md**: skills count 60 → 71.
- **docs/SKILL-TIERS.md**: new "Infra / Quality / Release" tier with the 11 new skills.

## [2.7.0] - 2026-08-27

### Added

- **project-setup skill**: FASE 0 deep research + 10-step setup loop for bootstrapping `.devin/` configuration in projects.
- **Cross-skill wiring**: `context7`, `deep-mode`, and `research` wired into 35+ skills where library docs, unfamiliar code, or primary-source investigation is needed.
- **Engineering skill integration in `project-setup`**: Passo 4.5 now explicitly runs `grilling`, `domain-modeling`, `project-memory`, `triage`, and `planning-pipeline` to populate the project's knowledge base before work begins.

### Changed

- **Agent-produced artifact paths**: `docs/specs/` → `.devin/specs/`, `docs/plans/` → `.devin/plans/`, `docs/obsidian/` → `.devin/obsidian/` (with legacy fallback) in `grilling`, `writing-plans`, `dispatching-parallel-agents`, `code-review`, and `obsidian-workflow`.
- **manifest.json**, **README.md**, **audit.py**: version bumped to 2.7.0.

## [2.6.0] - 2026-08-27

### Added

- **project-memory skill**: captures project-specific knowledge as plain-text
  Markdown notes under `.devin/memory/`, with user approval, cue-anchored
  frontmatter, and Obsidian-compatible wikilinks.
- **Memory helper scripts**: `capture-memory.py`, `query-memory.py`, and
  `audit-memory.py` for note lifecycle and link/orphan validation.
- **Cue-anchored memory hooks** (arXiv:2607.20972, arXiv:2608.15008):
  - `memory-retrieval.py` on `UserPromptSubmit` (keyword cues)
  - `memory-post-edit.py` on `PostToolUse` `write`/`edit` (path cues)
  - `memory-post-exec.py` on `PostToolUse` `exec` (symbol/keyword cues)
  - `memory-stop.py` on `Stop` (session review nudge)
- **Rule 21**: "Don't think through uncertainty — research or ask".

### Changed

- `manifest.json`, `README.md`, `docs/TOOLS-MAP.md`, `audit.py`: updated
  script counts to 17, hook script counts to 15.
- `docs/MODEL-GUIDE.md`: added arXiv:2607.20972 and arXiv:2608.15008 to the
  source verification table.

## [2.5.3] - 2026-08-26

### Fixed

- `audit.py`: removed hardcoded version and badge checks, using manifest and runtime counts.

## [2.5.2] - 2026-08-26

### Added (iter 8.5 — continuous improvement + mermaid + cleanup)

- **continuous-improvement skill**: FASE 0 deep research + 10-step self-improvement
  loop based on Constitutional AI, RISE, Six-Step Reframing, and held-out
  validation. Enforces the full directive and prevents skipped steps.
- **PermissionRequest and SessionEnd hook events**: added to `config.json` and
  `hooks.v1.json` to match all 8 Devin CLI lifecycle events. Audit check [30]
  prevents future drift.
- **Mermaid architecture diagram in README.md**: replaced ASCII diagram with
  a `flowchart TB` Mermaid block, validated by `validate-mermaid.py`.

### Changed

- **README.md and SKILL-TIERS.md**: skill count 49 → 50, added
  `continuous-improvement` to skill inventory and tier list.
- **scripts/validate-skill-format.py**: default scan now includes bundle root
  `skills/` as the source of truth, plus project `.devin/skills/` and global
  installs.
- **TOOLS-MAP.md and audit.py**: updated skill count checks 49 → 50.

### Removed

- **ci-logs.zip**, `__pycache__/`, `.pytest_cache/`: cleaned project junk.

### Added (iter 8.1 — CLI replicas of cloud-only features)

- **deep-mode skill**: replicates Ask Devin's Deep Mode (`!deep` in
  Slack/Teams) for the CLI. Multi-pass agentic search (broad sweep ->
  deep read -> cross-file synthesis -> architecture map) with
  mandatory file:line citations. Sources: docs.devin.ai/work-with-devin/ask-devin,
  docs.devin.ai/integrations/slack, cognition.ai/blog/new-self-serve-plans-for-devin.
- **data-analyst skill**: replicates Devin cloud's Data Analyst Agent
  (DANA) for the CLI. SQL-first exploration via MCP data sources,
  schema discovery + caching, query formulation, analysis, and
  matplotlib/seaborn-style visualizations. Read-only by design.
  Sources: docs.devin.ai/work-with-devin/data-analyst,
  docs.devin.ai/use-cases/gallery/dana-slack-data-analyst,
  docs.devin.ai/release-notes/2025.
- **playbook skill**: replicates Devin cloud's Playbook feature for
  the CLI. Structured prompt template (Procedure, Specifications,
  Advice, Forbidden Actions, Required from User), local library
  (`.devin/playbooks/*.devin.md`), macro approximation, create-from-
  session workflow. Sources: docs.devin.ai/product-guides/creating-playbooks,
  docs.devin.ai/product-guides/using-playbooks,
  docs.devin.ai/work-with-devin/advanced-capabilities.
- **obsidian-workflow skill enhanced**: 4 new steps (17-20) complementing
  existing rigor to match DeepWiki cloud. Effort levels (low/medium/high)
  in `wiki-config.json` controlling depth. Deep Research pass (Step 18)
  — architecture critique, anti-patterns, optimization opportunities,
  senior-reviewer-level analysis. TechDebt page (Step 19, `11-TechDebt.md`)
  — cited issues, numbered (AP-001/OPT-001), categorized. Conversational
  Q&A (Step 20) — `deep-mode` skill integration for multi-pass search
  over wiki with double citations (wiki + source). Backward compatible:
  absent `effort` defaults to `high` (existing behavior). Sources:
  docs.devin.ai/work-with-devin/deepwiki, cognition.com/blog/deepwiki,
  marktechpost.com/2025/04/27/devin-ai-introduces-deepwiki.
- **obsidian-workflow validators**: 2 new scripts + 1 updated.
  `validate_wiki_content.py` (9 content rigor checks: source path:line
  format, min 5 sources per page, Sources: footers, overview links to
  all root pages, function ## Links, source columns in tables, TechDebt
  content, architecture critique, effort valid). `find_orphan_pages.py`
  (graph orphan detection — referenced in checklist but did not exist).
  `validate_wiki_structure.py` updated with 3 new checks (effort valid,
  TechDebt exists, arch critique section). SKILL.md updated with
  validation scripts table and content rigor checklist item.
- **manifest.json scripts list**: added `scripts` array (was missing —
  `script_count: 12` but no list). 12 .py + 1 .js entry. audit.py check
  [9b] validates consistency (count match, disk existence). Check count
  23 -> 24.
- **Counts updated**: 46 -> 49 skills in README.md (summary, diagram,
  tree, badge), TOOLS-MAP.md, SKILL-TIERS.md (3 new entries in
  Pesquisa/Data/Planejamento sections), manifest.json (3 entries +
  skill_count 46->49), audit.py (checks [9] and [18]).

### Fixed (iter 8.3 — self-improvement loop: hook FP/FN fixes + audit hardening)

- **destructive-gate.py commit message parsing**: strip_commit_message()
  now extracts only the command portion before `-m`/`-F`/`--message`,
  preventing the gate from blocking descriptive commit messages that
  mention gate names. (ref-030)
- **check-ai-signature.py self-detection skip**: write/edit to
  check-ai-signature.py or validate-skill-format.py was blocked because
  the detector code contains the signature patterns. Added self-detection
  skip. Also fixed exec handler to extract `-m` message. (ref-031)
- **silent-error-review.py false positives**: bare exception-name regex
  matched past-tense fix descriptions ("the fix resolved the KeyError").
  Fixed: require colon after exception name or Traceback/raise prefix.
  (ref-032)
- **validate-refinement-evidence.py tool-call patterns**: flagged
  ref-002 as PHANTOM despite evidence containing write/edit/exec. Added
  write|edit|exec to REPRODUCIBLE_PATTERNS regex. (ref-033)
- **check-ai-signature.py allowed contexts**: "AI-assisted tooling"
  blocked descriptive documentation. Added ALLOWED_CONTEXTS denylist for
  AI-assisted tooling/development/review and AI-generated content/images.
  (ref-034)
- **behavioral-nudge.py syntax error**: muted print left multi-line dict
  literal active, causing SyntaxError. Restored print call. (ref-035)
- **constraint-pinning.py empty main()**: main() was `pass` with no
  `__main__` guard — hook never wrote markers or re-injected constraints.
  Restored full implementation. (ref-036)
- **check-push-green.py empty main()**: main() was `pass` — hook never
  blocked any git push. Restored full implementation with stdin parse,
  PreToolUse/exec/git-push checks, test runner, held-out gap. (ref-037)
- **check-push-green.py gap check investigation**: empty tests/validation/
  makes gap check dead code (val_passed=False never blocks). No code
  change — test infrastructure gap. (ref-038, investigated)
- **.gitignore .pytest_cache**: added .pytest_cache/ to .gitignore
  (was not ignored despite internal .gitignore). (ref-039)
- **audit.py __main__ guard check**: added check [2b] to detect hook
  scripts missing `if __name__ == "__main__"` guard. Would have caught
  iters 4-6 bugs. Updated check count 24->25. (ref-040)
- **check-ai-signature.py multi-context strip**: check_text with two
  allowed contexts returned True (blocked) because loop stripped one
  context at a time. Fixed: strip ALL contexts cumulatively, then check.
  (ref-041)
- **destructive-gate.py SQL false positives**: SQL_DESTRUCTIVE regex
  matched echo/grep/cat commands containing keywords. Added SQL_CLIENTS
  regex — gate now requires both SQL_DESTRUCTIVE and SQL_CLIENTS. (ref-042)
- **destructive-gate.py WinRM false negatives**: Remove-Item with path
  before flags, or no target, was not blocked. Added WIN_RM_RE_PATH_FIRST
  and WIN_RM_RE_NOTARGET patterns. (ref-043)
- **validate-skill-format.py AI signature false positives**: flagged
  descriptive contexts inconsistently with check-ai-signature.py. Added
  AI_ALLOWED_CONTEXTS tuple matching check-ai-signature.py. (ref-044)
- **destructive-gate.py force-with-lease**: GIT_FORCE_PUSH blocked
  `--force-with-lease` (safe alternative). Removed from alternation,
  added negative lookahead. (ref-045)
- **check-ai-signature.py .bak file filtering**: substring match
  filtered .bak variants as self-files. Replaced with regex matching
  exact filename at end of git diff path. (ref-046)
- **silent-error-review.py warning+error lines**: signal_lines stripped
  entire lines containing warning keywords, causing false negatives when
  a line had both warning AND error indicators. Fixed: only strip if
  noise without error. (ref-047)

### Fixed (iter 8.4 — continuous improvement directive: data integrity + gap check activation)

- **refinements.log.jsonl duplicate IDs**: 48 entries had 30 unique IDs
  (16 duplicates) — rollback-by-ID was ambiguous. Renumbered all entries
  sequentially ref-001 to ref-048. (ref-048, LOOP 1)
- **audit.py refinement ID uniqueness check**: added check [25] to
  detect duplicate IDs in refinements.log.jsonl. Prevents recurrence.
  Check count 25->26. (ref-048, LOOP 2)
- **tests/validation/ populated**: 4 infrastructure smoke tests added
  (audit passes, skill-format passes, refinement-evidence valid).
  Activates check-push-green.py gap check (was dead code with empty
  validation/). Rule 16 reward hacking guard now operational. (ref-048,
  LOOP 3)
- **manifest.json stale purposes**: diagnosing-bugs and primeagent-
  reference had outdated purpose fields vs SKILL.md descriptions. Synced
  to current frontmatter. (ref-048, LOOP 4)
- **audit.py manifest/SKILL.md sync check**: added check [26] to detect
  stale manifest purposes vs SKILL.md descriptions. Prevents recurrence.
  Check count 26->27. (ref-048, LOOP 4)

### Fixed (iter 8.2 — self-improvement loop: stale refs + model info + encoding)

- **dispatching-parallel-agents model info**: skill table said
  implementer/debugger use "parent" model, but `agents/implementer.md`
  and `agents/debugger.md` pin `model: swe-1-7`. Updated table and
  Model Selection section to reflect SWE-1.7 (free, 262K) as default
  for implementers. Source: cognition.com/blog/swe-1-7.
- **subagent-router stale model info**: 5 agent profiles had stale
  SWE-1.6/$ cost info. Updated all to SWE-1.7 (262K, FREE), added
  `subagent_explore` PAID warning, fixed 4 references to pruned
  `subagent-driven-development` skill.
- **Agent profiles AgentCARD**: added bottleneck role awareness to
  all 5 profiles (architect=planner for debugging, reviewer=reviewer
  for doc analysis, researcher=executor for research). Source:
  arXiv:2606.20629.
- **MODEL-GUIDE.md benchmarks**: added SWE-1.7 vs GLM-5.2 comparison
  table (FrontierCode 42.3% vs 24.5%, Terminal-Bench 81.5% vs 81.0%,
  SWE-Bench 77.8% vs 74.5%) and 10-task routing matrix. Source:
  cognition.com/blog/swe-1-7.
- **render-graphs.js stale ref**: example used `subagent-driven-
  development` (deleted in iter 8.0). Replaced with `obsidian-
  workflow` (only skill with Mermaid diagrams).
- **obsidian-workflow validators rename**: 3 scripts had stale
  `obsidian-project-docs` in docstrings/argparse (skill renamed to
  obsidian-workflow in iter 8.0). Fixed to "Obsidian codebase wiki".
- **primeagent-reference adaptation status**: SKILL.md said "9/9
  features adapted" but 2 were pruned (session-checkpoint, heartbeat).
  Fixed to "7/9 adapted, 2 pruned" — consistent with README bullets.
- **README adaptation status**: 2 stale "9/9 features" references
  (lines 262, 288) contradicted own bullet list ("2 pruned") and
  primeagent-reference skill. Fixed to "7/9 adapted (2 pruned)".
- **install.ps1/export.ps1 encoding**: PowerShell 5.x read UTF-8
  files without BOM as Windows-1252, causing parser errors on
  em-dashes. Added UTF-8 BOM (EF BB BF) to both .ps1 files.
- **CHANGELOG missing iter 8.2**: Unreleased section had iter 8.1
  and 8.0 but was missing 9 refinements (ref-011 to ref-019) from
  subsequent sessions. Added iter 8.2 Fixed section.
- **TOOLS-MAP missing hook entry**: hooks table missing
  `behavioral-nudge.py` (UserPromptSubmit) — added in commit bfef22b
  but not documented. Added row.
- **README hooks table missing 2 entries**: missing `validate-
  mermaid.py` (PreToolUse write/edit) and `behavioral-nudge.py`
  (UserPromptSubmit). Added 2 rows to match hooks.v1.json.
- **SKILL-TIERS stale token counts**: 3 skills updated after
  2026-08-20 measurement had stale counts: primeagent-reference
  7876→10091 (28% off), obsidian-workflow 14798→17435 (18% off),
  dispatching-parallel-agents 9710→10065 (3.7% off). Updated counts
  + measurement date to 2026-08-22.
- **manifest.json vague purpose fields**: planning-pipeline and
  obsidian-workflow both had the identical string "merged planning/
  obsidian pipeline" as their purpose — two different skills with the
  same description. Fixed to their real SKILL.md frontmatter
  descriptions (spec/tickets/questionnaire; Obsidian 4 modes).
- **SKILL-TIERS 4 more stale token counts**: writing-plans 1746→1704,
  executing-plans 551→535, wayfinder 2936→2938, playbook 2400→1496
  (60% off — playbook SKILL.md was rewritten shorter in iter 8.1).
  Updated 4 counts in the planning/decision domain rows.
- **Planning flow unification (grilling vs ask-matt)**: grilling
  SKILL.md mandated writing-plans as its ONLY terminal state ("Do NOT
  invoke any other implementation skill"), but ask-matt SKILL.md
  routed grilling → planning-pipeline (Spec) → planning-pipeline
  (Tickets) → implement without mentioning writing-plans. Unified:
  grilling now offers both exits (planning-pipeline/Tickets canonical,
  writing-plans alternative for single-session detailed plans);
  ask-matt now mentions writing-plans → executing-plans as alternative
  to Tickets → implement; writing-plans now documents its input
  sources and positions itself vs Tickets mode. Updated 3 token
  counts (grilling 2511→2656, writing-plans 1704→1785, ask-matt
  2893→3037). Synced 3 skills to live.

### Fixed (iter 8.0 — doc count consistency + hook events accuracy + legacy cleanup)

- **Deleted 3 legacy skill dirs**: obsidian-project-docs (consolidado em
  obsidian-workflow), subagent-driven-development (consolidado em
  dispatching-parallel-agents), systematic-debugging (consolidado em
  diagnosing-bugs). Reduzido 49→46 skills. README "Merged from" table
  mantida como histórico de consolidação.
- **TOOLS-MAP.md stale counts**: "46 skills" → "49 skills" → "46 skills"
  (legacy cleanup), "11 scripts" → "12 scripts", "6 eventos" → "8 eventos",
  "25 ativas + 2 modo-dependentes" → "26 ativas + 2 modo-dependentes"
  (28 total), "19/27" → "19/28", "8 excluídas" → "9 excluídas".
  Verified against disk and docs.devin.ai/cli/extensibility/hooks/overview
  (8 events). Bundle uses 6 of 8; PermissionRequest and SessionEnd
  documented as available but unused.
- **README.md stale counts**: diagram "46 skills" → "49 skills" →
  "46 skills", "6 events" → "8 events"; hooks header "6 events" →
  "8 events"; install summary "6 hook events" → "8 hook events";
  badge skills-49 → skills-46.
- **SKILL-TIERS.md**: typo double period `PAGO)..` → `PAGO).`.
- **manifest.json**: removed 3 legacy skill entries, skill_count 49→46,
  tool_count 27→28.
- **audit.py check [24]**: new check verifies TOOLS-MAP.md and README.md
  counts match disk reality (skills, scripts, hook events, tools, excluded).
  Prevents future stale-count regressions.
- **validate-refinement-evidence.py**: added PowerShell cmdlet patterns
  (Select-String, Get-ChildItem, etc.) to REPRODUCIBLE_PATTERNS — fixes
  false phantom-guardrail flag on Windows-documented refinements.
- **Sources**: docs.devin.ai/cli/extensibility/hooks/overview (8 events),
  docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks (event details),
  Get-ChildItem skills/scripts (disk counts).

### Changed (iter 7.3 — política de modelos CONDICIONAL)

- **Política alterada de FREE-ONLY para CONDICIONAL**: modelos pagos agora
  são permitidos para subagents **quando o parent está em modelo pago**
  (usuário fez `/model opus`, `/model sonnet`, etc.). Quando o parent está
  em modelo FREE (default `glm-5-2`), subagents DEVEM ser FREE.
- **Caso 1 (Parent FREE)**: FREE-ONLY mantido. `subagent_explore` (SWE-1.6
  pago), `swe` alias (SWE-1.7 Lightning pago) e todos os modelos pagos
  proibidos para subagents.
- **Caso 2 (Parent PAGO)**: `subagent_explore` (SWE-1.6, $0.5/$2.5) é
  permitido — mais barato que o parent. `subagent_general` herda o modelo
  pago do parent. Custom profiles com `model: swe-1-7` continuam FREE
  (preferir quando possível).
- **Arquivos atualizados**: `AGENTS.md` Rule 20, `MODEL-GUIDE.md` (novo
  protocolo condicional com 2 casos), `TOOLS-MAP.md`, e 5 skills
  (`dispatching-parallel-agents`, `primeagent-reference`, `context-folding`,
  `obsidian-workflow`, `self-extend`) — todas as annotations "NUNCA usar
  `subagent_explore`" agora dizem "NUNCA usar quando parent é FREE".

### Fixed (iter 7.1 — `subagent_explore` PAGO bug)

- **BUG CRÍTICO DE CUSTO (iter 7.1)**: o profile built-in `subagent_explore`
  roda no **default subagent model (SWE-1.6, PAGO $0.5/$2.5 MTok)**. Não há
  override local — apenas enterprise settings podem mudar isso. O system
  prompt do Devin CLI recomenda `subagent_explore` para read-only exploration,
  então qualquer dispatch desse profile incorre em custo.
- **Solução**: adicionada regra em `AGENTS.md` (Rule 20) e `MODEL-GUIDE.md`
  proibindo `subagent_explore`. Direcionado para o profile customizado
  `researcher` (`agents/researcher.md`, pin `model: swe-1-7`, gratuito, 262K)
  que tem as mesmas capacidades read-only.
- **Skills corrigidas**: 5 skills (`dispatching-parallel-agents`,
  `primeagent-reference`, `context-folding`, `obsidian-workflow`,
  `self-extend`) tinham 10 referências ativas a `subagent_explore` como
  recomendação de uso. Todas substituídas por `researcher` com annotation
  "NOT `subagent_explore` — PAID SWE-1.6".
- **Fonte**: docs.devin.ai/cli/subagents — "subagent_explore: The default
  subagent model — a fast, cheap model (SWE-1.6 by default)".

### Changed (iter 7.0 — FREE-ONLY policy enforcement)

- **Protocolo de escalada pago REMOVIDO**: `MODEL-GUIDE.md` tinha um
  protocolo de 6 níveis que recomendava GLM-5.2 Max ($0.7/$2.2),
  DeepSeek V4 Flash ($0.14/$0.28), Opus ($5/$25) e GPT-5.4 ($2.5/$15)
  como fallbacks. Substituído por protocolo FREE-ONLY: se GLM-5.2 High +
  SWE-1.7 fan-out falharem, parar e reportar ao usuário — nunca escalar
  para pago.
- **AGENTS.md Rule 20**: "Só usar como fallback após 3+ tentativas
  documentadas" → "🚫 NUNCA usar modelos pagos. Se falharem, parar e
  reportar ao usuário."
- **Skills corrigidas**: `dispatching-parallel-agents`, `primeagent-reference`
  e `self-extend` recomendavam `sonnet` (pago, $2/$10) e `SWE-1.6` (pago,
  $0.5/$2.5) para subagent profiles. Corrigido para `SWE-1.7` (gratuito,
  262K) em todas as referências.
- **TOOLS-MAP.md**: tabela de aliases agora marca todos os modelos pagos
  com "**PAGO** — não usar" e adiciona `swe-1-7-medium` (gratuito) como
  alternativa.
- **Regra ABSOLUTA adicionada**: "NUNCA usar modelos pagos. Os modelos
  gratuitos (GLM-5.2 High + SWE-1.7) cobrem 100% dos casos."

## [2.5.1] - 2026-08-21

GLM-5.2 High + SWE-1.7 optimization. 9 iterations, all changes verified against
primary sources (`devin models list`, docs.devin.ai, cognition.com, z.ai).

### Fixed (CRÍTICO — agents/ usando modelo PAGO em vez de gratuito)

- **BUG CRÍTICO DE CUSTO**: todos os 5 agents/ (architect, debugger,
  implementer, researcher, reviewer) usavam `model: swe` que é alias para
  `swe-1.7-lightning` (PAGO, $2.5/$12.5 MTok, 202K context). O modelo
  gratuito é `swe-1-7` (SWE-1.7 Max, 262K context, Free). Corrigido: todos
  os agents/ agora usam `model: swe-1-7`. Descoberto via `devin models list`.
- **Impacto**: cada subagent dispatch estava custando ~$2.5/$12.5 MTok
  desnecessariamente. O modelo gratuito tem MAIS contexto (262K vs 202K).
  Correção salva dinheiro E dá mais headroom de contexto.
- **SWE-1.7 context window** — corrigido de "200K/256K ambíguo" para
  definitivamente 262K. Verificado contra `devin models list` e fontes
  primárias (cognition.com/blog/swe-1-7, HuggingFace Kimi-K2.7-Code card).
- **BOM em agent files**: 4 de 5 agent files tinham BOM (EF BB BF) no início.
  BOM em YAML frontmatter pode impedir o parser de reconhecer `---`, fazendo
  `model: swe-1-7` ser ignorado — agent cairia para SWE-1.6 (PAGO). BOM
  removido. `install.ps1`/`install.sh` agora stripam BOM automaticamente.
- **`validate-mermaid.py` fail-closed → fail-open**: quando Node.js/mermaid
  indisponível, o hook bloqueava TODOS writes com mermaid. Corrigido para
  fail-open (consistente com os demais hooks do bundle).
- **`constraint-pinning.py` marker not session-scoped**: marker usava filename
  fixo sem session_id — sessions paralelas sobrescreviam markers um do outro.
  Corrigido: filename inclui session_id. SessionStart limpa markers stale.
- **`constraint-pinning.py` dead code removido**: `inject("PostCompaction")`
  era chamado mas PostCompaction não suporta `additionalContext` (per docs).
  Chamada removida; mecanismo correto é marker-based re-injection no
  UserPromptSubmit.
- **`refine-review-prompt.py` skill ref fixa**: referência a skill `refine`
  inexistente → `primeagent-reference` Refine mode.
- **`mermaid-parse-check.js` hardcoded paths**: paths machine-specific
  (`C:\Users\Fingertech\scoop\...`) → portable lookup (require.resolve,
  npm root -g, Linux paths, Windows fallback).
- **MODEL-GUIDE.md dados de GLM-4.6 atribuídos a GLM-5.2**: max output
  128K → 131,072. Custos $1.4/$4.4 removidos (GLM-5.2 High é gratuito).
- **24 broken skill references**: `subagent-driven-development`→`dispatching-parallel-agents`,
  `systematic-debugging`→`diagnosing-bugs`, `to-spec`→`planning-pipeline`,
  `find-skills`→`tool-and-skill-discovery`, `grill-with-docs`→`grilling`,
  `wiki-audit/audit.py`→`obsidian-workflow/scripts/audit.py` (11 skills).
- **`hooks.v1.json` `%APPDATA%` → `{{APPDATA}}`**: sintaxe Devin-native.
- **`audit.py` live_base stale**: `C:\Users\leand\...` → auto-detect
  (WSL/Linux/Windows).

### Added

- **Rule 20: Model-aware operation** — GLM-5.2 High (200K, gratuito, thinking,
  tool-use nativo) é primário; SWE-1.7 (262K, gratuito, self-compaction,
  1000 TPS) é subagent via `model: swe-1-7`. Non-pinned. Ver MODEL-GUIDE.md.
- **MODEL-GUIDE.md** — specs verificadas (GLM-5.2 + SWE-1.7), linhagem,
  estratégia de model pin, context budget, protocolo de escalada (6 níveis),
  reasoning effort guide, subagent vs compaction decision table.
- **TOOLS-MAP.md** — mapeamento completo do runtime: 27 ferramentas, 7
  subagentes, 6 eventos de hook, 11 scripts, configs, modos, modelos.
- **validate-tool-args.py**: 6 validators adicionados (`ask_user_question`,
  `browser_preview`, `close_browser_preview`, `todo_write`, `apply_patch`,
  `exit_plan_mode`). Matcher depois otimizado 28→19 tools (removidos 9 no-ops).
- **install.ps1/install.sh**: `strip_bom` (remove BOM de agent files) e
  `dedup_agents_md` (remove duplicatas lowercase em FS case-sensitive).
- **context-budget.py**: reporta share de 200K (GLM-5.2) e 262K (SWE-1.7).
- **SKILL-TIERS.md**: custos de tokens medidos (bytes÷4), modelos alvo,
  anti-patterns expandidos.

### Changed

- **`silent-error-review.py` scope narrowed (noise reduction)** — PostToolUse
  matcher de `""` (all tools) → `^(exec|mcp_call_tool)$`. ALTK scope
  (arXiv:2603.15473): "best suited for verbose/tabular responses". Regexes
  tightened (error requer colon, test-failures requer count > 0). Max 1
  finding por call. Addresses PR #1 review comment on hook noise.
- **`validate-tool-args.py` matcher narrowed (latency reduction)** — 28→19
  tools. Removidos 9 tools com checks triviais/no-ops. Zero perda de
  validação real. Saves ~9 Python process spawns per session.
- **SKILL-TIERS.md reescrito** — custos medidos em vez de estimativas.
- **README.md** — 8 inconsistências corrigidas (rules 18→19, skills 47→46,
  tools 15→28→19, events 4→6, scripts 4→11).

### Verified

- `devin models list` — primary source (swe-1-7 = Free/262K, swe alias = Lightning/$2.5/202K)
- docs.devin.ai/cli/subagents — default router = SWE-1.6
- docs.devin.ai/cli/models — short names resolve to latest
- cognition.com/blog/swe-1-7 — SWE-1.7 specs (Kimi K2.7 base, self-compaction, 1000 TPS)
- HuggingFace Kimi-K2.7-Code card — Context Length: 256K (262,144 tokens)
- z.ai/blog/glm-5.2 — GLM-5.2 specs (gratuito, 200K, 131K max output)

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
