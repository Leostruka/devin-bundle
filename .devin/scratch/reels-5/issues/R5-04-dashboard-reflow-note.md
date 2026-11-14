# frontend-design: editable dashboard-grid (spring reflow) pattern note

status: resolved
priority: P3
source: reels batch-5 survey, moxen.studio DfYMlgrBQiy

## Evidence

Reel is music-only (`.devin/scratch/reels-5/transcripts/DfYMlgrBQiy.txt` = "[Música]"); caption carries the content: "Parrilla": users assemble their own dashboard panel; drag widgets, neighbors move aside with spring physics, each widget resizes in grid steps. Spanish studio moxen.studio = moxen.cl (Chilean custom-software studio); fits their free `/recursos/` series of dependency-free vanilla-JS interaction demos. VERIFIED 2026-11-07: `https://moxen.cl/recursos/parrilla/` is live ("Panel de widgets que se apartan y vuelven a encajar"; spring displacement, grid-step resize, save/restore layout as data, free download) and the site footer links `instagram.com/moxen.studio` directly.

Bundle gap: `skills/frontend-design` motion section (R4-02) covers micro-interactions but not layout-reflow patterns for user-editable grids (drag/resize with animated neighbor displacement, distinct from list stagger).

## Task

Add 3-5 lines to the frontend-design motion/layout guidance noting the pattern: editable dashboard grids should animate neighbor displacement with spring physics and snap resizes to grid steps; cite `https://moxen.cl/recursos/parrilla/` (verified live 2026-11-07) as the working vanilla-JS reference.

## Acceptance

- [x] Pattern note added, source verified live (or fallback citation recorded)
- [x] `python audit.py` green

## Answer

Added to `skills/frontend-design/SKILL.md` motion block: user-editable grids animate neighbor displacement with spring physics and snap resizes to grid steps; cites https://moxen.cl/recursos/parrilla/ (verified live 2026-11-07).
