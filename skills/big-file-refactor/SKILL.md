---
name: big-file-refactor
description: Use when a source file has grown past roughly 1000 lines, when context compaction is losing track of a file's content, or when asked to break an oversized file into modules safely.
disable-model-invocation: true
---

# Big-file refactor

Oversized files (>~800-1500 lines, language-dependent) rot agent context: reads get truncated, compaction loses content, edits hallucinate against what is no longer visible. This is the mechanical protocol for splitting one - never a rewrite.

## Phase 0 - Gate

- A test suite must exist and be green BEFORE the first move. If coverage is thin, write characterization tests first (`edge-coverage`, `architecture`'s characterization-test pattern). No suite, no split.
- Confirm the file is actually the problem: is it on the hot path of edits, or just big? Splitting cold files adds churn for nothing.

## Phase A - Inventory

- List every top-level symbol (class, function, constant) with line ranges.
- Map dependents: who imports this file, and which symbols each importer uses (`grep` for each symbol).
- Group symbols by cohesion: same data, same collaborator, same caller. These groups are the module candidates. A file that is one cohesive class is NOT a split candidate - extract methods or accept the size.

## Phase B - Extraction

- One mechanical move at a time: cut a cohesion group into its target module, rewire imports, commit or checkpoint.
- Move code verbatim. Do NOT "improve" it while moving - renaming, reformatting, and logic edits belong to a separate pass after the split is green.
- Keep a compatibility shim (re-export from the old path) while external callers migrate; delete the shim only when no importer needs it.
- Target: leaf modules first (utilities, constants, types), then the groups with the fewest inbound edges.

## Phase C - Verify

- Tests green after EVERY move, not at the end. A red move gets reverted, not patched forward.
- After the last move: no file should exceed the threshold, the old path either re-exports cleanly or is gone, and the import graph has no cycles.
- Sanity: `grep` the codebase for stale references to moved symbols.

## Heuristics

- Threshold ~800-1000 lines for dense logic languages; generated/vendored/data files exempt.
- Prefer fewer, deeper modules over many shallow ones (`architecture` deep-module rule).
- If a move fights you (symbols tangled, everything references everything), stop - the file needs redesign, not relocation. Say so.

## Related

- `lean-code` for what to cut once modules are visible; `de-slop`/`unslop` for the cleanup pass after structure settles; `architecture` for seam design.
