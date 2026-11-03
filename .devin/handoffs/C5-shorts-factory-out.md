# C5: shorts-factory skill + stock-footage fetcher

**Status:** DONE_WITH_CONCERNS
**Branch:** skill/shorts-factory (worktree `.worktrees/shorts-factory`,
rebased onto `feat/reels-adoption` a72cfc7)
**Commit:** 334aea1 feat(shorts): shorts-factory skill + stock-footage fetcher

## Changes

- `skills/shorts-factory/SKILL.md`
  - Pipeline doc: topic -> script (agent prompt pattern) -> narration via
    `tts` skill (voicebox default or `--backend voicestudio`) ->
    alignment via `extensions/asr` -> scene-plan v2 (reuses the
    animation-direction schema) -> render via `remotion-render` ->
    ffmpeg composite (captions, 9:16/16:9/1:1).
  - Concrete step-by-step example flow with real commands.
  - Typed-error table per stage; explicit non-goals: no auto-publishing,
    no batch daemon, no paid services. No em-dash characters.
- `extensions/stock-footage/fetch.py`
  - stdlib urllib only; `search` (query, provider, per_page, orientation)
    and `download` (smallest file meeting `--min-width`, writes `--out`).
  - Keys from `PEXELS_API_KEY`/`PIXABAY_API_KEY`; absent ->
    `{"ok": false, "status": "missing", "hint": ...}`, zero network calls.
  - Bounded reads (4 MiB JSON, 200 MiB file), timeouts, typed envelope
    (`ok`, `status`, `action`, `result|error`, `duration_s`); HTTP errors
    -> `http_error:<code>`, never a traceback.
  - `if __name__ == "__main__"` guard.
- `tests/test_stock_footage_fetch.py` (6 tests, all passing)
  - no-key paths return `status: missing` with urlopen mocked and
    asserted not called; `_pick` smallest-adequate logic; typed
    `http_error:429`; happy-path Pexels search with fake response.

## Verification

- `python -m pytest -q tests/test_stock_footage_fetch.py`: 6 passed.
- `python audit.py`: 5 errors, all stale-count (manifest skill_count,
  README count/badge, TOOLS-MAP count, diagram skills count) -- the
  expected +1 skill delta the orchestrator reconciles post-merge.
- `python -m pytest -q tests/`: 2120 passed, 20 failed, 5 skipped.
  All 20 failures trace to the same un-reconciled +1 skill count
  (157 manifest vs 158 on disk):
  - `test_audit_passes.py` x3 -- audit exits nonzero on stale counts.
  - `test_egm_upgrade_contract.py` x16 -- all assert audit `Errors: 0`.
  - `test_red_team_skills.py::test_manifest_covers_red_team_components`
    -- asserts `skill_count == len(disk_skills)`.
  Verified on clean `feat/reels-adoption` (a72cfc7): all 28 checked
  validation tests pass; failure class is count-reconciliation only.

## Notes / concerns

- Base branch moved during work (a72cfc7 reconcile commit); branch was
  rebased so the only delta is the +1 un-reconciled skill, per contract.
- Pexels `download` resolves files via `/videos/videos/{id}`; Pixabay
  via `?id=` on the same endpoint. Pixabay has no server-side video
  orientation param; filtered client-side.
- No push performed; main checkout untouched except this report file.
