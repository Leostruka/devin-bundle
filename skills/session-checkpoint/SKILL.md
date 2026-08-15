---
name: session-checkpoint
description: Use when a session needs to be preserved for later continuation, when the user wants to pause and resume work across CLI exits, or when emulating PrimeAgent's daemon-backed session reattach within Devin CLI's single-process runtime.
---

# Session Checkpoint (Cross-Session Continuation)

## When to Use

- Session is complex and may be interrupted (CLI exit, crash, compaction)
- User wants to pause work and resume in a new session
- Before `/compact` when the full trajectory matters for continuation
- Long-running tasks that span multiple CLI invocations
- Emulating PrimeAgent's `prime-agent attach <id>` pattern

## When NOT to Use

- Simple task that completes in one session — just finish it
- Session is already compacted and the summary suffices — use the summary
- No meaningful state to preserve — starting fresh is cleaner

## Source

Adapts PrimeAgent's daemon-backed sessions (PrimeIntellect blog, 2026-08-05).
PrimeAgent has a background daemon that owns all sessions via local socket.
`prime-agent attach <id>` reattaches to a running session. Workers recover from
JSONL + kernel state snapshots. Devin CLI has no daemon — sessions live in the
CLI process and end on exit. This skill emulates reattach via checkpoint files.

## Core Concept

**A checkpoint is a structured snapshot of session state.** It captures:
- What was done (completed todos)
- What remains (pending todos)
- Key decisions made (with rationale)
- Files modified (with paths)
- Context needed to resume (compacted summary + key facts)
- Verification status (what passed, what's pending)

The checkpoint is written to a file. A new session reads it and resumes.

## Checkpoint Format

```json
{
  "id": "ckpt-001",
  "created": "2026-08-15T15:30:00-03:00",
  "session": "PrimeAgent feature adaptation",
  "status": "in-progress",
  "todos": {
    "completed": ["Map improvements vs architecture", "Create context-folding skill"],
    "pending": ["Implement a2a-mailbox", "Final audit"],
    "in_progress": "Implement session-checkpoint"
  },
  "decisions": [
    {"decision": "Depth=1 only for context-folding", "rationale": "arXiv:2603.02615: depth=2 causes overthinking"},
    {"decision": "File-based A2A instead of IPC", "rationale": "Devin CLI has no daemon"}
  ],
  "files_modified": [
    "C:\\Users\\leand\\AppData\\Roaming\\devin\\skills\\context-folding\\SKILL.md",
    "C:\\Users\\leand\\AppData\\Roaming\\devin\\skills\\refine\\SKILL.md"
  ],
  "verification": {
    "passed": ["AGENTS.md sync", "hooks.v1.json valid", "skill count match"],
    "pending": ["a2a-mailbox skill creation", "heartbeat skill creation"]
  },
  "key_facts": [
    "Rule 12 and 13 added to AGENTS.md",
    "4 new skills created: context-folding, refine, autonomous-gates, primeagent-reference",
    "post-compaction-reminder updated with rules 7-10",
    "check-push-green.py updated with .NET detection"
  ],
  "next_actions": [
    "Create a2a-mailbox skill",
    "Create session-checkpoint skill",
    "Create heartbeat skill",
    "Run final audit"
  ]
}
```

## Workflow

### Step 1: Write checkpoint before exiting

When the session is interrupted or the user wants to pause:

```
write .devin/checkpoints/ckpt-<NNN>.json <checkpoint JSON>
```

Also write a marker so the next session knows to resume:

```
write .devin/.resume-pending "checkpoint: .devin/checkpoints/ckpt-<NNN>.json"
```

### Step 2: Resume in new session

At the start of a new session, check for pending checkpoints:

```
exec: if exist .devin\.resume-pending (type .devin\.resume-pending)
```

If a checkpoint exists, read it:

```
read .devin/checkpoints/ckpt-<NNN>.json
```

### Step 3: Reconstruct state

From the checkpoint, reconstruct:
1. **Todo list** — recreate from `todos` field, mark completed ones as completed
2. **Decisions** — load as context (don't re-decide)
3. **Files modified** — verify they still exist and match expected state
4. **Verification** — re-run any pending checks
5. **Next actions** — start from the first pending action

### Step 4: Verify checkpoint accuracy

Per Rule 12: don't trust the checkpoint blindly. Verify:
- Files listed as modified actually exist
- Completed todos are actually done (spot-check)
- Verification status matches reality (re-run if uncertain)

### Step 5: Continue work

Resume from `next_actions`. Update the checkpoint as you progress.

### Step 6: Clean up on completion

When the task is fully complete:

```
exec: rm .devin/.resume-pending
```

Keep the checkpoint file for reference, or archive it:

```
exec: mv .devin/checkpoints/ckpt-<NNN>.json .devin/checkpoints/archive/
```

## Integration with Existing Skills

- **`handoff` skill:** compacts the full conversation into a document. This
  skill is more structured — it captures specific fields for resumption.
  Use `handoff` for full context; use `session-checkpoint` for structured resume.
- **`refine` skill:** before checkpointing, run refine to extract lessons.
  Lessons go into the checkpoint's `key_facts` field.
- **`verification-before-completion` skill:** verification status in the
  checkpoint follows VF definitions from that skill.

## Limitations vs PrimeAgent Daemon

| Feature | PrimeAgent | Session Checkpoint (this skill) |
|---|---|---|
| Background daemon | Yes (socket server) | No (file-based) |
| Real-time reattach | Yes (session still running) | No (session ended) |
| Kernel state recovery | Yes (JSONL + snapshot) | No (only structured state) |
| Agents View (running/idle/inactive) | Yes | No (manual file check) |
| Worker recovery | Yes (automatic) | No (manual resume) |
| Cross-machine sync | Yes (via daemon) | Yes (via devin-bundle git) |

## Anti-Patterns

- **Don't checkpoint every action.** Checkpoint at natural pause points (task boundaries, before exit).
- **Don't skip verification of checkpoint accuracy.** Files may have changed since the checkpoint was written.
- **Don't use checkpoints as the primary work product.** The work product is the code/docs/skills. The checkpoint is a resume aid.
- **Don't forget to clean up.** Stale `.resume-pending` markers cause confusion in new sessions.
- **Don't checkpoint without running refine first.** Lessons may be lost if not extracted before checkpointing.

## Evidence Summary

| Claim | Source | Status |
|---|---|---|
| PrimeAgent daemon owns sessions via socket | PrimeAgent blog | Verified |
| `prime-agent attach <id>` reattaches | PrimeAgent blog | Verified |
| Workers recover from JSONL + kernel snapshots | PrimeAgent blog | Verified |
| Agents View lists running/idle/inactive | PrimeAgent blog | Verified |
| Devin CLI has no background daemon | Devin CLI docs (self-extend skill) | Verified |
