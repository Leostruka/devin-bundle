---
name: primeagent-reference
description: Use when researching agent harness design patterns, when comparing Devin CLI to PrimeAgent/RLM architectures, or when evaluating which PrimeAgent features could be adapted to Devin CLI. Reference card of verified findings and adaptation status.
---

# PrimeAgent/RLM Reference

## Purpose

Documents the verified findings from the PrimeAgent/RLM research and maps
each feature to its adaptation status in Devin CLI. Preserves the full
research so future work can revisit non-applied features without re-doing
the verification.

## Verified Sources

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

## Feature Adaptation Map

| # | PrimeAgent/RLM feature | Adapted to Devin CLI | How |
|---|---|---|---|
| 1 | RLM context folding (prompt-as-variable, REPL, recursive sub-queries) | **Yes** — `context-folding` skill | Offload to file, grep/partition, subagent_explore sub-queries (depth=1 only) |
| 2 | Continual Harness `/refine` (self-improving harness state) | **Yes** — `refine` skill + `refine-review-prompt.py` Stop hook | Trajectory review → small evidence-backed edits to skills/rules/agents/hooks. Auto-trigger via Stop hook + `.refine-pending` marker. Outcome tracking via `refinements.log.jsonl`. |
| 3 | Persistent subagents with A2A messaging | **Yes (emulated)** — `a2a-mailbox` skill | Filesystem as message broker. Mailboxes per agent (parent/subagent). Sequential A2A via file routing. Not real-time, not persistent handles, but preserves the pattern. |
| 4 | Skills as importable Python packages | **Partial** — already supported | Skills can have `scripts/` dirs with Python. `self-extend` skill documents this. |
| 5 | Daemon-backed sessions with reattach | **Yes (emulated)** — `session-checkpoint` skill | Structured checkpoint file (todos, decisions, files, verification, next actions). New session reads checkpoint and resumes. Not real reattach, but structured cross-session continuation. |
| 6 | Heartbeats and schedules | **Yes (emulated)** — `heartbeat` skill | OS scheduler (Task Scheduler/cron) + heartbeat script launches new Devin CLI session with prompt. In-session periodic nudges via PostToolUse hook. Not real re-entry, but scheduled re-launch. |
| 7 | Bounded autonomous mode with quality gates | **Yes** — `autonomous-gates` skill | Define gates at planning time, run after each step, final gate before done |
| 8 | "Not a security sandbox" warning | **Yes** — Rule 13 in AGENTS.md | Explicit rule with guardrails |
| 9 | Reward hacking guard (Factorio lesson) | **Yes** — in `refine` skill + Rule 13 | Guardrails in refine workflow, explicit reference to Factorio case |

## Adaptation Status: 9/9 features adapted

- **3 direct adaptations** (1, 7, 8): feature maps cleanly to Devin CLI runtime
- **3 emulated adaptations** (3, 5, 6): feature doesn't map directly, but the pattern is preserved via file-based workarounds. Each emulation documents its limitations vs PrimeAgent.
- **1 partial** (4): already supported by Devin CLI's `scripts/` directory mechanism
- **2 guardrails** (2, 9): adapted with safety mechanisms (reward hacking guard, auto-trigger with outcome tracking)

## Emulated Features — Limitations vs PrimeAgent

### 3. A2A Mailbox (emulates persistent subagents)

| Feature | PrimeAgent | A2A Mailbox |
|---|---|---|
| Real-time messaging | Yes (socket) | No (file polling) |
| Bidirectional during execution | Yes | No (subagent runs to completion) |
| Persistent handles | Yes | No (ephemeral subagents) |
| Multi-agent concurrent chat | Yes | No (sequential only) |

### 5. Session Checkpoint (emulates daemon-backed reattach)

| Feature | PrimeAgent | Session Checkpoint |
|---|---|---|
| Background daemon | Yes (socket server) | No (file-based) |
| Real-time reattach | Yes (session still running) | No (session ended) |
| Kernel state recovery | Yes (JSONL + snapshot) | No (only structured state) |
| Worker recovery | Yes (automatic) | No (manual resume) |

### 6. Heartbeat (emulates scheduled re-entry)

| Feature | PrimeAgent | Heartbeat |
|---|---|---|
| Re-enters existing session | Yes | No (launches new session) |
| Built-in `/heartbeat` command | Yes | No (OS scheduler + script) |
| In-session periodic check | Yes | Via PostToolUse hook (nudge, not re-entry) |

## Key Numbers (All Verified)

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
| PrimeAgent 9-eval table | Opus 5 beats Claude Code 6/9, GPT-5.6 beats Codex 6/9, GLM-5.2 beats Pi-mono 8/9 | PrimeAgent blog |
| Context rot models tested | 18 (5 Anthropic, 7 OpenAI, 3 Google, 3 Alibaba) | Chroma report |

## Errors in the Source Video (Corrected)

| Video claim | Correct value | Source |
|---|---|---|
| "GPT-V mini" | GPT-5-mini | arXiv:2512.24601 |
| "Opus-V beat Claude Code" | Opus 5 beat Claude Code | PrimeAgent blog |
