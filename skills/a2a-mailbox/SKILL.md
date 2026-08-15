---
name: a2a-mailbox
description: Use when subagents need to communicate with each other or with the parent agent across time, when dispatching sequential subagents that need to share state, or when emulating PrimeAgent's persistent subagent A2A messaging within Devin CLI's ephemeral subagent runtime.
---

# A2A Mailbox (File-Based Subagent Communication)

## When to Use

- Two or more subagents need to share findings with each other
- A subagent needs to send results back to the parent asynchronously
- Sequential subagents need to pass state (agent B reads what agent A produced)
- Emulating PrimeAgent's `agent_message.send()` pattern within Devin CLI

## When NOT to Use

- Single subagent, single return — just use `run_subagent` normally
- Subagents are truly independent (no shared state) — use `dispatching-parallel-agents`
- Real-time bidirectional messaging is needed — Devin CLI can't do this; use the workaround below

## Source

Adapts PrimeAgent's A2A messaging (PrimeIntellect blog, 2026-08-05). PrimeAgent
subagents communicate via `agent_message.send()` with persistent handles. Devin
CLI subagents are ephemeral (`run_subagent` returns once, no handle). This skill
emulates the pattern using the filesystem as a message broker.

## Core Concept

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

## Message Format

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

## Workflow

### Step 1: Set up mailboxes

Before dispatching subagents, create the mailbox structure:

```
exec: mkdir -p .devin/mailboxes/parent/inbox .devin/mailboxes/parent/outbox .devin/mailboxes/subagent-a/inbox .devin/mailboxes/subagent-a/outbox
```

### Step 2: Write task messages to subagent mailboxes

```
write .devin/mailboxes/subagent-a/inbox/msg-001.json {"id":"msg-001","from":"parent","to":"subagent-a","type":"task","content":"Analyze /tmp/chunk_aa for references to X.","status":"unread"}
```

### Step 3: Dispatch subagent with mailbox instructions

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

### Step 4: Parent reads results from inbox

After subagent returns, the parent reads its inbox:

```
exec: ls .devin/mailboxes/parent/inbox/
read .devin/mailboxes/parent/inbox/msg-001.json
```

### Step 5: Forward between subagents (sequential)

To pass findings from subagent A to subagent B:

```
read .devin/mailboxes/parent/inbox/msg-001.json   # A's result
write .devin/mailboxes/subagent-b/inbox/msg-001.json {"id":"msg-001","from":"subagent-a","to":"subagent-b","type":"forward","content":"<A's findings>","status":"unread"}
```

Then dispatch subagent B with the same mailbox instructions.

### Step 6: Verify subagent returns (Rule 12)

Per Rule 12: do not trust subagent returns without verification. The mailbox
pattern makes this easier — check that the subagent actually wrote to the
mailbox, and that the content matches what it reported verbally.

### Step 7: Clean up

After all messages are processed:

```
exec: rm -rf .devin/mailboxes/
```

Or keep for debugging if the session is complex.

## Limitations vs PrimeAgent A2A

| Feature | PrimeAgent | A2A Mailbox (this skill) |
|---|---|---|
| Real-time messaging | Yes (socket) | No (file polling) |
| Bidirectional during execution | Yes | No (subagent runs to completion) |
| Persistent handles | Yes | No (ephemeral subagents) |
| Cross-compaction survival | Yes | No (files persist, but subagent is gone) |
| Multi-agent concurrent chat | Yes | No (sequential only) |
| Nuclear family (parent/sibling/child) | Yes | Emulated via file routing |

## Anti-Patterns

- **Don't poll files during subagent execution.** Subagent runs to completion; read mailbox after return.
- **Don't use this for single subagent tasks.** Overhead exceeds value. Use `run_subagent` directly.
- **Don't forget to verify mailbox content.** Subagent may report success but not write the file. Check.
- **Don't leave mailboxes across sessions.** Clean up or they accumulate stale messages.
- **Don't use this for depth=2+ communication.** Depth=1 only per context-folding skill.

## Evidence Summary

| Claim | Source | Status |
|---|---|---|
| PrimeAgent A2A via `agent_message.send()` | PrimeAgent blog | Verified |
| Subagents have persistent handles | PrimeAgent blog | Verified |
| Nuclear family communication (parent/sibling/child) | PrimeAgent blog | Verified |
| Devin CLI subagents are ephemeral | Devin CLI docs (self-extend skill) | Verified |
| Filesystem as message broker is standard pattern | Standard CS practice | N/A (adaptation) |
