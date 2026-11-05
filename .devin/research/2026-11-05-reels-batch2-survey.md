# Reels batch-2 survey - 16 Instagram reels vs the bundle (2026-11-05)

Pipeline: `extensions/asr/transcribe.py` (yt-dlp -> whisper.cpp base, local).
Transcripts: `.devin/scratch/reels-2/transcripts/*.json`.
Issues: `.devin/scratch/reels-2/issues/R2-NN-*.md`. Plan: `.devin/plans/2026-11-05-reels-batch2-plan.md`.

Ratings: ADOPT (build now), ADAPT (port/extend existing), BACKLOG (later), COVERED (already shipped), SKIP.

## Per-reel decode and verdict

| # | Author | Content (decoded) | Verdict | Issues |
|---|---|---|---|---|
| 01 | catlabs | No MCP/connector -> tell the agent to build a CLI tool to drive the app (example: full DAW control). Side note: "flagged for cyber risk". | ADAPT | R2-01 |
| 02 | alvim_ai | 3 repos: Cloudflare sec-audit skill (maps architecture/trust/attack surface), AI job-apply pipeline (agent writes code+cover letter, second agent researches company, critiques resume). | BACKLOG | R2-02 |
| 03 | guilhermemorais.ia | 10-repo roundup: task-master, serena, understanding agents, superpowers, trail-of-bits, STRIX pentest. | COVERED mostly; confirm matrix | R2-03 |
| 04 | breakingbreach | 30-item web performance checklist prompt (skeleton loading, WebP, debounce, pagination, CDN, queues, n+1, brotli, redis, streaming, optimistic UI, lazy-load, parallel reqs, db indexes, OTEL, SSR, defer, code-split, virtualization, pooling, re-renders, cache, LB, fonts, RUM). | ADOPT | R2-04 |
| 05 | matheusgomes (a) | Big-file context rot: files >1k lines compact/hallucinate; refactor prompt splits into modules. | ADOPT | R2-05 |
| 06 | youraveragetechbro (b) | Merge without manual review via create/maintain-verification-skill (video 1/7). | COVERED (#309) + dogfood opportunity | R2-06 |
| 07 | jotabusinessbr | 9 open-source SaaS alternatives (voice studio, OpenSEO, AppFlowy, open-whisper, Chatwoot, Cap). | BACKLOG | R2-07 |
| 08 | eduardocavalcanti | NVIDIA Personaplex-7B realtime voice model, open weights, ElevenLabs-realtime class. | ADAPT | R2-08 |
| 09 | rodrigotadewald | Model routing command: main model cheap, subagents cheapest, hard decisions escalate to strongest (advisor pattern). | ADAPT | R2-09 |
| 10 | leikauskas.dev | HF model-name decoder anatomy (maker/size/claims/scores/surgery/packaging); Heretic = abliteration tool. | ADAPT small | R2-10 |
| 11 | j.t.rivard | Claude Code power features: youshouldknow watcher agent, /loop fixed-interval, auto-compact earlier, ultra-code (JS-coordinated swarm), ultrathink one-turn max effort. | ADOPT | R2-11 |
| 12 | fabianocarvalhojr | Game-dev repos: game-studio agent pack (49 agents), Unreal-Claude, Godot-MCP, AceStep-1.5 audio, NVIDIA audio2face. | BACKLOG | R2-12 |
| 13 | matheusgomes (b) | Same big-file technique: 3-prompt sequence (analyze -> code-gates -> break into modules), public repo. | ADOPT (merges R2-05) | R2-05, R2-13 |
| 14 | vicentecondee | Anthropic 5 archetypes: Prototyper, Builder, Simplifier, Grower, Maintainer. Roles not titles. | BACKLOG doc | R2-14 |
| 15 | youraveragetechbro (a) | Quality-skills reel (ponytail, pstack, thermonuclear). | COVERED (v3.19.0 wave) | - |
| 16 | super_invencoes | Alt-data investing: satellite car counts, oil tank shadow radar, frost weather fronts -> alpha. | MERIDIAN | R2-15 |

## Cross-cutting reads

- **Verification-skills theme confirmed twice** (reels 06, 15): our #309 adoption is validated; dogfooding them on the atlas/bundle itself is the natural next proof (R2-06).
- **Big-file context rot appears twice** (05, 13): real community pain; our `context-hygiene`/`lean-code` cover principles but nothing operationalizes the 3-phase modularization refactor or guards file size (R2-05, R2-13).
- **Performance checklist** (04): `benchmark-checklist` vets numbers; nothing gives the frontend fix-list itself (R2-04).
- **Agent-watching-agent** (11): `chief-of-staff` watches the environment, nobody watches agent output quality mid-run (R2-11).
- **MERIDIAN item** (16): alt-data sources belong to the investment lane per standing instruction.
