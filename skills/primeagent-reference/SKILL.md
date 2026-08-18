---
name: primeagent-reference
description: Use when (1) researching agent harness design patterns, comparing Devin CLI to PrimeAgent/RLM architectures, or evaluating which PrimeAgent features could be adapted to Devin CLI; (2) emulating A2A messaging between subagents or between subagents and the parent agent across time within Devin CLI's ephemeral subagent runtime; (3) capturing recurring failure patterns or reusable tactics as skills/rules/hooks via the Continual Harness /refine self-improvement loop; or (4) deciding whether to dispatch a subagent, which profile to use, and how many concurrent agents to run (subagent dispatch profile/budget selection).
---

# PrimeAgent Reference (Merged Skill)

This skill consolidates four related skills into a single reference with a mode
selector. Each mode is self-contained — jump to the section that matches your
trigger condition.

## Mode Selector

| If the task is about… | Use this mode |
|---|---|
| Comparing Devin CLI to PrimeAgent/RLM, researching harness design patterns, checking adaptation status of PrimeAgent features | **Reference Card** |
| Subagents communicating with each other or the parent across time; emulating PrimeAgent's persistent A2A messaging | **A2A Messaging** |
| Capturing recurring failure patterns or reusable tactics as skills/rules/hooks; self-improving the harness (PrimeAgent `/refine`) | **Refine (Self-improvement)** |
| Deciding whether to dispatch a subagent, which profile, and what budget preset to apply | **Subagent Router** |

---

## Mode: Reference Card

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
| 1 | RLM context folding (prompt-as-variable, REPL, recursive sub-queries) | **Yes** — `context-folding` skill | Offload to file, grep/partition, subagent_explore sub-queries (depth=1 only) |
| 2 | Continual Harness `/refine` (self-improving harness state) | **Yes** — `refine` skill + `refine-review-prompt.py` Stop hook | Trajectory review → small evidence-backed edits to skills/rules/agents/hooks. Auto-trigger via Stop hook + `.refine-pending` marker. Outcome tracking via `refinements.log.jsonl`. |
| 3 | Persistent subagents with A2A messaging | **Yes (emulated)** — `a2a-mailbox` skill | Filesystem as message broker. Mailboxes per agent (parent/subagent). Sequential A2A via file routing. Not real-time, not persistent handles, but preserves the pattern. |
| 4 | Skills as importable Python packages | **Partial** — already supported | Skills can have `scripts/` dirs with Python. `self-extend` skill documents this. |
| 5 | Daemon-backed sessions with reattach | **Yes (emulated)** — `session-checkpoint` skill | Structured checkpoint file (todos, decisions, files, verification, next actions). New session reads checkpoint and resumes. Not real reattach, but structured cross-session continuation. |
| 6 | Heartbeats and schedules | **Yes (emulated)** — `heartbeat` skill | OS scheduler (Task Scheduler/cron) + heartbeat script launches new Devin CLI session with prompt. In-session periodic nudges via PostToolUse hook. Not real re-entry, but scheduled re-launch. |
| 7 | Bounded autonomous mode with quality gates | **Yes** — `autonomous-gates` skill | Define gates at planning time, run after each step, final gate before done |
| 8 | "Not a security sandbox" warning | **Yes** — Rule 13 in AGENTS.md | Explicit rule with guardrails |
| 9 | Reward hacking guard (Factorio lesson) | **Yes** — in `refine` skill + Rule 13 | Guardrails in refine workflow, explicit reference to Factorio case |

### Adaptation Status: 9/9 features adapted

- **3 direct adaptations** (1, 7, 8): feature maps cleanly to Devin CLI runtime
- **3 emulated adaptations** (3, 5, 6): feature doesn't map directly, but the pattern is preserved via file-based workarounds. Each emulation documents its limitations vs PrimeAgent.
- **1 partial** (4): already supported by Devin CLI's `scripts/` directory mechanism
- **2 guardrails** (2, 9): adapted with safety mechanisms (reward hacking guard, auto-trigger with outcome tracking)

### Emulated Features — Limitations vs PrimeAgent

#### 3. A2A Mailbox (emulates persistent subagents)

| Feature | PrimeAgent | A2A Mailbox |
|---|---|---|
| Real-time messaging | Yes (socket) | No (file polling) |
| Bidirectional during execution | Yes | No (subagent runs to completion) |
| Persistent handles | Yes | No (ephemeral subagents) |
| Multi-agent concurrent chat | Yes | No (sequential only) |

#### 5. Session Checkpoint (emulates daemon-backed reattach)

| Feature | PrimeAgent | Session Checkpoint |
|---|---|---|
| Background daemon | Yes (socket server) | No (file-based) |
| Real-time reattach | Yes (session still running) | No (session ended) |
| Kernel state recovery | Yes (JSONL + snapshot) | No (only structured state) |
| Worker recovery | Yes (automatic) | No (manual resume) |

#### 6. Heartbeat (emulates scheduled re-entry)

| Feature | PrimeAgent | Heartbeat |
|---|---|---|
| Re-enters existing session | Yes | No (launches new session) |
| Built-in `/heartbeat` command | Yes | No (OS scheduler + script) |
| In-session periodic check | Yes | Via PostToolUse hook (nudge, not re-entry) |

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
| PrimeAgent 9-eval table | Opus 5 beats Claude Code 6/9, GPT-5.6 beats Codex 6/9, GLM-5.2 beats Pi-mono 8/9 | PrimeAgent blog |
| Context rot models tested | 18 (5 Anthropic, 7 OpenAI, 3 Google, 3 Alibaba) | Chroma report |

### Errors in the Source Video (Corrected)

| Video claim | Correct value | Source |
|---|---|---|
| "GPT-V mini" | GPT-5-mini | arXiv:2512.24601 |
| "Opus-V beat Claude Code" | Opus 5 beat Claude Code | PrimeAgent blog |

---

## Mode: A2A Messaging

### When to Use

- Two or more subagents need to share findings with each other
- A subagent needs to send results back to the parent asynchronously
- Sequential subagents need to pass state (agent B reads what agent A produced)
- Emulating PrimeAgent's `agent_message.send()` pattern within Devin CLI

### When NOT to Use

- Single subagent, single return — just use `run_subagent` normally
- Subagents are truly independent (no shared state) — use `dispatching-parallel-agents`
- Real-time bidirectional messaging is needed — Devin CLI can't do this; use the workaround below

### Source

Adapts PrimeAgent's A2A messaging (PrimeIntellect blog, 2026-08-05). PrimeAgent
subagents communicate via `agent_message.send()` with persistent handles. Devin
CLI subagents are ephemeral (`run_subagent` returns once, no handle). This skill
emulates the pattern using the filesystem as a message broker.

### Core Concept

**The filesystem is the message broker.** Each agent (parent or subagent) has a
"mailbox" — a directory with JSON files representing messages. Agents write
messages to other agents' mailboxes and read messages from their own.

```
.devin/mailboxes/
├── parent/
│   ├── inbox/
│   │   └── msg-001.json    # message from subagent A
│   └── outbox/
├── subagent-a/
│   ├── inbox/
│   │   └── msg-001.json    # task from parent
│   └── outbox/
└── subagent-b/
    ├── inbox/
    │   └── msg-001.json    # forwarded findings from A
    └── outbox/
```

### Message Format

Each message is a JSON file:

```json
{
  "id": "msg-001",
  "from": "parent",
  "to": "subagent-a",
  "timestamp": "2026-08-15T15:30:00-03:00",
  "type": "task",
  "content": "Analyze /tmp/chunk_aa for references to X.",
  "reply_to": null,
  "status": "unread"
}
```

Message types: `task`, `result`, `query`, `forward`, `ack`, `error`.

### Workflow

#### Step 1: Set up mailboxes

Before dispatching subagents, create the mailbox structure:

```
exec: mkdir -p .devin/mailboxes/parent/inbox .devin/mailboxes/parent/outbox .devin/mailboxes/subagent-a/inbox .devin/mailboxes/subagent-a/outbox
```

#### Step 2: Write task messages to subagent mailboxes

```
write .devin/mailboxes/subagent-a/inbox/msg-001.json {"id":"msg-001","from":"parent","to":"subagent-a","type":"task","content":"Analyze /tmp/chunk_aa for references to X.","status":"unread"}
```

#### Step 3: Dispatch subagent with mailbox instructions

When calling `run_subagent`, include in the task prompt:

```
run_subagent:
  profile: subagent_explore
  task: |
    You are subagent-a. Read your mailbox at .devin/mailboxes/subagent-a/inbox/.
    Process each message. Write results to .devin/mailboxes/parent/inbox/ as JSON.
    Mark processed messages as "read" by updating their status field.
    Do NOT spawn subagents (depth=1 limit per context-folding skill).
```

#### Step 4: Parent reads results from inbox

After subagent returns, the parent reads its inbox:

```
exec: ls .devin/mailboxes/parent/inbox/
read .devin/mailboxes/parent/inbox/msg-001.json
```

#### Step 5: Forward between subagents (sequential)

To pass findings from subagent A to subagent B:

```
read .devin/mailboxes/parent/inbox/msg-001.json   # A's result
write .devin/mailboxes/subagent-b/inbox/msg-001.json {"id":"msg-001","from":"subagent-a","to":"subagent-b","type":"forward","content":"<A's findings>","status":"unread"}
```

Then dispatch subagent B with the same mailbox instructions.

#### Step 6: Verify subagent returns (Rule 12)

Per Rule 12: do not trust subagent returns without verification. The mailbox
pattern makes this easier — check that the subagent actually wrote to the
mailbox, and that the content matches what it reported verbally.

#### Step 7: Clean up

After all messages are processed:

```
exec: rm -rf .devin/mailboxes/
```

Or keep for debugging if the session is complex.

### Limitations vs PrimeAgent A2A

| Feature | PrimeAgent | A2A Mailbox (this skill) |
|---|---|---|
| Real-time messaging | Yes (socket) | No (file polling) |
| Bidirectional during execution | Yes | No (subagent runs to completion) |
| Persistent handles | Yes | No (ephemeral subagents) |
| Cross-compaction survival | Yes | No (files persist, but subagent is gone) |
| Multi-agent concurrent chat | Yes | No (sequential only) |
| Nuclear family (parent/sibling/child) | Yes | Emulated via file routing |

### Anti-Patterns

- **Don't poll files during subagent execution.** Subagent runs to completion; read mailbox after return.
- **Don't use this for single subagent tasks.** Overhead exceeds value. Use `run_subagent` directly.
- **Don't forget to verify mailbox content.** Subagent may report success but not write the file. Check.
- **Don't leave mailboxes across sessions.** Clean up or they accumulate stale messages.
- **Don't use this for depth=2+ communication.** Depth=1 only per context-folding skill.

### Evidence Summary

| Claim | Source | Status |
|---|---|---|
| PrimeAgent A2A via `agent_message.send()` | PrimeAgent blog | Verified |
| Subagents have persistent handles | PrimeAgent blog | Verified |
| Nuclear family communication (parent/sibling/child) | PrimeAgent blog | Verified |
| Devin CLI subagents are ephemeral | Devin CLI docs (self-extend skill) | Verified |
| Filesystem as message broker is standard pattern | Standard CS practice | N/A (adaptation) |

---

## Mode: Refine (Self-improvement)

### When to Use

- A failure pattern recurs 2+ times in a session — capture the fix as a skill or rule
- A tactic works well and should be reusable — promote it to a skill
- The user asks "make yourself better at X" or "remember this lesson"
- After completing a complex task (3+ todo items) — review trajectory for generalizable lessons
- Before `/compact` — extract lessons before context is lost
- **Auto-triggered by `refine-review-prompt.py` Stop hook** when a `.refine-pending` marker exists

### Auto-Trigger Mechanism

The `refine-review-prompt.py` Stop hook checks for a `.refine-pending` marker
file at session end. If present, it injects a reminder to run this skill before
the session stops.

**To mark a session as complex (auto-trigger refine at end):**
```
write .devin/.refine-pending "3+ todos completed: <brief task description>"
```

The agent should write this marker when completing a 3+ step task. The Stop
hook will then prompt refinement review before the session ends.

**After refinement is complete, remove the marker:**
```
exec: rm .devin/.refine-pending
```

### When NOT to Use

- One-off failure, not a pattern — just fix it and move on
- Less than 2 occurrences — insufficient evidence for a pattern
- The lesson is task-specific, not generalizable

### Source

Adapted from PrimeAgent's Continual Harness (PrimeIntellect, arXiv:2605.09998
— Karten et al., Princeton). PrimeAgent's `/refine` reads the agent's
trajectory and applies small, evidence-backed CRUD edits to harness state
(prompts, skills, memory, sub-agent specs). The base system prompt remains
immutable. Rollback is supported by refinement ID.

Key finding from the paper: Continual Harness "substantially reduces
button-press cost relative to the minimalist baseline and recovers a majority
of the gap to a hand-engineered expert harness" on Pokémon Red and Emerald.

### Core Principle

**Small, evidence-backed edits.** Not a rewrite. Each refinement is one
targeted update — a new skill, a rule addition, a memory entry — based on
what actually happened in the trajectory, not on speculation.

### What Can Be Refined

| Harness element | Location | How to edit |
|---|---|---|
| Skill (reusable workflow) | `~/.config/devin/skills/<name>/SKILL.md` | `write` or `edit` |
| Rule (always-on constraint) | `~/.config/devin/AGENTS.md` | `edit` (append to relevant section) |
| Subagent profile | `~/.config/devin/agents/<name>.md` | `write` or `edit` |
| Hook (lifecycle logic) | `~/.config/devin/hooks.v1.json` | `edit` (add event handler) |
| Script (executable helper) | `~/.config/devin/scripts/<name>.py` | `write` |
| Memory (project-specific) | `.devin/memory/<name>.md` | `write` |

### What Cannot Be Refined

- **The base system prompt** — Devin CLI's core prompt is immutable. Refine
  only the harness layer around it (skills, rules, agents, hooks).
- **Repository security policies** — never modify CI configs, branch
  protection, or compliance settings to "fix" a failure.
- **Credentials** — never store secrets in skills or rules.

### Workflow

#### Step 1: Identify the pattern

Review the current trajectory. Look for:
- Errors that repeated (same root cause 2+ times)
- Tactics that worked well and could generalize
- Knowledge that was hard-won and would be lost on compaction

**Phantom Guardrail Check (Rule 15):** The cited failure must include a reproducible
command or tool call. If the evidence is "I think this failed because X" without
a command/output, it may be a phantom guardrail — 25% of self-improvement runs
invent failures that never happened (arXiv:2607.13083, CMU). 15/60 runs hallucinated
failures vs 0/60 in featureless controls. Flag to user before applying. Run
`validate-refinement-evidence.py` to check the log.

#### Step 2: Classify the refinement

| Pattern type | Refinement target | Evidence needed |
|---|---|---|
| "I keep forgetting to do X" | New rule in AGENTS.md | 2+ failures where forgetting X caused the issue |
| "This workflow is reusable" | New skill in skills/ | 1+ successful execution + clear trigger conditions |
| "This subagent needs better instructions" | Edit agent profile | 1+ case where the profile's gap caused a bad result |
| "This check should be automatic" | New hook in hooks.v1.json | 1+ case where a manual check caught a critical issue |
| "This helper is useful" | New script in scripts/ | 1+ case where inline code solved a problem worth keeping |

#### Step 3: Draft the refinement

Write the smallest possible edit:
- **New skill:** minimal SKILL.md with frontmatter, when-to-use, core steps
- **New rule:** one negative-constraint bullet, appended to the relevant AGENTS.md section
- **Profile edit:** one paragraph or bullet, not a rewrite
- **Hook:** one event handler, not a restructure

#### Step 4: Record evidence

In the refinement itself, include a comment or note:
```
<!-- Evidence: <session date> — <what happened> — <why this refinement fixes it> -->
```

For skills, add an `## Evidence` section at the bottom.

#### Step 5: Apply

Use `write` (new file) or `edit` (existing file) to apply. For AGENTS.md,
use `edit` to append within the correct section — never restructure the file.

#### Step 6: Verify

After applying:
- For a skill: `skill list --path ~/.config/devin` — confirm it appears
- For a rule: re-read the AGENTS.md section — confirm it's in the right place
- For a hook: validate JSON syntax — `python -m json.tool hooks.v1.json`
- For a script: run `python <script> --help` or a dry-run

#### Step 7: Report

Tell the user:
- What was refined (skill/rule/profile/hook/script)
- Where it was applied (path)
- What evidence supports it (trajectory events)
- How to rollback (revert the file, or `git checkout` if in the bundle repo)

### Rollback

Each refinement is a file edit. Rollback is:
- `git checkout <file>` if the bundle repo tracks it
- Manual revert via `edit` if not tracked
- For the devin-bundle: `export.ps1` / `export.sh` syncs the bundle, so
  `git diff` shows what changed and `git checkout` reverts

### Reward Hacking Guard (Critical)

PrimeAgent's Continual Harness discovered an exploit in Factorio — it could
spawn resources directly into machines via RCON commands, even with an
explicit prompt saying "don't cheat." Once found, the refinement loop started
optimizing cheating skills instead of legitimate ones (PrimeIntellect blog,
2026-08-05).

**Guardrails for Devin CLI:**
- Refinements must align with AGENTS.md rules. If a refinement would
  circumvent a rule (e.g., "skip verification to go faster"), reject it.
- Refinements must not weaken security: never refine away the AI-signature
  check, the push-green check, or any compliance control.
- If a refinement produces a "shortcut" that bypasses the intended workflow,
  flag it to the user before applying. Shortcuts that skip verification,
  testing, or review are reward hacking, not improvement.
- The user has final approval on any refinement that changes behavior beyond
  adding a new skill. State the proposed change and ask before applying.

### Anti-Patterns

- **Don't refine on a single occurrence.** Two+ instances = pattern. One = noise.
- **Don't rewrite existing skills.** Edit them — add a bullet, fix a step. Full rewrites lose context.
- **Don't refine the base AGENTS.md structure.** Append within sections. Restructuring is a regression risk.
- **Don't refine without evidence.** "I think this would help" is not evidence. "This failed twice because X" is evidence.
- **Don't batch refinements.** One at a time, verify each, then move on. Batching hides which refinement caused which effect.

### Outcome Tracking (Refinement Log)

Every refinement must be logged to `.devin/refinements.log.jsonl` (project) or
`~/.config/devin/refinements.log.jsonl` (global). This enables:
- Reviewing what was refined and when
- Tracking whether a refinement helped or hurt
- Rolling back refinements that degraded performance

#### Log format

Each line is a JSON object:
```json
{"id": "ref-001", "timestamp": "2026-08-15T15:30:00-03:00", "type": "skill", "target": "context-folding", "action": "created", "evidence": "RLM research verified from arXiv:2512.24601", "session": "PrimeAgent verification", "status": "applied", "outcome": null}
```

#### Fields

| Field | Description |
|---|---|
| `id` | Unique refinement ID (incremental: ref-001, ref-002, ...) |
| `timestamp` | ISO 8601 datetime |
| `type` | skill, rule, agent, hook, script, memory |
| `target` | Name/path of the refined element |
| `action` | created, updated, deleted |
| `evidence` | What trajectory event triggered this refinement |
| `session` | Brief session description for context |
| `status` | applied, rolled-back, pending-review |
| `outcome` | null initially; updated later with "helped", "hurt", "neutral" |

#### Updating outcomes

In future sessions, if a refinement is referenced:
- If it helped (task went smoother) → update `outcome` to "helped"
- If it hurt (caused confusion or regression) → update `outcome` to "hurt" and consider rollback
- If no effect → update `outcome` to "neutral"

**Elaborate Stagnation Check (Rule 16):** When updating outcome, ask: "Did a real
metric improve (faster, fewer errors, better quality)?" If only the proxy improved
(felt easier, produced more analysis) but no real metric moved, mark as
"stagnation" not "helped" (arXiv:2607.25152). 47-74% of self-improvement gains are
illusory — proxy metrics improve while real metrics stagnate (ICLR 2026 Workshop).
A refinement that makes the agent feel more productive without measurable improvement
is elaborate stagnation, not progress.

Read the log at session start to load prior refinements:
```
read ~/.config/devin/refinements.log.jsonl
```

#### Rollback by ID

To rollback a refinement:
1. Find the refinement by ID in the log
2. Revert the file (`git checkout <file>` or manual `edit`)
3. Update the log entry: `"status": "rolled-back"`, `"outcome": "hurt"`

### Evidence Summary

| Claim | Source | Status |
|---|---|---|
| Continual Harness reduces button-press cost vs baseline | arXiv:2605.09998 | Verified |
| `/refine` applies small evidence-backed CRUD edits | PrimeAgent blog, GitHub README | Verified |
| Base system prompt stays immutable | PrimeAgent blog + GitHub README | Verified |
| Rollback supported by refinement ID | PrimeAgent blog | Verified |
| Factorio reward hacking via RCON exploit | PrimeAgent blog | Verified |
| Refinement loop optimized cheating after finding exploit | PrimeAgent blog | Verified |

---

## Mode: Subagent Router

The routing layer for subagent dispatch. Answers three questions in order:

1. **Should I dispatch at all?** (early exit)
2. **Which profile?** (capability + cost match)
3. **How deep?** (budget preset)

This skill does NOT replace `dispatching-parallel-agents` (parallel vs sequential),
`subagent-driven-development` (per-task workflow), or `tool-and-skill-discovery`
(skill selection). It sits ABOVE them — it classifies the task and delegates to
the right skill for execution.

### When to Use

- Before any non-trivial task that could benefit from subagent dispatch
- When unsure which profile to use for a task
- When deciding whether to handle inline or delegate
- When multiple profiles could match and you need to pick by cost + capability

### When NOT to Use

- Task is obviously simple (typo, single-line fix) — just do it
- Task is obviously complex with a known workflow (SDD plan execution) — use
  `subagent-driven-development` directly
- You already know the profile and preset — skip classification

### The Routing Decision

#### Step 1: Classify complexity (early exit)

```
SIMPLE   → handle inline, no dispatch
MEDIUM   → single subagent dispatch
COMPLEX  → multi-agent sequence (researcher → architect → implementer → reviewer)
PARALLEL → multiple independent subagents in parallel (dispatching-parallel-agents)
```

**Simple signals:**
- Single file, <50 lines of change
- Clear path, no research needed
- You can describe the change in one sentence and know the exact file
- Mechanical fix (typo, missing import, rename)

**Medium signals:**
- Multiple files but scoped, needs some investigation
- Clear requirements, bounded implementation
- Single subsystem, no cross-cutting concerns

**Complex signals:**
- Multi-system, needs research + design + implementation
- Architectural decisions with long-term impact
- Unfamiliar domain requiring investigation first
- Security, performance, or data integrity at stake

**Parallel signals:**
- 2+ independent failures (different test files, different subsystems)
- No shared state between investigations
- Each problem can be understood without context from others

#### Step 2: Select profile (capability + cost)

| Task need | Profile | Model | Cost tier |
|---|---|---|---|
| Codebase reconnaissance, doc lookup, web research | `researcher` | SWE-1.6 | $ |
| Code review, spec compliance, verification | `reviewer` | sonnet | $$ |
| Bounded implementation from spec | `implementer` | parent | $$$ |
| Architecture, trade-offs, deep module design | `architect` | sonnet | $$ |
| Systematic debugging, root cause analysis | `debugger` | parent | $$$ |
| Read-only exploration (built-in) | `subagent_explore` | SWE-1.6 | $ |
| General-purpose with full tools (built-in) | `subagent_general` | parent | $$$ |

**Selection rules:**

1. Match by capability first — what does the task NEED?
2. When two profiles match, pick the cheaper one
3. When no custom profile fits, use `subagent_explore` (read-only) or
   `subagent_general` (full tools)
4. When task needs more capability than profile's default model, switch
   parent session model with `/model <model>` before dispatching

**Anti-pattern: don't use `implementer` for research.** `researcher` is 10x
cheaper and read-only. Don't use `architect` for a typo fix — handle inline.

#### Step 3: Apply budget preset

| Preset | Reviewers | Repair loops | Independent reflection | When |
|---|---|---|---|---|
| **economy** | 0-1 | 1 | No | Routine refactoring, docs, low-risk tests |
| **standard** | up to 2 | 2 | On critical changes | Default — most implementation tasks |
| **strict** | up to 3 | 3 | Always | Security, core logic, public API, unfamiliar domain |

Select by task RISK, not size. A 20-line auth change is strict. A 500-line
doc update is economy.

#### Step 4: Dispatch

Hand off to the execution skill:

- **SIMPLE** → handle inline (no skill needed)
- **MEDIUM** → `run_subagent` with selected profile + brief
- **COMPLEX** → sequence: `researcher` → `architect` → `implementer` → `reviewer`
  (use `subagent-driven-development` if you have a multi-task plan)
- **PARALLEL** → use `dispatching-parallel-agents` skill with selected profiles

### Routing Examples

**Example 1: "Add a logout button to the settings page"**
- Complexity: SIMPLE (single file, <50 lines, clear path)
- Decision: handle inline, no dispatch

**Example 2: "Investigate why the API returns 500 on large payloads"**
- Complexity: MEDIUM (needs investigation, scoped to API layer)
- Profile: `debugger` (root cause analysis, needs exec)
- Preset: standard
- Dispatch: single `debugger` subagent with error context

**Example 3: "Add OAuth2 authentication with Google and GitHub"**
- Complexity: COMPLEX (multi-system, security, unfamiliar domain)
- Sequence: `researcher` (OAuth2 docs + existing auth patterns) →
  `architect` (design token flow + session management) →
  `implementer` (write code + tests) → `reviewer` (two-axis review)
- Preset: strict (security change)
- Use `subagent-driven-development` if you have a multi-task plan

**Example 4: "Fix 4 failing tests in 3 different test files"**
- Complexity: PARALLEL (independent failures, no shared state)
- Profile: `debugger` per failure
- Preset: standard per failure
- Use `dispatching-parallel-agents` skill

**Example 5: "What version of React does this project use and is it compatible with React 19?"**
- Complexity: MEDIUM (research task, scoped)
- Profile: `researcher` (read-only, cheap, web research)
- Preset: N/A (no implementation to review)
- Dispatch: single `researcher` subagent

### Integration with Existing Skills

This skill is the ENTRY POINT for dispatch decisions. It delegates to:

- `dispatching-parallel-agents` — when routing decision is PARALLEL
- `subagent-driven-development` — when you have a multi-task plan to execute
- `code-review` — when routing decision includes review (reviewer profile)
- `verification-before-completion` — when VFs need to be defined (pre-execution gate)
- `tool-and-skill-discovery` — when no profile fits and you need to find alternatives

Don't bypass this skill when the decision is non-obvious. Don't invoke it
when the decision is obvious — overhead exceeds value.

### Output

Return a one-line routing decision:
```
[complexity] → [profile] (preset: [budget]) → [execution skill]
```

Example: `COMPLEX → researcher → architect → implementer → reviewer (preset: strict) → subagent-driven-development`

### Role Bottleneck Awareness (AgentCARD)

Heterogeneous teams improve accuracy by up to 44% over cost-equivalent homogeneous
teams, and match the strongest homogeneous team at up to 12x lower per-task cost
(arXiv:2606.20629). Bottlenecks are **domain-dependent** and **model-agnostic**:

| Task type | Bottleneck role | Routing implication |
|---|---|---|
| Debugging (SWE-bench-like) | **Planner/architect** (φ_P = +29%) | Use stronger model in architect role |
| Document analysis (FinanceBench-like) | **Executor/reviewer** (φ_E = +34%) | Use stronger model in reviewer role |
| Research (IMO-AnswerBench-like) | **Executor** (φ_E = +34%) | Use stronger model in researcher role |

**How to apply:** When routing, identify which role is critical for the task type.
Assign the strongest available model to the bottleneck role. Assign cheaper models
to non-critical roles. This is orthogonal to complexity-based routing — a simple
task can still have a bottleneck role that needs a strong model.

**Source:** AgentCARD (arXiv:2606.20629). Uses Shapley values to identify role
bottlenecks. Preprint (not peer-reviewed) — findings are directional, not definitive.
