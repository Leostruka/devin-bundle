---
name: leo
description: Use when starting a Devin CLI session in this bundle and the next skill or workflow is not obvious, or when the user needs a quick entry point to seed local AFK issues.
---

# /leo — Bundle-aware session start and router

## Goal

Run at the start of a session to load the bundle's rules, run the behavioral self-check, and route to the right workflow or skill. Preserves the existing operating discipline and adds a quick map for common flows and AFK setup.

## When to use

- The user starts a session with "leo", a vague request, or no clear objective.
- The user needs help choosing the first skill or flow.
- The user wants to prepare local AFK issues for unattended implementation.
- At any session start when the next action is non-trivial.

## Procedure

1. **Self-check before responding**
   - Scope: do EXACTLY what was asked, no more, no less.
   - Telegraphic output: no preamble, filler, opinion, or unsolicited explanation.
   - Skills: for non-trivial tasks, invoke matching skills before acting.
   - Verify: use `read`/`exec`/`grep`/`glob`/`run_subagent` before asserting.
   - Opinion-silent: don't critique, reframe, or suggest unless asked.
   - If the objective is clear, route to the matching flow in the situation router.
   - If the objective is unclear or the user just says "leo" / "start", ask the quick-start menu with `ask_user_question` before routing.

2. **Skill discovery**
   - Before any non-trivial action, invoke all matching skills.
   - Start with `using-skills` to reinforce the skill-first rule.
   - If uncertain, use `tool-and-skill-discovery` or `skill search`/`skill list`.
   - For fast decisions, read `docs/SKILL-TIERS.md`.
   - For the full idea-to-ship map, invoke `ask-matt`.

3. **Planning**
   - For 3+ step tasks, create a `todo_write` immediately.
   - Every plan must be detailed, sequential, verifiable, with no loose ends.
   - Mark `in_progress` when starting, `completed` when done — no batching.
   - For explicit acceptance criteria, use `unlazy` or `autonomous-gates`.

4. **Execution and verification**
   - Never deduce. Use tools to observe reality first.
   - For each step: state what must be true, how to verify, and the expected evidence.
   - Before claiming done, run local checks (build/test/lint/typecheck/dry-run).
   - After routing, verify the target skill is loaded and its first step is started.

## Bundle context

Keep this in mind for every session:

- Devin CLI validated release: `3000.6.7` (see `docs/DEVIN-CLI-COMPATIBILITY.md`).
- Models: parent `glm-5-2`; custom subagents `swe-1-7` (free). Never use `swe`, `opus`, `sonnet`, `gpt`, etc. when the parent is free.
- Issue tracker: local Markdown under `.devin/scratch/<feature-slug>/`, conventions in `.devin/agents/issue-tracker.md` and `.devin/agents/triage-labels.md`.
- Skills: 76 in the bundle; discovery via `docs/SKILL-TIERS.md`.
- Hooks: 8 lifecycle events (see `docs/TOOLS-MAP.md` and `config.json`).
- Verification baseline: `python audit.py` and `python -m pytest`.

## Situation router

Pick the entry skill from the user's situation. If the situation is not in this table, route to `ask-matt` for the full map or `tool-and-skill-discovery` for an external skill.

| Situation | Entry skill | Next |
|---|---|---|
| Build / change / implement something | `grilling` (With-docs) if decisions remain, or `review-cadence` if trivial | → `planning-pipeline` Spec → Tickets → `implement` + `tdd` → `code-review` → `verification-before-completion` → `finishing-a-development-branch` |
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
| Set up this repo for Devin | `project-setup` or `setup-matt-pocock-skills` | |
| Not sure which skill / flow fits | `ask-matt` | full map |
| No skill matches | `tool-and-skill-discovery` | evaluate / install |

For the main flow details (idea → ship, on-ramps, phase boundaries), see `ask-matt`.

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

- Subagents: use `swe-1-7` profiles (free). Never use `subagent_explore` (paid).
- Deep search: use the `researcher` subagent profile (`swe-1-7`).
- Models: parent is `glm-5-2`; subagents are `swe-1-7`. Don't use the `swe` alias (paid).
- Context: prefer `clear` between unrelated tasks; don't paste large documents into chat.
- Secrets: never display `.env`/`credentials.toml` values; name the variable and symptom only.
- Fact doubt → research (`web_search`, `webfetch`, `grep`, `exec`).
- Intent doubt → ask (`ask_user_question`).
- Cross-skill: `leo` is the session-start wrapper. Use `using-skills` to reinforce skill-first behavior. Use `ask-matt` for the full flow map when the quick router is not enough. Use `tool-and-skill-discovery` for external or missing skills.

## Forbidden Actions

- Deduce state, file content, or command output without using tools.
- Start non-trivial work without skill discovery.
- Push or commit with failing local checks (Rule 5).
- Sign commits, files, PRs, or docs as AI (Rule 2).
- Display secret values (Rule 19).
- Run destructive/irreversible actions without explicit user confirmation.
- Use `subagent_explore` or paid models when the parent is free.
- Compact when `clear` is sufficient; let context grow unchecked.
- Start `afk-loop` without local issues in `ready-for-agent` state.

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
