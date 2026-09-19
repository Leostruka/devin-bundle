# Mode: Harness Reference Card

### Purpose

Documents the verified findings from the PrimeAgent/RLM research and maps
each feature to its adaptation status in Devin CLI. Preserves the full
research so future work can revisit non-applied features without re-doing
the verification.

### Verified Sources

| Source | URL | Verified |
|---|---|---|
| RLM paper | arXiv:2512.24601 | Zhang, Kraska, Khattab — MIT CSAIL |
| RLM blog | alexzhang13.github.io/blog/2025/rlm/ | Alex Zhang |
| RLM reproduction | arXiv:2603.02615 | Daren Wang — depth analysis |
| PrimeAgent blog | primeintellect.ai/blog/prime-agent | PrimeIntellect, 2026-08-05 |
| PrimeAgent GitHub | github.com/PrimeIntellect-ai/prime-agent | 16.2k stars, MIT |
| Continual Harness paper | arXiv:2605.09998 | Karten et al. — Princeton |
| Context rot report | trychroma.com/research/context-rot | Chroma, 18 models |
| ARC-AGI-3 leaderboard | arcprize.org/leaderboard/community | Retrodict 99.86%, Schema 99% |
| Opus 5 ARC result | arcprize.org/results/anthropic-claude-opus-5 | 30.16% (High) |
| PrimeIntellect funding | TechCrunch, Intel Capital, SiliconANGLE | $130M Series A, $1B, 6k customers |

### Feature Adaptation Map

| # | PrimeAgent/RLM feature | Adapted to Devin CLI | How |
|---|---|---|---|
| 1 | RLM context folding (prompt-as-variable, REPL, recursive sub-queries) | **Yes** — `context-hygiene` skill | Offload to file, grep/partition, `researcher` sub-queries (depth=1 only; do NOT use `subagent_explore` when the parent is free — check `cost_tier` in `data/bundle-models.json`) |
| 2 | Continual Harness `/refine` (self-improving harness state) | **Yes** — `self-improvement` Refine mode + `refine-review-prompt.py` Stop hook | Trajectory review → small evidence-backed edits to skills/rules/agents/hooks. Auto-trigger via Stop hook + `.refine-pending` marker. Outcome tracking via `refinements.log.jsonl`. |
| 3 | Persistent subagents with A2A messaging | **Yes (emulated)** — A2A Messaging mode in this skill | Filesystem as message broker. Mailboxes per agent (parent/subagent). Sequential A2A via file routing. Not real-time, not persistent handles, but preserves the pattern. See "Mode: A2A Messaging" below. |
| 4 | Skills as importable Python packages | **Partial** — already supported | Skills can have `scripts/` dirs with Python. `devin-config` skill documents this. |
| 5 | Daemon-backed sessions with reattach | **Pruned** — didn't fit Devin CLI's single-process runtime | Originally emulated via a `session-checkpoint` skill (structured checkpoint file). Pruned because Devin CLI has no background daemon to reattach to. |
| 6 | Heartbeats and schedules | **Pruned** — didn't fit Devin CLI's single-process runtime | Originally emulated via a `heartbeat` skill (OS scheduler + script). Pruned because Devin CLI cannot re-enter an existing session. |
| 7 | Bounded autonomous mode with quality gates | **Yes** — `gates` skill | Define gates at planning time, run after each step, final gate before done |
| 8 | "Not a security sandbox" warning | **Yes** — Rule 13 in AGENTS.md | Explicit rule with guardrails |
| 9 | Reward hacking guard (Factorio lesson) | **Yes** — Refine mode in this skill + Rule 13 | Guardrails in refine workflow, explicit reference to Factorio case |

### Adaptation Status: 7/9 features adapted, 2 pruned

- **3 direct adaptations** (1, 7, 8): feature maps cleanly to Devin CLI runtime
- **1 emulated adaptation** (3): A2A Messaging mode in this skill — pattern preserved via file-based workarounds, documents limitations vs PrimeAgent
- **1 partial** (4): already supported by Devin CLI's `scripts/` directory mechanism
- **2 guardrails** (2, 9): adapted with safety mechanisms (reward hacking guard, auto-trigger with outcome tracking)
- **2 pruned** (5, 6): `session-checkpoint` and `heartbeat` emulations didn't fit Devin CLI's single-process runtime — no background daemon, no session re-entry

### Emulated Features — Limitations vs PrimeAgent

#### 3. A2A Messaging (emulates persistent subagents)

| Feature | PrimeAgent | A2A Messaging (this skill) |
|---|---|---|
| Real-time messaging | Yes (socket) | No (file polling) |
| Bidirectional during execution | Yes | No (subagent runs to completion) |
| Persistent handles | Yes | No (ephemeral subagents) |
| Multi-agent concurrent chat | Yes | No (sequential only) |

### Key Numbers (All Verified)

| Metric | Value | Source |
|---|---|---|
| RLM(GPT-5-mini) vs GPT-5 on OOLONG @132k | +34 points (114%) | arXiv:2512.24601 |
| RLM(GPT-5-mini) vs GPT-5 on OOLONG @263k | +15 points (49%) | arXiv:2512.24601 |
| RLM cost per query | $0.11 - $0.99 | arXiv:2512.24601 |
| Claude Code cost per query | $0.98 - $6.75 | arXiv:2512.24601 |
| RLM handles | 10M+ tokens | arXiv:2512.24601 |
| Depth=2 time inflation | 3.6s → 344.5s (95x) | arXiv:2603.02615 |
| PrimeAgent ARC-AGI-3 | 95.5% RHAE (vs 95.4% human) | PrimeAgent blog |
| Opus 5 ARC-AGI-3 | 30.16% | arcprize.org |
| Retrodict ARC-AGI-3 | 99.86%, $654, 5.5x fewer tokens | GitHub + leaderboard |
| Schema ARC-AGI-3 | 99% (Opus 4.8 + Fable 5) | schema-harness.github.io |
| PrimeAgent GitHub | 16.2k stars, 1.7k forks, MIT | GitHub |
| PrimeIntellect funding | $130M Series A, $1B valuation, 6k customers | TechCrunch |
| PrimeAgent 9-eval table | Opus 5 beats Claude Code 6/9, GPT-5.6 beats Codex 6/9, bundle parent model (per `BUNDLE_DEFAULT_MODEL` / `data/bundle-models.json`) beats Pi-mono 8/9 | PrimeAgent blog |
| Context rot models tested | 18 (5 Anthropic, 7 OpenAI, 3 Google, 3 Alibaba) | Chroma report |

### Errors in the Source Video (Corrected)

| Video claim | Correct value | Source |
|---|---|---|
| "GPT-V mini" | GPT-5-mini | arXiv:2512.24601 |
| "Opus-V beat Claude Code" | Opus 5 beat Claude Code | PrimeAgent blog |

---

