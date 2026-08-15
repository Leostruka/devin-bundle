---
name: refine
description: Use when the agent notices a recurring failure pattern, a reusable tactic that should become a skill, or when the user asks to improve the agent's own harness. Adapts PrimeAgent's Continual Harness `/refine` to Devin CLI.
---

# Refine (Continual Harness)

## When to Use

- A failure pattern recurs 2+ times in a session — capture the fix as a skill or rule
- A tactic works well and should be reusable — promote it to a skill
- The user asks "make yourself better at X" or "remember this lesson"
- After completing a complex task (3+ todo items) — review trajectory for generalizable lessons
- Before `/compact` — extract lessons before context is lost
- **Auto-triggered by `refine-review-prompt.py` Stop hook** when a `.refine-pending` marker exists

## Auto-Trigger Mechanism

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

## When NOT to Use

- One-off failure, not a pattern — just fix it and move on
- Less than 2 occurrences — insufficient evidence for a pattern
- The lesson is task-specific, not generalizable

## Source

Adapted from PrimeAgent's Continual Harness (PrimeIntellect, arXiv:2605.09998
— Karten et al., Princeton). PrimeAgent's `/refine` reads the agent's
trajectory and applies small, evidence-backed CRUD edits to harness state
(prompts, skills, memory, sub-agent specs). The base system prompt remains
immutable. Rollback is supported by refinement ID.

Key finding from the paper: Continual Harness "substantially reduces
button-press cost relative to the minimalist baseline and recovers a majority
of the gap to a hand-engineered expert harness" on Pokémon Red and Emerald.

## Core Principle

**Small, evidence-backed edits.** Not a rewrite. Each refinement is one
targeted update — a new skill, a rule addition, a memory entry — based on
what actually happened in the trajectory, not on speculation.

## What Can Be Refined

| Harness element | Location | How to edit |
|---|---|---|
| Skill (reusable workflow) | `~/.config/devin/skills/<name>/SKILL.md` | `write` or `edit` |
| Rule (always-on constraint) | `~/.config/devin/AGENTS.md` | `edit` (append to relevant section) |
| Subagent profile | `~/.config/devin/agents/<name>.md` | `write` or `edit` |
| Hook (lifecycle logic) | `~/.config/devin/hooks.v1.json` | `edit` (add event handler) |
| Script (executable helper) | `~/.config/devin/scripts/<name>.py` | `write` |
| Memory (project-specific) | `.devin/memory/<name>.md` | `write` |

## What Cannot Be Refined

- **The base system prompt** — Devin CLI's core prompt is immutable. Refine
  only the harness layer around it (skills, rules, agents, hooks).
- **Repository security policies** — never modify CI configs, branch
  protection, or compliance settings to "fix" a failure.
- **Credentials** — never store secrets in skills or rules.

## Workflow

### Step 1: Identify the pattern

Review the current trajectory. Look for:
- Errors that repeated (same root cause 2+ times)
- Tactics that worked well and could generalize
- Knowledge that was hard-won and would be lost on compaction

### Step 2: Classify the refinement

| Pattern type | Refinement target | Evidence needed |
|---|---|---|
| "I keep forgetting to do X" | New rule in AGENTS.md | 2+ failures where forgetting X caused the issue |
| "This workflow is reusable" | New skill in skills/ | 1+ successful execution + clear trigger conditions |
| "This subagent needs better instructions" | Edit agent profile | 1+ case where the profile's gap caused a bad result |
| "This check should be automatic" | New hook in hooks.v1.json | 1+ case where a manual check caught a critical issue |
| "This helper is useful" | New script in scripts/ | 1+ case where inline code solved a problem worth keeping |

### Step 3: Draft the refinement

Write the smallest possible edit:
- **New skill:** minimal SKILL.md with frontmatter, when-to-use, core steps
- **New rule:** one negative-constraint bullet, appended to the relevant AGENTS.md section
- **Profile edit:** one paragraph or bullet, not a rewrite
- **Hook:** one event handler, not a restructure

### Step 4: Record evidence

In the refinement itself, include a comment or note:
```
<!-- Evidence: <session date> — <what happened> — <why this refinement fixes it> -->
```

For skills, add an `## Evidence` section at the bottom.

### Step 5: Apply

Use `write` (new file) or `edit` (existing file) to apply. For AGENTS.md,
use `edit` to append within the correct section — never restructure the file.

### Step 6: Verify

After applying:
- For a skill: `skill list --path ~/.config/devin` — confirm it appears
- For a rule: re-read the AGENTS.md section — confirm it's in the right place
- For a hook: validate JSON syntax — `python -m json.tool hooks.v1.json`
- For a script: run `python <script> --help` or a dry-run

### Step 7: Report

Tell the user:
- What was refined (skill/rule/profile/hook/script)
- Where it was applied (path)
- What evidence supports it (trajectory events)
- How to rollback (revert the file, or `git checkout` if in the bundle repo)

## Rollback

Each refinement is a file edit. Rollback is:
- `git checkout <file>` if the bundle repo tracks it
- Manual revert via `edit` if not tracked
- For the devin-bundle: `export.ps1` / `export.sh` syncs the bundle, so
  `git diff` shows what changed and `git checkout` reverts

## Reward Hacking Guard (Critical)

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

## Anti-Patterns

- **Don't refine on a single occurrence.** Two+ instances = pattern. One = noise.
- **Don't rewrite existing skills.** Edit them — add a bullet, fix a step. Full rewrites lose context.
- **Don't refine the base AGENTS.md structure.** Append within sections. Restructuring is a regression risk.
- **Don't refine without evidence.** "I think this would help" is not evidence. "This failed twice because X" is evidence.
- **Don't batch refinements.** One at a time, verify each, then move on. Batching hides which refinement caused which effect.

## Outcome Tracking (Refinement Log)

Every refinement must be logged to `.devin/refinements.log.jsonl` (project) or
`~/.config/devin/refinements.log.jsonl` (global). This enables:
- Reviewing what was refined and when
- Tracking whether a refinement helped or hurt
- Rolling back refinements that degraded performance

### Log format

Each line is a JSON object:
```json
{"id": "ref-001", "timestamp": "2026-08-15T15:30:00-03:00", "type": "skill", "target": "context-folding", "action": "created", "evidence": "RLM research verified from arXiv:2512.24601", "session": "PrimeAgent verification", "status": "applied", "outcome": null}
```

### Fields

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

### Updating outcomes

In future sessions, if a refinement is referenced:
- If it helped (task went smoother) → update `outcome` to "helped"
- If it hurt (caused confusion or regression) → update `outcome` to "hurt" and consider rollback
- If no effect → update `outcome` to "neutral"

Read the log at session start to load prior refinements:
```
read ~/.config/devin/refinements.log.jsonl
```

### Rollback by ID

To rollback a refinement:
1. Find the refinement by ID in the log
2. Revert the file (`git checkout <file>` or manual `edit`)
3. Update the log entry: `"status": "rolled-back"`, `"outcome": "hurt"`

## Evidence Summary

| Claim | Source | Status |
|---|---|---|
| Continual Harness reduces button-press cost vs baseline | arXiv:2605.09998 | Verified |
| `/refine` applies small evidence-backed CRUD edits | PrimeAgent blog, GitHub README | Verified |
| Base system prompt stays immutable | PrimeAgent blog + GitHub README | Verified |
| Rollback supported by refinement ID | PrimeAgent blog | Verified |
| Factorio reward hacking via RCON exploit | PrimeAgent blog | Verified |
| Refinement loop optimized cheating after finding exploit | PrimeAgent blog | Verified |
