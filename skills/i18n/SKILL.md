---
name: i18n
description: Use when the user wants to add or review internationalization and localization. Covers locale files, translation keys, pluralization, RTL, and date/number formatting.
triggers: [user, model]
---

# i18n

Internationalization and localization for multi-language apps.

## When to use

- Adding a new language.
- Hardcoded strings need extraction.
- Date, number, currency, or pluralization must vary by locale.
- RTL layout support is needed.

## Core protocol

1. **Find hardcoded strings.** Grep for user-facing text in code.
2. **Extract keys.** Move strings to locale files with meaningful keys.
3. **Choose library.** i18next, react-intl, FormatJS, gettext, etc.
4. **Handle plural/gender.** Use ICU messages or library helpers.
5. **Format locale-aware.** Dates, numbers, currencies, relative time.
6. **Verify.** Switch locales and confirm layout for LTR/RTL.

## See also

- `a11y-audit` — accessibility, including RTL layout.
- `i18n` — multi-language, pluralization, and locale formatting.

## Output rule

- After changes, show a sample in 2+ locales and run the app tests.
