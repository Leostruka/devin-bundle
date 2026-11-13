# Quality gates

Product quality criteria applied at G3 (per slice), G4 (release), and G5
(excellence). Green tests are necessary and insufficient.

## UX acceptance: Nielsen heuristics

Run as a checklist against each user-facing slice:

- visibility of system status
- match between system and real world
- user control and freedom
- consistency and standards
- error prevention
- recognition rather than recall
- flexibility and efficiency of use
- aesthetic and minimalist design
- helps users recognize, diagnose, recover from errors
- help and documentation

For UI work invoke `impeccable` (design quality) and `a11y-audit`
(accessibility) rather than re-deriving their checklists here.

## Performance budget (when a UI exists)

- LCP <= 2.5s
- INP <= 200ms
- CLS <= 0.1

Measure on the real user path, not a synthetic route. Budget violations
block the release gate the same as test failures.

## Convenience bar

Convenience is a requirement, declared per feature at intake
(`intake-vision.md`) and measured at the gate:

- **time-to-value**: seconds from first launch to first useful outcome
- **step count**: actions required for the core task, counted on the
  recorded path
- **required config**: what the user must set up before value; the bar is
  near zero unless the intake explicitly accepts otherwise

## Excellence gate procedure (G5)

1. Define the user path: the shortest real route a user takes to value.
2. Record the walkthrough with `computer-use`: `record.py --seconds N`
   produces video + contact sheet. For CLI/API products record the terminal
   session the same way.
3. Review the frames, not isolated screenshots. Look for what only motion
   reveals: flicker, loading gaps, focus loss, premature feedback, dead
   states between actions.
4. Score the path against the bar: amazing, easy, convenient, beautiful,
   intuitive, fast, secure. Any dimension below bar blocks the close.
5. On failure: file findings as issues in the project tracker and route
   back through G3. Two consecutive failures on the same release candidate
   escalate to the user.

## Evidence

Each gate outcome lands in the Progress Ledger with evidence: the recording
path, the measured values (timings, step counts), and the checklist result.
