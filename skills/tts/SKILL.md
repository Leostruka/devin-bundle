---
name: tts
description: Use when generating speech, narration, voiceover, or any text-to-speech audio locally. Routes to extensions/voicebox/wrapper.py, an HTTP client for a user-started voicebox backend (jamiepine/voicebox, FastAPI on 127.0.0.1:17493).
triggers: [user, model]
---

# TTS

Local text-to-speech via `extensions/voicebox/wrapper.py` -- thin HTTP
client for the voicebox backend. voicebox is not pip-installable: the
user clones jamiepine/voicebox and runs `python -m backend.main` inside
the checkout. Models are downloaded by the backend itself.

## Commands

```bash
W=extensions/voicebox/wrapper.py

python $W doctor                                        # liveness + models
python $W models                                        # list engines/models
python $W generate --text "..." --voice <id> --out out.wav [--engine <e>]
```

All output is JSON (`status`, `action`, `result|error`, `duration_s`).
Backend down reports `status: missing` with a start hint; never
fabricate audio or a voice list.

## Workflow

1. `doctor` once per session; `missing` means tell the user to start
   `python -m backend.main` in their voicebox checkout.
2. `models` to pick an available engine/voice; use only listed voices.
3. `generate` per line or paragraph; keep segments short for easier
   re-takes. Generation on CPU is slow -- expect tens of seconds per
   sentence; a GPU-backed engine is strongly recommended for anything
   beyond short clips.

## Narration pipeline

For narrated videos compose across wrappers:

1. `tts` (this skill) -> per-line WAV files.
2. `extensions/asr` -> transcribe generated audio for word-level
   timestamps (subtitle/sync anchor).
3. `animation-direction` skill -> drive scene/animation timing from the
   transcript timestamps.

## Boundaries

- Localhost only; `VB_HOST` overrides must be loopback.
- No voice cloning of real people without consent.
- Backend-managed models only; no manual model path injection.
