# C3: VoiceStudio backend path for extensions/voicebox/wrapper.py

**Status:** DONE
**Branch:** feat/voicestudio-path (worktree `.worktrees/voicestudio-path`)
**Commit:** f18d1403f6344936ff707bc6efb099ec963fdd45

## Changes

- `extensions/voicebox/wrapper.py`
  - `--backend {voicebox,voicestudio}` CLI flag (top-level, before subcommand)
    and `VB_BACKEND` env var; flag wins, default `voicebox`.
  - `BACKENDS` table: per-backend default host + missing hint.
    VoiceStudio default host `http://127.0.0.1:3900`, hint
    "start the VoiceStudio app (API on 127.0.0.1:3900)".
  - `resolve_base_url(backend)` still enforces loopback-only `VB_HOST`,
    http scheme, same for both backends.
  - VoiceStudio actions (shared `http_request` => same MAX_BODY cap and
    timeouts):
    - `doctor`/`models`: GET `/v1/models`; `status: missing` + hint when
      unreachable.
    - `generate`: POST `/v1/audio/speech` with
      `{model: --engine or "tts-1", voice, input: --text,
      response_format: "wav"}`; audio bytes written to `--out`.
  - Voicebox path byte-for-byte compatible: default host, `/health` +
    `/models` doctor, `/generate` payload and envelope unchanged.

- `skills/tts/SKILL.md`
  - New "VoiceStudio backend" section: flag/env, :3900 endpoint,
    payload mapping, license caveat (app AGPL-3.0; default OmniVoice
    engine non-commercial; per-engine licenses vary).

## Verification (inside worktree)

- `python extensions/voicebox/wrapper.py doctor` -> `status: missing`,
  exit 1, voicebox hint.
- `python extensions/voicebox/wrapper.py --backend voicestudio doctor`
  -> `status: missing`, exit 1, VoiceStudio hint, base_url :3900.
- `python -m pytest -q tests/test_voicebox_wrapper.py` -> 5 passed.
- `python audit.py` -> 0 errors (7 pre-existing warnings incl.
  `skills/tts live != bundle` expected until export).

## Boundaries respected

- Worktree only; no push; main checkout untouched; stdlib only;
  edits confined to `extensions/voicebox/` and `skills/tts/`.

## Notes

- Added git safe.directory exception for the worktree path
  (filesystem lacks ownership records); required to commit.
