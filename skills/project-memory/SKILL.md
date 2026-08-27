---
name: project-memory
description: Use when the session produces knowledge worth remembering across sessions, such as answered user questions, business rules, project conventions, failed approaches, reusable solutions, or decisions. Captures it with user approval and stores it as plain-text notes inside .devin/ for future retrieval.
---

# Project Memory

Cross-session memory for Devin CLI, stored as plain-text, user-auditable notes inside `.devin/`.

## When to use

- User answers a question that resolves ambiguity (fiscal quarters, naming convention, scope, etc.).
- A project convention, constraint, or business rule is discovered.
- A decision is made and needs rationale preserved.
- A fix or approach failed and should not be retried.
- A reusable pattern or workaround is found.
- Ending a session and summarizing what matters for the next one.

## When NOT to use

- Short, self-contained tasks — keep stateless.
- Preferences that belong in AGENTS.md or skills.
- Secrets, credentials, or sensitive values.

## Core pattern

1. **Notice**. Spot something that future sessions or other agents will need.
2. **Propose**. Use `ask_user_question` to show the captured note and storage path. Wait for approval.
3. **Write**. On approval, save a Markdown note under `.devin/memory/`.
4. **Link**. Update `.devin/memory/MOC.md` and the relevant daily/logbook entry.
5. **Retrieve**. Use `python .devin/memory/scripts/query-memory.py "<query>"` or `/deep-mode` scoped to `.devin/memory/`.

## Quick reference

| What to capture | Exact path | Filename pattern |
|---|---|---|
| Answered question / business rule | `.devin/memory/notes/YYYY/MM/<topic>.md` | `<topic>.md` |
| Daily session log | `.devin/memory/logbook/YYYY/MM/YYYY-MM-DD.md` | `YYYY-MM-DD.md` |
| Decisions / ADRs | `.devin/memory/decisions/ADR-NNN-<slug>.md` | `ADR-NNN-<slug>.md` |
| Index | `.devin/memory/MOC.md` | `MOC.md` |

For the fiscal-quarters example on 2026-08-27, the note path is `.devin/memory/notes/2026/08/fiscal-quarters.md`.

## Note format

See `templates/note.md` for the full note template and a concrete example.

Required frontmatter: `title`, `date`, `session`, `category`, `tags`, `status`, and `cues:` (path/symbol/keyword triggers).

## Rules

1. **No capture without approval.** Always use `ask_user_question` to confirm the note text and path before writing.
2. **Plain text, plain structure.** No vector DB, no embeddings. Markdown + frontmatter + grep.
3. **One fact per note.** Notes are small and linkable; the MOC groups them.
4. **Cite sources.** Every claim must have `source: path:line` or `session:` reference.
5. **Write cues, not just facts.** Frontmatter `cues:` tells future agents when to recall this.
6. **Prune stale notes.** On each capture, review `MOC.md` for outdated entries and mark `status: archived` or delete.
7. **User owns the contract.** Notes must be viewable, editable, and deletable by the user; never hide them.

## Common mistakes

- **Auto-saving every user answer.** Captures noise and causes contamination. Ask first.
- **Dumping into one giant MEMORY.md.** Becomes unsearchable and drifts.
- **No cues.** A note without `cues:` is unlikely to be retrieved at the right moment.
- **Storing secrets.** Memory files are project-tracked; never put credentials there.

## Red flags

- "I'll just remember this for next time" — no, write it or lose it.
- "The user already told me once, I don't need approval" — always ask before persisting.
- "One big file is easier" — it is not.

## Scripts

- `python .devin/memory/scripts/capture-memory.py --note <file> --update-moc`
- `python .devin/memory/scripts/query-memory.py "<query>"`
- `python .devin/memory/scripts/audit-memory.py`

## Evidence

- arXiv:2505.16067: selective add+delete beats naive memory growth by ~10%.
- arXiv:2605.07313 / 2605.17830: naive accumulation causes 16-20pp reliability loss and temporal contamination.
- arXiv:2607.20972: voluntary memory use ≈ 0; effective memory is harness-owned and cue-anchored.
- arXiv:2606.12329 (PROJECTMEM): event-sourced, plain-text project memory with deterministic pre-action judgment.
