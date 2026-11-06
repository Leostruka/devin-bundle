---
name: impeccable
description: Use when the user asks for UI/UX work, wants to fix or polish a page/component, or when an interface looks bland, inconsistent, or like a default template.
triggers: [user]
---

# Impeccable

Design vocabulary for production-grade frontend interfaces. Adapted from `github.com/pbakaus/impeccable` @ c3bb418 (Apache 2.0) + direction protocol from `github.com/alchaincyf/huashu-design` (MIT). Muscle: `extensions/design-intelligence/` (`design_lint.py`, `search.py`).

## When to use

- User asks for UI/UX work: landing page, dashboard, component, app shell, form, settings, onboarding, empty state.
- Existing UI looks bland, loud, inconsistent, or like a default template.
- Need to audit, polish, or iterate a frontend surface.
- Not for backend-only or non-UI tasks.

## Context files

Two files hold durable truth. Everything else is transient.

### PRODUCT.md - durable product truth (schema 1)

Fixed sections, in order: `Platform` - `Users` - `Product Purpose` - `Positioning` - `Operating Context` - `Capabilities and Constraints` - `Brand Commitments` - `Evidence on Hand` - `Product Principles` - `Accessibility & Inclusion`. Emit a `<!-- impeccable:product-schema 1 -->` marker near the top. Never invent claims, testimonials, benchmarks, pricing, or deployment facts - `Evidence on Hand` records what exists; absence is recorded, not fabricated.

### DESIGN.md - visual system

YAML frontmatter (normative, the portable token export): `name`, `description`, `colors:` map in oklch/hex with per-token comments, plus typography/space/radius/motion maps as needed. After the frontmatter, fixed sections in order: `1. Overview` - `2. The Kit` - `3. Colors` - `4. Typography` - `5. Elevation and Material` - `6. Components` - `7. Do and Do Not`. When a stylesheet/tokens file is the source of truth, say so in a comment inside the frontmatter and mirror values verbatim.

## Command vocabulary (24, synced to upstream @ c3bb418)

| Command | Use when |
|---|---|
| `impeccable` | General design request; pick next step. |
| `shape` | Plan UX/UI before writing code (see Direction protocol). |
| `init` | One-time capture of `PRODUCT.md` per the schema above. |
| `document` | Generate `DESIGN.md` from existing project code (frontmatter + fixed sections). |
| `extract` | Pull reusable components/tokens into a design system. |
| `critique` | Design review with scoring and detection. |
| `audit` | Technical quality check (layout, performance, accessibility). |
| `polish` | Meticulous final pass between good and great. |
| `bolder` | Push safe designs toward impact. |
| `quieter` | Tone down designs that are shouting. |
| `distill` | Ruthless subtraction; strip to essence. |
| `harden` | Production-ready edge cases, i18n, errors, overflow. |
| `onboard` | First-run experiences, empty states, paths to value. |
| `animate` | Purposeful motion that conveys state. |
| `colorize` | Add strategic color without going garish. |
| `typeset` | Fix typography that feels generic or accidental. |
| `layout` | Fix spacing, rhythm, alignment. |
| `delight` | Small moments of personality. |
| `clarify` | Rewrite confusing UX copy. |
| `adapt` | Responsive or cross-context adaptation. |
| `optimize` | UI performance (LCP, bundle size). |
| `overdrive` | Push past conventional limits. |
| `craft` | Deprecated alias for an ordinary new-work request. |
| `live` | Iterate UI in the browser with variants. |
| `generate` | Produce variants/alternatives of a named element to choose from. |

## Direction protocol (huashu port, used by `shape` and new surfaces)

1. **sec0 fact-verify** - before any direction work, verify product facts (name, purpose, platform, versions, audience) with `web_search`/repo evidence. Write verified facts to `product-facts.md`; if a material fact cannot be verified, ask the user - never invent.
2. **Five Form Questions** - answer all five against the facts: papel narrativo, distancia de audiencia, temperatura visual, capacidade/densidade, motivo visual. Map each to `extensions/design-intelligence/search.py --domain` (style, product, colors, typography) - the corpus dial, not taste.
3. **Direction gate** - generate 6 direction candidates; select 3 real directions + 3 documented alternatives with rationale. Write `direction-approved.md` recording the choice, the alternatives rejected, and every exemption verbatim (exact user words granting each exception). Exemptions are never paraphrased.
4. Only after the gate, produce the brief and (if asked) implementation.

## Muscle wiring (deterministic first pass)

- `audit` / `critique`: run `python extensions/design-intelligence/design_lint.py <target> --json` first; report its findings verbatim, then apply LLM judgment only to what the linter cannot see (narrative, hierarchy intent, brief fit). Exit 2 findings are deterministic facts, not opinions.
- `colorize` / `typeset` / `layout`: query `search.py "<brief>" --domain <colors|typography|style>` before proposing; cite the retrieved rows.
- React/Next/React Native/Expo targets: also consult `extensions/design-intelligence/data/frontend-rules/<stack>/` before implementing.

## Push vs Pull for Design Patterns

- **Push (to critique/audit):** the reviewer or audit pass receives the design context - `PRODUCT.md`, `DESIGN.md`, `direction-approved.md`, anti-references, brand tone, surface type, and lint findings. Push these constraints before the critique so the reviewer verifies against them.
- **Pull (by implementer):** the implementer reaches for the right command (`shape`, `layout`, `harden`, etc.), the lint output, and the direction artifacts before writing UI, instead of waiting for critique to catch generic design.

## Frontend loop

When the user says "fix the design" without naming a command, run in order and stop when the result is good enough:

1. `audit` - design_lint.py first; then a11y labels, focus rings, contrast, motion preference, no-JS fallbacks, overflow. Findings to `.devin/plans/impeccable-<surface>-audit.md`.
2. `critique` - lint findings + top-3 judgment issues to `.devin/plans/impeccable-<surface>-critique.md`.
3. `distill` (optional) - strip non-essential elements.
4. `layout` - spacing, rhythm, alignment, breakpoints.
5. `typeset` - hierarchy, line-height, weights, casing.
6. `colorize` - all color uses map to theme tokens (`primary`, `on-primary`, `surface`); fix mismatched tokens.
7. `harden` - reduced motion, keyboard nav, screen-reader labels, error states, long text, small viewports, dark mode.
8. `polish` - shadows, transitions, radius consistency, icon sizing.

## Output rule

After each pass that produces code changes: run the project's tests/build; commit with a focused message.

## Verification checklist

- [ ] `design_lint.py` clean or every finding waived verbatim in `direction-approved.md`.
- [ ] Color tokens are correct for each surface.
- [ ] Focus states are visible.
- [ ] Motion respects `prefers-reduced-motion`.
- [ ] No-JS fallback works where applicable.
- [ ] Tests and build pass.

## Boundaries

- Missing `PRODUCT.md` alone does not make a project greenfield; infer the incumbent world from code first, offer `init` after.
- Refinement preserves the incumbent identity; redesign replaces the look but keeps product truth - never split the difference into polish on a discarded look.
- The brief wins: honor pinned aesthetics, eras, fonts, palettes even when they collide with lint warnings - record the collision as a verbatim exemption.
- Emblems tied to militarism, supremacy, or hate movements are never motifs or ornament; content documenting them as fact stays.

## Cross-skills

- `a11y-audit` - WCAG verification (contrast, focus, labels) before shipping.
- `creative-engineering` - named visual styles/archetypes (CRT, dither, brutalist): load its retrieval step-0 and technical anatomy.
- `context7` - named UI framework (React, Vue, Svelte, Tailwind, shadcn): fetch docs before proposing implementation.

## References

- `extensions/design-intelligence/` - local muscle (lint + BM25 corpus).
- `https://impeccable.style/slop/` - anti-pattern gallery behind the 62-rule registry.
