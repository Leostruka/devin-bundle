# Note template

```markdown
---
title: "<concise title>"
date: "YYYY-MM-DD"
session: "<session-id-or-trace>"
category: [question|convention|decision|failure|solution]
tags:
  - <tag>
status: active
cues:
  - path: "src/<file>.ext"
  - symbol: "<function/name>"
  - keyword: "<term>"
---

# <title>

## What was learned
<2-3 sentences, no speculation.>

## Source
- `source: <path>:<line>`
- User answer from session `<session>`.

## When this applies
<Trigger conditions: which files, terms, or situations should recall this.>

## Related
- [[MOC]]
- [[logbook/YYYY/MM/YYYY-MM-DD|Daily note]]
- [[other-note]]
```

# Example: answered question

User said: "For this project, we always use fiscal quarters ending in January, April, July, and October."

Proposed note path: `.devin/memory/notes/2026/08/fiscal-quarters.md`

```markdown
---
title: "Fiscal quarters end in Jan/Apr/Jul/Oct"
date: "2026-08-27"
session: "<trace>"
category: convention
tags:
  - quarter
  - fiscal
  - convention
status: active
cues:
  - keyword: "quarter"
  - keyword: "fiscal"
  - keyword: "Q1"
---

# Fiscal quarters end in Jan/Apr/Jul/Oct

## What was learned
This project uses fiscal quarters ending in January, April, July, and October, not calendar quarters.

## Source
- User answer from session `<trace>`.

## When this applies
Any code or report that computes or labels quarters.

## Related
- [[MOC]]
- [[logbook/2026/08/2026-08-27|Daily note]]
```
