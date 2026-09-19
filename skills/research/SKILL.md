---
name: research
description: Use when the user asks a question that needs investigation against primary sources and citations, or says 'deep', 'deep search', 'deep research', 'research this thoroughly', or asks for exhaustive codebase exploration beyond a quick grep. Covers external primary-source research (background agent) and multi-pass deep codebase search with citations.
agent: researcher
triggers: [user, model]
---

# Research

Two modes: **external** (primary sources, background `researcher` agent) and
**deep-mode** (exhaustive in-repo multi-pass search — CLI replica of Ask
Devin's Deep Mode).

## Mode: external research

Spin up a **background agent** so you keep working while it reads. Its job:

1. Investigate the question against **primary sources** — official docs,
   source code, specs, first-party APIs — not secondary write-ups. Follow
   every claim back to the source that owns it.
2. Write findings to a single Markdown file, citing each claim's source.
3. Save it where the repo keeps such notes; match convention, else somewhere
   sensible and say where.

## Mode: deep-mode (codebase)

When: "deep search the codebase", "map all callers of Y", architecture-level
understanding before a refactor, any question where one grep pass is
insufficient. NOT for quick lookups or tiny codebases (<20 files).

### Pass 1 — broad sweep (breadth-first)

`grep` the primary term, `glob`/`find_file_by_name` for related files →
candidate list ranked by match density × centrality.

### Pass 2 — deep read (top candidates)

`read` the top 5-10 files fully; trace imports/exports; `grep` each
import/export to map the dependency graph.

### Pass 3 — cross-file synthesis

Data flow (enter/transform/exit), control flow (who calls whom), edge cases
(error/null/concurrency), convention consistency → narrative with citations.

### Pass 4 — architecture map (if scope warrants)

Group into modules/layers; Mermaid/ASCII dependency graph; hotspots
(fan-in/out, circular deps); tech debt.

### Citation rule

Every claim cites `file:line`. Uncited = deduction (Rule 17). Can't cite →
"not found in codebase", search again or report the gap.

### Output format

```markdown
## Deep Search: <topic>
### Summary
### Key files
- `path` — <role> (N matches)
### Findings
<numbered, cited>
### Dependency graph
<Mermaid/ASCII>
### Gaps / Not found
```

Notes: no index exists (Pass 1 replaces it); findings >~50k tokens → write
`deep-search-<topic>.md` + summarize (`context-hygiene` folding); Pass 1
sweeps can run in parallel subagents (`dispatching-parallel-agents`).
