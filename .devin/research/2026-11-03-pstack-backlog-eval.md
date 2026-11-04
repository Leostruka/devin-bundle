# pstack backlog eval - remaining skills + vercel-labs extras (2026-11-03)

Backlog pass over pstack after adopting no-comments, unslop,
typescript-best-practices, vercel-react-best-practices (vendored in the
Q2/Q3 lanes), the thermos review set, and the de-slop composite;
poteto-mode was evaluated and skipped (Cursor coupling). Ratings vs the
bundle's 160 skills: ADOPT = vendor/port in, ADAPT = port with rewiring,
SKIP = do not take, COVERED-BY-x = existing skill/agent already does it.

## pstack workflow skills

| skill | upstream description (abridged) | rating | reason |
|---|---|---|---|
| architect | Sketch types, signatures, module shape before code; stays in the loop while implementation fills in | COVERED-BY-architecture | `architecture` + `codebase-design` + the `architect` subagent already own pre-code shape work |
| arena | Spawn N parallel candidates at one brief, pick a base, graft the strongest parts of the losers into it | ADAPT | `dispatching-parallel-agents` fans out but the tournament + graft-into-base merge is novel; port via `run_subagent` + worktrees |
| automate-me | Draft a personal -mode skill from your recent transcripts | COVERED-BY-self-extend | `self-extend` + `retro` already turn session patterns into skills/rules/hooks |
| benchmark-checklist | Vet a measured speedup/regression (limiter, tuning, errors, repeat runs, e2e relevance) before reporting or acting | ADOPT | Small vendor; `performance` measures but nothing audits whether a number is trustworthy - feeds `gates` evidence |
| blast-radius | For a small-looking change: what else it could break, with the one safety fact proven by running code, not asserted | ADAPT | Diff-scoped dependent-impact check is a gap; `scan`/`dead-wire` hunt wide, `review-cadence` only sizes risk |
| bro | Restate the last reply in plain words, no jargon | COVERED-BY-wait-what | `wait-what` already re-pitches a message that did not land |
| correct | Find mistakes agents keep repeating in the repo; kill each class at the highest level (architecture > types > lint > test > docs) | ADOPT | Novel: hardens the repo itself against agent error classes; `retro`/`self-improvement` fix our env, not the project |
| figure-it-out | Design an auditable playbook when none fits: falsifiable done, rigor gates, hypothesis loop, decision log | COVERED-BY-wayfinder | `wayfinder` + `planning`/`execution` + `afk-loop` + `gates` ledger already decompose and audit long runs |
| how | Walkthrough of how a subsystem works | COVERED-BY-research | `research`/`deep-mode` do multi-pass cited codebase walkthroughs; `researcher` agent too |
| why | Why something was built this way; discovers MCPs at run time and queries each evidence category in parallel | COVERED-BY-research | Same investigation lane; the multi-MCP fan-out is a recipe `research` can absorb later |
| in-your-own-words | Play back the goal and the problem before the agent starts | COVERED-BY-intention-capture | Intent/landing-zone validation exists; `grilling` stress-tests it |
| interrogate | Different models review a diff and try to break it; a finding survives only when a run proves it | COVERED-BY-thermos | Adopted thermos lanes do adversarial break-it review; multi-model arms blocked by free-model policy anyway |
| ketchup | Catch the user up on what changed in this chat since their last message + calls waiting on them | SKIP | Session-UX nicety tuned for async cloud-agent workflows; `handoff` covers durable state |
| ketchup-video | /ketchup as a short subtitled video of slides | SKIP | Media pipeline for a niche catch-up format; `shorts-factory` exists if ever wanted |
| make-bot-ui | Build a UI that wakes a Grok Bot via a webhook routine, hosted over Tailscale | SKIP | Grok `update_state` routine + Tailscale coupling; `webhooks` covers receiver discipline |
| poteto-help | pstack navigator: finds what you are trying to do, hands you a prompt to type | SKIP | pstack-internal router; `ask-bundle`/`skill-discovery` are ours |
| recall | Rebuild recent context on a topic from chat history + shared record into a tight current-state brief | COVERED-BY-project-memory | `project-memory` + `memory-retrieval` hook + `handoff` cover resume-context |
| reflect | Three parallel subagents mine the transcript for learnings and route each to a concrete skill edit | COVERED-BY-self-improvement | The /refine loop + `continuous-improvement` + `retro` already mine sessions into env edits |
| setup-pstack | Detect available models and write the pstack model-per-role rule file | SKIP | pstack/Cursor-Claude config; `data/bundle-models.json` + `devin-config` own model routing |
| sharpen | Rewrite a prompt deeper not bigger (expert bar, raw material, methods, outside check); hands it back | COVERED-BY-prompt-compiler | `prompt-compiler` is the same pre-flight optimizer; `grilling` adds the adversarial pass |
| show-me-your-work | Keep a reviewable TSV decision trail (ts, phase, decision, why, evidence, result) for long or unattended work | COVERED-BY-gates | `.devin/ledgers/` outcome/check/expect/evidence format is the same artifact |
| statechart | Model a state system in TLA+, run TLC, draw a Mermaid statechart with the shortest path to each rule-breaking state | SKIP | TLA+/TLC + bundled TS script is a heavy toolchain for a niche; revisit inside the formal-verification lane |
| swarm | Fan out N workers over slices or races, drain them, return one report; worker model from pstack settings | COVERED-BY-dispatching-parallel-agents | Same fan-out + aggregate; `scan` adds Plan-Shard-Map-Reduce; the pstack model line is Cursor coupling |
| tdd | Fix a bug test-first when a cheap local test exists | COVERED-BY-tdd | Bundle `tdd` + `testing` + `edge-coverage` already enforce red-green |
| teach | Explain a body of work plainly by composing how + why into one explanation | COVERED-BY-teach | Name collision; ours teaches the user, theirs narrates code - `research` output covers the narration |
| technical-writing | Layered docs standard: Diataxis structure, Google dev style sentences, STE instruction rules, Global English | ADOPT | Real gap: `writing-for-agents`/`writing-skills` target agent-facing text; nothing lints user-facing docs |

## verification-skill generators (4)

| skill | upstream description (abridged) | rating | reason |
|---|---|---|---|
| create-verification-skill | Generate a project-local skill that gives agents a scripted way to drive the real app and prove behavior | ADAPT | The reel's core pattern; port to emit under project `.devin/skills/` wired to `e2e-testing` + `gates` |
| maintain-verification-skill | Bring a generated verification skill and its feature map back in line with the app after changes | ADAPT | Pairs with the generator; `drift-report` is adjacent machinery to reuse |
| create-formal-verification-skill | Generate a project-local skill that formally verifies the code where bugs cost most and tests reach least | SKIP | Needs a per-project formal toolchain (TLA+/model checker); defer until a correctness-critical component justifies it |
| maintain-formal-verification-skill | Keep a formal model/harness in line with changed code; classify failures as drift vs bug | SKIP | Same lane; revisit alongside `statechart` |

## principle-* library (24 leaf skills) - one row

| skill | upstream description (abridged) | rating | reason |
|---|---|---|---|
| principle-* (24 leaf skills) | One named principle per skill, loaded on demand so a name can steer an agent mid-task | ADAPT | About half duplicate AGENTS rules/skills; compress the rest into one reference skill |

The 24 principle skills are single-idea leaves that other pstack skills cite
by name. Roughly half are already encoded in the bundle: fix-root-causes
(Rule 11), guard-the-context-window and subtract-before-you-add (Rule 18),
prove-it-works (Rules 12/15 + `gates`), outcome-oriented-execution and
never-block-on-the-human (Rules 7/13), laziness-protocol (`unlazy`/`gates`),
minimize-reader-load (Rule 8 + `lean-code`), sequence-verifiable-units
(`executing-plans`), encode-lessons-in-structure (`retro`/`self-improvement`),
separate-before-serializing-shared-state (`using-git-worktrees` /
`dispatching-parallel-agents`), migrate-callers-then-delete-legacy-apis
(`legacy-refactor`), model-the-domain (`domain-modeling`),
test-behavior-not-implementation (`testing`/`edge-cases`), attack-the-premise
and exhaust-the-design-space (`grilling`). The remainder (explain-the-number,
build-the-lever, boundary-discipline, experience-first,
foundational-thinking, redesign-from-first-principles,
make-operations-idempotent, type-system-discipline, and a few more) deserve
one compressed `principles` SKILL.md: a table of all 24 names with a one-line
rule each, short sections only for the non-covered set, and a cross-ref
column pointing each name at its owning AGENTS rule or bundle skill. One
file (~10-15 KB) instead of 24 dirs; keeps the steer-by-name UX without the
bloat.

## vercel-labs extras

| skill | upstream description (abridged) | rating | reason |
|---|---|---|---|
| composition-patterns | React composition that scales: compound components, state lifting, internal composition vs boolean-prop sprawl | ADOPT | Same MIT rulebook format as adopted `vercel-react-best-practices`; covers API shape, a lane the perf rules do not |
| react-native-skills | React Native + Expo best practices (list perf, animations, navigation, native modules) | SKIP | No RN/Expo surface in scope today; zero-port vendor to pull when a mobile project lands |
| react-view-transitions | React View Transition API: ViewTransition component, addTransitionType, Next.js integration | SKIP | Single-API scope; `animation-direction` + `vercel-react-best-practices` cover motion/perf; pull with a Next.js project |
| vercel-optimize | Audit a deployed Vercel project for cost, perf, caching, function usage, billing | SKIP | Vercel-platform coupled (collects Vercel metrics first); `cost-optimization` + `performance` cover the general case |
| web-design-guidelines | Review UI code for Web Interface Guidelines compliance | COVERED-BY-a11y-audit | `a11y-audit` + `impeccable` + `frontend-design` cover UI review; Vercel's handbook adds little |
| writing-guidelines | Review docs/prose for Writing Guidelines compliance | SKIP | Subsumed by the recommended `technical-writing` adoption; `humanizer`/`unslop` cover AI-tell cleanup |

## Recommended next batch

1. `correct` (ADOPT, port) - highest-leverage gap: turns repeated agent
   mistakes into repo-level enforcement (architecture > types > lint >
   test), which none of our review or self-improvement skills do.
2. `technical-writing` (ADOPT, vendor) - fills the user-facing docs
   standard gap; single file, no deps.
3. `benchmark-checklist` (ADOPT, vendor) - tiny; adds number-vetting
   discipline to `performance` and feeds `gates` evidence rules.
4. `blast-radius` (ADAPT, port) - diff-scoped dependent-impact check
   proven by running code; slots between `code-review` and `thermos`.
5. `principles` compression (ADAPT, one new skill) - one SKILL.md folding
   the ~10 uncovered principle names with cross-refs to AGENTS rules;
   captures the steer-by-name UX at a fraction of the cost.

Bigger follow-on, not in this batch: `create-verification-skill` +
`maintain-verification-skill` (ADAPT) - the reel's per-project generated
verification skills that let unattended agents self-verify; worth a
dedicated contract once the cheap wins land.

## Sources

- github.com/cursor/plugins - `pstack` skills (58) + `thermos` plugin;
  LICENSE MIT (c) Lauren Tan (pstack), MIT (c) Cursor (thermos). SKILL.md
  frontmatter via the repo, cursor.com/marketplace/cursor/pstack, and the
  agentlefs.com mirror.
- github.com/vercel-labs/agent-skills - skill frontmatter `license: MIT`.
- Bundle coverage read from `skills/*/SKILL.md` descriptions,
  `.devin/docs/TOOLS-MAP.md`, prior handoffs Q1-Q3, and research
  `2026-11-03-reel-quality-skills-survey.md`.
