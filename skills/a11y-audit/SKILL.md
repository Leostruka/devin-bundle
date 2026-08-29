---
name: a11y-audit
description: Use when the user wants to check a frontend for accessibility. Covers keyboard navigation, screen-reader labels, color contrast, focus management, and WCAG alignment.
triggers: [user, model]
---

# A11y Audit

Accessibility review for web and mobile interfaces.

## When to use

- User asks to check accessibility or WCAG compliance.
- New UI component or page is ready.
- Bug report about keyboard or screen-reader usage.
- Before a public-facing release.

## Core protocol

1. **Run automated tools.** Use axe, Lighthouse, WAVE, or similar if available.
2. **Manual keyboard check.** Tab order, focus visibility, skip links, traps.
3. **Screen-reader labels.** Verify alt text, aria labels, headings, landmarks.
4. **Color and contrast.** Check ratios and do not rely on color alone.
5. **Resize and motion.** Test 200% zoom, reduced motion preference.
6. **Document issues.** List impact, WCAG criterion, and fix.

## See also

- `impeccable` — visual design and frontend aesthetics.
- `a11y-audit` — accessibility compliance and assistive-tech verification.

## Output rule

- Output findings with severity and WCAG criterion.
- Include a verification command for re-checking.
