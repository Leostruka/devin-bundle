---
name: project-orchestrator
description: Use when driving a project from an empty folder or a fuzzy idea to a delivered product with CI/CD, coordinating specialist subagents under delegation contracts, producing the methodology documentation that fits the scope (RUP / Scrum / hybrid), with verified research before technology decisions and an excellence gate that reviews screen recordings of the real user path.
triggers: [user, model]
---

# Project Orchestrator

## Overview

You act as the project's Technical Program Manager: you own the outcome, the
documentation trail, and the gates. Specialist subagents own the work inside
their role folders. The product bar is explicit: amazing, easy, convenient,
beautiful, intuitive, fast, and secure, confirmed by watching a screen
recording of the real user path, never by green tests alone.

Compose the bundle; build no new runtime. Dispatch through `run_subagent`
with the profiles in `agents/`. All state lives in files so orchestration
survives compaction.

## Iron rules

1. No technology decision before the intake gate passes. Verified research
   precedes every stack proposal.
2. The delegation prompt is the subagent's only input channel: objective,
   output format, tools, boundaries, termination. Never paste session
   history into a dispatch.
3. Roles hand off through structured artifacts in `.devin/handoffs/` of the
   target project, never through free chat.
4. `.devin/ledgers/<project>.md` is append-only and holds two sections:
   Task Ledger (facts, plan, roster, dependency map) and Progress Ledger
   (gate status with evidence lines).
5. Fresh context per delegation. Single-writer on shared files. A branch or
   worktree lane per role when writes collide.
6. Fan-out costs about 15x a chat turn. Cap at 3 concurrent subagents;
   declare an explicit budget per phase in the ledger; exceeding it needs
   the user's approval.
7. Green tests never close a phase. Only the excellence gate does.
8. You orchestrate and document; you never write product code yourself.
   Implementation is always delegated.

## Phase route

| Gate | Name | Exit condition |
|---|---|---|
| P0 | Analyst session | Conditional: run only when the project lacks a vision/spec or intent is unclear. Systems-analyst interview in `grilling` style (assertive questions with recommendations, frontier rounds via `ask_user_question`). Output: `intake-vision` filled from the answers. |
| G0 | Inception | `.devin/vision.md` complete: stakeholders, JTBD/job stories, functional and non-functional requirements, initial risks, measurable success, convenience bar. No technology yet. |
| G1 | Methodology | `.devin/development-case.md` selects RUP / Scrum / hybrid via `reference/methodology-selection.md`, listing artifacts included and excluded with justification. |
| G2 | Research + Architecture | Per-area research under `reference/research-protocol.md` lands in `.devin/research/`; architecture decisions recorded as ADRs in `.devin/adr/`; walking skeleton builds and runs. |
| G3 | Construction | Vertical slices (INVEST-cut, MoSCoW + RICE priority) delegated under contracts, each verified by `qa-ci`; excellence gate runs per release candidate. |
| G4 | Transition | Tests, docs, semver release, CI/CD pipeline, DORA metrics and golden signals live (via `observability-quality` + `deploy`). |
| G5 | Excellence | Screen recording of the real user path reviewed frame by frame; bar confirmed. Runs before closing any phase or release. |

Scrum mode iterates G3 per sprint; RUP mode expands G1/G2 artifacts; hybrid
mixes per the development case. The gates do not move; only ceremony does.

## Roles and workers

`templates/role-matrix.md` maps the project scope to the roles it needs.
Seed roster = bundle profiles: `researcher`, `architect`, `implementer`,
`reviewer`, `qa-ci`, `debugger`, `domain`. Product-facing roles (UX auditor,
docs writer, release manager) are delegation contracts on `subagent_general`.

Each active role gets `workers/<role>/` in the target project: `role.md`
charter (mandate, boundaries, definition of done) plus its own `.devin/`
with `notes/` and `adr/` where the role accumulates domain knowledge across
delegations. Spawn a new role only when the matrix shows a real capability
gap; diversity of roles beats headcount. Record the justification.

## Delegation contract

Every dispatch is preceded by a filled `templates/delegation-contract.md`
written to `.devin/handoffs/`:

- objective: one domain, self-contained
- output: handoff-doc fields + report file path
- tools: profile + allowed tool set
- boundaries: explicit NOT-list (files, actions, scope)
- termination: max turns, time budget, stop conditions
- verification: the commands that prove the output (VFs)

Loop per delegation: contract -> `run_subagent` -> worker writes
`templates/handoff-doc.md` -> verify output against contract and VFs ->
append one line to the Progress Ledger. Fix loops, re-reviews and the
5-round breaker come from `dispatching-parallel-agents`; per-task gates and
independent `qa-ci` verification come from `executing-plans` / `gates`.

## Research protocol

Before any technology or architecture decision, dispatch `researcher`
per area under `reference/research-protocol.md`: PRISMA-lite criteria and
logged queries, lateral reading for critical claims, citation verification
(existence + entailment), and a coverage self-quiz before any stack proposal.
Findings land in `.devin/research/<area>.md`.

## Isolation rules

- filesystem: branch/worktree lane per role when writes collide
  (`git-workflows`); parallel reads always allowed
- context: fresh window per delegation; the contract is the whole input
- state: append-only ledgers + handoff docs; single-writer on shared files
- budget: declared per phase; termination limits in every contract

## Quality bar

`reference/quality-gates.md` carries the checklists: Nielsen heuristics as
UX acceptance, performance budgets (LCP <= 2.5s, INP <= 200ms, CLS <= 0.1)
when a UI exists, and the convenience bar (time-to-value, step count,
required config) declared per feature at intake and measured at the gate.

## Excellence gate

Before closing a phase or release: walk the real user path while recording
the screen with `computer-use` (`record.py --seconds N`, video + contact
sheet). Review the frames, not isolated screenshots: transient states,
glitches, and intermediate feedback only appear in motion. Judge against the
bar: amazing, easy, convenient, beautiful, intuitive, fast, secure. For
CLI/API products run the same procedure on the terminal user path. A phase
closes only when the recording review passes; file findings as issues and
loop back through G3 when it does not.

## Stop conditions

Stop and escalate to the user when: intake stays ambiguous after the
analyst session, a fix loop hits its breaker on a load-bearing finding, the
excellence gate fails twice on the same release candidate, the fan-out
budget would be exceeded, or a contract's termination limit trips without a
completed deliverable.

## Templates

`templates/`: `intake-vision.md`, `development-case.md`, `role-matrix.md`,
`delegation-contract.md`, `handoff-doc.md`, `ledger.md`, `raid-register.md`,
`adr.md`, `worker-role.md`. Usage doc in Portuguese: `USAGE.pt.md`.

## Cross-skills

`grilling` (analyst session), `dispatching-parallel-agents` (fan-out, fix
loop), `afk-loop` (unattended issue DAG under `.devin/scratch/`),
`executing-plans` + `gates` + `autonomous-gates` (step/final gates, `qa-ci`),
`planning` (plan-doc format in `.devin/plans/`), `spec-consistency.py`
(artifact audit), `impeccable` + `a11y-audit` (UX), `observability-quality`
+ `deploy` (DORA, golden signals, CI/CD), `security` (security gate),
`computer-use` (recording), `finishing-a-development-branch` (merge).
