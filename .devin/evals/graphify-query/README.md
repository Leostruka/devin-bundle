# Spike: graphify query -> memory-retrieval hook (issue #442)

Branch: eval/reels-7-batch. Source reel: R7-09 (`DcEBQNPNPzs`).

## What the reel actually says

The transcript is a *rebuttal* of naive graphify-style tooling: auto-generated
"wiki knowledge graphs" (Obsidian-style or the `graphify` repo) without real
ontological modeling and multi-hop traversal are "a big mess" that eats
context. The actionable kernel: retrieval should go through a structured
index with traversal, not raw grep over files.

## What already exists (verified by reading code)

| Piece | Path | State |
|---|---|---|
| Code-graph indexer (SQLite, FTS5 over camel/snake-split symbol tokens, incremental mtime+sha1) | `extensions/code-graph/code_graph.py`, `index.py` | Working. `index.db` at `.devin/code-graph/index.db`: 1035 files, 5964 symbols, 2963 import edges |
| Query CLI (symbols/outline/refs/files) | `extensions/code-graph/query.py` | Working; human-oriented output, exits 2 when index missing ("GRAPH-DOWN") |
| Memory retrieval hook (cue-anchored: keyword/path/symbol frontmatter, top-3) | `scripts/memory-retrieval.py` | Wired into `scripts/user-prompt.py` (UserPromptSubmit consolidated hook) |
| Memory store | `.devin/memory/` | Only `MOC.md`; zero real notes, so the memory cue path is dormant |
| Hook envelope runner | `scripts/_hookrun.py` | Merges additionalContext from sub-hooks |

So "graph-before-grep" infrastructure already exists in two halves: a symbol
FTS graph (code side) and a cue-matched note graph (memory side). What was
missing: one ranked entry point an agent (or hook) can call with a
natural-language-ish query instead of reaching for `grep -r`.

## What the spike built

`scripts/graph-query.py`: tokenizes a query (stopword-stripped), runs
per-term FTS5 symbol matches + path LIKE over the code-graph index, folds in
`.devin/memory` cue hits (note body terms + `path:` cue promotion), ranks by
term coverage then symbol hits, emits `{"ok": true, "results": [{file,
score, matched_terms, rationale}]}`. Degrades gracefully (ok still true,
`degraded` list populated) when the index is absent; exits non-zero only on
`ok: false` per CLI contract. UTF-8 pinned. `--root` defaults to repo root.

Tests: `tests/test_graph_query.py`, 4 passed
(`python -m pytest tests/test_graph_query.py -x -q`).

## Measured evidence

Queries run against this repo. Baselines counted over
`scripts/ + extensions/code-graph/ + tests/` (308 files): grep-OR = files
matching any term (unranked), grep-AND = files containing all terms
(unranked). Full-tree grep over `extensions/` was too slow to complete in a
reasonable window (huge media/binary trees), itself evidence that indexed
retrieval beats raw grep here.

| Query | graph-query top hit (rank) | grep-OR files | grep-AND files |
|---|---|---|---|
| memory retrieval scoring | scripts/memory-retrieval.py (#1, score 21) | 37 | 0 (miss) |
| block em dash | scripts/no-em-dash.py (#1, score 22) | 248 | 5 |
| incremental code graph index | extensions/code-graph/code_graph.py (#1, score 31) | 181 | 4 |
| constraint pinning | scripts/constraint-pinning.py (#2, score 21; #1 is its held-out test) | 11 | 5 |
| push green validation | scripts/check-push-green.py (#1, score 21) | 83 | 4 |

Result: 5/5 queries put the expected file in the top 2. grep-AND missed
query 1 entirely (no single file contains all three terms; `score()` is a
symbol-level hit only the FTS token index catches, since it splits
`memory-retrieval`/`scoring` differently than substring grep). grep-OR is
useless at 37-248 unranked candidates.

Latency: graph-query answers in <1s on the warm index; the equivalent
repo-wide grep did not finish promptly (see above).

## Caveats

- Index staleness: `index.db` mtime was older than the working tree; run
  `python extensions/code-graph/index.py` to refresh. A hook that relies on
  it needs a freshness check or a cheap auto-reindex.
- Memory side is unproven: `.devin/memory/` has no notes yet, so memory-cue
  promotion is implemented and unit-tested but contributed nothing in the
  live runs.
- Edges table (imports) is populated but not yet used for traversal; could
  boost files that import a strongly-matched file.
- Score weighting (term coverage * 10 + capped symbol hits) is heuristic,
  tuned on these 5 queries only.

## Recommendation

Adapt, do not adopt and do not skip.

- Adopt as-is is wrong: the reel's warning holds, and this spike confirms a
  flat FTS+path index already delivers the practical benefit without an
  ontology layer.
- Concretely:
  1. Keep `scripts/graph-query.py` as the canonical "graph-before-grep" tool;
     reference it from agent docs/skills so agents try it before `grep -r`.
  2. Add an index-freshness check (compare newest source mtime vs db mtime,
     or run incremental `index.py` which is already mtime-based and fast).
  3. Seed 2-3 real `.devin/memory/` notes with `path:`/`keyword:` cues to
     activate the second retrieval leg, then re-measure.
  4. Optional: 1-hop edge expansion (files importing a top hit) as a small
     score bonus; measure before keeping.
- Do not build a YAML/wiki knowledge-graph generator: no traversal semantics,
  high context cost, contradicts the source material.

## Reproduce

```sh
python extensions/code-graph/index.py            # refresh index
python scripts/graph-query.py "constraint pinning" --limit 5
python -m pytest tests/test_graph_query.py -x -q
```
