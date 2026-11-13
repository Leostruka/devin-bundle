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
5. Fresh context per delegation. Single-writer on shared files. One
   worktree + branch lane per writing role; read-only roles get
   `Lane: read-only`.
6. Fan-out costs about 15x a chat turn. Cap at 3 concurrent subagents;
   declare an explicit budget per phase in the ledger and record `consumed`
   per contract; exceeding it needs the user's approval.
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

Each active role gets `workers/<role>/` in the target project root as its
durable home: `role.md` charter (mandate, boundaries, definition of done)
plus its own `.devin/` with `notes/` and `adr/` where the role accumulates
domain knowledge across delegations. The durable home is not a working
directory: execution happens in the role's worktree lane (Isolation rules).
Spawn a new role only when the matrix shows a real capability gap;
diversity of roles beats headcount. Record the justification.
Reassigning a role = editing `workers/<role>/role.md` plus a fresh dispatch
carrying standing context; record `reassign:` in the Progress Ledger.

## Delegation contract

Every dispatch is preceded by a filled `templates/delegation-contract.md`
written to `.devin/handoffs/`:

- objective: one domain, self-contained
- lane: worktree path + branch + Lane setup / Lane teardown commands
  (worktree is the default for writing roles; `read-only` otherwise)
- inputs: artifact paths + `Readable refs` allowlist of root docs
- frozen inputs: sha256 hash per input file, pinned at dispatch and
  re-hashed at verify; drift is a contract failure
- output: handoff-doc fields + report file path
- tools: profile + allowed tool set
- boundaries: explicit NOT-list (files, actions, scope)
- peer consults: allowed roles + cap; routed by you, never direct
- termination: max turns, time budget, stop conditions
- verification: the commands that prove the output (VFs)

Loop per delegation: contract (with frozen-input hashes) -> `run_subagent`
-> record `handle: <agent_id>` -> worker writes `templates/handoff-doc.md`
-> verify output against contract and VFs and re-hash frozen inputs ->
append one line with `handle:` and `spent:` to the Progress Ledger ->
rewrite `## Status`. A handoff carrying `ESCALATE` stops the loop and goes
to the user. A `CONSULT:` request is relayed by you (resume the peer's
handle, cap 2 exchanges, or a micro-contract) and logged; `resume` for
bounded follow-up (<=2 questions) counts against the contract budget.
Fix loops, re-reviews and the 5-round breaker come from
`dispatching-parallel-agents`; per-task gates and independent `qa-ci`
verification come from `executing-plans` / `gates`.

## Research protocol

Before any technology or architecture decision, dispatch `researcher`
per area under `reference/research-protocol.md`: PRISMA-lite criteria and
logged queries, lateral reading for critical claims, citation verification
(existence + entailment), and a coverage self-quiz before any stack proposal.
Findings land in `.devin/research/<area>.md`.

## Subconscious advisor

A peer `devin` session you own via `computer-use` terminal control, consulted
before decisions, after cycles, on the event triggers in
`reference/advisor-protocol.md` (gate outcomes, contract cadence, ESCALATE
handoffs, RESET_WORKER flags), and when re-planning approach or roster.
Charter: `templates/advisor-charter.md`.

- Spawn: `terminal.py spawn` PTY running `devin`, onboarded with the charter;
  record `Advisor:` in the ledger. Resume-loop (`run_subagent` + `resume`)
  and `devin acp` are the documented fallbacks when CU control is unwanted or
  restarts must be survived.
- Consult: typed prompt is the trigger; artifacts are the payload. Reply
  contract: VERDICT / RATIONALE / RISKS / HYGIENE / MEMORY DELTA / marker.
- State: `.devin/advisor/` (charter, managed notes, consultation log,
  onboarding) written by the advisor; you own ledgers and handoffs.
- Hygiene is literal: `/clear` typed into the peer resets it; the advisor's
  `HYGIENE: RESET_ORCHESTRATOR` arrives as a typed request message, and you
  ask the user to `/clear` + re-invoke (advisor never clears you uninvited).
- Advisory only: its VERDICT never auto-executes; 1 consult per decision,
  debate cap 2 rounds, peer sessions count against the fan-out budget.

## Isolation rules

- filesystem: you and the advisor are anchored in the project root. You own
  the root `.devin/` (ledgers, handoffs, vision, adr, research, raid) and
  are the single writer of `ledgers/` and the contract docs in `handoffs/`;
  the advisor is a peer session on the root workspace, owns `.devin/advisor/`
  and reads everything else read-only. Each writing role executes inside its
  own worktree lane at `$ROOT/.worktrees/<role>` on branch `<slug>-<role>`
  (fallback: sibling dir `<repo>-<role>` when `.gitignore` is untouchable);
  read-only roles keep `Lane: read-only`. `workers/<role>/` stays at the
  root as the role's durable home (charter, notes, adr), never as a cwd.
  Worktrees are separate checkouts and untracked `.devin/` files are not
  shared, so handoffs, reports, frozen inputs, VFs and the durable home
  resolve as absolute paths under `$ROOT`, never against the worktree cwd;
  a worker writes only the `-out` handoff and report path its contract
  declares. Root docs reach a worker only through the contract's
  `Readable refs` allowlist. Lane setup / Lane teardown commands declared in
  the contract run with `$LANE_PATH`, `$BRANCH`, `$ROOT` (`git-workflows`;
  rationale in `reference/worktree-lanes.md`); parallel reads always allowed
- context: fresh window per delegation; the contract is the whole input
- state: append-only ledgers + handoff docs; single-writer on shared files;
  `## Status` is the only rewritten section
- budget: declared per phase with `consumed` recorded per contract;
  termination limits in every contract

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
budget would be exceeded, a contract's termination limit trips without a
completed deliverable, a handoff arrives with `ESCALATE` set, or the
advisor's RESET_ORCHESTRATOR fires twice in one phase.

## Templates

`templates/`: `intake-vision.md`, `development-case.md`, `role-matrix.md`,
`delegation-contract.md`, `handoff-doc.md`, `ledger.md`, `raid-register.md`,
`adr.md`, `worker-role.md`, `advisor-charter.md`, `team-pack.md`
(exportable roster: role-matrix + charters + conventions, importable into
another project). Usage doc in Portuguese: `USAGE.pt.md`.

## Cross-skills

`grilling` (analyst session), `dispatching-parallel-agents` (fan-out, fix
loop), `afk-loop` (unattended issue DAG under `.devin/scratch/`; recurring
checks become `every gate` ledger items or afk-loop issues - the skill has
no scheduler of its own),
`executing-plans` + `gates` + `autonomous-gates` (step/final gates, `qa-ci`),
`planning` (plan-doc format in `.devin/plans/`), `spec-consistency.py`
(artifact audit), `impeccable` + `a11y-audit` (UX), `observability-quality`
+ `deploy` (DORA, golden signals, CI/CD), `security` (security gate),
`computer-use` (recording, peer-session terminal control for the advisor),
`finishing-a-development-branch` (merge).
