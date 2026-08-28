---
description: "Design vocabulary and frontend improvement loop for production-grade interfaces. Use when the user asks for UI/UX work, wants to fix or polish a page/component, or when an interface looks bland, inconsistent, or like a default template."
triggers: [user, model]
---

# Impeccable

Design vocabulary for production-grade frontend interfaces. Adapted from `https://impeccable.style/` by Paul Bakaus (Apache 2.0).

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

## Frontend loop

Use this loop when the user says something like "fix the design" without naming a specific command. Run the passes in order. Stop when the result is good enough; otherwise write a short plan, fix, then move to the next pass.

1. **`audit`** — Technical quality check.
   - Run the page in `browser_preview`.
   - Check for: accessibility labels, focus rings, color contrast, motion preference, no-JS fallbacks, layout overflow, and component misuse.
   - Output: findings list in `.devin/plans/impeccable-<surface>-audit.md`.

2. **`critique`** — Design review.
   - Look for slop and score the page. List the top 3 issues.
   - Output: `.devin/plans/impeccable-<surface>-critique.md`.

3. **`distill`** (optional) — Strip non-essential elements that do not support the task.

4. **`layout`** — Fix spacing, rhythm, alignment, and responsive breakpoints.

5. **`typeset`** — Check hierarchy, line-height, font weights, and label casing.

6. **`colorize`** — Verify all color uses map to the project theme tokens (`primary`, `on-primary`, `surface`, etc.). Fix mismatched tokens like `bg-primary-container text-on-primary`.

7. **`harden`** — Test reduced motion, keyboard navigation, screen-reader labels, error states, long text, small viewports, and dark mode.

8. **`polish`** — Final pass on shadows, transitions, border radius consistency, and icon sizing.

## Output rule

After each pass that produces code changes:
- Run `php artisan test` if PHP/Blade changed.
- Run `npm run build` if CSS/JS changed.
- Commit with a focused message.

## Verification checklist

- [ ] No generic template aesthetics.
- [ ] Color tokens are correct for each surface.
- [ ] Focus states are visible.
- [ ] Motion respects `prefers-reduced-motion`.
- [ ] No-JS fallback works where applicable.
- [ ] Tests and build pass.

## Implementation notes

- Prefer real data and concrete labels over lorem ipsum.
- Use `browser_preview` after significant UI changes.
- If the user names a UI framework (React, Vue, Svelte, Tailwind, shadcn, etc.), invoke `context7` before proposing implementation details.
- If a local `npx impeccable` CLI is installed and trusted, prefer its detector output for `audit` and `critique`; otherwise apply the principles above.
- Keep files small and focused; do not let design context leak into backend logic.

## References

- `https://impeccable.style/docs/` — full command reference.
- `https://impeccable.style/slop/` — anti-pattern gallery.
- `https://impeccable.style/designing/` — design principles.
