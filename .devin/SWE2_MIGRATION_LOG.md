# SWE-2 Migration Log

Branch: `bundle-swe2`
Goal: migrate the devin-bundle to a SWE-2-native architecture — routing by effort level (Medium/High/Max), outcome-plus-acceptance-criteria prompts, no forced chain-of-thought or reasoning micro-management.

## Paradigm removed vs introduced

| Legacy paradigm | SWE-2 paradigm |
|---|---|
| Model-size routing (`glm-5-2` parent, `swe-1-7`/`swe-1-7-medium` subagents) | Effort-level routing (`swe-2-medium` / `swe-2-high` / `swe-2-max`, all free, 262K) |
| Prescriptive reasoning ("think step by step", "plan before acting", "explore exhaustively") | WHAT + measurable acceptance criteria; HOW left to native reasoning |
| Legacy "thinking" config key | Removed — effort is embedded in the `model_uid` variant |
| `subagent_explore` as default exploration profile | Custom `researcher` profile pinned to `swe-2-max` (free) |

## Files changed

### Model routing and configuration

| File | Removed | Introduced |
|---|---|---|
| `data/bundle-models.json` | `glm-5-2`/`swe-1-7` registry, size-based roles | `swe-2-*` registry with `effort` field per model; `default_parent_model: swe-2-high`, `max_role_model: swe-2-max`, `medium_role_model: swe-2-medium`; `effort_levels` block |
| `data/model-context-windows.json` | `glm-5-2` (200K), `swe-1-7`, `swe-1-7-medium` | `swe-2-medium`/`swe-2-high`/`swe-2-max` (262144) |
| `data/recipes.json` | Roles described by model size | Same `preferred_model_role` field (mechanically read by `context-pressure.py`) now resolves to effort variants via the registry; `effort_routing` block added |
| `config.json` | `agent.model: glm-5-2`, empty `thinking: {}` | `agent.model: swe-2-high`; `thinking` key removed |
| `agents/*.md` (6 profiles) | `model: swe-1-7`/`swe-1-7-medium` pins | `swe-2-max` (architect, researcher, reviewer) / `swe-2-medium` (debugger, implementer, qa-ci) |
| `.devin/agents/*.md` (4 profiles) | `model: swe-1-7` | `swe-2-max` (domain, reviewer) / `swe-2-medium` (issue-tracker, triage-labels) |

### Global rules and agent-facing text

| File | Removed | Introduced |
|---|---|---|
| `AGENTS.md` | Rule 20 model-size policy, paid-alias assumptions | Rule 20 effort-aware operation; "SWE-2 plans natively — never add forced chain-of-thought"; subagent profile table with effort levels |
| `.devin/global_rules.md` | — | No change needed (already model-agnostic); verification rules retained |

### Hooks (simplified, mechanism retained)

| File | Removed | Introduced |
|---|---|---|
| `scripts/behavioral-nudge.py` | Verbose process checklist | 4-line outcome checklist (scope, telegraphic output, skill discovery, tool verification) |
| `scripts/constraint-pinning.py` | — | Retained as-is: re-injects hard governance constraints (safety/verification rules), not reasoning choreography — correct under SWE-2 |
| `scripts/refine-review-prompt.py` | Process-reminder text | Reminder rewritten as acceptance criteria (capture failures/tactics, cite reproducible commands, log to refinements.jsonl) |
| `scripts/context-pressure.py` | Hardcoded legacy windows | Reads `swe-2-*` windows from `bundle-models.json`; role resolution kept (mechanical) |
| `scripts/context-budget.py` | Legacy model ids in report rows | Reads registry dynamically |
| `scripts/validate-skill-format.py` | Paid-alias list referencing legacy models | `paid_aliases` set + messages now point to `swe-2-max`/`swe-2-medium` per Rule 20 |

### Skills (~90 SKILL.md swept)

| File (representative) | Removed | Introduced |
|---|---|---|
| `skills/effort-calibration/SKILL.md` | low/medium/high generic effort framing | SWE-2 Medium/High/Max table mapped to `swe-2-*` ids; "reasoning is native, not prompted" |
| `skills/dispatching-parallel-agents/SKILL.md` | Model-size profile mapping | Effort mapping: researcher/reviewer/architect→`swe-2-max`, implementer/debugger→`swe-2-medium` |
| `skills/leo/SKILL.md` | Hardcoded `glm-5-2`/`swe-1-7`, CLI version pin | `BUNDLE_*` env vars + effort variants; `qa-ci` at Medium |
| `skills/context-folding/SKILL.md` | `subagent_explore` default | `researcher` dispatch with paid-router warning |
| `skills/cost-optimization/SKILL.md`, `skills/agent-cost-guard/SKILL.md` | Legacy paid-model tables | Free SWE-2 variants + conditional paid policy |
| `skills/primeagent-reference/SKILL.md` | Legacy model refs | Effort-level language |
| `skills/project-setup/templates/agents.md` | "Think before you code" | "Intent and boundaries before code" (outcome, not process) |
| `skills/executing-plans`, `self-extend`, `continuous-improvement`, `deep-mode`, `using-skills`, `obsidian-workflow` | Legacy ids / prescriptive reasoning | Effort-level routing + acceptance-criteria framing |

Intentionally retained: `obsidian-workflow`'s `low/medium/high` is a `wiki-config.json` domain field (controls which wiki-generation steps run), not model routing. `playbook`/`wizard` "step by step" refer to literal procedures for humans, not reasoning hacks.

### Documentation

| File | Removed | Introduced |
|---|---|---|
| `docs/MODEL-GUIDE.md` | GLM/SWE-1 policy, size-based matrix | Full rewrite: effort-level table, SWE-2 implications, free/conditional-paid policy |
| `docs/TOOLS-MAP.md` | GLM-5.2 variant rows | `swe-2-medium`/`high`/`max` rows with effort column |
| `docs/SKILL-TIERS.md` | Legacy model table | SWE-2 effort table |
| `README.md` | `glm-5-2`/`swe-1-7`/`SWE-1.6` refs | `swe-2-*` effort-level routing description |

### Coupled validation

| File | Removed | Introduced |
|---|---|---|
| `audit.py` check 31 | `glm-5-2`/`swe-1-7` required entries | `swe-2-medium`/`swe-2-high`/`swe-2-max` @ 262144 |
| `tests/validation/test_cli_3000_6_14_compatibility.py` | `assert model == "glm-5-2"` | `assert model == "swe-2-high"` |
| `tests/validation/test_context_pressure.py` | `glm-5-2`/`swe-1.7` window asserts | `swe-2-high`/`swe-2-max` @ 262144 |
| `tests/validation/test_task_adaptive_harness.py` | `swe-1-7`/`gemini-3-7-flash`/`glm-5-2` model args | `swe-2-medium`/`swe-2-max`/`swe-2-high` |

## Historical records intentionally excluded (per approval)

Not rewritten — they document the old decision, they are not live prompts:
`CHANGELOG.md`, `.devin/EXECUTION_CHANGELOG.md`, `.devin/GLOBAL_BUNDLE_AUDIT.md`, `ledgers/*`, `.devin/ledgers/*`, `docs/plans/*`, `.devin/notes/*`, `.devin/scratch/*`, `.devin/adr/*`.

## Out of scope (unchanged)

Pure PowerShell execution logic (`devin-N.ps1`, `devin-session-launcher.ps1`), `install.ps1/.sh`, `export.ps1/.sh` — no prompt strings or model-invocation params. Mechanical hooks with no injected text unchanged.

## Verification

- `python audit.py` — **0 errors**, 10 warnings (all benign: `__pycache__` dirs; live-vs-bundle drift expected because the live `%APPDATA%\devin` install still holds the pre-migration export — resolved by the next install/export cycle)
- `python -m pytest` — **289 passed** (1 initial failure: `test_nudge_emits_additional_context` asserted the old uppercase nudge tokens; test updated to the new nudge contract, re-verified)
- `pwsh -File export.ps1 -DryRun` — **OK**, 0 failed components (note: `powershell.exe` on this machine lacks `Get-FileHash`; use `pwsh`)
- JSON parse check for `config.json`, `data/*.json`, `manifest.json`, `hooks.v1.json` — OK
- Residual grep for `glm-5-2`, `swe-1-7`, `swe-1-6`, `chain of thought`, `step by step` in active surfaces — clean (remaining hits are anti-pattern descriptions or literal procedures)
- `manifest.json` `export_hash` values regenerated for all modified scripts/agents
- `git status` on `bundle-swe2` — 41 modified + `.devin/SWE2_MIGRATION_LOG.md` (this file); no root-level log
