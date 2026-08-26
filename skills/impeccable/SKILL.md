---
name: impeccable
description: Use when the user asks to design, redesign, shape, critique, audit, polish, animate, colorize, typeset, adapt, clarify, distill, harden, onboard, optimize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, and empty states. Not for backend-only or non-UI tasks.
model: swe-1-7
---

# Impeccable

Design vocabulary for production-grade frontend interfaces. Adapted from `https://impeccable.style/` by Paul Bakaus (Apache 2.0). Helps avoid generic agent-default aesthetics by establishing design context before building and applying targeted design commands.

## When to use

- User asks for UI/UX work: landing page, dashboard, component, app shell, form, settings, onboarding, empty state.
- Existing UI looks bland, loud, inconsistent, or like a default template.
- Need to audit, polish, or iterate a frontend surface.
- Not for backend-only or non-UI tasks.

## Core protocol

1. **Gather design context first.** If the project lacks `PRODUCT.md` and `DESIGN.md` (or `.impeccable.md`) with the required context, ask the user or infer from existing code. Required context:
   - Target audience and use cases.
   - Brand personality/tone (bolder vs quieter, warm vs cold, playful vs serious).
   - Anti-references (styles to avoid).
   - Color, typography, and component constraints.
   - Surface type: brand (marketing/landing/portfolio) or product (app/dashboard/tool).

2. **Pick one command** that matches the goal. Do not chain passes unless the user asks.

3. **Implement real working code** with attention to spacing, hierarchy, typography, color, motion, and edge cases. Use `browser_preview` to verify visual output when possible.

4. **Audit before declaring done.** Check against common slop patterns:
   - Generic gradients, purple-to-blue, beige body background, cards nested in cards.
   - Rounded-square icon tiles above every heading.
   - Gray text on colored backgrounds, Inter for everything.
   - Vague headlines like "Unlock your potential".
   - Equal visual weight on unrelated metrics.

## Command vocabulary

| Command | Use when |
|---|---|
| `impeccable` | General design request; pick next step. |
| `shape` | Plan UX/UI before writing code. |
| `polish` | Meticulous final pass between good and great. |
| `critique` | Design review with scoring and detection. |
| `audit` | Technical quality check (layout, performance, accessibility). |
| `distill` | Ruthless subtraction; strip to essence. |
| `clarify` | Rewrite confusing UX copy. |
| `layout` | Fix spacing, rhythm, alignment. |
| `typeset` | Fix typography that feels generic or accidental. |
| `colorize` | Add strategic color without going garish. |
| `animate` | Purposeful motion that conveys state. |
| `bolder` | Push safe designs toward impact. |
| `quieter` | Tone down designs that are shouting. |
| `delight` | Small moments of personality. |
| `adapt` | Responsive or cross-context adaptation. |
| `harden` | Production-ready edge cases, i18n, errors, overflow. |
| `onboard` | First-run experiences, empty states, paths to value. |
| `optimize` | UI performance (LCP, bundle size). |
| `extract` | Pull reusable components/tokens into a design system. |
| `document` | Generate `DESIGN.md` from existing code. |
| `live` | Iterate UI in the browser with variants. |
| `init` | One-time setup of `PRODUCT.md` and `DESIGN.md`. |

## Implementation notes

- Prefer real data and concrete labels over lorem ipsum.
- Use `browser_preview` after significant UI changes.
- If a local `npx impeccable` CLI is installed and trusted, prefer its detector output for `audit` and `critique`; otherwise apply the principles above.
- Keep files small and focused; do not let design context leak into backend logic.

## References

- `https://impeccable.style/docs/` — full command reference.
- `https://impeccable.style/slop/` — anti-pattern gallery.
- `https://impeccable.style/designing/` — design principles.
