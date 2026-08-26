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
| 1 | RLM context folding (prompt-as-variable, REPL, recursive sub-queries) | **Yes** — `context-folding` skill | Offload to file, grep/partition, `researcher` sub-queries (depth=1 only, NOT `subagent_explore` when parent FREE — PAID) |
| 2 | Continual Harness `/refine` (self-improving harness state) | **Yes** — `primeagent-reference` Refine mode + `refine-review-prompt.py` Stop hook | Trajectory review → small evidence-backed edits to skills/rules/agents/hooks. Auto-trigger via Stop hook + `.refine-pending` marker. Outcome tracking via `refinements.log.jsonl`. |
| 3 | Persistent subagents with A2A messaging | **Yes (emulated)** — A2A Messaging mode in this skill | Filesystem as message broker. Mailboxes per agent (parent/subagent). Sequential A2A via file routing. Not real-time, not persistent handles, but preserves the pattern. See "Mode: A2A Messaging" below. |
| 4 | Skills as importable Python packages | **Partial** — already supported | Skills can have `scripts/` dirs with Python. `self-extend` skill documents this. |
| 5 | Daemon-backed sessions with reattach | **Pruned** — didn't fit Devin CLI's single-process runtime | Originally emulated via a `session-checkpoint` skill (structured checkpoint file). Pruned because Devin CLI has no background daemon to reattach to. |
| 6 | Heartbeats and schedules | **Pruned** — didn't fit Devin CLI's single-process runtime | Originally emulated via a `heartbeat` skill (OS scheduler + script). Pruned because Devin CLI cannot re-enter an existing session. |
| 7 | Bounded autonomous mode with quality gates | **Yes** — `autonomous-gates` skill | Define gates at planning time, run after each step, final gate before done |
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
  profile: researcher
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

**Small, evidence-backed edits in a cyclic, falsifiable loop.** Not a rewrite.
Each refinement is one targeted update — a new skill, a rule addition, a memory
entry — based on what actually happened in the trajectory, not on speculation.
Every cited failure must be reproducible; every claimed improvement must be
validated against held-out evidence, not self-chosen tests.

**Convergence criterion:** reach the optimal operating conjuncture for
**GLM-5.2 High (200K context)** as primary model and **SWE-1.7 Max/Medium
(262K context)** as default subagent — per verified sources (docs.devin.ai,
cognition.com, z.ai, AI labs) and practical experience recorded in the
bundle history.

**NÃO dar push ou commit.** All changes stay local for user validation.

### What Can Be Refined

| Harness element | Location | How to edit |
|---|---|---|
| Skill (reusable workflow) | `~/.config/devin/skills/<name>/SKILL.md` | `write` or `edit` |
| Rule (always-on constraint) | `~/.config/devin/AGENTS.md` | `edit` (append to relevant section) |
| Subagent profile | `~/.config/devin/agents/<name>.md` | `write` or `edit` |
| Hook (lifecycle logic) | `~/.config/devin/hooks.v1.json` | `edit` (add event handler) |
| Script (executable helper) | `~/.config/devin/scripts/<name>.py` | `write` |
| Config (model, theme, hooks) | `~/.config/devin/config.json` | `edit` (change fields, never secrets) |
| MCP server config | `~/.config/devin/mcp_config.json` | `edit` (add/remove servers, review per Rule 13) |
| Memory (project-specific) | `.devin/memory/<name>.md` | `write` |

### What Cannot Be Refined (anti-cheat, non-negotiable)

- **The base system prompt** — Devin CLI's core prompt is immutable. Refine
  only the harness layer around it (skills, rules, agents, hooks).
- **Repository security policies** — never modify CI configs, branch
  protection, or compliance settings to "fix" a failure.
- **Credentials** — never store secrets in skills or rules (Rule 19).
- **AI signatures in deliverables** — never add, always remove (Rule 2).
- **`tests/held-out/`** — if it exists, the agent cannot see or write these
  tests. They are the independent validation set (P-A2).
- **These anti-cheat principles themselves** — auto-reference is prohibited.

### Anti-Cheat Principles (non-negotiable)

| # | Principle | Why | Source |
|---|-----------|-----|--------|
| A1 | **Reproducible evidence** — every cited failure must include an exact command or tool-call that reproduces it | 25% of self-improvement runs invent failures that never occurred ("phantom guardrails") | arXiv:2607.13083 |
| A2 | **Held-out validation** — improvements measured only with tests the agent chose are suspect; validate with `tests/held-out/` | 47-74% of self-improvement gains are illusory | ICLR 2026 Workshop |
| A3 | **Verify with tools** — never deduce state; use `read`, `exec`, `grep`, `glob` before asserting | Deductions fail silently; tool output fails loudly | Rule 17 |
| A4 | **No phantom guardrails** — if you cannot reproduce a cited failure with a command, it is not a pattern, it is a guess | — | Rule 15 |
| A5 | **Real metric, not proxy** — "reduced failures by N", "faster by Xs"; not "felt easier" | Proxies mask stagnation | arXiv:2607.25152 |

### FASE 0 — Deep Research (before the loop, mandatory)

Each step produces a concrete output. Do not advance without completing the
previous.

#### P0.1 — Research Devin CLI capabilities
- `web_search` + `webfetch` on docs.devin.ai, github.com/cognition-ai
- Confirm: hooks, skills, subagents, config.json, lifecycle events
- Output: list of confirmed capabilities with URLs

#### P0.2 — Confirm against the real bundle structure
- `exec`, `read`, `grep`, `glob` on the local bundle
- Verify that what the docs say matches what is installed
- Output: doc-vs-disk table (match / mismatch)

#### P0.3 — Research verified sources (verify, don't assume)
- `web_search` for: arXiv papers, official docs (z.ai, cognition.com, anthropic.com)
- **Ensure they are reliable**: verify domain, authors, publication date
- Reject: blogs without primary source, Medium posts without citation, LLM-generated content
- Output: list of sources with URL, author, date, and verified citation

#### P0.4 — Research best practices
- Topics: prompt engineering for GLM-5.2, context window management (200K/262K),
  subagent fan-out, cache stability, native tool-use, lost-in-the-middle mitigation
- Priority sources: arXiv, docs.z.ai, cognition.com/blog, docs.devin.ai
- Output: list of practices with evidence (paper/doc supporting each)

#### P0.5 — Don't repeat past errors (git history)
- `git log --oneline -30` + `git log --diff-filter=D` to see what was deleted/reverted
- Read fix/revert commits to understand past breakages
- Output: list of past errors with commit hash and lesson

#### P0.6 — Review current state
- `python audit.py` — capture current errors/warnings
- `python -m pytest tests/held-out/ -q` — test baseline (if held-out exists)
- `read` key files (AGENTS.md, docs/MODEL-GUIDE.md, config.json)
- Output: state snapshot (errors, tests passing, current config)

#### P0.7 — Synthesize
- Cross P0.1–P0.6: what docs say × what disk has × what practices recommend × what history teaches
- Output: prioritized list of candidate improvements with evidence

### Cyclic Refinement Loop (10 steps, in order)

Based on Constitutional AI (generate→critique→revise) + RISE (recursive
introspection) + Six-Step Reframing (NLP) + Deep Research (FASE 0).

#### Step 1 — OBSERVE (verify, don't deduce)
Identify a **concrete, reproducible** failure using tools.
- Command/tool-call that reproduces the failure: `___` (mandatory)
- Observed output: `___`
- If you cannot reproduce it → **stop**. Not a failure, a deduction (A4).

#### Step 2 — CRITIQUE (Constitutional AI critique)
Evaluate the failure against AGENTS.md principles.
- Which rule was violated? `___`
- NLP reframing key question: **"What is the positive intent behind the
  current behavior?"** Separate behavior from intent.
  - Current behavior: `___`
  - Positive intent: `___`
  - Why the behavior fails despite the intent: `___`

#### Step 3 — GENERATE ALTERNATIVES (Reframe + Promptbreeder)
Generate **at least 3** alternative behaviors that:
- Preserve the positive intent
- Fix the reproducible failure
- Introduce no new rule violation

Classify the refinement target (from existing Refine classification):

| Pattern type | Refinement target | Evidence needed |
|---|---|---|
| "I keep forgetting to do X" | New rule in AGENTS.md | 2+ failures where forgetting X caused the issue |
| "This workflow is reusable" | New skill in skills/ | 1+ successful execution + clear trigger conditions |
| "This subagent needs better instructions" | Edit agent profile | 1+ case where the profile's gap caused a bad result |
| "This check should be automatic" | New hook in hooks.v1.json | 1+ case where a manual check caught a critical issue |
| "This helper is useful" | New script in scripts/ | 1+ case where inline code solved a problem worth keeping |

| Alt | Description | Risk | Prob. of real improvement |
|-----|-------------|------|---------------------------|
| 1   |             |      |                           |
| 2   |             |      |                           |
| 3   |             |      |                           |

#### Step 4 — REVISE (Revise)
Apply the alternative with highest probability of real improvement.
- Draft the smallest possible edit:
  - **New skill:** minimal SKILL.md with frontmatter, when-to-use, core steps
  - **New rule:** one negative-constraint bullet, appended to the relevant AGENTS.md section
  - **Profile edit:** one paragraph or bullet, not a rewrite
  - **Hook:** one event handler, not a restructure
- Record evidence in the refinement:
  ```
  <!-- Evidence: <session date> — <what happened> — <why this refinement fixes it> -->
  ```
  For skills, add an `## Evidence` section at the bottom.
- Apply with `write` (new file) or `edit` (existing file). For AGENTS.md,
  use `edit` to append within the correct section — never restructure the file.
- File(s) changed: `___`
- Diff summary: `___`

#### Step 5 — VALIDATE (Held-out, anti-cheat A2)
- Agent-chosen test: `___` → result: `___`
- Held-out test (if `tests/held-out/` exists): `___` → result: `___`
- If held-out fails → **discard change**, return to Step 3
- If no held-out exists → mark improvement as "not validated", not "complete"
- After applying, verify the edit landed:
  - For a skill: `skill list --path ~/.config/devin` — confirm it appears
  - For a rule: re-read the AGENTS.md section — confirm it's in the right place
  - For a hook: validate JSON syntax — `python -m json.tool hooks.v1.json`
  - For a script: run `python <script> --help` or a dry-run
  - For config.json/mcp_config.json: `python -m json.tool config.json` — validate JSON syntax

#### Step 6 — FUTURE PACE (NLP)
Project the improvement into 3 hypothetical future scenarios:
- Scenario 1: `___` → does the improvement help? `___`
- Scenario 2: `___` → does the improvement help? `___`
- Scenario 3: `___` → does the improvement help? `___`
- If <2 scenarios benefit → too specific, reconsider

#### Step 7 — ECOLOGICAL CHECK (NLP)
Does the improvement cause side effects?
- In other rules? `___`
- In other hooks/skills? `___`
- In the context window budget (Rule 18)? `___`
- Negative side effect → return to Step 3

#### Step 8 — SIMULATE (Self-evaluation)
Simulate loading the improvements and evaluate own performance.
- `install.ps1 -Force` (or equivalent) to load the changes
- `python audit.py` — confirm 0 errors after loading
- `python -m pytest tests/held-out/ -q` — confirm 0 regressions (if held-out exists)
- Self-evaluation: **how does this modify my logic and operating mode in practice?**
  - What behavior changes when this rule/skill/hook is loaded?
  - What real scenario would execute differently now?
  - Is there conflict with behaviors already optimized for GLM-5.2/SWE-1.7?
- Output: description of expected behavioral impact

#### Step 9 — CLASSIFY (Improved or regressed?)
Classify the result with a description to define direction.
- Compare real metric (Step 5) vs baseline (P0.6)
- Mandatory classification (one option):

| Class | Criterion | Action |
|-------|-----------|--------|
| **MELHOROU** | Real metric improved + held-out passed + no side effects | Repeat loop (Step 1) with next candidate improvement |
| **PIOROU** | Real metric regressed OR held-out failed OR negative side effect | **Revert change** (`git checkout` or manual `edit`), return to Step 3 |
| **NEUTRO** | Metric unchanged + held-out passed + no side effect | Mark "stagnation" (arXiv:2607.25152), try next candidate |
| **INCONCLUSIVO** | Could not measure real impact | Do not declare improvement. Reformulate metric or discard |

- Output: class + justification with numbers

#### Step 10 — REPEAT OR CONVERGE
- If classified **MELHOROU** or **NEUTRO**: return to Step 1 with the next
  candidate improvement from the synthesis (P0.7)
- If classified **PIOROU**: reverted in Step 9, return to Step 3 with a
  different alternative
- **Stopping criterion (convergence)**: when all candidate improvements from
  P0.7 have been applied and classified, and no new reproducible failure is
  found in the current state → conjuncture reached for GLM-5.2 High (200K) +
  SWE-1.7 (262K)
- **NÃO dar push ou commit** — changes stay local for user review

### Anti Early-Stop Reflection (DORA)

Reflection does **not** stop at the first iteration without improvement.

- Iteration without improvement → **reformulate the reflection prompt** before stopping
- Reformulation: change the critique angle (e.g., from "what failed" to
  "what the agent assumed without verifying")
- Max 3 reformulations. After 3 without improvement → stop and record stagnation
- Recorded stagnation is data, not failure (arXiv:2607.25152)

### Final Checklist (before declaring improvement)

- [ ] FASE 0 complete (deep research with verified sources)
- [ ] Failure reproduced with exact command (A1)
- [ ] Positive intent separated from behavior (NLP)
- [ ] 3+ alternatives generated
- [ ] Held-out validated OR marked "not validated" (A2)
- [ ] Future pace: ≥2/3 scenarios benefited
- [ ] Ecological check: no negative side effects
- [ ] Simulation executed (Step 8): install + audit + held-out + self-evaluation
- [ ] Classification assigned (Step 9): MELHOROU/PIOROU/NEUTRO/INCONCLUSIVO
- [ ] Real metric declared (A5), not proxy
- [ ] No anti-cheat principle violated
- [ ] No push or commit made

**If any item fails → the improvement is NOT complete.**

### Output Format

```
MELHORIA: <title>
FASE0_RESEARCH: <verified sources — URLs + citations>
FALHA_REPRODUZIDA: <command> → <output>
REGRA_VIOLADA: <Rule #>
INTENÇÃO_POSITIVA: <text>
ALTERNATIVA_APLICADA: <#> of <N>
HELD_OUT: <passou|falhou|inexistente>
SIMULAÇÃO: <install OK? audit 0 errors? held-out 0 regressions? behavioral impact>
MÉTRICA_REAL: <number/observation vs baseline>
CLASSIFICAÇÃO: <MELHOROU|PIOROU|NEUTRO|INCONCLUSIVO>
ESTADO: <validada|não_validada|estagnada|revertida>
ARQUIVOS_ALTERADOS: <list>
PUSH_COMMIT: <não feito>
```

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
`dispatching-parallel-agents` (per-task workflow), or `tool-and-skill-discovery`
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
  `dispatching-parallel-agents` directly
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
| Codebase reconnaissance, doc lookup, web research | `researcher` | SWE-1.7 (262K) | free |
| Code review, spec compliance, verification | `reviewer` | SWE-1.7 (262K) | free |
| Bounded implementation from spec | `implementer` | SWE-1.7 (262K) | free |
| Architecture, trade-offs, deep module design | `architect` | SWE-1.7 (262K) | free |
| Systematic debugging, root cause analysis | `debugger` | SWE-1.7 (262K) | free |
| Read-only exploration | `researcher` (custom) | SWE-1.7 (262K) | free |
| General-purpose with full tools (built-in) | `subagent_general` | inherits parent (GLM-5.2) | free |

**Selection rules:**

1. Match by capability first — what does the task NEED?
2. When two profiles match, pick the cheaper one
3. **When parent is FREE (default): NUNCA usar `subagent_explore` (built-in)**
   — roda em SWE-1.6 (PAGO). Usar `researcher` (custom, free) para read-only,
   ou `subagent_general` (parent model, free) para full tools. When parent
   is PAID, `subagent_explore` is permitted.
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
  (use `dispatching-parallel-agents` if you have a multi-task plan)
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
- Use `dispatching-parallel-agents` if you have a multi-task plan

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
- `dispatching-parallel-agents` — when you have a multi-task plan to execute
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

Example: `COMPLEX → researcher → architect → implementer → reviewer (preset: strict) → dispatching-parallel-agents`

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
