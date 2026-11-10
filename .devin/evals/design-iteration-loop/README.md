# R7-13 / GH #446 - bounded design-iteration loop, converge by gate

Source: YT `DByAR5Su1Yw`
(`.devin/scratch/yt-batch2/transcripts/DByAR5Su1Yw.en.vtt`) - Nate
Herk ran "make it better" 100x on a bad coffee-shop site. Survey
summary (`.devin/research/2026-11-10-reels-batch7-survey.md` line 14):
Sonnet plateaus around round 32; Opus accretion-collapses (~21k LOC of
slop); LOC is not a quality metric. Lesson: unbounded improve-loops
either plateau silently or bloat; iteration must converge on a gate,
not a count.

## Current state of loop bounding in the bundle

- `skills/impeccable/SKILL.md` "Frontend loop": fixed ordered list
  (audit -> critique -> distill -> layout -> typeset -> colorize ->
  harden -> polish) with "stop when the result is good enough" - a
  single pass, no re-entry, no explicit gate criteria or max count.
- Gate machinery exists but is not wired to iteration:
  `design_lint.py` exit codes (0 clean / 2 findings), the SKILL.md
  verification checklist, and the `direction-approved.md` waiver
  mechanism (boundaries section).
- Other bundle loops for reference: `scripts/design-lint-gate.py`
  (warn-only PostToolUse), `skills/arena/SKILL.md` uses convergence
  of candidates as a stop signal (line 40). No skill defines
  "iterate until gate or N max" for design refinement.

## Proposed contract

Iterate the audit/critique/fix sub-loop until the gate passes or the
budget is spent - whichever first.

- **Gate (pass condition):** `design_lint.py` exits 0, or every
  remaining finding is waived verbatim in `direction-approved.md`;
  the SKILL.md verification checklist is fully checked.
- **Max iterations:** N = 3 full critique-fix cycles per surface
  (empirically past the plateau onset for single-component work;
  per the source video, model output plateaus well before 100).
- **Progress rule:** each cycle must close at least one lint finding
  or one checklist item; a cycle that changes nothing terminates the
  loop early (plateau detection, the Sonnet-r32 failure mode).
- **Accretion guard:** if a cycle grows the file >20% without
  closing findings, stop and distill instead of adding (the
  Opus-21k-LOC failure mode).
- **Escalation:** if gate not met at N, write the remaining findings
  to `.devin/plans/impeccable-<surface>-audit.md` and stop; do not
  keep polishing silently.

## Edit made

The contract was added to `skills/impeccable/SKILL.md` under the
"Frontend loop" section as a "Bounded iteration" subsection: gate
definition, N = 3, progress rule, accretion guard, escalation
behavior. Single small block; no other sections touched.
