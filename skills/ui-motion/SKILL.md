---
name: ui-motion
description: Use when creating or modifying UI animations, transitions, loading states, skeleton screens, lazy loading, or any motion in frontend files (.tsx, .vue, .svelte, .css, .scss, .html). Covers purpose-driven motion, timing, easing, accessibility (WCAG 2.2), and performance.
triggers: [user, model]
allowed-tools: [read, grep, glob, edit, write, exec]
---

# UI Motion Principles

Evidence-based motion design for web and mobile interfaces. Synthesized from Material Design 3, Apple HIG, WCAG 2.2, and 20+ academic studies (CHI, PACM HCI, INTERACT, JCR).

## Core principle: purpose-driven motion

Motion serves a user goal. It is not decoration. Apply the frequency gate before animating:

| Interaction frequency | Motion policy |
|---|---|
| Monthly (onboarding, first-run) | Delightful animation OK |
| Daily (dashboard, settings) | Subtle polish only |
| 100s/day (lists, buttons, inputs) | Minimal or no animation |
| Keyboard-initiated | Never animate (Emil Kowalski rule) |

Motion hierarchy (most to least important):
1. **Feedback** — confirms an action happened
2. **Continuity** — maintains spatial relationship between states
3. **Communication** — conveys character, causality, hierarchy
4. **Delight** — first-impression only, use sparingly

Everything else is ornament. Ornament in software is rarely free — it costs tokens, frame budget, and user attention.

## Loading states (context-dependent, NOT universal skeleton)

Research shows no single loading pattern wins everywhere:

| Context | Best loading state | Evidence |
|---|---|---|
| Informational content, full-page loads | Skeleton screen | CHI 2018, APJCRI 2025 |
| Educational / entertainment | Progress bar | APJCRI 2025 |
| Any context, best overall | Progressive rendering | Uppsala study: users preferred progressive rendering over skeleton |
| Short waits (<300ms) | Nothing | Don't show loading for sub-300ms |
| Long waits with known duration | Progress bar with power/inverse-power function | IJHCI 2017: perceived shorter than linear |
| Long waits with unknown duration | Skeleton + looped animation | Drexel study: most effective combination |

**Never use spinners as default.** Spinners received lowest ratings across studies despite being most common. They are equivalent to no feedback if they don't communicate layout or progress.

## Lazy loading (context-dependent)

| Usage pattern | Strategy | Evidence |
|---|---|---|
| Few interactions per session | Lazy loading (40.8% faster initial load) | BTH study |
| Intensive interaction (filtering, search) | Eager loading (400x faster filtering) | BTH study |
| Below-the-fold content | Lazy load with IntersectionObserver | Standard practice |
| Images, media | Lazy load with `loading="lazy"` or native lazy | Standard practice |

After 2 interactions, eager loading becomes 21.6% faster overall. Choose based on usage, not dogma.

## Timing (canonical ranges)

| Category | Duration | Easing | Example |
|---|---|---|---|
| Micro-interactions | 100-200ms | ease-out | Hover, focus, button press |
| Standard transitions | 200-300ms | ease-out | Component enter/exit, dropdown |
| Page transitions | 300-500ms | ease-in-out | Route change, modal reveal |
| Decorative / onboarding | 400-600ms | emphasized | Use sparingly |
| Loading loops | 800-1500ms | linear | Spinners (if used), progress |

- **100ms** perceived as instant
- **500ms** maximum perceived as instant
- **>600ms** feels slow and annoying
- **Exit animations**: ~75% of entrance duration, ease-out

## Asymmetric timing

| Trigger type | Intro | Outro |
|---|---|---|
| User-triggered (tap, click) | Fast (~100ms) | Slow (~300ms) |
| System-triggered (error, modal) | Slow (~300ms) | Fast (~100ms) |

Always favor the user's interaction — shorter durations when responding to taps/clicks.

## Easing curves

```css
--ease-out:        cubic-bezier(0.22, 1, 0.36, 1);   /* default for 90% of UI: entrances, hover, state changes */
--ease-in-out:     cubic-bezier(0.65, 0, 0.35, 1);   /* same-layer transitions, layout morphs */
--ease-emphasized: cubic-bezier(0.2, 0, 0, 1);       /* hero reveal, single attention-grabbing element per viewport */
--ease-soft:       cubic-bezier(0.4, 0, 0.2, 1);     /* Material standard, general purpose */
```

**Avoid:**
- `ease-in` for UI (slow start delays feedback)
- `linear` except for loading indicators and scroll-linked progress
- `bounce` / `elastic` on functional UI (reads dated)

## Accessibility (WCAG 2.2 — mandatory)

WCAG 2.2 SC 2.3.3: Motion from interactions must be disableable unless essential to functionality.

**Every animation MUST handle `prefers-reduced-motion`:**

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

JavaScript detection:
```javascript
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
if (!prefersReducedMotion.matches) {
  // run animation
}
```

**Who this protects:** Vestibular disorders (dizziness, nausea), ADHD, epilepsy, migraine, scotopic sensitivity. Also benefits low-battery and low-end devices.

**Essential test:** Is the animation essential to functionality or information being conveyed? If no, it must be disableable. If yes, provide an alternative.

## Performance (60fps target)

**Only animate compositor-only properties:**
- `transform` (translate, scale, rotate)
- `opacity`

**Never animate layout-triggering properties:**
- `width`, `height`, `top`, `left`, `margin`, `padding`
- These trigger layout recalculation → frame drops

**FLIP technique for layout animations:**
1. **F**irst — record element's initial position
2. **L**ast — record element's final position
3. **I**nvert — apply transform to make element appear in initial position
4. **P**lay — remove transform, let it animate to final position

This animates layout changes using only `transform` → 60fps.

**Lottie caution:** Small file size but expensive runtime rendering. Destroy off-screen animations. Use `setSubframe(false)`. Avoid matte effects. Can crash mobile browsers.

## When NOT to animate

- Keyboard-initiated actions (tab navigation, shortcuts)
- High-frequency interactions (100s/day)
- Elements nobody is focused on
- When it delays the user's ability to complete tasks
- When it overrides `prefers-reduced-motion`
- For decoration alone (ornament is friction disguised as polish)

## Framework notes

- **React**: Framer Motion / Motion for component animations. `AnimatePresence` for exit animations.
- **Vue**: `<Transition>` and `<TransitionGroup>` built-in. GSAP for complex sequences.
- **Svelte**: `transition:` and `animate:` directives built-in.
- **CSS**: `@keyframes` + `transition` for simple cases. No library needed.
- **GSAP**: For scroll-linked (ScrollTrigger), timelines, complex sequencing. See `gsap-scrolltrigger` and `gsap-timeline` skills.
- **View Transitions API**: For page transitions and theme toggles, prefer CSS-first approach via `document.startViewTransition()`. [Transition-kit](https://github.com/AbdullahMukadam/Transition-kit) provides 32 ready-to-use CSS transitions (Circle Reveal, Cube, Fade, Slide, etc.) as shadcn-compatible components for React/Next.js/Vue/Svelte/vanilla. Copy-only, zero dependencies, falls back to instant swap when API unsupported. Customize duration, easing, and direction per template.

## Audit checklist

When reviewing existing motion:
- [ ] Does every animation serve feedback, continuity, communication, or delight?
- [ ] Are loading states context-appropriate (not universal skeleton)?
- [ ] Is timing within canonical ranges (100-500ms)?
- [ ] Is easing correct (ease-out default, no ease-in for UI)?
- [ ] Does every animation handle `prefers-reduced-motion`?
- [ ] Are only `transform` and `opacity` animated (no layout properties)?
- [ ] Are exit animations ~75% of entrance duration?
- [ ] Is asymmetric timing applied (user-triggered vs system-triggered)?
- [ ] Are high-frequency interactions minimal or non-animated?
- [ ] Are keyboard-initiated actions non-animated?

## Sources

- CHI 2018: Skeleton screens study — https://doi.org/10.1145/3232078.3232086
- PACM HCI 2024: False front pages — https://dl.acm.org/doi/10.1145/3735593
- APJCRI 2025: Loading microinteraction perception — https://doi.org/10.47116/apjcri.2025.10.28
- Uppsala: Perceived performance loading strategies — https://www.uppsatser.se/uppsats/2a189f903e/
- Material Design 3 Motion — https://m3.material.io/styles/motion/overview
- Apple HIG Motion — https://developer.apple.com/design/human-interface-guidelines/motion
- WCAG 2.2 SC 2.3.3 — https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html
- web.dev: Asymmetric animation timing — https://web.dev/articles/asymmetric-animation-timing
- FLIP technique — https://aerotwist.com/blog/flip-your-animations
- JCR 2024: Animation speed and perceived waiting time — https://doi.org/10.1093/jcr/ucaf037
- BTH study: Lazy vs eager loading — http://urn.kb.se/resolve?urn=urn%3Anbn%3Ase%3Abth-27984
- kylezantos/design-motion-principles (cookbook reference, not canonical) — https://github.com/kylezantos/design-motion-principles
