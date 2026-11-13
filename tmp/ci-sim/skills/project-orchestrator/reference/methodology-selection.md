# Methodology selection

Gate G1. The output is a filled `templates/development-case.md` saved as
`.devin/development-case.md` in the target project. The choice is never
defaulted silently; it follows the decision rule below and records its
justification.

## Inputs

1. **Cynefin domain** of the problem space:
   - clear: known knowns, best practice exists
   - complicated: known unknowns, expertise and analysis resolve them
   - complex: unknown unknowns, probe-sense-respond
   - chaotic: no stable patterns; act first
2. **Regulation**: compliance, audit, or certification requirements that
   force documentation and traceability (low / medium / high).
3. **Size**: expected scope in roles, duration, and artifact surface
   (small / medium / large).

## Decision rule

| Domain | Regulation | Size | Selection |
|---|---|---|---|
| complex | any | any | agile flow: Scrum skeleton, short iterations |
| complicated | low-med | small-med | hybrid: Scrum cadence + RUP-lite inception/elaboration docs |
| complicated or clear | high | med-large | RUP: fuller artifact set, formal gates |
| clear and stable | any | small | lean predictive: minimal artifacts |
| chaotic | - | - | act first to stabilize, then reclassify |

Uncertain between two? Pick the hybrid and record why: field evidence shows
most real projects run hybrid, and the development case lets you expand or
shed ceremony at the next gate without rewriting history.

## What each selection changes

- **RUP**: full inception/elaboration/construction/transition artifact set;
  vision, use-case model, architecture document, risk list, iteration plans.
  Use `templates/` fully; heavier Progress Ledger granularity.
- **Scrum**: vision + product backlog replace the RUP document set; sprints
  carry G3; the development case documents which RUP artifacts are excluded
  and why.
- **Hybrid**: per-artifact decision. Common pattern: RUP-lite intake, ADRs,
  and risk register; Scrum execution and review cadence.

## Non-goals

No SAFe, LeSS, or other enterprise scaling frameworks. Team-of-teams
coordination is out of scope for this skill.
