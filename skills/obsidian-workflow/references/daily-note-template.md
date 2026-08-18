# Daily Note / Logbook Template

Each daily note is a small running log. It captures what happened, why, and what comes next. It acts as a lightweight version of the project history.

## File naming

Obsidian daily note: `Daily/YYYY-MM-DD.md`

Example: `Daily/2026-08-11.md`

## Template

```markdown
---
title: "{{PROJECT_NAME}} — {{DATE}}"
date: "{{DATE}}"
parent: 10-Logbook
tags:
  - logbook
  - {{PROJECT_TAG}}
---

# {{DATE}}

## Relevant source files
- `source: path/to/source/file.ext:line`

## Context
_What is the current focus of the project / sprint / task?_

## Done
- _Finished item with link to commit/PR/note_

## Tried
- _Approach or experiment attempted_

## What worked
- _Why it worked; link to evidence_

## What failed / blocked
- _What did not work, why, and what was learned_

## Decisions made
| Decision | Rationale | Consequences | ADR / note |
|----------|-----------|--------------|------------|
| _Decision text_ | _Why this way_ | _What it locks in or opens up_ | [[09-Decisions]] |

## Open questions
- _Questions for later_

## Next
- _Next action(s) for the next session_

## Links
- [[10-Logbook]]
- [[01-SRS]]
- [[02-Architecture]]
```

## Capture discipline

- Write the log **at the end of each session**, not at the start.
- Every decision gets a rationale. If the rationale is unknown, write "rationale TBD".
- Every failure gets a lesson. If no lesson yet, write "investigate why".
- Link to notes, commits, PRs, diagrams. Use wikilinks.
- Use tags to group log entries: `#decision`, `#blocker`, `#try`, `#success`, `#revert`.

## Aggregating in 10-Logbook.md

The `10-Logbook.md` note is an index. It does not duplicate entries; it links to each daily note:

```markdown
## Activity log

### [[2026-08-11]]
- Initial modeling session

### [[2026-08-12]]
- Implemented core logic
```
