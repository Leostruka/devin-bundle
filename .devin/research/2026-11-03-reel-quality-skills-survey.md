# Reel survey: DePGBFXtswr - AI coding quality skills (2026-11-03)

Reel: `https://www.instagram.com/reel/DePGBFXtswr/` by `youraveragetechbro`
Series: "10x AI-native developer", video 5 of 7.
Method: yt-dlp metadata + local whisper transcription (`extensions/asr`).
Claim: ships ~30 PRs/day via cloud agents; keeps quality with a stack of
simplification/review skills run per PR, sometimes multi-pass.

## 1. Items identified

| Reel mention | Resolved item | Source | License |
|---|---|---|---|
| ponytail (ponytail.dev) | `DietrichGebert/ponytail` | already adopted | MIT |
| "peacestack" (misheard) | `cursor/plugins` -> `pstack` plugin, 58 skills, by poteto (Lauren Tan, Cursor/React core) | github.com/cursor/plugins | MIT |
| no comment skill | `pstack/skills/no-comments` (+ `comment-sicko` agent) | same | MIT |
| typescript best practices | `pstack/skills/typescript-best-practices` | same | MIT |
| "onslaught" (misheard) | `pstack/skills/unslop` - cut AI tells from writing | same | MIT |
| thermonuclear code quality review | `cursor/plugins` -> `thermos` plugin: `thermo-nuclear-code-quality-review`, `thermo-nuclear-review`, `thermos` orchestrator + 2 subagent agents | same | MIT |
| react best practices (caption) | `vercel-labs/agent-skills` -> `skills/react-best-practices` (name `vercel-react-best-practices`, 70 rules, 8 categories) | github.com/vercel-labs/agent-skills | MIT (frontmatter) |
| "one simplified command" | composite pattern: chain all simplification passes per PR, multi-pass for non-determinism | n/a | n/a |

## 2. pstack inventory (58 skills, MIT)

Named in reel: `no-comments`, `typescript-best-practices`, `unslop`.
Orchestrator: `poteto-mode` (agent style; spawns Cursor subagents, model
routing, custom modes - heavy Cursor coupling).
Verification family: `create-verification-skill`,
`maintain-verification-skill`, `create-formal-verification-skill`,
`maintain-formal-verification-skill` (videos 1-4 theme: per-project
verification skills that let cloud agents merge unsupervised).
Principles library: 20+ `principle-*` leaf skills loaded on demand
(attack-the-premise, boundary-discipline, build-the-lever,
encode-lessons-in-structure, exhaust-the-design-space, experience-first,
explain-the-number, fix-root-causes, foundational-thinking,
guard-the-context-window, laziness-protocol, make-operations-idempotent,
migrate-callers-then-delete-legacy-apis, minimize-reader-load,
model-the-domain, never-block-on-the-human, outcome-oriented-execution,
prove-it-works, redesign-from-first-principles,
separate-before-serializing-shared-state, sequence-verifiable-units,
subtract-before-you-add, test-behavior-not-implementation,
type-system-discipline).
Other workflows: architect, arena, automate-me, benchmark-checklist,
blast-radius, bro, correct, figure-it-out, how, in-your-own-words,
interrogate, ketchup(+video), make-bot-ui, poteto-help, recall, reflect,
setup-pstack, sharpen, show-me-your-work, statechart, swarm, tdd, teach,
technical-writing, why.

## 3. Evaluation vs bundle (158 skills)

| Item | Bundle today | Gap | Verdict |
|---|---|---|---|
| ponytail | `skills/lean-code` (adopted, PR #293) | none | DONE - no action |
| thermo-nuclear-code-quality-review | `code-review` covers review workflow; nothing enforces the 1k-line/spaghetti/code-judo rubric | harsh maintainability rubric missing | ADOPT (vendor+adapt) |
| thermo-nuclear-review (bugs/security branch audit) | `security-audit` + `security-audit-cf` exist but are audit-machine skills, not a diff-scoped branch audit | diff-scoped bug/breakage audit missing | ADOPT (same lane) |
| thermos parallel orchestrator | nothing runs two review passes in parallel and synthesizes | novel pattern for us | ADOPT - port to `run_subagent` background lanes |
| unslop (AI tells in prose) | `check-ai-signature.py` hook only blocks signature lines | stylistic AI-tell cleanup missing | ADOPT (vendor verbatim) |
| no-comments | nothing hunts comment smells / constraint comments | missing; needs `comment-sicko` -> our reviewer mapping | ADAPT (port) |
| typescript-best-practices | no TS-specific skill | missing | ADOPT (vendor; resolve principle-* refs) |
| vercel-react-best-practices | `a11y-audit` exists; no React perf rulebook | missing | ADOPT (vendor) |
| composite simplify pass | none | the reel's core pattern | BUILD `skills/de-slop` sequencing lean-code -> unslop -> thermo -> no-comments, multi-pass guidance |
| principle-* library (~20) | ~50% overlaps AGENTS rules (fix-root-causes=R11, guard-context=R18, prove-it-works=R12/15, subtract-before-add=R18) | non-overlapping set valuable but 20 dirs = bloat | BACKLOG: eval table, possible single compressed skill |
| poteto-mode | agent-style orchestrator, Cursor Task/custom-mode coupled | ports poorly | SKIP vendor; pattern absorbed by de-slop + our orchestrator |
| verification-skill generators | `gates`, `afk-loop`, held-out harness cover runtime | per-project generated verification skills novel | BACKLOG |
| remaining pstack (architect, arena, swarm, statechart, reflect, sharpen, how/why/teach, ketchup, recall, bro, correct, figure-it-out, interrogate, in-your-own-words, show-me-your-work, automate-me, benchmark-checklist, blast-radius, make-bot-ui, poteto-help, setup-pstack, tdd, technical-writing) | partial coverage via architect/reviewer/debugger/copywriter profiles + skills | case-by-case | BACKLOG eval table (C4) |
| other vercel skills (composition-patterns, react-native, view-transitions, vercel-optimize, web-design, writing-guidelines) | n/a | out of reel scope | BACKLOG note only |

## 4. Adoption scope

Adopt now (this plan): thermo-review (3-file vendor+adapt), unslop,
typescript-best-practices, vercel-react-best-practices, no-comments (port),
de-slop (new composite). New skill dirs: 6 -> skill_count 158 -> 164.

Backlog (doc only): principle-* compression, verification-skill generator,
remaining pstack eval, vercel extras. MERIDIAN: nothing in this reel is
investment-scope.

## 5. Sources

- Reel + transcript: local ASR output, 2026-11-03.
- github.com/cursor/plugins (pstack LICENSE MIT (c) Lauren Tan;
  thermos + cursor-team-kit LICENSE MIT (c) Cursor).
- github.com/vercel-labs/agent-skills (skill frontmatter `license: MIT`).
- Prior adoption: PR #293 (lean-code), `.devin/plans/2026-11-03-reels-adoption-plan.md`.
