# Alignment fix applied and re-reviewed

## Plan executed

Based on `ledgers/alignment-fix-plan-v2.7.1.md`.

### Phase 1 — SKILL-TIERS
- Added `effort-calibration`, `unlazy`, `mcp-lazy-enablement` to Núcleo.
- Added `pr-review` to Programação.
- Added `project-memory`, `memory-hygiene` to Meta.
- Added `project-setup` to Setup.

### Phase 2 — Core cross-skill wiring
- `using-skills` → `ai-coding-dictionary`, `context-window-hygiene`, `effort-calibration`, `mcp-lazy-enablement`
- `implement` → `review-cadence`, `effort-calibration`, `verification-before-completion`
- `executing-plans` → `review-cadence`, `code-review`, `verification-before-completion`, `finishing-a-development-branch`
- `tdd` → `review-cadence`, `effort-calibration`
- `planning-pipeline` → `review-cadence`
- `dispatching-parallel-agents` → `context-window-hygiene`, `handoff`
- `autonomous-gates` → `review-cadence`, `handoff`
- `finishing-a-development-branch` → `review-cadence`, `handoff`

### Phase 3 — Secondary cross-skill wiring
- `code-review` → `effort-calibration`
- `jira` → `mcp-lazy-enablement`
- `mcp-context-audit` → `mcp-lazy-enablement`

### Phase 4 — Vocabulary / glossary wiring
- `ask-matt` → `ai-coding-dictionary`
- `project-setup` → `ai-coding-dictionary`
- `self-extend` → `ai-coding-dictionary`, `continuous-improvement`
- `writing-for-agents` → `ai-coding-dictionary`, `context-window-hygiene`
- `writing-skills` → `ai-coding-dictionary`

### Phase 5 — Continuous-improvement wiring
- `improve-codebase-architecture` → `continuous-improvement`
- `mutation-testing` → `continuous-improvement`
- `setup-matt-pocock-skills` → `continuous-improvement`

### Phase 6 — Re-review
- Subagent verified all 60 skills present in `docs/SKILL-TIERS.md`.
- Subagent verified all required cross-skill references present.
- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest` → 139 passed.
- `python scripts/validate-skill-format.py` → 119/119 passing.
