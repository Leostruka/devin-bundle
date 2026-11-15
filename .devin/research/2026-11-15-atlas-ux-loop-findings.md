# Atlas UX loop - findings (32 cycles, 2026-11-15)

Branch: `feat/atlas-ux-loop`. 4 batteries of 8 cycles each, each cycle = one shipped change.
Verify: `python site/build.py` + serve `site/dist` + DOM/curl checks + screenshots.

## Baseline vs final

| metric | before | after |
|---|---|---|
| index.html payload | 2,083 KB inline | 134 KB (-94%) |
| initial blocking JS lib | mermaid 2MB CDN eager | lazy, only when a diagram exists |
| section DOM build | all grids eager on load | deferred to first tab visit |
| deep links | none | `#skill/x`, `#agent/x`, `#app/x`, `#adr/x`, `#doc/x` |
| install CTA | none | hero clone+install, copyable |
| mobile layout | grid overflow | responsive reader + wrap |
| themes | 1 (phosphor) | 3 (phosphor/amber/mono), persisted |

## Battery 1 - conversion/findability (c1-8)

- c1 install CTA on boot: the page had zero conversion path; hero now carries the clone+install command with a copy button.
- c2 hero search: intent (find a skill) was buried one tab deep; global corpus search on the landing view.
- c3 GitHub issues clickable: `html_url` plumbed from API to table anchor.
- c4 tab count badges: scale legibility at a glance.
- c5 deep links: every modal maps to a hash; closing restores the section hash.
- c6 fuzzy palette: substring -> subsequence scoring (fzf-style) with ranked results.
- c7 REPL real data: `stats`, `issues` wired to live D payload.
- c8 reader keyboard nav: `[` `]` `j` `k` arrows across ADR/doc entries.

## Battery 2 - edges + a11y (c9-16)

- c9 mobile layout fixes, c10 skip link + dialog semantics + focus restore,
  c11 quick-filter chips, c12 `<mark>` search highlighting, c13 boot replay,
  c14 section transitions, c15 modal copy-link state, c16 skill sort toggle.

## Battery 3 - performance (c17-24)

- c17-18 lazy HTML split: bodies of skills/agents/apps/adrs/docs/changelog
  written to `dist/data/*.html`, fetched on demand, Map-cached. 2.09MB -> 185KB.
- c19 mermaid lazy CDN: script injected only when `pre.mermaid` exists.
- c20 deferred section renders via `_renderers` map keyed by section.
- c21 grep debounce 90ms + single compiled regex.
- c22 preconnect jsdelivr, dns-prefetch github.com.
- c23 reduced-motion: transitions killed under media query; boot/matrix already gated.
- c24 changelog lazy -> index 134KB final.

## Battery 4 - delight/polish (c25-32)

- c25 theme cycle (phosphor/amber/mono) + localStorage.
- c26 `matrix` + `sudo` easter eggs in REPL, tab-completable, hidden from help.
- c27-29 focus-visible ring, theme-color meta, completion, statusline var fix.
- c30 design_lint pass: 8 findings -> 5 intentional CRT language kept, real fix =
  9 hardcoded colors moved to var()/color-mix so themes stay coherent.
- c31 this document.
- c32 PR.

## What the data says

- Skills were 69% of payload; splitting detail HTML gave the single biggest win.
- The terminal metaphor is the brand: every delight choice (matrix rain, sudo joke,
  phosphor themes, `~/` tabs) reinforces it rather than bolting on generic UI.
- Lint false-positives are features here: blinking cursor, scanlines, ASCII logo
  leading, app-shell max-width are the design language, not defects.

## Follow-ups (not shipped)

- Per-item `?raw` endpoints for curl users.
- Issue board filters (open/resolved, group).
- Offline ServiceWorker for the data/*.html cache.
