# devin-bundle

[![CI](https://github.com/Leostruka/devin-bundle/actions/workflows/ci.yml/badge.svg)](https://github.com/Leostruka/devin-bundle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Skills](https://img.shields.io/badge/skills-54-blue.svg)](#skills-54)
[![Rules](https://img.shields.io/badge/rules-13-green.svg)](#regras-consolidadas-agentsmd)
[![Version](https://img.shields.io/badge/version-2.1.0-orange.svg)](CHANGELOG.md)

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

Done. Devin CLI now has 54 skills, 13 rules, 5 subagent profiles, 4 hooks, and 4 hook scripts configured.

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
│  │ (13 rules│  │ (54 skills│  │ (5 profiles│  │ (4 events│    │
│  │  always-on)│ │  invoked) │  │  dispatched)│ │  enforced)│    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │          │
│       └──────────────┴──────┬───────┴──────────────┘          │
│                             │                                 │
│                    ┌────────▼────────┐                        │
│                    │   scripts/ (4)  │                        │
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
├── AGENTS.md            # 13 consolidated rules (negative-constraint framed)
├── agents/              # 5 subagent profiles (architect, debugger, implementer, researcher, reviewer)
├── skills/              # 54 skills (auto-discover, not limited to manifest)
├── config.json          # model, theme, attribution (org_id MASKED by default)
├── hooks.v1.json        # PreToolUse + PostCompaction + Stop hooks (4 events)
├── scripts/             # 4 hook Python scripts
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

13 rules, all framed as negative constraints (evidence: arXiv:2604.11088 — positive directives hurt, only negative constraints help individually):

| # | Rule | Summary |
|---|---|---|
| 1 | Don't start with technology | Start with customer experience, then choose tech |
| 2 | No AI signatures | Never sign commits, files, PRs with an AI tool |
| 3 | Don't use outdated skills | Update wrong skills before use; create for recurring patterns |
| 4 | Don't start without skill discovery | Invoke matching skills before touching code |
| 5 | No push without green | Run local checks before committing |
| 6 | graphify trigger | `/graphify` runs first |
| 7 | Execute-first, opinion-silent | Don't reframe, suggest alternatives, or critique clear tasks |
| 8 | Telegraphic output | No filler, no preamble, structured formats |
| 9 | Don't add observability without skill | Context-dependent, not universal |
| 10 | Don't execute without planning | Todo list for 3+ step tasks; verify before claiming done |
| 11 | Never fail from failures | Resolve or deliver a working solution |
| 12 | Maximum precision | Every claim verified against primary source. Subagent returns are leads, not answers |
| 13 | Not a security sandbox | Run untrusted code externally. Guard against reward hacking |

## Hooks (4 events, 4 scripts)

| Event | Script | Function |
|---|---|---|
| PreToolUse (exec/write/edit) | `check-ai-signature.py` | Blocks AI signatures in commits (-m and -F), writes, edits |
| PreToolUse (exec) | `check-push-green.py` | Blocks push without green tests (npm, pytest, cargo, go, dotnet) |
| PostCompaction | `post-compaction-reminder.py` | Re-primes critical rules 1-10 after compaction (counters 5.6%/step compliance decay, arXiv:2605.10039) |
| Stop | `check-ai-signature.py` | Scans staged changes for AI signatures before stopping |
| Stop | `refine-review-prompt.py` | Prompts refinement review if `.refine-pending` marker exists |

Evidence: symbolic guardrails = 74% of policies enforceable (arXiv:2604.15579).

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
5. **config.json** — **MERGE** by default (preserves local `org_id`, applies model/theme from bundle). `-Force` to overwrite completely
6. **hooks.v1.json** — install
7. **scripts/** — install hook Python scripts
8. **mcp_config.json** — skip if values MASKED. `-Force` for masked structure
9. **credentials.toml** — only with `-RestoreSecrets`. Skip if MASKED
10. Prints summary: installed, overwritten, merged, skipped, backups

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
4. **config.json** — copy with `org_id` MASKED (or real with `-NoMask`)
5. **hooks.v1.json** — copy
6. **scripts/** — copy hook Python scripts
7. **mcp_config.json** — copy with env values MASKED (or real with `-NoMask`)
8. **credentials.toml** — copy with ALL values MASKED (or real with `-NoMask`)
9. **Pre-push validation** (with `-Push`): validates JSON syntax + Python syntax before pushing. Aborts on failure
10. **Commit** (with `-Commit`): `git add -A && git commit` with detailed message
11. **Push** (with `-Push`): `git push` after validation passes

### Secrets masking

| File | Default | With -NoMask |
|---|---|---|
| config.json | org_id → MASKED | real org_id |
| mcp_config.json | env values → MASKED | real tokens |
| credentials.toml | ALL values → MASKED | real API keys |

**WARNING:** `-NoMask` exports real secrets. NEVER push to a public repo with `-NoMask`.
Use `-NoMask` only for local backup or direct transfer between trusted machines.

## Skills (54)

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

### PrimeAgent/RLM-adapted skills (7)

Adapted from research verified against primary sources (arXiv:2512.24601, arXiv:2605.09998, arXiv:2603.02615, PrimeAgent blog/GitHub, ARC Prize leaderboard). See `primeagent-reference` skill for the full verification map.

| Skill | Source | Adaptation |
|---|---|---|
| `context-folding` | RLM (arXiv:2512.24601) | Offload to file + grep/partition + subagent_explore (depth=1 only). Depth=2+ causes overthinking (3.6s→344.5s) |
| `refine` | Continual Harness (arXiv:2605.09998) | Trajectory review → evidence-backed edits. Auto-trigger via Stop hook. Outcome tracking via `refinements.log.jsonl`. Reward hacking guard |
| `autonomous-gates` | PrimeAgent `--autonomous-gate` | Gates at planning time, after each step, final gate before done |
| `primeagent-reference` | All verified sources | Reference card: 9/9 features adapted, key numbers, video errors corrected |
| `a2a-mailbox` | PrimeAgent A2A messaging | Filesystem as message broker. Sequential A2A via file routing |
| `session-checkpoint` | PrimeAgent daemon-backed reattach | Structured checkpoint for cross-session continuation |
| `heartbeat` | PrimeAgent `/heartbeat` + `schedule` | OS scheduler + script launches new Devin CLI session |

### Adaptation status: 9/9 features

- **3 direct adaptations** (context-folding, autonomous-gates, Rule 13): feature maps cleanly to Devin CLI runtime
- **3 emulated adaptations** (a2a-mailbox, session-checkpoint, heartbeat): pattern preserved via file-based workarounds, each documents limitations vs PrimeAgent
- **1 partial** (skills as Python packages): already supported by Devin CLI's `scripts/` directory
- **2 guardrails** (refine + reward hacking guard): adapted with safety mechanisms

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
| Hooks not firing | Wrong hooks path | Verify `hooks.v1.json` is at `%APPDATA%\devin\hooks.v1.json` |
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
| [AGENTS.md](AGENTS.md) | The 13 rules (loaded by Devin CLI every session) |
| [manifest.json](manifest.json) | Skill metadata (name, source, purpose) |

## License

[MIT](LICENSE) — 2026 Leostruka
