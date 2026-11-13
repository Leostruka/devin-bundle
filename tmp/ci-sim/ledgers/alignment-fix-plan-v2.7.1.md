# Fix plan: alignment / cross-skills / overheads

## Source of analysis

- `python audit.py` → 0 errors, 0 warnings
- `python scripts/validate-skill-format.py` → 119/119
- Subagent cross-skill wiring gap analysis
- Subagent SKILL-TIERS / overlap / overhead analysis

## Findings

### 1. SKILL-TIERS.md is missing 7 skills

| Missing skill | Best section | Tok (estimado) | Impact |
|---|---|---|---|
| `effort-calibration` | Núcleo | 2435 | Users won't know to invoke it before over-spending thinking tokens. |
| `mcp-lazy-enablement` | Núcleo | 1163 | Sibling of `mcp-context-audit`; missing makes MCP enable/disable undiscoverable. |
| `memory-hygiene` | Meta | 1736 | Cross-session memory management; needed by `project-memory` and `context-window-hygiene`. |
| `pr-review` | Programação | 1576 | GitHub PR review workflow; currently confused with `code-review` and `receiving-code-review`. |
| `project-memory` | Meta | 1042 | Capturing project knowledge across sessions. |
| `project-setup` | Setup | 2622 | General onboarding; currently only `setup-matt-pocock-skills` is listed. |
| `unlazy` | Núcleo | 1048 | Completion-discipline skill; required by `pr-review` line 11. |

### 2. High-priority missing cross-skill references

| From skill | Should reference | Why |
|---|---|---|
| `using-skills` | `ai-coding-dictionary`, `context-window-hygiene`, `effort-calibration`, `mcp-lazy-enablement` | Universal entry skill; must route jargon, context pressure, effort, and MCP decisions. |
| `implement` | `effort-calibration`, `verification-before-completion` | Implementation effort and final gate are currently missing. |
| `executing-plans` | `code-review`, `verification-before-completion` | Step 3 "Complete Development" needs review + verification gate. |
| `code-review` | `effort-calibration` | Review effort should be calibrated. |
| `tdd` | `review-cadence` | Decision logic should include "how much upfront discussion" branch. |
| `planning-pipeline` | `review-cadence` | Should decide how much planning is needed before running. |
| `dispatching-parallel-agents` | `context-window-hygiene`, `handoff` | Parallel agents multiply context pressure and may need cross-session handoff. |
| `mcp-context-audit` | `mcp-lazy-enablement` | After audit, selectively enabling servers is the next logical step. |
| `jira` | `mcp-lazy-enablement` | Jira is an MCP server; lazy enablement should be referenced. |
| `autonomous-gates` | `review-cadence`, `handoff` | Gate depth and multi-session resumability. |
| `finishing-a-development-branch` | `handoff`, `review-cadence` | Capture context before ending or decide final review depth. |

### 3. Overlaps (clarify, do not merge)

| Pair | Verdict | Action |
|---|---|---|
| `code-review` / `pr-review` | Specialization | `pr-review` is GitHub-specific workflow; `code-review` is generic two-axis review. Keep separate; cross-reference. |
| `receiving-code-review` / `pr-review` | No overlap | One acts on feedback, other publishes comments. |
| `planning-pipeline` / `writing-plans` | Sequential | `planning-pipeline` produces spec/tickets; `writing-plans` turns spec into task plan. Cross-reference. |
| `unlazy` / `verification-before-completion` | Distinct but adjacent | `unlazy` is a completion discipline (mental pattern); `verification-before-completion` is a concrete gate. Keep both. |
| `project-setup` / `setup-matt-pocock-skills` | Scope differs | `project-setup` is general onboarding; `setup-matt-pocock-skills` is skill-engineering setup. Clarify in descriptions. |
| `mcp-lazy-enablement` / `mcp-context-audit` | Complementary | Audit then enable/disable. Already partially wired. |
| `memory-hygiene` / `context-window-hygiene` | Scope differs | `memory-hygiene` for cross-session memory; `context-window-hygiene` for within-session context. Already defers. |

### 4. Overheads (no new action beyond existing anti-patterns)

| Skill | Tok | Status |
|---|---|---|
| `obsidian-workflow` | 17435 | Already flagged in anti-patterns. OK. |
| `dispatching-parallel-agents` | 10065 | Large but justified; fan-out cost is in subagent, not parent context. OK. |
| `primeagent-reference` | 10091 | Reference-only; OK. |
| `writing-skills` | 6717 | Heavy but only during skill authoring; OK. |

## Proposed fix plan

### Phase 1 — Discovery (SKILL-TIERS)

1. Add the 7 missing skills to `docs/SKILL-TIERS.md` with measured tok values and correct sections.
2. Update `README.md` skill count diagram / list if any section changes.

### Phase 2 — Core cross-skill wiring

3. Add a `## Cross-skills` section to `using-skills/SKILL.md` pointing to `ai-coding-dictionary`, `context-window-hygiene`, `effort-calibration`, `mcp-lazy-enablement`.
4. Update `implement/SKILL.md` to mention `effort-calibration` and `verification-before-completion`.
5. Update `executing-plans/SKILL.md` to mention `code-review` and `verification-before-completion`.
6. Update `planning-pipeline/SKILL.md` to mention `review-cadence`.
7. Update `tdd/SKILL.md` to mention `review-cadence`.
8. Update `dispatching-parallel-agents/SKILL.md` to mention `context-window-hygiene` and `handoff`.

### Phase 3 — Secondary cross-skill wiring

9. Update `code-review/SKILL.md` → `effort-calibration`.
10. Update `mcp-context-audit/SKILL.md` → `mcp-lazy-enablement`.
11. Update `jira/SKILL.md` → `mcp-lazy-enablement`.
12. Update `autonomous-gates/SKILL.md` → `review-cadence`, `handoff`.
13. Update `finishing-a-development-branch/SKILL.md` → `handoff`, `review-cadence`.

### Phase 4 — Vocabulary / glossary wiring

14. Update `ask-matt/SKILL.md` → `ai-coding-dictionary`.
15. Update `project-setup/SKILL.md` → `ai-coding-dictionary`.
16. Update `self-extend/SKILL.md` → `ai-coding-dictionary`, `continuous-improvement`.
17. Update `writing-for-agents/SKILL.md` → `ai-coding-dictionary`, `context-window-hygiene`.
18. Update `writing-skills/SKILL.md` → `ai-coding-dictionary`.

### Phase 5 — Continuous-improvement wiring

19. Update `improve-codebase-architecture/SKILL.md` → `continuous-improvement`.
20. Update `mutation-testing/SKILL.md` → `continuous-improvement`.
21. Update `setup-matt-pocock-skills/SKILL.md` → `continuous-improvement`.

### Phase 6 — Verification

22. Run `python audit.py`.
23. Run `python -m pytest`.
24. Run `python scripts/validate-skill-format.py`.

## Note on architecture

`improve-codebase-architecture` also identified non-skill code seams (hook I/O module, bundle sync, memory index). Those are not skill-alignment issues and are out of scope for this plan.
