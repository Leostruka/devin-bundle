# Archetype map - Anthropic's 5 roles vs the bundle

Source: reel 14 (vicentecondee) describing the Anthropic observation: post-AI teams organize around modes of operation, not job titles. Five archetypes; healthy teams run all five; the valuable professional transits two or three.

| Archetype | Does what | Bundle machinery |
|---|---|---|
| **Prototyper** | Generates ideas at scale; most die, some set direction | `research`, `wayfinder`, `brainstorm`, `prototype`, `agent-reach` (trend scanning) |
| **Builder** | Turns a chosen idea into a real product fast | `implementer`, `tdd`, `execution`, `planning-pipeline` |
| **Simplifier** | Cleans and optimizes what was built so it scales without chaos | `lean-code`, `de-slop`, `unslop`, `no-comments`, `big-file-refactor`, `thermos` |
| **Grower** | Evolves the product toward PMF; business vision on top of shipping | `product-manager`, `copywriter`, `data-analyst`, `social-midia`, `shorts-factory` |
| **Maintainer** | Keeps the system safe, fast, reliable as it scales | `chief-of-staff`, `scrum-master`, `watchdog`, `correct`, push-gate + hook machinery |

## Coverage gaps the map exposes

- **Grower is the thinnest row** - PM/copywriter are spec-side; nothing tracks metrics/funnels. `data-analyst` is the closest runtime.
- **Prototyper** relies on external input (reels/research) - fine, that is what the survey pipeline is for.
- Transit = the meta-skills: `ask-bundle` routes across rows; `afk-loop` keeps a Build row running unattended.
- Multi-agent parallel runs of different archetypes = `run_subagent` profiles (implementer + reviewer + watchdog is literally Builder+Maintainer+Simplifier in parallel). The alvim job-apply reel is the clean public demo of this: a drafter agent writing and a reviewer agent critiquing maps to `copywriter` + `reviewer` (Grower + Maintainer).
