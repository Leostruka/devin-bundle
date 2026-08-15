# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
