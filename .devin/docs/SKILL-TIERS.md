# Skill Tiers - fast discovery by domain

Skills by domain of use + cost (tok = SKILL.md bytes÷4, measured 2026-10-31).
They only cost when invoked. Use this (~1700 tok) instead of `skill list` (~1600 tok).
Consolidated skills are routers: the SKILL.md is expensive up front; detail lives in
`modes/`/`reference/` and is read only on demand (`+defer`).

## Target models (SWE-2, routing by effort level)

| model_uid | Effort | Context | Use | Notes |
|---|---|---|---|---|
| `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | 262K | Simple tasks, spot fixes, isolated scripts | **free** |
| `{{BUNDLE_DEFAULT_MODEL}}` (`swe-2-high`) | High | 262K | Primary (parent); multi-file | **free**, general default |
| `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | 262K | Max subagent (`model:` pin); open-ended/long-horizon | **free** |

Custom subagents use `model: {{BUNDLE_MAX_MODEL}}` (Max) or `{{BUNDLE_MEDIUM_MODEL}}` (Medium), per `data/bundle-models.json` and the `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL` variables. **DO NOT use unverified paid aliases** - they may resolve to a paid model.
Without a pin, custom agents use the CLI default router (possibly paid). `subagent_general` inherits the parent (`{{BUNDLE_DEFAULT_MODEL}}`) when it is free. **Avoid `subagent_explore`** - it may resolve to a paid model; use the custom `researcher` (free, see `data/bundle-models.json`).

## Core (logical reasoning, any work)

| Skill | Does | Tok | When |
|---|---|---|---|
| `skill-discovery` | Finds the right skill + installs/evaluates external ones + usage guide | 861 | Start of task, before non-trivial action |
| `planning` | Spec → plan + tickets + questionnaire + wayfinder (4 modes, +9.8k defer) | 765 | Before implementing complex work |
| `execution` | Executes with checkpoints, implements from spec, AFK loop, cadence | 1153 | Structured implementation |
| `context-hygiene` | Large doc in 200k, clear vs compact, cost, effort | 1191 | Context tightening, doc/log > 50k tok |
| `mcp-governance` | Tool-def costs + which MCPs to keep active (+5.8k defer) | 908 | Before adding an MCP |
| `dispatching-parallel-agents` | Subagents have their own 262k + plan execution | 10590 | 2+ independent tasks |
| `project-orchestrator` | Drives a project from empty folder/fuzzy idea to delivered product via delegation contracts + specialist subagents | 2736 | Full project build, coordinated multi-agent delivery |
| `gates` | Proof of completion, unlazy ledger, autonomous gates | 1127 | Before "done" |
| `testing` | Test-first, test gaps, mutation (+7.5k defer) | 478 | Feature/bugfix |

Rarely >3 per task (~5000 tok).

## Documentation

| Skill | Does | Tok | When |
|---|---|---|---|
| `writing-skills` | Create skills with TDD + docs agents consume (+27k defer) | 706 | Writing/creating a skill, rule, doc |
| `knowledge-modeling` | Glossary, ADRs, bounded contexts, extraction and ontology (+19.8k defer) | 699 | Modeling a domain, structuring knowledge |
| `planning` | Spec + Tickets + Questionnaire (modes) | 765 | Conversation → spec/tickets/quest |
| `architecture-diagrams` | Physical diagram artifacts (.svg/.png): C4, class diagrams, network topology via PlantUML (not Mermaid-in-Markdown) | 883 | Diagram deliverable file needed |
| `humanizer` | Removes AI tells from prose; rewrites so it reads like the writer without changing meaning | 1508 | Editing/reviewing prose for AI voice |
| `prompt-compiler` | `/prompt` pre-flight optimizer: compiles/refines a prompt into an approved super-prompt | 821 | Compile or optimize a prompt before execution |

## Programming

| Skill | Does | Tok | When |
|---|---|---|---|
| `execution` | Implements from spec/tickets | 1153 | Spec exists |
| `code-review` | 2-axis review, PR via `gh`, receive feedback (3 modes, +7.8k defer) | 599 | Before merge, reviewing/receiving PR |
| `architecture` | Deep modules, seams, deepening, strangler-fig (+3k defer) | 935 | Designing/refactoring architecture, legacy |
| `prototype` | Throwaway code for a design question | 780 | Design doubt |

## Debug

| Skill | Does | Tok | When |
|---|---|---|---|
| `debugging` | Unified 6-phase pipeline + diagnosis across builds/jobs/envs (+8.8k defer) | 615 | "Debug this", non-obvious bug, CI failing |

## Git/GitHub

| Skill | Does | Tok | When |
|---|---|---|---|
| `git-workflows` | Branches, commits, isolated worktree, conflicts | 813 | Git workflow, isolate feature, merge conflict |
| `gh` | GitHub CLI with JSON | 2294 | Issues, PRs, Actions |
| `finishing-a-development-branch` | Tests + integration options | 1870 | Branch complete |

## Issue tracker

| Skill | Does | Tok | When |
|---|---|---|---|
| `jira` | Issue tracker via configured MCP (example in `mcp_config.json.example` and `data/bundle-integrations.json`) | 1713 | Interacting with issue tracker (requires MCP) |
| `intake` | Triage + sizing + intent into tickets (+4.2k defer) | 997 | Triaging issues/PRs, estimating PR, validating intent |

## Obsidian and file organization

| Skill | Does | Tok | When |
|---|---|---|---|
| `obsidian-workflow` | Build + Reorganize + Audit + Cross-session (4 modes, +73k defer) | 17485 | Any Obsidian operation |

High cost. Invoke only for a real Obsidian operation.

## Planning/decision

| Skill | Does | Tok | When |
|---|---|---|---|
| `planning` | Decision-ticket map (wayfinder mode) | 765 | Work > 1 session |
| `grilling` | Stress-test an idea (3 modes: default, stateless, with-docs, +21.8k defer) | 3508 | Design/plan to be challenged |
| `playbook` | Reusable playbook with Procedure/Specs/Advice (replicates cloud) | 1516 | Repeated task, "make this reusable" |
| `execution` | Decides where to place review/planning checkpoints (cadence) | 1153 | Can a small task skip grilling? |

## Research

| Skill | Does | Tok | When |
|---|---|---|---|
| `research` | Subagent investigates with citations + multi-pass deep search | 651 | Investigation with sources, "deep search" |
| `scan` | Codebase-wide investigation by objective (equiv. Devin Cloud `/scan`): Plan→Shard→Map→Reduce with subagents → prioritized report in `.devin/scans/` | 936 | "find dead code", test gaps, migration/style audit |
| `fact-check` | Verifies every checkable claim in an article/draft against online primary sources | 2435 | Fact-check, nitpick, pre-publish review |
| `scrape-tools` | Structured extraction from web/HTML: CSS/XPath, TLS-impersonated fetch, adaptive selectors → `extensions/scrape-tools` | 387 | Scraping pages or HTML files |
| `context7` | Up-to-date library docs | 339 | Question about a library |
| `youtube-fetcher` | YouTube URL + caption JSON → raw transcript + metadata in `.devin/notes/youtube/` | 1334 | Ingesting a user-provided video transcript |
| `ai-coding-dictionary` | Canonical definitions for AI-coding jargon | 346 | Aligning terms like harness engineering |
| `rag` | Build retrieval over a project corpus: tier ladder (agentic lexical → BM25 → local hybrid → hosted), golden-set eval, chunking, failure checklist | 1423 | "Agent can't find things in the docs", chunking/embedding/vector-store questions |

## Data

| Skill | Does | Tok | When |
|---|---|---|---|
| `data-analyst` | SQL-first exploration via MCP, schema-aware, charts (replicates DANA cloud) | 1519 | Query DB, data analysis, charts |

## Meta (session management)

| Skill | Does | Tok | When |
|---|---|---|---|
| `ask-bundle` | Universal orchestrator - classifies objective, routes skills/flows (+8.3k defer) | 1642 | Session start, vague objective, orchestration |
| `memory-management` | Cross-session memory: when/how to use + hygiene (+7k defer) | 1092 | Note to persist, cross-session memory |
| `devin-config` | Audits `.devin/` (scan/explain/diff/doctor/plan) + adds skill/hook/MCP/rule (+15k defer) | 993 | `.devin/` audit, evolving Devin CLI |
| `handoff` | Compacts for another agent | 262 | Passing work along |
| `wait-what` | Re-explains a message | 121 | Re-explaining |
| `gates` | Gates for autonomous mode | 1127 | "Run unattended" |
| `scheduled-turns` | Recurring agent turns via OS scheduler, no daemon | 704 | Periodic checks, polling, "run every morning" |

## Setup (one-time)

| Skill | Does | Tok | When |
|---|---|---|---|
| `project-bootstrap` | `.devin/` + repo onboarding for skills eng + pre-commit (+8.6k defer) | 473 | Initial setup, first configuration |
| `devin-config` | Adds skill/hook/MCP/rule | 993 | Evolving Devin CLI |

## Research artifacts (not daily use - PrimeAgent/RLM)

| Skill | Does | Tok | When |
|---|---|---|---|
| `self-improvement` | PrimeAgent reference (4 modes) + 10-step improvement loop with held-out (+15k defer) | 668 | Researching PrimeAgent/RLM, bundle improvement |

## Design / Frontend

| Skill | Does | Tok | When |
|---|---|---|---|
| `impeccable` | Design vocabulary for frontend interfaces: avoids generic aesthetics, defines context before building, applies design commands (polish, audit, distill, etc.) | 1593 | Designing, refactoring, auditing or polishing UI/UX |
| `brag` | Generates a 15-25s launch video of the project via Hyperframes: inspect → storyboard → compose → render (+refs defer; bundled mp3/ogg assets; needs Node+ffmpeg) | ~2200 | "/brag", launch video, sharing what you built |
| `ai3d-gen` | Generative 3D assets (text-to-3D, image-to-3D) via self-hosted open models → `extensions/comfyui-operator` (local ComfyUI); direct-model fallbacks | 1032 | Text/image → 3D mesh generation |
| `operate-blender` | Create/render/animate/export 3D content headlessly → `extensions/blender-operator` (TCP exec loop, full bpy) | 1481 | Blender scenes, models, renders, procedural geometry |
| `operate-godot` | Build/import/export Godot 4 projects headlessly (`godot --headless --script`) | 584 | Realtime 3D delivery, game scenes |
| `mesh-utils` | Inspect/convert/clean/validate meshes (OBJ, STL, GLB, FBX, USD) → `extensions/mesh-utils/meshops.py` | 529 | Mesh file operations |
| `implement-laya` | Fast typed decisions (classification, triage, scoring, routing) over text/JSON via the `laya` engine | 1819 | Non-autoregressive typed inference, guardrails |
| `creative-engineering` | Apply visual styles/effects to code: CSS/GLSL shaders, OpenCV/FFmpeg (CRT, dither, datamosh, night-mode) | 809 | "Style/theme/effect" requests on code or media |
| `media-tools` | Generate visual artifacts (ASCII art, halftone, dither, matrix-rain, VHS, pixel-sort, voronoi) from images/GIFs/video/GLB/webcam | 754 | Image/video FX artifact generation |

## Infra / Quality / Release

| Skill | Does | Tok | When |
|---|---|---|---|
| `deploy` | Deploy, release, rollback and smoke tests | 344 | Publishing or promoting a version |
| `security` | SAST, dependencies, secrets + `.env`/endpoints/destruction checklist (+1.2k defer) | 693 | Security audit, before commit/deploy |
| `performance` | Profile, benchmark and optimization | 290 | Slowness or bottleneck |
| `a11y-audit` | WCAG, keyboard, screen-reader, contrast | 303 | Checking accessibility |
| `api-spec` | REST/OpenAPI/contract + specs as context for AI | 509 | API design or review |
| `database` | Schema, migrations, queries, indexes | 294 | DB modeling or optimization |
| `e2e-testing` | Playwright/Selenium/Cypress journeys | 294 | Critical journey tests |
| `docker` | Build, run, compose, image scanning | 398 | Containers and stacks |
| `i18n` | Translations, plural, LTR/RTL, formats | 277 | Multi-language |

## Local extensions (tools, not skills)

Executable utilities installed in `~/.config/devin/extensions/` (Windows: `%APPDATA%\devin\extensions\`). Full documentation lives in each extension's `USAGE.md`. An extension may have a skill wrapper in `skills/<name>/` only for self-discovery (the SKILL.md points back to the `USAGE.md`).

| Extension | Does | When | Full docs |
|---|---|---|---|
| `computer-use` | Screen screenshot, mouse click/movement at (X,Y), text typing and shortcuts - replicates Devin Cloud Computer Use on the CLI. Skill wrapper: `skills/computer-use/` | Automating desktop GUI, visually validating an app, interacting with an app without API | `extensions/computer-use/USAGE.md` |
| `ai-tools` | Offline-first local ML tools (abliteration PoC etc.) - JSON stdout, `--self-test`, no download. Skill wrapper: `skills/ai-tools/` | Interpretability/local-model experiments | `extensions/ai-tools/USAGE.md` |
| `system-control` | Authorized OS control: process/service inventory, bounded one-shot exec, persistent sessions, event streams, hash-verified file copy. Deny-wins + one-shot confirmations; no privileged daemon by default. Skill wrapper: `skills/system-control/` | System APIs instead of GUI computer-use | `extensions/system-control/USAGE.md` |

## Others

| Skill | Does | Tok | When |
|---|---|---|---|
| `teach` | Guided multi-session learning | 2471 | Learning a concept |
| `wizard` | Scripts for manual procedures | 1033 | One-off provisioning |
| `observability-quality` | Observability infra with evidence | 2370 | Adding logging/metrics/tracing |
| `cu-realtime` | Measured low-latency patterns for computer-use (wait, batch, reflex) | 850 | Fast reaction in CU/terminal |
| `social-midia` | Draft/post/schedule/analyze content on social networks via official APIs; 8 nested child skills (facebook, instagram, linkedin, reddit, threads, tiktok, x-twitter, youtube) | 692 | Social network posting/analytics |

## Logical line for parent + subagent

```
Task → AGENTS.md (~4900 tok, fixed, cache-stable) → read SKILL-TIERS.md (~1700 tok)
  → identify domain → invoke 1-3 skills (~500-3500 tok router; modes/ on demand)
  → work (50k-150k tok in parent `{{BUNDLE_DEFAULT_MODEL}}`; per subagent `{{BUNDLE_MAX_MODEL}}`)
  >60% used? → context-hygiene | dispatching-parallel-agents (parallel) | clear (task changed)
  → gates before done
```

The parent (`{{BUNDLE_DEFAULT_MODEL}}`) has thinking mode (reasons before output) and tool-use during inference
(decides when to use tools natively). The subagent (`{{BUNDLE_MAX_MODEL}}`) has trained self-compaction
(resumes + continues from the summary) and high TPS (cheap fan-out in wall-clock). See `data/bundle-models.json` for windows and costs.

## Anti-patterns

| Avoid | Alternative |
|---|---|
| `skill list` without need | Read SKILL-TIERS.md |
| `self-improvement` without research motive | Do not invoke - it is a reference |
| MCPs without use | Activate only when needed |
| Compact when you need the detail | `context-hygiene` |
| `obsidian-workflow` for a spot edit (~17485 tok) | Only for real Obsidian operations |
| General subagent for research | Use researcher (`{{BUNDLE_MAX_MODEL}}`, free, see `data/bundle-models.json`) |
| `model: paid` pin on read-only agents | Pin `model: {{BUNDLE_MAX_MODEL}}` → free Max subagent (see `data/bundle-models.json`) |
