---
name: handoff
description: Use when the user needs to compact the current conversation into a document for another agent to continue.
argument-hint: What will the next session be used for?
triggers: [user]
---
Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Use this structure (adapted from the `devin acp` summarizer schema, eval #455):

```
## Overview
<2-3 sentences: what was being done and the outcome so far>

## Key Details & Breadcrumbs
- <file path>: <what it contains / what changed, with line refs where useful>
- <command or artifact>: <result worth re-checking>

## Current State
<where the work stands right now: pending items, blockers, next step>

## Suggested skills
- <skills the next agent should invoke>
```

Breadcrumbs are the contract: every file or artifact the next agent needs appears as a path it can re-read, not a retelling of its contents.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

**Cross-skill:** If the handoff captures a decision, convention, or gotcha worth remembering across sessions, also invoke `memory-management` with the user's approval.

**Cross-skill:** Inside `adaptive-agenda-calendar-routine-engine`, this document is the artifact the block-transition handoff rite requires between HH:MM-HH:MM blocks.
