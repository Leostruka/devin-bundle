# design-intelligence: visual-style taxonomy reference

status: ready-for-agent
priority: P3
source: reels batch-5 survey, talhaxcodes DdMUB4kskYv

## Evidence

Transcript (`.devin/scratch/reels-5/transcripts/DdMUB4kskYv.txt`): reel lists ~22 visual styles for UI/brand inspiration: claymorphism, cybercore, neo-brutalism, scrapbook, surrealism, Y2K, pixel art, synthwave, glassmorphism, neumorphism, bento-grid, editorial, Swiss, minimalism, maximalism, luxury typography, conceptual sketch, ethereal, bohemian, Victorian, cyberpunk, wabi-sabi ("wavy-sablu" in ASR).

Research: near-1:1 match with https://filtercoffee.dev/blog/a-field-guide-to-web-design-styles/ (Oct 2026, same 22 styles in 5 groups). Alternate live-rendered references: quantumaccordbg.com/designs (35 styles), ui-design-styles.vercel.app (42), namethatui.org/styles (13, with agent prompts). Reel's pinned-comment source unconfirmed.

Bundle surface: `extensions/design-intelligence` (BM25 corpus: 12 domain CSVs + stack CSVs + frontend-rules) and `skills/frontend-design`. A style taxonomy is reference material for design retrieval, not a new engine.

## Task

Pick ONE canonical style-taxonomy source (recommend filtercoffee field guide: closest match, grouped) and wire it as a reference:

- Option A (preferred, smallest): add a "style taxonomy" pointer block in `skills/frontend-design/SKILL.md` or the design-intelligence README/USAGE listing the canonical URL + the 5 groups, so `search.py` users know where style vocabulary lives.
- Option B: vendor a compact `styles` CSV/domain into the design-intelligence corpus if schema fits (check `validate_csv.py` contract first; only if it maps cleanly to existing columns).

Record the decision + rejected alternative in the issue Answer. Do NOT scrape/mirror the full external list into the repo (licensing + drift).

## Acceptance

- [ ] One canonical source cited in the chosen surface
- [ ] No bulk vendored content
- [ ] `python audit.py` green
