# 49 -- Memory hook pipeline (retrieval/scoring/storage) undocumented

- **Status**: open
- **Category**: documentation
- **Severity**: P2
- **File**: scripts/memory-retrieval.py

## Evidence
Four scripts implement a memory subsystem: `memory-retrieval.py`
(UserPromptSubmit), `memory-post-exec.py`, `memory-post-edit.py`
(PostToolUse), `memory-stop.py` (Stop/SessionEnd), all reading/writing
`.devin/memory/` with `BUNDLE_MEMORY_DIR`/`DEVIN_MEMORY_DIR` overrides
(per EXECUTION_CHANGELOG). No doc explains the scoring/cue model
(keyword vs symbol matching), write triggers, file layout, or how memory
entries are authored and approved (README step 7 mentions "sempre com
aprovacao do usuario" but nowhere defines the approval mechanism).
Related skills (`memory-hygiene`, `memory-management`, `project-memory`)
exist but the runtime pipeline itself has no reference doc.

## Recommendation
Write `.devin/docs/MEMORY-PIPELINE.md` (or a TOOLS-MAP section): event
points, scoring cues, `.devin/memory/` schema, env overrides, and the
user-approval contract for writes.

## Verification
Reader can predict which hook fires for a given event and where entries
land; cross-check against the four scripts' stdin handling.
