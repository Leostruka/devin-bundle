# Survey: yt-batch5 + reels-11 + web batch (2026-11-18)

Inputs: 11 YouTube videos, 35 Instagram reels, 5 web articles, 1 GitHub
repo supplied by the user. Deduplication vs prior batches: 11 reels +
3 videos already surveyed (reels-10, yt-batch3, yt-batch4) -> 24 new
reels, 8 new videos, 6 web sources analyzed fresh.

Artifacts: `.devin/scratch/yt-batch5/` (info.json x8, transcripts/ x3
native VTT, asr/ x5 whisper.cpp `base` all ok, media/, metadata.md),
`.devin/scratch/reels-11/descriptions.md`.

Retrieval notes: YouTube subs endpoint 429'd again (3/8 native VTT;
5 covered by whisper.cpp `base` via extensions/asr). Instagram
anonymous extraction broke since 2026-11-14: yt-dlp (incl. 2026.10.26)
gets "empty media response" (login wall); DPAPI cookie extraction
fails (Chrome app-bound). Captions recovered via `webfetch` render
(22/24 full; 2 degraded to oembed first-line: Df0oeQmILhf,
Dfpzj3AjRur).

## Theme clusters

### T1. Agent distraction / stale-context trust (1 source, HIGH)

- JhZB3spnuIY "Google Just Released Something To Fix Claude Code's
  Biggest Problem" (AI LABS): Google's internal study - agents treat
  outdated files as tasks ("side quests"): 1-in-7 sessions hit stale
  bug notes, 4/5 unprompted; distracted sessions +70% actions, +77%
  tokens, >2x duration. 9/10 agents follow an outdated CLAUDE.md over
  the actual code. Fixes: code-as-source-of-truth rule (flip to 9/10
  correct), ticket status tags, "leave alone anything not asked",
  plan-overlap check before building unticketed work, fresh session
  per task, a "sweep" skill that hunts stale notes (report-only,
  separate checker agent that sees claims but not the main agent's
  suspicions, conflicts listed separately, archive + PreToolUse
  read-block on archived files).

### T2. Codebase hygiene for agents (3 sources, dominant cluster)

- github.com/caldoai/skills (1.5k stars, MIT): `untangle-codebase` -
  one-pass whole-codebase refactor via "should these pieces change
  together" taxonomy (hidden links / needless links / surplus /
  special cases), redesign-first-principles, decision log, subagent
  verification sweeps, git-as-evidence. `prune-tests` - delete tests
  anchored to the past / nothing / the implementation; rewrite
  internals-bound tests against behavior.
- Df0YS__h_yV (billyia_): same untangle-codebase skill - "code gets
  messier the longer AI works on it; temp fixes, dup functions,
  unnecessary files".
- Df2vU-tvzti (olle.ai): Lauren Tan (SpaceX AI, pstack): "your code is
  the biggest piece of memory you give your agent - bad code spreads
  and so does good code".

### T3. Memory / knowledge architecture for agents (4 sources)

- lNpDxKfBlf8 "Did Stanford Just Solve AI Memory? (Memorilla)"
  (Better Stack): trainable compressor -> 16 memory tokens read by
  frozen Qwen3-8B; flat ~0.12s answer time at 512 docs; best avg on
  their benchmarks BUT failed the author's custom "buried clue" test -
  works on benchmark-like data, weak on precise recall.
- FeAysJe6FGA "Omnigraph" (Roman Pronskiy): open-source graph DB for
  agent world models - typed ontology enforced at write time,
  per-agent branches + PR-style review/merge, git-like commits/rewind,
  hybrid keyword+vector+graph query, S3-compatible open format.
- DfncrVjh-0u (devvveloper): NVIDIA auto-ontology (GH trending #1) -
  reads DB schemas/samples/query history, builds business-term
  dictionary, human certifies, agent consults dictionary before SQL;
  Postgres/Snowflake/Databricks/DuckDB via MCP/CLI/API, Apache.
- Df2r8ASmWZS (radaropensource): mmap-style on-disk weight loading
  for big local models (MEMORIA).

### T4. Token-cost / context engineering (2 sources)

- daily.dev "7 AI tools" (CodeHead RwtaADjOi0Q): CloudM (observer
  writes session notes -> next-session index), RTK "Rust token killer"
  (compresses terminal output -66% tokens), Herder (multi-agent tmux),
  Hallmark "slop lint", Hyperframes (HTML->MP4), Hermes Agent
  (self-hosted, writes reusable skills after tasks), n8n.
- Df2VmAKo3RQ (justinmendez.ai): Tencent LoopForge - agent-checks-
  agent completion loops; advice: extract ideas, build your own.

### T5. Agent perception / UI-for-agents (3 sources)

- zQPZ2982i78 "UI SDK" (OrcDev): Vercel UI SDK - UI behaviors not
  components; agents drive UI w/o screenshots/DOM clicking; three
  layers + createAgent (form/kanban/swipe-inbox demo).
- DfvH6dPgd9u (radaropensource): Dynamic Island for React via shadcn.
- DfxBT6yqW5E (aartstock): ReactBits.dev animated components.

### T6. Devices / integrations (4 sources)

- 4cO6gKPkF08 "The Screen I Use More Than My iPhone" (Andres Vidoza):
  Even Realities G2 long-term review - display-only glasses (no
  camera/speaker), micro-LED text HUD, Even Hub widgets, Conversate
  live transcription/translation, teleprompter/lists, Even AI 2.0 with
  memory + Conversate Pro beta. USER FLAGGED: wants to buy glasses and
  build something in this style.
- Dfpzj3AjRur (dopanimers): CapriCore - free Windows desktop AI
  companion reacting to screen + mouse/keyboard control w/ consent.
- Dfx7Cv4CR8J (gab.gouvea): Mailflare - self-hosted email/calendar/
  scheduling on own Cloudflare account; MCP lets Claude read agenda;
  README ships paste-into-agent deploy prompt.
- Dfhy9BtpDff (luizsantos.ia): Reverse API Engineer - records site
  backend calls, generates client code; works on API-less sites.

### T7. External validation of bundle practices (4 sources)

- freecodecamp "Learn Agentic Coding with Codex": AGENTS.md,
  plan mode, skills, characterization tests+TDD, git/secrets safety,
  permissions/config.toml, MCP - the bundle's exact surface.
- DfpaKb1k2Og / prior reels: metrics-over-review (Uncle Bob).
- firethering "7 small local models": Phi-4-mini, Qwen3.5-4B,
  Llama3.2-3B, Gemma3-4B, Mistral Nemo 12B, R1-Distill-7B, SmolLM -
  validates ai-tools/laya local-model lane.
- Hallmark slop-lint + Hermes self-skill-writing: design_lint.py +
  continuous-improvement validation.

### T8. Misc / low relevance

- UMjeSU6C4qU $80K/mo mobile app tutorial; UyPbjmLUtEo Riddled
  anti-sycophancy notebook; 1KqUVQbX_J0 6 Rust libs (Rerun, GPUI Kit,
  thiserror, Pingora); DfywFF4S7IH Blender Skills 94-pack;
  Dfutd4mROBz Meshy ThreeRT path tracing; Df0lfaNAn7z pixel-art
  Gaussian splats; daily.dev WFC infinite-worlds algo; Miro homepage
  (ad); Df3-nsBoGdG "manual" thin; Df2rodDhDzy 5-skill vibecoding
  list; Df0oeQmILhf waitlist bait; DfsXtr9PhtD game feel;
  DfzqNyhhafm AI-team promo; Dc2Ah6Vhvar uv; DfxADRilTsZ Rust
  download mgr; Dfu150nT95z link-bait; Dfv3TVbBnGV Kiri.

## Coverage check vs bundle (T1-T6)

- T1 anti-distraction: Rule 7 (no more than asked) covers
  leave-alone; `drift-report` covers sweep-report-only; `sentinel`/
  `qa-ci` cover independent checking; tracker `Status:` covers ticket
  tags. RESIDUAL: no explicit code-over-docs precedence rule in
  AGENTS.md; no plan-overlap check.
- T2 untangle/prune: `legacy-refactor` (incremental strangler) !=
  goal-driven full untangle; `mutation-testing` finds gaps but
  `prune-tests` (delete non-guards) has no equivalent.
- T3: `project-memory`+BM25 covers CloudM; Memorilla is research-
  stage; Omnigraph/auto-ontology adjacent to `knowledge-modeling` +
  `ontology-validator` + `data-analyst` dictionary practice.
- T4: token-saver hook + quiet-mode post-exec already cover
  RTK/CloudM patterns.
- T5: element-tree perception eval already tracked (#632/#633).
- T6: `devin-integrate`/`device-repurpose` cover device lane;
  glasses-HUD is a new surface worth noting.
