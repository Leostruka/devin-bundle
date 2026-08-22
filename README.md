# devin-bundle

[![CI](https://github.com/Leostruka/devin-bundle/actions/workflows/ci.yml/badge.svg)](https://github.com/Leostruka/devin-bundle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Skills](https://img.shields.io/badge/skills-46-blue.svg)](#skills-46)
[![Rules](https://img.shields.io/badge/rules-19-green.svg)](#regras-consolidadas-agentsmd)
[![Version](https://img.shields.io/badge/version-2.5.1-orange.svg)](CHANGELOG.md)

Export + installer for [Devin CLI](https://devin.ai) to synchronize your **entire setup** across machines.
Bundles skills, consolidated rules, config, hooks, scripts, MCP, and credentials —
restores everything to the correct destination with a single command.

---

## Quick start

```bash
git clone https://github.com/Leostruka/devin-bundle.git
cd devin-bundle
./install.sh --force          # Linux / macOS / WSL
.\install.ps1 -Force          # Windows (PowerShell)
```

Done. Devin CLI now has 46 skills, 19 rules, 5 subagent profiles, 8 hook events, 10 hook scripts, and 2 manual-run scripts configured.

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| [Devin CLI](https://devin.ai) | The agent this bundle configures | `devin --version` |
| Python 3.8+ | Hook scripts are Python | `python --version` |
| Git | Versioning and cloning | `git --version` |
| OS | Windows, Linux, or macOS | — |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Devin CLI Runtime                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ AGENTS.md│  │ skills/  │  │ agents/  │  │  hooks   │    │
│  │ (19 rules│  │ (46 skills│  │ (5 profiles│  │ (8 events│    │
│  │  always-on)│ │  invoked) │  │  dispatched)│ │  enforced)│    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │          │
│       └──────────────┴──────┬───────┴──────────────┘          │
│                             │                                 │
│                    ┌────────▼────────┐                        │
│                    │   scripts/ (12) │                        │
│                    │  Python hooks   │                        │
│                    └────────┬────────┘                        │
│                             │                                 │
│                    ┌────────▼────────┐                        │
│                    │  MCP + config   │                        │
│                    └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │ install.ps1 / install.sh           │ export.ps1 / export.sh
         │ (bundle → live)                    │ (live → bundle)
         │                                    │
┌────────┴──────────┐              ┌──────────┴──────────┐
│   devin-bundle/   │              │   Live config       │
│   (this repo)     │              │   %APPDATA%\devin\  │
│                   │              │   ~/.config/devin/  │
│   Git-tracked     │              │   Used by Devin CLI │
└───────────────────┘              └─────────────────────┘
```

## What's inside

```
devin-bundle/
├── AGENTS.md            # 19 consolidated rules (negative-constraint framed)
├── agents/              # 5 subagent profiles (architect, debugger, implementer, researcher, reviewer)
├── skills/              # 46 skills (auto-discover, not limited to manifest)
├── config.json          # model, theme, attribution, hooks (org_id MASKED by default)
├── hooks.v1.json        # project-level hooks template (.devin/hooks.v1.json)
├── scripts/             # 12 Python scripts (10 hooks + 2 manual-run)
├── mcp_config.json      # MCP server config (tokens MASKED by default)
├── credentials.toml     # API keys (ALL values MASKED by default)
├── manifest.json        # skill metadata (name, source, purpose)
├── export.ps1           # exporter — Windows (PowerShell)
├── export.sh            # exporter — Linux/WSL/macOS (bash)
├── install.ps1          # installer — Windows (PowerShell)
├── install.sh           # installer — Linux/WSL/macOS (bash)
├── LICENSE              # MIT
├── SECURITY.md          # security policy (Rule 13)
├── CONTRIBUTING.md      # contribution guide
├── CHANGELOG.md         # version history
├── .github/             # CI workflow + issue/PR templates
├── .gitattributes       # LF for .sh, CRLF for .ps1
├── .gitignore           # ignores __pycache__, .devin/scratch, secrets
└── README.md            # this file
```

## Consolidated rules (AGENTS.md)

19 rules, all framed as negative constraints (evidence: arXiv:2604.11088 — positive directives hurt, only negative constraints help individually):

| # | Rule | Summary |
|---|---|---|
| 1 | Don't start with technology | Start with customer experience, then choose tech |
| 2 | No AI signatures | Never sign commits, files, PRs with an AI tool |
| 3 | Don't use outdated skills | Update wrong skills before use; create for recurring patterns |
| 4 | Don't start without skill discovery | Invoke matching skills before touching code |
| 5 | No push without green | Run local checks before committing |
| 7 | Execute-first, opinion-silent | Don't reframe, suggest alternatives, or critique clear tasks |
| 8 | Telegraphic output | No filler, no preamble, structured formats |
| 9 | Don't add observability without skill | Context-dependent, not universal |
| 10 | Don't execute without planning | Todo list for 3+ step tasks; verify before claiming done |
| 11 | Never fail from failures | Resolve or deliver a working solution |
| 12 | Maximum precision | Every claim verified against primary source. Subagent returns are leads, not answers |
| 13 | Not a security sandbox | Run untrusted code externally. Guard against reward hacking |
| 14 | Constraint Pinning survives compaction | Governance constraints re-injected after compaction (arXiv:2606.22528) |
| 15 | Refinement evidence must be reproducible | Phantom guardrails occur in 25% of self-improvement runs (arXiv:2607.13083) |
| 16 | Self-improvement loops produce 47-74% illusory gains | Validate with held-out tests, not agent-chosen tests (ICLR 2026 Workshop) |
| 17 | Don't deduce — verify with tools | Use read/exec/grep/glob before asserting; guesses fail silently (arXiv:2307.03172 lost-in-the-middle) |
| 18 | Keep the context window lean | Default to clear over compact; small rules files; audit MCP servers; bigger window ≠ better retrieval |
| 19 | Never read secrets or sensitive env vars | Use keys/env vars but never display their contents; report missing/empty without exposing value |
| 20 | Model-aware operation | GLM-5.2 (200K, tool-use, thinking) for main; SWE-1.7 Max (262K, fast, **gratuito**) for subagents. See MODEL-GUIDE.md |

## Hooks (8 events, 10 hook scripts + 2 manual-run scripts)

All hook scripts follow the Devin CLI contract: they read the event payload from
stdin (`hook_event_name`, `tool_name`, `tool_input`, `tool_response`, ...), block
with **exit code 2** plus a `{"decision":"block","reason":...}` payload, and
inject context via `hookSpecificOutput.additionalContext` where the event
supports it. See [Lifecycle Hooks](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks).

| Event | Matcher | Script | Function |
|---|---|---|---|
| PreToolUse | `^exec$` | `destructive-gate.py` | Blocks `rm -rf /`, `git push --force` without `--dry-run`, `DROP TABLE`, `chmod -R 777 /` |
| PreToolUse | `^exec$` | `check-ai-signature.py` | Blocks AI signatures in commit messages (`-m` and `-F`/`--file`) |
| PreToolUse | `^exec$` | `check-push-green.py` | Blocks push without green tests + held-out gap check (Rule 16) |
| PreToolUse | `^(write\|edit)$` | `check-ai-signature.py` | Blocks AI signatures in file content |
| PreToolUse | 19 tool names | `validate-tool-args.py` | Validates paths, regexes, URLs, profiles, UI fields before execution (ALTK SPARC) |
| PostToolUse | `^(exec\|mcp_call_tool)$` | `silent-error-review.py` | Flags `success:true` with error indicators in verbose/tabular output (ALTK scope) |
| PostCompaction | all | `constraint-pinning.py` | Detects dropped constraints, writes re-injection marker (Rule 14) |
| UserPromptSubmit | all | `constraint-pinning.py` | Re-injects pinned constraints when a marker exists |
| SessionStart | all | `constraint-pinning.py` | Clears stale markers from prior sessions |
| SessionStart | all | `context-budget.py` | Reports AGENTS.md token cost to stderr (transparency, no context bloat) (Rule 18) |
| Stop | all | `check-ai-signature.py` | Scans staged + unstaged changes for AI signatures |
| Stop | all | `refine-review-prompt.py` | Blocks once for refinement review if `.refine-pending` exists |
| Manual | — | `validate-refinement-evidence.py` | Checks `refinements.log.jsonl` for phantom guardrails (Rule 15) |
| Manual | — | `validate-skill-format.py` | Scores SKILL.md files against the 8-point quality checklist |

`constraint-pinning.py` spans three events because `PostCompaction` cannot inject
context (only `UserPromptSubmit`, `SessionStart` and `PostToolUse` support
`additionalContext`). It therefore records a marker at compaction time and
re-injects on the next user prompt.

Evidence: symbolic guardrails = 74% of policies enforceable (arXiv:2604.15579). Deterministic gates raise success 29.6%→42.0% (arXiv:2607.07405, KDD 2026 Workshop).

## Install

### Windows (PowerShell)
```powershell
cd devin-bundle
.\install.ps1                    # install all (skip existing, merge config)
.\install.ps1 -DryRun            # show what it would do
.\install.ps1 -Force             # overwrite differences
.\install.ps1 -Force -Backup     # overwrite, saving backup first
.\install.ps1 -RestoreSecrets    # also install credentials.toml (if unmasked)
```
Destination: `%APPDATA%\devin\`

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x install.sh
./install.sh                     # install
./install.sh --dry-run           # show only
./install.sh --force             # overwrite
./install.sh --restore-secrets   # install credentials.toml
```
Destination: `${XDG_CONFIG_HOME:-~/.config}/devin/`

### What the installer does

1. Creates `%APPDATA%\devin\` (or `~/.config/devin/`) if missing
2. **AGENTS.md** — install if absent; skip if identical; `-Force` to overwrite
3. **agents/** — install each `.md` profile
4. **skills/** — install each skill; skip if identical; `-Force` to update
5. **config.json** — **MERGE** by default (preserves local `org_id`, applies model/theme/**hooks** from bundle). `-Force` to overwrite completely
6. **scripts/** — install hook Python scripts
7. **mcp_config.json** — skip if values MASKED. `-Force` for masked structure
8. **credentials.toml** — only with `-RestoreSecrets`. Skip if MASKED
9. Prints summary: installed, overwritten, merged, skipped, backups

## Export (regenerate bundle from source machine)

### Windows (PowerShell)
```powershell
cd devin-bundle
.\export.ps1                    # export with secrets MASKED
.\export.ps1 -DryRun            # show what it would do
.\export.ps1 -Commit -Push      # export + validate + commit + push
.\export.ps1 -NoMask -Commit    # export with real secrets + commit (DO NOT push to public repo)
```

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x export.sh
./export.sh                     # export with secrets MASKED
./export.sh --dry-run           # show only
./export.sh --commit --push     # export + validate + commit + push
./export.sh --no-mask --commit  # export with real secrets + commit
```

### What the exporter does

1. **AGENTS.md** — copy from live to bundle (LF line endings)
2. **agents/** — copy all `.md` profiles
3. **skills/** — **auto-discovers** ALL skills in the live directory (not limited to manifest). Compares hashes, only copies if changed
4. **config.json** — copy with `org_id` MASKED (or real with `-NoMask`). Includes hooks under `"hooks"` key
5. **scripts/** — copy hook Python scripts
6. **mcp_config.json** — copy with env values MASKED (or real with `-NoMask`)
7. **credentials.toml** — copy with ALL values MASKED (or real with `-NoMask`)
8. **Pre-push validation** (with `-Push`): validates JSON syntax + Python syntax before pushing. Aborts on failure
9. **Commit** (with `-Commit`): `git add -A && git commit` with detailed message
10. **Push** (with `-Push`): `git push` after validation passes

### Secrets masking

| File | Default | With -NoMask |
|---|---|---|
| config.json | org_id → MASKED | real org_id |
| mcp_config.json | env values → MASKED | real tokens |
| credentials.toml | ALL values → MASKED | real API keys |

**WARNING:** `-NoMask` exports real secrets. NEVER push to a public repo with `-NoMask`.
Use `-NoMask` only for local backup or direct transfer between trusted machines.

## Skills (49)

The bundle auto-discovers all skills in `%APPDATA%\devin\skills\`. The `manifest.json` contains metadata (name, source, purpose) for reference, but the exported skill list is determined by the live directory, not the manifest.

### Unified skills (3)

| Unified skill | Source A | Source B | Decision logic |
|---|---|---|---|
| `tdd` | test-driven-development (iron law) | tdd (seams, vertical slices) | Seams-first for WHERE; iron law for HOW |
| `code-review` | requesting-code-review (subagent dispatch) | code-review (two-axis Standards vs Spec) | Subagent dispatch for context; two-axis for methodology |
| `grilling` | brainstorming (one question at a time) | grilling (design tree, frontier rounds) | Brainstorm to explore; grill to stress-test |

### Adapted skills (2)

| Adapted skill | Original source | What changed |
|---|---|---|
| `mutation-testing` | `chunk-testing-gaps` (CircleCI) | Local-first with optional CI |
| `debug-ci-failures` | `debug-ci-failures` (CircleCI) | CI-agnostic: GitHub Actions, CircleCI, GitLab, Jenkins |

### PrimeAgent/RLM-adapted skills (3)

Adapted from research verified against primary sources (arXiv:2512.24601, arXiv:2605.09998, arXiv:2603.02615, PrimeAgent blog/GitHub, ARC Prize leaderboard). See `primeagent-reference` skill for the full verification map — it now consolidates the former `a2a-mailbox`, `refine`, and `subagent-router` skills into modes.

| Skill | Source | Adaptation |
|---|---|---|
| `context-folding` | RLM (arXiv:2512.24601) | Offload to file + grep/partition + subagent_explore (depth=1 only). Depth=2+ causes overthinking (3.6s→344.5s) |
| `autonomous-gates` | PrimeAgent `--autonomous-gate` | Gates at planning time, after each step, final gate before done |
| `primeagent-reference` | All verified sources | Reference card + A2A messaging + refine + subagent router (4 modes). 9/9 features adapted, key numbers, video errors corrected |

### Context window skills (2)

Adapted from "Context Windows Explained for Coding Agents" (Matt Pocock, AI Hero). Key lessons: context window = input + output tokens (hard-capped); lost-in-the-middle deprioritizes the middle of long chats; default to `clear` over `compact`; keep rules files small; MCP servers bloat context fast; bigger window ≠ better retrieval.

| Skill | Source | Adaptation |
|---|---|---|
| `context-window-hygiene` | Context window video (Matt Pocock) | Practical hygiene: clear-vs-compact, lean rules, MCP paranoia, subagent context savings. Backed by lost-in-the-middle (arXiv:2307.03172) |
| `mcp-context-audit` | Context window video + arXiv:2606.30317 | Estimates per-server tool-definition token cost; flags >15 tools/server and >5% window share. `--config` static + `--tools` measured modes |

Rule 18 ("Keep the context window lean") pins these lessons into AGENTS.md and survives compaction via `constraint-pinning.py`. `context-budget.py` (SessionStart hook) reports the rules-file token cost to stderr every session.

### Consolidated skills (5)

Skills merged in v2.4.0 to reduce namespace bloat and maintenance overhead. Each preserves all content from its sources via mode selectors:

| Skill | Merged from | Modes |
|---|---|---|
| `grilling` | grilling + grill-me + grill-with-docs | Default, Stateless, With-docs |
| `diagnosing-bugs` | diagnosing-bugs + systematic-debugging | Unified 6-phase debugging pipeline |
| `tool-and-skill-discovery` | tool-and-skill-discovery + find-skills | Discovery + install/evaluate |
| `dispatching-parallel-agents` | dispatching-parallel-agents + subagent-driven-development | General dispatch + plan execution |
| `planning-pipeline` | to-spec + to-tickets + to-questionnaire | Spec, Tickets, Questionnaire |
| `obsidian-workflow` | obsidian-project-docs + vault-organizer + wiki-audit + memory-bridge | Build, Reorganize, Audit, Cross-session |

### Adaptation status: 9/9 features

- **3 direct adaptations** (context-folding, autonomous-gates, Rule 13): feature maps cleanly to Devin CLI runtime
- **1 emulated adaptation** (primeagent-reference A2A mode): pattern preserved via file-based workarounds, documents limitations vs PrimeAgent
- **1 partial** (skills as Python packages): already supported by Devin CLI's `scripts/` directory
- **2 guardrails** (refine mode + reward hacking guard): adapted with safety mechanisms
- **2 pruned** (session-checkpoint, heartbeat): emulations that didn't fit Devin CLI's single-process runtime

## Sync machines

This is a normal Git repo:
```powershell
cd devin-bundle
git init
git add -A
git commit -m "initial devin bundle"
git remote add origin <your-repo>
git push -u origin main
```

On the other machine:
```bash
git clone <your-repo> devin-bundle
cd devin-bundle
./install.sh --force          # or install.ps1 -Force on Windows
```

To restore credentials.toml on the other machine:
1. On source machine: `.\export.ps1 -NoMask` (DO NOT push)
2. Transfer `credentials.toml` manually (USB, scp, etc.)
3. On target machine: `.\install.ps1 -RestoreSecrets`

## Update the bundle

After changing skills/rules/config in daily work:
1. Run `.\export.ps1` to sync the bundle with the current machine
2. `.\export.ps1 -Commit -Push` to commit and push in one step (with validation)

The installer is idempotent — running again only updates what changed (with `-Force`).

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `install.ps1` cannot run | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Skills not appearing | Wrong install path | Verify destination: `%APPDATA%\devin\skills\` (Windows) or `~/.config/devin/skills/` (Linux) |
| Hooks not firing | Wrong hooks location | Verify hooks are in `config.json` under `"hooks"` key at `%APPDATA%\devin\config.json` (not `hooks.v1.json` at user-level) |
| `check-push-green.py` blocks all pushes | Test suite failing | Fix tests, then push. Or use `-Force` install to update the script |
| AI signature detected on Stop | Staged changes contain signature | Remove signature from staged files: `git commit --amend` |
| `export.ps1 -Push` aborts | JSON or Python syntax error | Fix the error, re-run export |
| Skills count mismatch | Manifest out of sync | Run `.\export.ps1` to sync manifest with disk |
| `.refine-pending` marker persists | Refinement not completed or marker not removed | Run `refine` skill, then `rm .devin/.refine-pending` |
| Post-compaction rules missing | Old `post-compaction-reminder.py` | Reinstall: `.\install.ps1 -Force` |

## Documentation

| Document | Purpose |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute (skill/rule/hook standards) |
| [SECURITY.md](SECURITY.md) | Security policy and guardrails |
| [AGENTS.md](AGENTS.md) | The 19 rules (loaded by Devin CLI every session) |
| [SKILL-TIERS.md](SKILL-TIERS.md) | Skills by domain of use + token costs (fast discovery, ~1500 tok vs ~2094 for `skill list`) |
| [MODEL-GUIDE.md](MODEL-GUIDE.md) | GLM-5.2 and SWE-1.7 model specs, pricing, context windows, best practices |
| [TOOLS-MAP.md](TOOLS-MAP.md) | Complete map of tools, subagents, hooks, configs, and modes |
| [manifest.json](manifest.json) | Skill metadata (name, source, purpose) |

## License

[MIT](LICENSE) — 2026 Leostruka
