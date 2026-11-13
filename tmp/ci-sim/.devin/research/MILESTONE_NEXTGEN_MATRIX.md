# MILESTONE NEXTGEN - Redundancy & Integration Matrix

Date: 2026-10-24 · Branch: `milestone/v3.8.0` · Ledger: `.devin/ledgers/milestone-nextgen-recon.md`
Sources: 10 (8 repos/sites + 2 video workflows), all verified via primary source
(URLs in Section I). Phase-1 table approved by user; corrections vs the original
brief are marked `[CORRECTION]`.

## A. Current bundle state (what the sources collide with)

| Layer | Exists today |
|---|---|
| Design brain | `skills/impeccable` (22 cmds, text-only port), `skills/creative-engineering` (16 archetype anatomy files under `extensions/media-tools/knowledge_bases/aesthetics/` + `index.json`), `agents/art-director.md` (docs/03 contract: tokens, WCAG AA, state matrix), `skills/a11y-audit`, `skills/humanizer` (prose anti-slop) |
| Design muscle | none (no local search index, no deterministic UI linter) |
| Memory/read path | `semble` external CLI (`--limit 20`, `[SEMBLE-DOWN]`->`rg` fallback), `extensions/laya-tools/filebool.py` (`ask_laya_glob`/`ask_laya_filebool` batch classification), `rg`, `read`; `.devin/memory/MOC.md` + `memory-*` hooks; `mcp_config.json` EMPTY |
| Harness evolution | `skills/self-improvement` modes (improvement-loop 10-step, refine, harness-reference w/ PrimeAgent+RLM map, a2a-messaging, subagent-router); `scripts/refine-review-prompt.py`, `validate-refinement-evidence.py`, `check-push-green.py`; `tests/held-out/` |
| Install/export | `install.ps1`/`install.sh` (copy+merge to `%APPDATA%/devin`), `export.ps1`/`export.sh`, `scripts/render-user-hooks.py` (deterministic renderer hooks.v1.json->config.json.hooks), `manifest.json` w/ `export_hash` per skill |
| Fleet/RTS | `extensions/agent-rts` (server.py :8798, event-sourced World, intent/decision file queues, repo collectors, Three.js web UI; "observes and relays, never dispatches" canon), `extensions/rtsd` (:8797 sibling), `.devin/rts/` (fleet.json, events.jsonl, intents/, decisions/), `scripts/rts-emit.py|rts-decision.py|rts-intents.py` |
| Orchestration | `.devin/orchestrator_prompts_v2.md` (v3 asset-driven DAG, 7 personas, upstream_hashes sha8, DRAFT/APPROVED/BLOCKED, laya router/guard transitions), `agents/*.md` (14 profiles), `skills/dispatching-parallel-agents`, `skills/using-git-worktrees`, `skills/scheduled-turns` |
| 3D/media | `extensions/blender-operator` (TCP JSONL exec loop, full bpy, headless), `extensions/media-tools` (fx/ pipeline, grainrad, ascii_mancer, glb_input, intent.py+laya shadow), `skills/operate-blender`, `skills/youtube-fetcher` |
| Output economy | Rule 8 telegraphic; `scripts/post-exec.py`; `context-budget.py`; `skills/context-hygiene`, `effort-calibration`; `data/bundle-models.json` (effort routing) |

## B. The 10-source matrix

| # | Source (license) | Anatomy core | Local collision | Decision | Landing |
|---|---|---|---|---|---|
| 1 | `google-research/harness2` (Apache-2.0, Oct-2026, active) | PPC loop (Propose 2k INV+DOM -> Probe 4k rollouts -> Compose k aggregators); harness = `c1..c8` dict[path->content] + `SurfaceSpec`; omitted-is-inherited diffs; anti-overfit = no ground truth in loop + `lib.retain(earlier-only)` + separate judge stage | self-improvement modes, refine hooks, held-out suite | UPGRADE_EXISTING + NEW_EXTENSION | brain: `self-improvement/modes/{improvement-loop,refine,harness-reference}.md`; muscle: `extensions/harness-tree/` |
| 2 | `vercel-labs/agent-skills` (MIT per-skill) | 16 skills; `react-best-practices` 70 rules/8 cats (async-waterfall, bundle-analyzable-paths, cache); `composition-patterns`; `react-native-skills`; view-transitions; `web-design-guidelines` fetches rules at runtime | impeccable audit/optimize (generic), art-director (generic) | NEW_EXTENSION (as corpus) + UPGRADE_EXISTING (brain pointers) | `extensions/design-intelligence/data/frontend-rules/*.md` indexed by BM25; `impeccable`+`art-director` cite it |
| 3 | `nextlevelbuilder/ui-ux-pro-max-skill` (MIT, v2.15) | stdlib BM25 (`core.py` ~60 LOC, k1=1.5/b=0.75, synonyms+typo recovery), `search.py` CLI, `design_system.py`, 12 CSV domains (79 styles, 192 palettes, 74 typo, 22 stacks/1.260 rules, ux-guidelines 119, icons 105, motion 17), top-3+truncation = context-lean | `creative-engineering` KB does same job w/o engine | NEW_EXTENSION | `extensions/design-intelligence/` engine + CSV corpus + aesthetics re-indexed |
| 4 | `alchaincyf/huashu-design` (MIT, zh-first, v3.0) | 窄桥 protocol: §0 fact-verify->`product-facts.md`; routing table; 5 Form Questions; 3-direction gate (6 cand -> 3 real+3 alt, `direction-approved.md`, verbatim exemptions); §5 anti-slop lists + readability floors; `design_lint.py` + look-ledger | impeccable init/shape, art-director contract, creative-engineering archetypes | UPGRADE_EXISTING (brain only) | protocol sections merged into `impeccable`, `art-director.md`, `creative-engineering`; lint concept feeds #5 muscle |
| 5 | `pbakaus/impeccable` (Apache-2.0, skill v4.7.0) | ~62-rule registry (`antipatterns.mjs` ~32 slop + ~27 quality +3 newer) + `checks.mjs` pure fns; `npx impeccable detect --json` exit 0/1/2; PRODUCT.md (durable truth) vs DESIGN.md (Stitch-YAML tokens, fixed sections); 23-24 cmds [CORRECTION: count unverified] | our `skills/impeccable` = direct port, text-only | UPGRADE_EXISTING + NEW_EXTENSION + HOOK_INTEGRATION | skill sync (cmds, PRODUCT/DESIGN spec); `design-intelligence/design_lint.py` (Python port of registry+checks); `scripts/design-lint-gate.py` PostToolUse |
| 6 | `agencyagents.app` + `msitarzewski/agency-agents{,-app}` (MIT x2) | `tools.json` format contract ("same format => byte-identical"); `convert.sh` ref renderers -> 16 CLIs; `installs.json`+`corpus-index.json` SHA-256 ledger; **5-state reconcile** [CORRECTION: Current/Outdated/Modified/Removed/Foreign]; `backup_if_differs` (outside tool dirs, abort-on-fail, skip-identical) | install/export already render+sync; `render-user-hooks.py`; upstream_hashes sha8 | UPGRADE_EXISTING | `install.ps1`/`export.sh`/`install.sh` + new stdlib `scripts/install-ledger.py`; `tools.json` data file (Devin target first) |
| 7 | `DeusData/codebase-memory-mcp` (MIT, v0.12.1) | C binary: 162 vendored tree-sitter->SQLite FTS5-BM25 (camel tokenizer), static nomic-embed vectors, 17 MCP tools, sub-ms Cypher subset. [CORRECTION: "99% token savings" NOT reproduced - skillproof.dev measured +127% MORE tokens; 17 tools > our 15 cap] | semble (semantic), rg (exact), ask_laya_glob (batch bool), empty mcp_config | NEW_SKILL (routing doc) + NEW_EXTENSION (pattern-port) + benchmark gate | `extensions/code-graph/` (SQLite FTS5 minimal index, stdlib `sqlite3`); routing table into `skill-discovery`/research docs; real cbm only if held-out bench proves savings |
| 8 | `stablyai/orca` (MIT, hyper-active) | Electron fleet ctl: PTY-per-worktree, SSH relay daemon (13-byte JSON-RPC frames), hibernation->`getAgentResumeArgv`, hook ingest w/ `x-orca-agent-hook-token` + session-id registry (bounded 512), fan-out->compare, RN/Expo mobile | agent-rts/rtsd observe-only canon; fleet.json; worktrees+dispatch skills exist | UPGRADE_EXISTING | agent-rts opt-in dispatch lane (intents->spawn), worktree lanes in fleet.json, provider resume-argv table; remote relay deferred |
| 9 | YT `mvfo3pUiCCA` (Kyle Skelly, Sep-2026) | Blender low-poly blockout + auto camera path -> playblast MP4 -> multimodal LLM sec-by-sec prompt -> Seedance 2.5 repaint (keeps camera/framing, reference imgs for adherence) -> scroll-scrub web hero. Bridge = Higgsfield MCP (not generic blender-mcp) [CORRECTION]. Prompt template + scroll code not published | `blender-operator` (generic bpy loop; no blockout/playblast presets), media-tools, creative-engineering | NEW_SKILL + muscle presets | `skills/camera-blocking/` (workflow+templates); `extensions/blender-operator/presets/{camera_rig,playblast}.py`; Seedance = prompt-template only (external SaaS) |
| 10 | YT `cCFAIrbt_s8` -> `aicodeking/pandacode` (MIT+attribution) | Real Tauri app. Token Saver = prompt-fragment presets (caveman/lean/quiet) sent ON CHANGE only + cached sys-prompt (~650 tok/msg); queue vs Cmd+Enter steer; per-turn git diff; 2-click worktrees; 1 architect+3 workers w/ guards (silent->fail, 20min kill, <=20 rounds); auto-resume at RL reset; permission modes | Rule 8 ~= caveman; post-exec.py; scheduled-turns; orchestrator_prompts v3 | HOOK_INTEGRATION + UPGRADE_EXISTING | `scripts/token-saver.py` (UserPromptSubmit injector w/ mode state); quiet-tools compression in `post-exec.py`; RL-detect->resume intent via `stop-guard.py`+scheduled-turns; team guards -> orchestrator_prompts v4 |

## C. Unified Design & Frontend Architecture (AC2)

One muscle, three brain upgrades, one gate. Zero new design skills.

```
extensions/design-intelligence/                  [NEW_EXTENSION - stdlib only]
|-- search.py             BM25 CLI (port of ui-ux-pro-max search.py+core.py,
|                         k1=1.5 b=0.75, synonyms, difflib typo recovery,
|                         --domain, --top-k=3, TRUNCATE_AT long fields)
|-- design_system.py      multi-domain fan-out -> MASTER.md + pages/*.md
|                         (variance/motion/density dials, --persist, --force)
|-- design_lint.py        ~62-rule detector (port of impeccable
|                         antipatterns.mjs+checks.mjs + huashu design_lint.py):
|                         html.parser+CSS regex, --json/--list-rules, exit 0/1/2,
|                         ignores add-file/add-value
|-- look_ledger.py        JSONL ledger + `compare` reskin check (huashu port)
|-- data/
|   |-- styles.csv colors.csv typography.csv products.csv ux-guidelines.csv
|   |   icons.csv motion.csv charts.csv landing.csv ui-reasoning.csv   (port)
|   |-- stacks/*.csv        22 stacks / ~1.260 rules                     (port)
|   |-- frontend-rules/     vercel rules vendored .md (indexed as docs)  (port)
|   |-- aesthetics/         symlink/alias -> media-tools/knowledge_bases/
|   |                       (single source stays; index.json -> corpus doc)
|-- tests/                fixture pages w/ seeded slop; search relevance set

skills/impeccable          [UPGRADE_EXISTING]
+ PRODUCT.md vs DESIGN.md spec (init/document cmds, Stitch-YAML frontmatter)
+ command sync 22->24 [verify exact upstream list before writing]
+ sec0 fact-verify -> product-facts.md (huashu)
+ 3-direction gate -> direction-approved.md (huashu; verbatim exemptions)
+ calls: design_lint.py inside audit/critique; search.py inside shape/colorize

skills/creative-engineering [UPGRADE_EXISTING]
+ BM25 retrieval step BEFORE reading archetype file (index.json stays alias layer)
+ 5 Form Questions mapped: motif -> archetype; temperature -> palette domain;
  capacity -> density dial; distance -> typography scale; role -> stack ruleset
+ vercel frontend-rules referenced for implementation passes

agents/art-director.md      [UPGRADE_EXISTING]
+ 5 Form Questions inside <deep_analysis>
+ direction-approved.md in output contract (3 real + 3 alternates evidence)
+ frontend-rules citation when docs/02 stack = React/Next/RN

hooks.v1.json -> PostToolUse (write|edit)  [HOOK_INTEGRATION]
`python scripts/design-lint-gate.py` - bounded subset (~12 rules) on
*.html/*.css/*.tsx/*.jsx/*.vue/*.svelte writes; advisory stderr, never blocks.
```

## D. Memory & Context Governance (AC3)

### D.1 Tripartite code-read routing (+ two primitives)

| Question class | Route | Why / bounds |
|---|---|---|
| Exact string, symbol name, pattern | `rg` / grep tool | deterministic, zero cost |
| Structural: definition/callers/callees, file outline, cross-file edges, dep graph | `extensions/code-graph` index (pattern-port) -> `query`/`outline`/`refs` cmds | AST facts from SQLite FTS5, sub-ms; **cbm as MCP only after gate D.2** |
| Semantic fuzzy ("where is auth handled", "find retry logic") | `semble search "<q>" ./ --limit 20` -> `[SEMBLE-DOWN]`->rg | vectors; bounded top-k per existing contract |
| Boolean batch >10 files ("has tests", "contains secrets") | `ask_laya_glob`/`ask_laya_filebool` (filebool-v1) | one forward pass/file, abstains; never a conclusion (Rule 12) |
| <10 files, fact directly checkable | `read` | cheapest certain path |
| "What changed since T" | git/`code-graph detect_changes` (if ported) | deterministic diff |

Rules: structural graph is for WHERE/HOW-WIRED questions, not "does X work".
Laya decides reading order, never facts. Semble bounded at --limit 20, max 2
extra pages w/ justification (orchestrator canon).

### D.2 cbm adoption gate (approved: pattern-port + benchmark)

1. Port pattern minimal: `extensions/code-graph/` = stdlib `sqlite3` FTS5 over
   file index (path, symbols via regex/tokenizer split, mtime+hash). No tree-
   sitter vendoring, no C binary, no daemon in v1.
2. Held-out benchmark issue: measure tokens-per-answer on our own repos
   (bundle + one consumer project) for N=20 structural queries, cbm-MCP vs
   code-graph vs rg baseline. Adopt cbm as **lazy-enabled MCP**
   (`mcp_config.disabled.json`) only if median savings >=30%; 17 tools exceeds
   the 15-cap, so adoption also requires per-server tool scoping review.

### D.3 Token-Saver modes (PandaCode port)

- `scripts/token-saver.py` on `UserPromptSubmit`: reads `.devin/output-mode.json`
  (`{"mode": "off|caveman|lean|quiet", "set_at": ts}`); injects the preset
  fragment ONLY when mode changed since last inject (state file under `.devin/`),
  mirroring the ~650 tok/msg cached-prompt saving.
- Presets (prompt fragments, agent-visible):
  - `caveman`: extreme-terse answers, bullet-only, no preamble (extends Rule 8).
  - `lean`: minimal-diff code, no prose around code, no refactor-not-asked.
  - `quiet`: suppress tool narration + collapse verbose tool output.
- `quiet` muscle half lives in `post-exec.py`: collapse repeated lines,
  tail-N on test logs, dedupe stack traces (bounded, opt-in via mode file).
- Auto-resume: `stop-guard.py` detects rate-limit signature in session tail ->
  writes `.devin/rts/intents/i*.json` `{"kind":"resume_at","when":<reset>}` +
  `scheduled-turns` entry; user-visible, opt-in.
- Per-turn footer: `scripts/post-exec.py` appends `git diff --stat` 1-liner when
  cwd is a git repo and mode != off (cheap, deterministic).

## E. Harness evolution (Phase 2 detail)

| harness2 element | Our mapping |
|---|---|
| `c1..c8` component tree (system prompt, guardrails, memory, tool guidance, subagents, skills, scripts, plugins) | `extensions/harness-tree/tree.py`: `dict[path->content]` over AGENTS.md, global_rules.md, hooks.v1.json, memory/, agents/, skills/, scripts/, mcp_config.json + `SurfaceSpec` per-target (devin now; gemini/claude/codex entries gated on platform branch) |
| Propose (2k INV+DOM candidates) | refine-mode: proposal queue already emits candidate diffs; add explicit INV vs DOM candidate classes + k-batching |
| Probe (4k rollouts, same task) | validation+held-out suites; probe = run candidate tree through `pytest tests/held-out` + ledger VF commands |
| Compose (k aggregators) | publish step: compose adopted tree from evidence; adoption keeps refined-or-base (never auto-worse) |
| `lib.retain(earlier-only)` | lessons/ledgers retention rule: a lesson may cite only evidence older than itself - add to refine mode + `validate-refinement-evidence.py` check |
| Contrast-only, no ground truth in loop | already our stance (Rule 15/16); codify in improvement-loop contract |
| `harness2-check` preflight | `scripts/session-start.py` optional `--check` variant: verifies ledger/refinements integrity |
| `harness2-judge` separate stage | `qa-ci` profile already = independent verifier; keep separation canon |

install/export drift ledger (agency-agents port):
- `scripts/install-ledger.py` (stdlib): `installs.json` records
  `{slug, tool, scope, dest, source_hash, rendered_hash(sha256 of bytes),
  installed_at, corpus_version}`; `corpus-index.json` slug->hashes (stable
  order); reconcile -> 5 states [Current/Outdated/Modified/Removed/Foreign];
  `backup_if_differs` -> `.devin/backups/<name>.<ts>` BEFORE overwrite,
  abort-on-fail, skip on byte-identical.
- `tools.json` at bundle root: renderer contract table; initial rows = devin
  (active). gemini/claude/codex rows added when `platform/gemini-argus` lands.
- Determinism rule ported verbatim: renderers forbid timestamps/randomness;
  same format => byte-identical (checked by a `check-tools`-style audit test).

## F. Fleet orchestration & multi-agent UX (Phase 3 detail)

agent-rts upgrades (preserves "game observes" canon - dispatch is opt-in lane):
- `POST /intent {"kind":"spawn", profile, task, worktree}` -> intent file
  consumed by an explicit user-approved bridge (not auto-exec); status back
  into fleet.json lanes.
- fleet.json schema += `lane` (worktree path), `resume_argv` (provider table:
  devin/claude/codex -> resume cmd), `hibernated_at`.
- Hook ingest hardening (orca pattern): `x-agent-hook-token` shared secret on
  `rts-emit.py` POST path; session-id-bound registry, bounded size, PTY-exit
  cleanup equivalent (subagent-id liveness sweep).
- PandaCode guards -> orchestrator_prompts v4: architect+3-worker template,
  silent-worker->fail-to-architect, 20min turn kill, <=20 rounds, pause never
  consumes retries; queue-vs-steer semantics documented (Devin CLI queues by
  nature; steer = next-turn inject).
- Worktree 2-click: `using-git-worktrees` += lane register/deregister cmds
  writing `.devin/rts/worktrees.json`; merge-back refuses dirty/conflict
  (PandaCode semantics).
- Deferred non-goals: SSH remote relay, Electron GUI, mobile companion.

## G. Blender camera-blocking pipeline (Phase 3 detail)

```
NEW_SKILL skills/camera-blocking/
  blockout conventions (low-poly greybox, camera path only, look irrelevant)
  -> blender-operator presets -> playblast MP4 -> sec-by-sec prompt template
  -> external repaint (Seedance-class, prompt adapter only) -> scroll-scrub
  hero scaffold (paused video, playhead bound to scrollY)

extensions/blender-operator/presets/        [muscle adds]
  camera_rig.py    spline/tracked camera path helpers, shot primitives
                   (orbit, dolly, crane, exploded-view spread)
  playblast.py     viewport/EEVEE fast render -> mp4 (fps/res args)
  blockout.py      primitive-kit scene builder (boxes/cylinders, grey mat)

boundary: Seedance/Higgsfield = external SaaS; the skill emits a
prompt-template (references + hard location map + timestamp beats), never a
client. scroll-scrub = scaffold HTML/JS generated into the user project.
```

## H. Issue DAG (Phase 4 output, `.devin/issues/`)

```
M2_01 design-intelligence scaffold (BM25+CSV+aesthetics index)   [no deps]
M2_02 design_lint.py port (~62 rules, --json, exit codes)        [no deps]
M2_03 impeccable skill upgrade (spec+cmds+sec0+3-dir gate)       [01,02]
M2_04 creative-engineering+art-director brain upgrades           [01]
M2_05 design-lint-gate.py hook (PostToolUse subset)              [02]
M2_06 install drift ledger (installs.json+5-state+backup)        [no deps]
M2_07 tools.json renderer contract (devin row first)             [06]
M2_08 self-improvement PPC upgrade (modes+anti-leakage)          [no deps]
M2_09 extensions/harness-tree (SurfaceSpec dict-diff engine)     [08]
M2_10 code-graph pattern-port (SQLite FTS5 index) + routing doc  [no deps]
M2_11 token-saver hooks (mode injector+quiet+RL-resume+diff-footer) [no deps]
M2_12 agent-rts dispatch lane + worktree lanes + resume-argv     [no deps]
M2_13 camera-blocking skill + blender presets                    [no deps]
M2_14 orchestrator_prompts v4 (team guards+direction contract)   [03,04]

parallel-capable: {01,02,06,08,10,11,12,13} then {03,04,05,07,09} then {14}
```

## I. Source register

- github.com/google-research/harness2 (Apache-2.0) + arXiv:2610.14224
- github.com/vercel-labs/agent-skills (MIT per-skill) - react-best-practices rules/*.md
- github.com/nextlevelbuilder/ui-ux-pro-max-skill (MIT, v2.15.0) - src/ui-ux-pro-max/{core,search,design_system}.py + data/*.csv
- github.com/alchaincyf/huashu-design (MIT, v3.0.0) - SKILL.md + references/{workflow,directions,design-context}.md + scripts/design_lint.py
- github.com/pbakaus/impeccable (Apache-2.0, v4.7.0) - skill/, cli/engine/registry/antipatterns.mjs, scripts/detector/rules/checks.mjs, reference/document.md
- github.com/msitarzewski/agency-agents + agency-agents-app (MIT) - tools.json, scripts/convert.sh+lib.sh, src-tauri/src/{render,install}/mod.rs, memory-bank/systemPatterns.md
- github.com/DeusData/codebase-memory-mcp (MIT, v0.12.1) - src/{mcp,store,pipeline}, docs/BENCHMARK.md, discussion#12, skillproof.dev replication
- github.com/stablyai/orca (MIT) - src/{relay,main,cli}, skills/, mobile/, cloud/
- youtube.com/watch?v=mvfo3pUiCCA (Kyle Skelly) - corroborated: moderncreator.app, qiita.com reproduction, rubenstom gumroad pack
- youtube.com/watch?v=cCFAIrbt_s8 (AI Code King) -> github.com/aicodeking/pandacode (MIT+attribution); goremy.ai/chooseto.ai coverage

## J. Non-goals (this milestone)

- No always-on MCP servers; no changes to active `mcp_config.json`.
- No new design/UX skills (unification, not duplication).
- No Seedance/Higgsfield clients; prompt-template boundary only.
- No SSH remote fleet relay, no Electron GUI, no mobile companion.
- No tree-sitter vendoring / C binaries in `extensions/` v1.
- No changes outside `.devin/` in this planning phase.
