# Memory pipeline

Deterministic, cue-anchored project memory. Notes live in
`.devin/memory/` as Markdown with YAML frontmatter; hooks inject the
top-scoring notes as `additionalContext`. Design evidence: retrieval
must be deterministic, not voluntary (arXiv:2607.20972); keep retrieved
context small (arXiv:2608.15008).

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
| `memory-retrieval.py` | UserPromptSubmit (inside `user-prompt.py`) | prompt text vs cues: `keyword` +3, `symbol` +4, `path` +2; body tags in first 1000 chars +1 each | 2 |
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

- New user prompt mentioning a cue keyword or symbol -> top 2 notes
  injected.
- Editing a file under a `path` cue -> up to 2 related notes injected.
- Running a command matching `symbol`/`keyword` cues -> up to 2 notes.
- Session end -> stderr summary only.
