# project-orchestrator: Design proposal (Phase 1)

Spec: `.devin/plans/2026-09-28-project-orchestrator.prompt.md`.
Approval gate: STOP after this document; Phase 2 only on approval.

## 1. What it is

`skills/project-orchestrator/` is a PM/PO-grade orchestration skill. Invoked in
the user's target project (empty folder or existing repo). Drives
intake → methodology → architecture → MVP → release/CI-CD by dispatching the
bundle's existing subagent profiles under explicit contracts, and records all
state in files so orchestration survives compaction.

No new runtime mechanisms. Composition only: `run_subagent` + profiles +
ledgers + gates + worktrees + `computer-use`.

## 2. Bundle file layout

```
skills/project-orchestrator/
  SKILL.md                     # dense core (<10KB): loop, gates, rules
  USAGE.pt.md                  # PT usage doc (in-scope item)
  reference/
    methodology-selection.md   # Cynefin/Stacey + regulation + size -> RUP/Scrum/hybrid
    research-protocol.md       # PRISMA-lite, lateral reading, citation checks, self-quiz
    quality-gates.md           # Nielsen checklist, perf budgets, convenience bar, excellence-gate procedure
  templates/
    intake-vision.md           # PR/FAQ + Vision: stakeholders, JTBD/job stories, FR/NFR, measurable success
    development-case.md        # artifact include/exclude + justification (RUP tailoring)
    role-matrix.md             # scope -> roles; spawn rule
    delegation-contract.md     # objective, output format, allowed tools, boundaries, termination
    handoff-doc.md             # structured artifact handoff between roles
    ledger.md                  # Task Ledger + Progress Ledger skeleton
    raid-register.md           # risks/assumptions/issues/dependencies + dependency map
    adr.md                     # Nygard/MADR skeleton
    worker-role.md             # workers/<role>/ charter + local .devin/ layout
tests/validation/test_project_orchestrator.py
```

SKILL.md holds what every run needs (loop, gates, stop rules). Methodology,
research protocol, and quality-gate detail sit behind pointers; progressive
disclosure per writing-skills.

## 3. Target-project artifact layout (what the orchestrator creates)

```
<project>/
  .devin/
    vision.md                  # intake output (AC2)
    development-case.md        # tailoring record (AC3)
    adr/NNN-*.md               # Nygard/MADR (AC7)
    ledgers/<project>.md       # Task Ledger + Progress Ledger, append-only (AC8)
    raid.md                    # RAID register + dependency map (AC8)
    research/<area>.md         # PRISMA-lite logs per research area (AC6)
    handoffs/<from>-<to>-<n>.md
  workers/<role>/
    role.md                    # charter: mandate, boundaries, definition of done
    .devin/notes/              # accumulated domain knowledge (AC4)
    .devin/adr/                # role-local ADRs
```

`workers/<role>/` sits at project root per spec ("uma pasta por papel, cada
qual com .devin/ próprio"). Roles are created lazily: a new role only when a
real capability gap exists (diversity > count).

## 4. Phase flow (lifecycle route, AC9)

```
P0 Analyst       CONDITIONAL: if the project has no vision/spec, or the
                 existing intent is unclear or incomplete, the orchestrator
                 runs a systems-analyst interview in `grilling` style
                 (assertive questions with recommendations, frontier rounds)
                 and fills intake-vision.md from the answers. Skipped when a
                 clear spec/PRD/vision already exists; then intake only
                 validates the material against the template.
G0 Inception     intake-vision filled; measurable success declared; no tech yet
G1 Methodology   development-case picks RUP / Scrum / hybrid (AC3 rule)
G2 Research+Arch per-area research protocol -> ADRs -> walking skeleton green
G3 Construction  vertical slices: INVEST-cut, MoSCoW+RICE priority; per-slice
                 delegation + qa-ci verification; excellence gate per release-candidate
G4 Transition    tests, docs, semver release, CI/CD + DORA metrics + golden signals
G5 Excellence    user-path screen recording + frame review (AC11) before closing
                 any phase/release
```

Methodology changes the ceremony, not the gates: Scrum mode iterates G3 per
sprint; RUP mode expands G1/G2 artifacts; hybrid mixes per development-case.

## 5. Methodology selection rule (AC3)

Explicit decision table in `reference/methodology-selection.md`:

| Cynefin domain | Regulation | Size | Methodology |
|---|---|---|---|
| complex (unknown unknowns) | any | any | agile/Scrum flow |
| complicated (expertise needed) | low-med | small-med | RUP-lite hybrid |
| complicated/clear | high (regulated) | med-large | RUP fuller artifact set |
| clear/stable | any | small | lean predictive, minimal artifacts |
| chaos | - | - | act first; no ceremony |

Output is always a filled `development-case.md`: artifacts included/excluded
with justification per item. Default when uncertain: hybrid (evidence: >50%
of real projects).

## 6. Role matrix (AC4)

Template `role-matrix.md` maps project scope to roles. Seed roster reuses
bundle profiles (`researcher`, `architect`, `implementer`, `reviewer`,
`qa-ci`, `debugger`, `domain`) plus product-facing roles that are pure
delegation contracts on `subagent_general` (UX auditor, docs writer, release
manager). Spawn rule: a new `workers/<role>/` only when the matrix shows a
gap no existing role covers; the matrix records the justification.

## 7. Delegation contract + dispatch loop (AC5, Magentic-One/Anthropic)

Every `run_subagent` dispatch is preceded by a filled
`delegation-contract.md` written to `.devin/handoffs/`:

- objective (one domain, self-contained)
- output format (handoff-doc fields + report file path)
- allowed tools / profile
- boundaries: explicit NOT-list (files, actions, scope)
- termination: max turns, token/time budget, stop conditions
- VFs: the commands that prove the output

Loop per delegation: contract -> dispatch -> worker writes structured
`handoff-doc.md` -> orchestrator verifies against contract + VFs -> append to
Progress Ledger. Free chat between roles is forbidden; only artifacts move.

## 8. Research protocol (AC6)

`reference/research-protocol.md`, dispatched to `researcher` (free) per area
before any technology decision:

- PRISMA-lite: declared inclusion/exclusion criteria, logged queries,
  claim -> source map
- lateral reading: never evaluate a source by its own claims
- citation verification at two levels: existence + entailment
- self-quiz as coverage audit before proposing a stack
- output: `.devin/research/<area>.md`

## 9. Ledgers and registers (AC8)

`.devin/ledgers/<project>.md`, append-only, two sections:

- **Task Ledger**: facts, plan, role roster, dependency map (what is true)
- **Progress Ledger**: per-gate status with evidence lines (what is proven)

`raid.md` holds the RAID register; dependency map lives as a section with
`Blocked by:` edges compatible with `afk-loop` issue DAG if the project drops
to unattended mode.

## 10. Isolation rules (AC13)

Codified in SKILL.md:

- filesystem: branch/worktree lane per role when writes collide
  (`git-workflows`); parallel reads always allowed
- context: fresh window per delegation; delegation prompt is the only input
  channel; no pasted history
- state: append-only ledgers + handoff docs; single-writer on shared files
- fan-out: default max 3 concurrent subagents (bundle rule); explicit budget
  per complexity; exceeding asks the user
- termination: every contract carries max turns/time; fix loops inherit the
  5-round breaker from `dispatching-parallel-agents`

## 11. Quality and excellence gates (AC10-12)

`reference/quality-gates.md`:

- Nielsen heuristics as UX acceptance checklist; `impeccable`/`a11y-audit`
  reused for UI work
- performance budget when applicable: LCP <= 2.5s, INP <= 200ms, CLS <= 0.1
- convenience bar declared per feature in intake: time-to-value, step count,
  required config, measured rather than assumed (AC12)
- **Excellence gate (AC11):** before closing each phase/release, walk the
  real user path while recording the screen via `computer-use`
  (`record.py --seconds N` -> video + contact sheet). Review frames, not just
  screenshots: transient states, glitches, intermediate feedback. The bar:
  amazing, easy, convenient, beautiful, intuitive, fast, secure. Green tests
  do not close this gate. For CLI/API products the same procedure runs on the
  terminal path.

## 12. Primitive reuse map (explicit)

| Need | Reuse |
|---|---|
| analyst interview (empty/unclear intake) | `grilling` |
| dispatch | `run_subagent` + `agents/*.md` profiles |
| fan-out discipline, fix loop, breaker | `dispatching-parallel-agents` |
| unattended issue DAG | `afk-loop` (issues under `.devin/scratch/`) |
| step/final gates, qa-ci | `gates`, `autonomous-gates`, `executing-plans` |
| plan format | `planning` plan-doc, saved `.devin/plans/` |
| plan/artifact audit | `scripts/spec-consistency.py` |
| UX surface | `impeccable`, `a11y-audit` |
| DORA/golden signals/CI quality | `observability-quality`, `deploy` |
| security gate | `security` |
| screen recording | `computer-use` (`record.py`) |
| branch finish | `finishing-a-development-branch` |

## 13. Contract tests (AC14)

`tests/validation/test_project_orchestrator.py` asserts, following
`test_ask_bundle_router.py` conventions:

- SKILL.md exists, frontmatter `name:` matches dir, description starts
  "Use when"
- all 9 templates + 3 reference docs + USAGE.pt.md exist
- required tokens present: Cynefin, PRISMA, delegation-contract fields,
  Task/Progress Ledger, RAID, MoSCoW, RICE, INVEST, DORA, LCP/INP/CLS,
  walking skeleton, `record.py`, `workers/`, `.devin/ledgers/`, qa-ci
- no em-dashes (hook convention), no AI signatures

Phase 3 gates: `pytest tests -q` 0 failures, `python audit.py` 0 errors
(manifest `skill_count` 59 -> 60 + new entry required; audit compares
manifest names to disk), README skill count 59 -> 60 (4 occurrences).

## 14. Open decisions

1. `workers/<role>/` at project root (spec-literal) vs `.devin/workers/`.
   Proposal: root, per spec.
2. SKILL.md in English (bundle convention) + `USAGE.pt.md` for the PT doc.
   Proposal: yes.
3. Phase names use RUP vocabulary (Inception/Elaboration/Construction/
   Transition) with agile mapping. Proposal: G0-G5 names above, RUP terms in
   templates.
