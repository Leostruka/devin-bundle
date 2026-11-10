# R7-12 / GH #445 - design state/motion coverage rules

Eval: does the design-intelligence surface (skill `impeccable` +
extension `extensions/design-intelligence/`) encode coverage rules for
component states and motion, or only static slop detection?

Source reels (`.devin/scratch/reels-7/transcripts/`):
`DcjkR2PSkml` (six button states), `DeK0AFcIRhf` (switch knob
fidelity: travel, stretch-on-width-not-scaleX, spring bounce,
release-commit animation), `DfUdibshw3A` (hairline: pointer-reactive
isometric components). `DfbKtE6iabf`, `DfYRPKEDSDJ` are music-only
transcripts, no usable content.

## Current state (verified against code)

- Skill: `skills/impeccable/SKILL.md` (frontmatter `name: impeccable`,
  line 9 declares `extensions/design-intelligence/` as muscle).
- Lint: `extensions/design-intelligence/design_lint.py` -
  deterministic static linter, exit 2 on findings, drives off
  `rules_registry.py` ANTIPATTERNS (62 rules) + `checks.py` CHECKS.
- Write-time gate: `scripts/design-lint-gate.py` - ~12 inline rules,
  warn-only PostToolUse hook, explicitly not the full set.
- Existing state/motion coverage is thin and negative-only:
  - `rules_registry.py` `blinking-cursor`, `marquee`,
    `bounce-easing` - ban decorative/degraded motion.
  - `checks.py` has no per-state rules; rules target tokens, fonts,
    palettes, buzzwords.
  - `impeccable/SKILL.md` checklist: "Focus states are visible" and
    "Motion respects prefers-reduced-motion" (2 checklist lines,
    unenforced by lint).
  - `harden` pass mentions "error states" and the `animate` command
    exists (SKILL.md line 47) but carries no coverage contract.

## Proposed coverage matrix (component states x motion properties)

Component states (rows), per DcjkR2PSkml + DeK0AFcIRhf:

| State | Required signal | Motion properties to check |
|---|---|---|
| default | looks pressable (fill/outline/shadow) | idle only, no ambient animation |
| hover | visual delta on pointer-over | quick ease-out <= 150ms; absent on touch |
| focus | visible focus ring (a11y) | no motion required; never suppress outline |
| pressed/active | immediate tactile feedback | darken/scale-down <= 100ms; ripple ok |
| loading | in-button loader, button stays put | spinner/indeterminate; label preserved |
| disabled | visibly non-interactive | no hover/press animation; explain why if possible |
| checked/toggled | knob travel reads as physical | translate not scaleX-stretch; spring bounce ok; release-commit allowed |

Motion properties (columns, where applicable): duration, easing
(exponential-out preferred per `bounce-easing` rule), property
animated (transform/opacity over layout), `prefers-reduced-motion`
fallback, interruptibility (press-release cancels cleanly).

## Gap table - covered vs missed

| Capability | Covered | Where | Missed |
|---|---|---|---|
| Ban decorative motion | yes | registry `blinking-cursor`, `marquee` | - |
| Ban tacky easing | yes | registry `bounce-easing` | - |
| Focus-visible presence | partial | SKILL.md checklist only | no lint rule; not in `checks.py` |
| reduced-motion fallback | partial | SKILL.md checklist + `harden` | no lint rule for missing media query |
| Hover/press/loading/disabled coverage | no | - | no state matrix anywhere |
| Switch/toggle travel semantics | no | - | DeK0AFcIRhf rules absent |
| Pointer-reactive components | no | - | out of lint scope (needs runtime) |
| Transition duration caps | no | - | no rule for >300ms UI transitions |

## Rule added

A short "State and motion coverage" section was appended to
`skills/impeccable/SKILL.md` encoding the seven-state matrix and the
motion-property checks as audit/harden inputs. No lint code changed;
a future `checks.py` pass can promote the deterministic subset
(missing `:focus-visible`, missing `prefers-reduced-motion` query).
