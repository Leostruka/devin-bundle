---
name: leo
description: Use when routing and orchestrating any work across this Devin bundle through one universal entry point, including direct specialist skills, multi-skill flows, and local AFK issues.
triggers: [user]
---

# /leo — Universal bundle orchestrator

## TL;DR

1. Self-check (scope, skills, verify, no opinion).
2. Classify objective; route directly to matching skill(s).
3. Start with `using-skills`; use `ask-bundle` only if unclear.
4. For 3+ steps, write `todo_write`; mark `in_progress` then `completed`.
5. Define Verification Function (gate/expect/evidence) per step.
6. Dispatch `qa-ci` to re-run every gate on clean checkout.
7. Run the project's verification commands (e.g., `python audit.py` and `python -m pytest` when present) before claiming done.

## Goal

Provide one entry point for the bundle's universal orchestration: classify the objective, invoke specialist skills directly, compose multi-skill flows, and retain control through verified completion. `ask-bundle` is the full routing reference, not a mandatory hop; `wayfinder` and every other clear specialist route are first-class entry paths.

## When to use

- The user starts a session with "leo", a vague request, or no clear objective.
- The user needs help choosing the first skill or flow.
- The user wants to prepare local AFK issues for unattended implementation.
- At any session start when the next action is non-trivial.
- The user wants Leo to coordinate an objective across one or more specialist skills.

## Procedure

1. **Self-check before responding**
   - Scope: do EXACTLY what was asked, no more, no less.
   - Telegraphic output: no preamble, filler, opinion, or unsolicited explanation.
   - Skills: for non-trivial tasks, invoke matching skills before acting.
   - Verify: use `read`/`exec`/`grep`/`glob`/`run_subagent` before asserting.
   - Opinion-silent: don't critique, reframe, or suggest unless asked.
   - If the objective is clear, route to the matching flow in the situation router.
   - If the objective is unclear or the user just says "leo" / "start", ask the quick-start menu (see **Quick-start menu** below) with `ask_user_question` before routing.

2. **Direct routing and composition**
   - Classify the objective from the user's words and observed repository state.
   - Route directly to every clearly matching specialist skill; invoke multiple skills when their responsibilities compose.
   - Start with `using-skills` to reinforce the skill-first rule.
   - Use `ask-bundle` only when the idea-to-ship path or phase boundary is unclear; it is a routing reference, not Leo's sole downstream router.
   - If no bundled skill matches, use `tool-and-skill-discovery` or `skill search`/`skill list`.
   - For fast domain lookup, read `docs/SKILL-TIERS.md`.

3. **Planning**
   - For 3+ step tasks, create a `todo_write` immediately.
   - Every plan must be detailed, sequential, verifiable, with no loose ends.
   - Mark `in_progress` when starting, `completed` when done — no batching.
   - For explicit acceptance criteria, use `unlazy` or `autonomous-gates`.

4. **Execution and verification (modular atomic action mode)**
   - Never deduce. Use tools to observe reality first.
   - Each step is atomic: one verifiable action, completed and verified before the next starts.
   - For each step, define a **Verification Function (VF)** before executing it:
     - `gate:` the exact command that proves the step done (build/test/lint/typecheck/dry-run).
     - `expect:` the output or exit code that constitutes pass.
     - `evidence:` where the raw output will be recorded (ledger line or file path).
   - Mark `in_progress` when starting a step, `completed` only after verification passes — no batching.
   - **Independent QA/CI verification (anti-gaming, mandatory for non-trivial steps):**
     - After a step claims done, dispatch the `qa-ci` subagent (Medium effort via `BUNDLE_MEDIUM_MODEL` / `data/bundle-models.json`, no write tools) to re-run every gate independently.
     - The QA/CI subagent sees only the diff and the spec — never the implementer's report.
     - It re-executes each gate on a clean checkout (fresh worktree when feasible), runs `tests/held-out/` if present, and audits the diff for overfitting (hard-coded constants, mocked gates, skipped tests, phantom guardrails).
     - A step is `completed` only when the QA/CI subagent returns `Verdict: PASS` with fresh command output + exit code as evidence.
     - If QA/CI returns `FAIL`, the step stays `in_progress`; feed the failure back and re-execute the fix loop. Never override a QA/CI FAIL with self-report.
   - Techniques that make verification gaming-resistant:
     - **Held-out tests** (`tests/held-out/`): the implementer cannot see or edit them; QA/CI runs them. Passing visible tests while held-out fails = FAIL.
     - **Independent verifier**: the QA/CI subagent has no `write`/`edit` tools, so it cannot alter the proof.
     - **Clean-room re-execution**: gates run on a fresh checkout, never on the implementer's polluted workspace.
     - **Evidence-based completion**: every "done" requires a fresh command + output + exit code from QA/CI, not self-report.
     - **CI as external immutable gate**: GitHub Actions / hooks run `audit.py`, AI-signature check, and push-green check independently of the agent.
   - Before claiming the session done, run `python audit.py` and `python -m pytest` and attach output.
   - After routing, verify the target skill is loaded and its first step is started.

5. **Return to Leo**
   - After each specialist finishes, compare its verified result with the original objective and current todo state.
   - Route the next unmet responsibility to the appropriate specialist; preserve artifacts and decisions across handoffs.
   - Stop only at verified completion, an explicit user decision boundary, or a reported blocker. Leo owns orchestration; specialists own domain procedure.

## Bundle context

Keep this in mind for every session:

- Devin CLI validated release: `{{VALIDATED_CLI_VERSION}}` from `data/bundle-identity.json` (see `docs/DEVIN-CLI-COMPATIBILITY.md`).
- Models: SWE-2 routes by effort level — parent `BUNDLE_DEFAULT_MODEL` / `data/bundle-models.json` (`default_parent_model`, High); custom subagents `BUNDLE_MAX_MODEL` (`max_role_model`, Max) or `BUNDLE_MEDIUM_MODEL` (`medium_role_model`, Medium), all free. Never use non-bundle aliases (`opus`, `sonnet`, `gpt`, etc.) when the parent is free.
- Issue tracker: local Markdown under `.devin/scratch/<feature-slug>/`, conventions in `.devin/agents/issue-tracker.md` and `.devin/agents/triage-labels.md`.
- Skills: discover via `tool-and-skill-discovery` or `docs/SKILL-TIERS.md`.
- Hooks: 8 lifecycle events (see `docs/TOOLS-MAP.md` and `config.json`).
- Verification baseline: run the project's own verification commands; common defaults are `python audit.py` and `python -m pytest` when they exist.

## Situation router

Pick the entry skill from the user's situation. If the situation is not in this table, route to `ask-bundle` for the full map or `tool-and-skill-discovery` for an external skill.

| Situation | Entry skill | Next |
|---|---|---|
| Build / change / implement something | `grilling` (With-docs) to capture intent and user impact, or `review-cadence` if trivial | → `planning-pipeline` Spec → Tickets (estimate PR size; split >500 lines) → `implement` + `tdd` → `security-audit` (if API, DB, secrets, endpoints, or infra) → `code-review` → `verification-before-completion` → `finishing-a-development-branch` |
| Run AFK / unattended on a feature | `afk-loop` only if issues exist and are `ready-for-agent`; otherwise use **Quick AFK issue creation** below | `afk-loop` |
| Hard / intermittent / unclear bug | `diagnosing-bugs` | → `tdd` regression → `improve-codebase-architecture` if no seam |
| CI is failing | `debug-ci-failures` | |
| Triage incoming issues / requests | `triage` | → `implement` |
| Large, foggy, multi-session effort | `wayfinder` | → `planning-pipeline` Spec → ... |
| Prototype to settle a design question | `prototype` (via `handoff`) | back to `grilling` / `planning-pipeline` |
| Research / deep codebase exploration | `research` or `deep-mode` | feed into `grilling` or Spec |
| Need input from another person | `planning-pipeline` Questionnaire | → `grilling` or Spec |
| Git merge / rebase conflict | `resolving-merge-conflicts` | |
| Improve architecture / find deep modules | `improve-codebase-architecture` | → `grilling` if it generates an idea |
| Improve / evolve a skill, rule, hook, or MCP | `continuous-improvement` | → `writing-skills` if editing one skill, `self-extend` if adding a new capability |
| Release / deploy / rollback | `deploy` | → `gh` for GitHub operations, then smoke tests |
| Security assessment | `security-audit` | → `implement` for approved remediations |
| Data query / analysis / charts | `data-analyst` | |
| UI / UX design or polish | `impeccable` | → `a11y-audit` / `e2e-testing` when applicable |
| Logging / metrics / tracing / quality infrastructure | `observability-quality` | |
| API or database design | `api-design` or `database` | → `implement` after contract/schema decisions |
| Performance or cost optimization | `performance` or `cost-optimization` | |
| Human-only procedure / provisioning | `wizard` | |
| Guided learning | `teach` | |
| Set up this repo for Devin | `project-setup` or the engineering-skills setup | |
| Not sure which skill / flow fits | `ask-bundle` | full map |
| No skill matches | `tool-and-skill-discovery` | evaluate / install |

For the main flow details (idea → ship, on-ramps, phase boundaries), see `ask-bundle`.

### Build/change flow gates

The default build/change flow is: `grilling` (intent and user impact) → `planning-pipeline` (spec + tickets) → `implement` + `tdd` → `security-audit` (when the change touches API, DB, secrets, endpoints, or infrastructure) → `code-review` → `verification-before-completion` → `finishing-a-development-branch`.

Gates applied inside that flow:

- **Intent and impact**: `grilling` captures the final goal, where the feature lands, and how the user is affected. Implementation does not start until intent is clear.
- **Size and boundaries**: `planning-pipeline` estimates the PR size. If the estimate exceeds ~500 lines, split the task into smaller tickets with clear input/output boundaries. Target PR size is ~300 lines.
- **TDD**: `tdd` is a default step, not optional. Tests verify intent; don't delete or skip them without explicit approval.
- **Pre-commit**: `setup-pre-commit` runs lint-staged and tests before commit when the project is set up by `project-setup` or `implement` touches pre-commit hooks.
- **Security audit**: `security-audit` is a gate, not optional, whenever the change touches API, DB, secrets, endpoints, or infrastructure.
- **Destructive work**: `docker` or a dev container is recommended for tasks that could be destructive (file system, DB, network, credentials).
- **Parallelism**: limit concurrent subagents to 1-3. If a task suggests more than 3 parallel agents, alert the user and ask for approval.

### Tool-output validation

After executing critical tools (API calls, DB writes, file-system changes, network calls), validate the output before allowing side effects or reporting success:

- **Type/schema check**: validate tool arguments and responses with Pydantic or an equivalent schema check before using them.
- **Ontology/reasonableness check**: check the result against the domain ontology or business rules (e.g., status values must be `paid`, `shipped`, or `refunded`; entities must be the expected type). If the result is not reasonable, go back to the LLM or ask the human — do not apply side effects.
- **No side effects until validated**: don't let a tool output drive destructive or state-changing actions before it passes the checks.

## Quick-start menu

When the user says "leo", "start", or the objective is unclear, ask a focused `ask_user_question` with 2–4 options. The tool adds an "Other" option automatically; route "Other" to `ask-bundle` or a follow-up question.

- **Build or change something in the repo** → `grilling` (With-docs) if decisions remain, or `review-cadence` if trivial
- **Improve / add a skill, rule, hook, or MCP** → `continuous-improvement`
- **Debug, fix, or research a problem** → `diagnosing-bugs` for bugs, `research` / `deep-mode` for exploration
- **Set up this repo for Devin or run AFK work** → `project-setup` / the engineering-skills setup for setup, `afk-loop` if issues already exist

## Quick AFK issue creation

When the user wants unattended work but there are no local tickets yet:

1. Confirm the feature slug and the high-level objective.
2. If there is no spec, run `grilling` (With-docs mode) or `planning-pipeline` (Spec mode) to write `.devin/scratch/<feature-slug>/spec.md`.
3. Run `planning-pipeline` (Tickets mode) to break the spec into vertical-slice tracer bullets.
4. Publish one file per ticket to `.devin/scratch/<feature-slug>/issues/<NN>-<slug>.md`:
   - Number from `01` in dependency order (blockers first).
   - Use the local ticket template from `planning-pipeline`.
   - Include `Status: ready-for-agent`.
   - Include `Blocked by: <numbers>` or `None — can start immediately`.
   - List acceptance criteria as checkboxes.
   - Focus on end-to-end "what to build" from the user's perspective, not layers.
5. Verify the files exist and the DAG is consistent:
   - `glob .devin/scratch/<feature-slug>/issues/*.md`
   - `read .devin/scratch/<feature-slug>/spec.md`
   - Parse `Status:` and `Blocked by:` from each issue.
6. Only then run `afk-loop` if the user explicitly authorizes unattended work.

## Specifications

- `AGENTS.md` rules are respected.
- `.devin/global_rules.md` is read when working inside this repo.
- `docs/SKILL-TIERS.md` is the fast path for skill discovery.
- Matching skills are invoked before non-trivial actions.
- 3+ step tasks use `todo_write` with updated states.
- Every claim is verified by a tool, not by reasoning.
- Output is terse, structured, and cited when making factual claims.

## Advice

- Subagents: use custom profiles pinned to bundle effort variants (`swe-2-max` / `swe-2-medium`, free). Never use `subagent_explore` or other paid aliases when the parent is free.
- Deep search: use the `researcher` subagent profile (`swe-2-max`).
- Models: parent is `BUNDLE_DEFAULT_MODEL` / `data/bundle-models.json` (`default_parent_model`); subagents are `BUNDLE_MAX_MODEL` (`max_role_model`) or `BUNDLE_MEDIUM_MODEL` (`medium_role_model`). Don't use paid aliases unless the parent is paid.
- Context: prefer `clear` between unrelated tasks; don't paste large documents into chat.
- Secrets: never display `.env`/`credentials.toml` values; name the variable and symptom only.
- Fact doubt → research (`web_search`, `webfetch`, `grep`, `exec`).
- Intent doubt → ask (`ask_user_question`).
- Cross-skill: `leo` is the session-start wrapper. Use `using-skills` to reinforce skill-first behavior. Use `ask-bundle` for the full flow map when the quick router is not enough. Use `tool-and-skill-discovery` for external or missing skills.

## Forbidden Actions

- Deduce state, file content, or command output without using tools.
- Start non-trivial work without skill discovery.
- Mark a step `completed` without an independent `qa-ci` PASS for non-trivial steps.
- Override a `qa-ci` FAIL with self-report, "should work", or confidence.
- Push or commit with failing local checks (Rule 5).
- Sign commits, files, PRs, or docs as AI (Rule 2).
- Display secret values (Rule 19).
- Run destructive/irreversible actions without explicit user confirmation.
- Use `subagent_explore` or paid models when the parent is free.
- Compact when `clear` is sufficient; let context grow unchecked.
- Start `afk-loop` without local issues in `ready-for-agent` state.
- Edit or read `tests/held-out/` from the implementer context; only `qa-ci` may run them.
- Reuse the implementer's shell, caches, or installed deps for QA/CI verification without re-installing from pinned manifests.

## Required from User

- A clear objective at the start of the session, or a choice from the quick-start menu.
- Clarification when the request is ambiguous and the deliverable would change.

## Priority Hierarchy

Hard constraints (never violated):
1. Safety and pinned `AGENTS.md` rules (Rules 2, 5, 7, 12-19, 21).
2. Verify with tools before asserting (Rule 17).
3. Execute exactly what was asked, without opinion (Rule 7).

Design preferences (when constraints allow):
4. User usefulness and real benefit.
5. Ease and pleasantness of interaction.
6. Quality of experience.
7. Technical coherence.
8. Performance and responsiveness.
