---
name: memory-management
description: Use when deciding whether to use cross-session agent memory (MEMORY.md, auto-memory), when auto-memory seems stale or preferences leak across tasks, or when the session produces knowledge worth remembering (answered questions, business rules, conventions, failed approaches, decisions). Covers memory hygiene (stateless vs managed vs naive) and capturing plain-text notes under .devin/ with user approval.
triggers: [user, model]
---

# Memory Management

Cross-session memory is a **contract with the user**, not a black box. Naive
accumulation degrades reliability; managed memory helps. Default: **explicit
user-authored preferences** (`.devin/global_rules.md`, skills, repo docs),
not auto-saved memory.

## Stateless vs managed vs naive

| Mode | When | Evidence |
|---|---|---|
| **Stateless** | Default for coding agents. Preferences live in rules/skills/docs the user controls. | Most predictable; no drift or contamination. |
| **Managed memory** (selective add+delete) | Long-horizon tasks where recalling past executions genuinely helps. User reviews and prunes. | +10% absolute vs naive (arXiv:2505.16067); MemGPT (arXiv:2310.08560). |
| **Naive auto-memory** (append-only) | Never. | 16-20pp reliability loss (arXiv:2605.07313); temporal contamination (arXiv:2605.17830); reasoning drift (arXiv:2607.02374). |

## Hygiene rules

1. **Prefer explicit** — user-authored preferences over agent-auto-saved memory.
2. **Never naive growth** — managed memory must have selective add AND delete.
3. **Audit periodically** — review auto-memory for stale/large/drifting entries; prune aggressively.
4. **Isolate preferences by task** — global injection of all preferences into every session causes contamination.
5. **Don't trust auto-inferred preferences** — preference following is <10% at 10 turns zero-shot (arXiv:2502.09597). Write them down.
6. **Memory is a contract** — user must be able to view, modify, delete anything saved (arXiv:2404.15269).

Anti-patterns: append-only MEMORY.md; auto-saving every preference; "delete
all memory" (managed memory helps); opaque memory.

## Capturing project memory

When the session produces knowledge worth keeping — answered questions,
business rules, project conventions, failed approaches, reusable solutions,
decisions:

1. **Notice** — spot something future sessions will need.
2. **Propose** — `ask_user_question` showing the note text and path. Wait for approval.
3. **Write** — on approval, save a Markdown note under `.devin/memory/`.
4. **Link** — update `.devin/memory/MOC.md` and the daily logbook entry.
5. **Retrieve** — `python scripts/query-memory.py "<query>"` (in this skill's
   `scripts/`) or `/deep-mode` scoped to `.devin/memory/`.

### Paths

| What | Path | Pattern |
|---|---|---|
| Answered question / business rule | `.devin/memory/notes/YYYY/MM/` | `<topic>.md` |
| Daily session log | `.devin/memory/logbook/YYYY/MM/` | `YYYY-MM-DD.md` |
| Decisions / ADRs | `.devin/memory/decisions/` | `ADR-NNN-<slug>.md` |
| Index | `.devin/memory/MOC.md` | `MOC.md` |

Note format: see `templates/note.md`. Required frontmatter: `title`, `date`,
`session`, `category`, `tags`, `status`, `cues:` (path/symbol/keyword
triggers).

### Capture rules

1. **No capture without approval** — always confirm via `ask_user_question`.
2. **Plain text** — Markdown + frontmatter + grep; no vector DB.
3. **One fact per note**; cite sources (`source: path:line` or `session:`).
4. **Write cues, not just facts** — `cues:` tells future agents when to recall.
5. **Prune stale notes** on each capture (`status: archived` or delete).
6. **No secrets** in notes (Rules 19, 24).

### Post-implementation capture

After a feature/fix lands and before `clear`/`compact`: capture intent (why),
state (what + deviations), lessons (worked/failed) — then ask approval.

## Evidence

| Claim | Source |
|---|---|
| Naive growth −16-20pp reliability | arXiv:2605.07313 |
| Contamination rises with exposure | arXiv:2605.17830 |
| Selective add+delete +10% vs naive | arXiv:2505.16067 |
| Reasoning drift despite fluent answers | arXiv:2607.02374 |
| Preference following <10% @10 turns | arXiv:2502.09597 |
| Managed memory > fixed context | arXiv:2310.08560 (MemGPT), arXiv:2410.10813 |
| Excessive retrieval harms agentic tasks | arXiv:2608.15008 |
