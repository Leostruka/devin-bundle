# frontend-design: editable dashboard-grid (spring reflow) pattern note

status: ready-for-agent
priority: P3
source: reels batch-5 survey, moxen.studio DfYMlgrBQiy

## Evidence

Reel is music-only (`.devin/scratch/reels-5/transcripts/DfYMlgrBQiy.txt` = "[Música]"); caption carries the content: "Parrilla": users assemble their own dashboard panel; drag widgets, neighbors move aside with spring physics, each widget resizes in grid steps. Spanish studio moxen.studio = moxen.cl (Chilean custom-software studio); fits their free `/recursos/` series of dependency-free vanilla-JS interaction demos (verified: `/recursos/cronograma/` uses the same "domino con resortes" spring-reflow idea; "Parrilla" page not yet indexed).

Bundle gap: `skills/frontend-design` motion section (R4-02) covers micro-interactions but not layout-reflow patterns for user-editable grids (drag/resize with animated neighbor displacement, distinct from list stagger).

## Task

Add 3-5 lines to the frontend-design motion/layout guidance noting the pattern: editable dashboard grids should animate neighbor displacement with spring physics and snap resizes to grid steps; cite moxen.cl/recursos/ as a working vanilla-JS reference series. Verify `https://moxen.cl/recursos/parrilla/` (or nearest) exists before citing; if 404, cite the series root + cronograma as evidence of the pattern family.

## Acceptance

- [ ] Pattern note added, source verified live (or fallback citation recorded)
- [ ] `python audit.py` green
