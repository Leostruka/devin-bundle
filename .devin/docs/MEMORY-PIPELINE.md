# Memory pipeline

Deterministic, cue-anchored project memory. Notes live in
`.devin/memory/` as Markdown with YAML frontmatter; hooks inject the
top-scoring notes as `additionalContext`. Design evidence: retrieval
must be deterministic, not voluntary (arXiv:2607.20972); keep retrieved
context small (arXiv:2608.15008).

The local `devin-memory` CLI (`extensions/devin-memory/README.md`) is a
separate, manual store with global and project scopes. Installing it does
not replace these hooks, migrate any notes, or inject its SQLite data.

## Storage

- Directory: `BUNDLE_MEMORY_DIR` else `DEVIN_MEMORY_DIR` else
  `<project>/.devin/memory/` (project root = `DEVIN_PROJECT_DIR` or
  cwd). All four scripts resolve the directory identically.
- Note format: `*.md` with frontmatter `title:`, `category:`,
  `status:` (`active` notes score full; others score half or are
  skipped), and a `cues:` list of `keyword:`, `symbol:`, `path:` entries.
  `MOC.md` is excluded from retrieval (map of content, not a note).
- Approval contract: memory writes are user-approved edits to
  `.devin/memory/` files; no hook writes memory notes automatically.
  The skills `memory-management`, `memory-hygiene`, and `project-memory`
  define when and how to author or prune notes; hooks only read.

## Retrieval events

| Script | Event | Cue matching | TOP_K |
|---|---|---|---|
| `memory-retrieval.py` | UserPromptSubmit (inside `user-prompt.py`) | prompt text vs cues: `keyword` +3, `symbol` +4, `path` +2; body tags in first 1000 chars +1 each | 3 |
| `memory-post-exec.py` | PostToolUse exec/mcp (inside `post-exec.py`) | command/output vs `symbol`/`keyword` cues | 2 |
| `memory-post-edit.py` | PostToolUse write/edit | edited file path vs `path` cues (substring either direction, normalized separators) +5 | 2 |
| `memory-stop.py` | Stop + SessionEnd | no retrieval; reports `.devin/memory/` state to stderr | - |

Scoring details:

- Non-`active` notes score half in prompt retrieval and zero in
  path retrieval.
- Output is a `> [!note] Project memory` block in
  `hookSpecificOutput.additionalContext`; it merges with other context
  via `_hookrun` concatenation.
- An unreadable note logs to stderr and never silences the rest.

## Write triggers

- `memory-stop.py` on `SessionEnd` logs the memory directory state
  (note count, stale entries) to stderr. On `Stop` it stays quiet for
  unconditional reporting, because Stop stderr becomes a new turn and
  would re-prompt the agent in a loop; it only speaks when there is
  something actionable.
- Nothing else writes notes. Compaction-triggered context loss is
  repaired by `constraint-pinning.py`, not by memory replay.

## Predicting behavior

- New user prompt mentioning a cue keyword or symbol -> up to 3 notes
  injected.
- Editing a file under a `path` cue -> up to 2 related notes injected.
- Running a command matching `symbol`/`keyword` cues -> up to 2 notes.
- Session end -> stderr summary only.

## Evaluated alternative: L0-L3 layered memory (Tencent, MIT) - issue #639

Video/vendor claims (-61% tokens, 33%->50% solve) are UNREPRODUCED;
evaluation verdict against this pipeline:

| Their layer | Our equivalent | Status |
|---|---|---|
| L0 raw log | durable session log (SessionStart/Stop hooks) | adopted already |
| L1 atoms (facts/cues per ~5 turns) | notes + frontmatter cues | adopted already |
| L2 scenes (episodic consolidation) | none | deferred: needs write-side auto-consolidation, which changes the no-auto-write contract |
| L3 persona (~50 memories) | AGENTS.md curated rules | adopted already |
| sqlite-vec BM25+vector RRF | cue-keyword scoring | rejected: new dep violates stdlib-only hooks |
| skip-injection on slow recall | deterministic O(notes) scan, TOP_K=3 at prompt time | adopted already (bounded by design) |

Residual risk they flag (prefix-cache poisoning via injected memory):
our injection is bounded (up to 3 notes, user-approved authors only). Re-eval
if an auto-consolidation writer is ever proposed.
