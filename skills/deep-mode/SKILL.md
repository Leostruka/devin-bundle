---
name: deep-mode
description: Use when the user says 'deep', 'deep search', 'deep research', 'research this thoroughly', or asks for exhaustive codebase exploration beyond a quick grep. Replicates Ask Devin's Deep Mode (!deep in Slack/Teams) for the CLI — multi-pass agentic search with citations, cross-file synthesis, and architecture mapping.
---

# Deep Mode (CLI replica of Ask Devin Deep Mode)

## What this replicates

Cloud Ask Devin has a **Deep Mode** toggle (`!deep` keyword in Slack/Teams,
"Deep Mode" in the web app) that switches from quick lookup to exhaustive
agentic search: multiple passes, cross-file synthesis, cited findings, and
architecture-level understanding. Usage-based billing in cloud; free here.

The CLI's `/ask` is a one-shot read-only question — no deep toggle. This
skill fills that gap by providing the deep-search workflow as an
invocable procedure.

**Sources:**
- docs.devin.ai/work-with-devin/ask-devin (Ask Devin overview)
- docs.devin.ai/integrations/slack (`!deep` keyword)
- docs.devin.ai/integrations/microsoft-teams (`!deep` keyword)
- cognition.ai/blog/new-self-serve-plans-for-devin (Deep Mode = usage-based)

## When to Use

- "Deep search the codebase for X"
- "Research how authentication works end-to-end"
- "Map all callers of function Y and their data flow"
- "Exhaustive exploration" / "research this thoroughly"
- Any question where a single grep pass is insufficient
- Architecture-level understanding before a refactor or ADR

## When NOT to Use

- Quick lookup (one file, one function) — use `grep`/`read` directly
- Single-needle search — `find_file_by_name` is cheaper
- The codebase is tiny (< 20 files) — direct reads suffice
- You need to make changes, not explore — use Plan mode instead

## Procedure (multi-pass agentic search)

### Pass 1 — Broad sweep (breadth-first)

Goal: identify all relevant files and entry points.

1. `grep` for the primary keyword/term across the codebase
2. `glob` for files by name pattern that might be relevant
3. `find_file_by_name` for config/test/docs that reference the topic
4. Record: file paths, match counts, module boundaries

Output: a list of candidate files ranked by relevance (match density x
centrality — files imported by many others rank higher).

### Pass 2 — Deep read (depth-first on top candidates)

Goal: understand the implementation in each candidate file.

1. `read` the top 5-10 candidate files (full read, not offset)
2. For each file, trace:
   - Imports (what does it depend on?)
   - Exports (what depends on it?)
   - Key functions/classes and their signatures
3. `grep` for each import/export to map the dependency graph

Output: annotated dependency graph (file -> imports -> imported-by).

### Pass 3 — Cross-file synthesis

Goal: connect the dots across files.

1. Identify data flow: where does data enter, transform, exit?
2. Identify control flow: who calls whom, in what order?
3. Identify edge cases: error paths, null handling, concurrency
4. Identify patterns: is this code consistent with the codebase's
   conventions, or is it an outlier?

Output: narrative explanation with **citations** (file:line references).

### Pass 4 — Architecture map (if scope warrants)

Goal: produce a visual/structural model.

1. Group files into modules/layers
2. Draw the dependency graph (Mermaid or ASCII)
3. Mark hotspots (high fan-in/fan-out, circular deps)
4. Note tech debt or divergence from stated architecture

Output: Mermaid diagram + layer description.

## Citation format

Every claim must cite its source:

```
The auth middleware checks JWT expiry before forwarding to the route
handler [src/middleware/auth.ts:42-58]. Expired tokens return 401
[src/middleware/auth.ts:61]. The refresh flow is handled separately
by the token refresher [src/auth/refresh.ts:15-30], which is called
from the 401 interceptor [src/client/http.ts:88-95].
```

Uncited claims = deductions (Rule 17 violation). If you cannot cite,
say "not found in codebase" and search again or report the gap.

## Output format

```markdown
## Deep Search: <topic>

### Summary
<2-3 sentence overview>

### Key files
- `path/to/file.ts` — <role> (N matches)
- ...

### Findings
<numbered findings with citations>

### Dependency graph
<Mermaid or ASCII>

### Gaps / Not found
<what you couldn't locate or verify>
```

## CLI-specific notes

- No index: cloud Ask Devin uses a pre-built codebase index. The CLI
  has no index — Pass 1 replaces it with grep/glob sweeps. Slower but
  complete (no stale index).
- No session handoff: cloud Ask Devin can "Send to Devin" to start an
  Agent session. In the CLI, the user switches modes manually after
  reading the deep-search output.
- Token budget: deep search generates a lot of context. Use
  `context-folding` if the output exceeds ~50k tokens — write findings
  to a file (`deep-search-<topic>.md`) and summarize in chat.
- Parallelism: use `dispatching-parallel-agents` to run Pass 1 sweeps
  across different directories concurrently (SWE-1.7 subagents, 262K
  each, gratuito).
