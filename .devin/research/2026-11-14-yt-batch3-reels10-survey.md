# Survey: yt-batch3 + reels-10 (2026-11-14)

Inputs: 15 YouTube videos + 15 Instagram reels supplied by the user.
Artifacts: `.devin/scratch/yt-batch3/` (agenda, transcripts/, asr/, metadata.md),
`.devin/scratch/reels-10/` (15x info.json, descriptions.md).
Coverage: 7 native VTT + 8 whisper.cpp ASR (subs endpoint 429 all session;
audio endpoint fine) + 15/15 reels descriptions. Raw facts below come only
from retrieved material; inference is marked.

## Theme clusters

### T1. Anti-AI-slop design / taste gates (5 sources, dominant)

- eQ74n4huAcA "Make AI-Generated UI Look Expensive (7 Fixes)" (Griffin
  Wooldridge): recurring AI-UI tells; fixes incl. one clear focal point,
  4/8px spacing scale; 7-question checklist; cites Linear/Stripe/Notion
  as bar; transitions.dev + Emil Kowalski animation skill.
- -bv2xKQzZio "Leon Lin's AI design workflow" (AI LABS): process over
  prompts; design system to catch slop; "Cook" skill that loops design
  until it hits the bar.
- lAE78Iorby0 "Fable 5.2 workflow" (Chase AI): 4 steps - Taste, Tools,
  Direction, Dial.
- 7FU98O0JLHs "Turn Claude Into A Design GENIUS" (Chase AI): injecting
  taste into Claude Code web design.
- DfphRvFBx54 (reel, charles.unemployed): design-law dump - UI anims
  under 300ms, Doherty threshold 400ms, Fitts, Hick, Miller 7-item
  chunking, frequency-of-use for animation, cite Raphael Salaja
  userinterface.wiki / Disney Illusion of Life / Laws of UX.
- Rk6t9Uq1y9M "Vibe code an animated app" (Jason Lee): iterative
  animation-quality passes incl. phone-tilt responsive animation.

Inference: the ecosystem has converged on "checklist + iteration loop"
as the slop antidote. The bundle has art-director/ux-researcher but no
distilled anti-slop checklist gate.

### T2. Agent UI perception without screenshots (3 sources)

- DfSn_x9gMsx (reel, the.mindloop): Vercel open-sourced agent-desktop;
  reads buttons/fields by name instead of screenshots; claimed
  198k -> 31k tokens (-84%).
- DfnKmAPIoAW (reel, louis_rlee): Rune (OpenCode team), Rust GPU UI
  framework, every app runs headless; agent renders PNG, reads element
  tree, clicks/types via scripts. MIT, pre-release.
- DfrQykkExGq (reel, radaropensource): Vercel UI SDK, keyboard nav,
  focus, a11y behaviors "for agents to program for you".

Inference: accessibility-tree/element-tree perception is becoming the
cheap default; screenshot is the fallback. Our computer-use perceives
via screenshots first.

### T3. Orchestration: one universal skill + agent workspaces (4 sources)

- ujW-e6w3NQA (PT-BR creator, Alethe author): skip orchestrator apps;
  install ONE skill into any agent (Claude Code, Codex, Gemini CLI);
  expensive model plans, cheap models execute; parallel task split;
  failover on rate limit; `npx skills add <repo>` distribution.
- VEMLsCkUkMI "Stop using tmux; use Herder": workspaces/sessions/tabs;
  "internal skills" auto-installed so agents control the workspace and
  message each other; remote access; agents read each other's output.
- zZYWQRE-0xs "Why I'm betting on Rex" (reemus_dev): Rex (Mitchell
  Hashimoto, libghostty) as multiplexer primitive; mirroring vs tmux
  compositing; API sessions/windows/blocks; closed beta.
- ihElfZhR-eI "Free AI rebuilds Claude Code": Kiln rebuild w/ OpenCode +
  free models (DeepSeek, GLM); REA tool (229 analysis tools) for
  study-not-copy; OpenRouter 50 req/day -> 429 -> NVIDIA free key.

Inference: distribution via `skills add` and "agent-controlled
workspace" are the two emergent patterns; the bundle is already a
shared-skills repo - we are the substrate, not a consumer of these apps.

### T4. Free/cheap model routing + token cuts (3 sources)

- ihElfZhR-eI: free model rotation (DeepSeek V4.1, GLM 5.3 Flash),
  rate-limit failover chains.
- DfpQW9nOggv (reel, reevesmilesai): QuadCode plugins - Ponytail
  (-50% tokens), OmniRoute (300+ free providers, 1.6B tokens/mo),
  Graphify (codebase knowledge graph), AgentSkills (24 skills).
- DdEea0wiU1_ (reel, baptisteodonovan): trending repos - OpenClaude
  (Claude Code on any model), Invidious, OpenMAIC, Academic Research
  Skills (~45k stars), MiniMind (train own model in 2h).

### T5. Measurable quality over review (1 source, strong echo)

- DfpaKb1k2Og (reel, imersaoexponencia): Uncle Bob stopped reading
  agent-written code; measures coverage, dependencies, complexity,
  module size, mutation testing. If agent writes in 10min and you
  review 2h, the queue outgrows any human.

Inference: external validation of the bundle's gates/held-out/metrics
philosophy - cite as evidence, no new capability needed.

### T6. Voice/audio agent UX (1 source)

- rPsZfcFsws4 "Give your agents a voice" (Kaua Miguel Dev): Fish Audio
  S2.1 TTS via Claude Code Stop/Notification hooks -> hook.js -> API;
  personas per agent; AGENTS.md rules control summary length.

### T7. OSINT / security (2 sources)

- zhTjzscNLEI "OSINT: Find Everything" (CyberFlow): IntelTechniques,
  Epieos (email->Google), Sherlock (username->400 sites), Holehe
  (email->platforms), Hunchly (evidence capture), Overpass Turbo geo,
  SpiderFoot, PACER.
- Dfmwvxattcl (reel, linuxparahackers): WhiteRabbitNeo/DeepHat open
  security model - MITRE, CVEs, pentest reports; V3 runs local.

### T8. Repo/org patterns (1 source)

- hWe-j78vNpc "The Home Repo" (Matt Pocock): shared agent skills,
  steering files, custom tooling across repos; personal wiki; why not
  monorepos. External validation of this bundle's model.

### T9. Misc / low relevance

- VSQjmrJ7KrU Taby device (open-sourced firmware after viral reel)
- fMWThgQmibw Rust ecosystem overview (bundle already has ADR-003)
- B65KJ3kUSSo study techniques; DZsE7FqoQpQ comedy; DfqVnDLgcAc Claude
  relationship automations; DfngW6OjLaN GPU task manager;
  DfoYtUxsErn prompt-bait; DfkUISAMnPb vague AI co-worker;
  DfoU9n2Bx0e text->3D world (Qwen-tagged; check ai3d-gen coverage);
  Dfby7sPgMPU 31-item vibe-coding perf checklist (perf-eng adjacent)
