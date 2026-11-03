---
name: shorts-factory
description: Use when producing short-form vertical or square videos (Shorts, Reels, TikTok) end to end from a topic -- script, narration, alignment, stock b-roll, scene plan, render, and ffmpeg composite with captions. Assembles tts + extensions/asr + extensions/stock-footage + animation-direction/remotion-render into a MoneyPrinterTurbo-equivalent pipeline.
triggers: [user, model]
---

# Shorts Factory

Topic in, captioned short video out. No video editor, no paid TTS/ASR.
Reuses bundle pieces; the only new moving part is
`extensions/stock-footage/fetch.py` for b-roll clips.

## Pipeline

```
topic -> script -> narration WAVs -> transcript segments
      -> scene-plan v2 (+ stock clips) -> render -> ffmpeg composite
```

### 1. Script (agent prompt pattern)

Prompt the agent for a spoken script, one line per caption beat:

- Target 45-90 words for a 30-60s short (160 WPM read time).
- One sentence per line; each line becomes a narration segment and a
  caption. No stage directions, no headers.
- End with a hook or call to action line.

### 2. Narration (tts skill)

One WAV per script line via `extensions/voicebox/wrapper.py`:

```bash
python extensions/voicebox/wrapper.py generate \
    --text "<line>" --voice <id> --out narration/line_01.wav
```

Default voicebox backend, or `--backend voicestudio` /
`VB_BACKEND=voicestudio` for the VoiceStudio app on 127.0.0.1:3900.
`doctor` first; `status: missing` means tell the user to start the
backend. Concatenate WAVs (ffmpeg `concat` demuxer) into `narration.wav`
recording each line's cumulative start offset.

### 3. Alignment (extensions/asr)

```bash
python extensions/asr/transcribe.py narration.wav --model base
# -> {"ok": true, "segments": [{start, end, text}], ...}
```

Segments anchor captions and scene `sync_range`s. Requires
`extensions/asr/bootstrap.py` to have fetched whisper.cpp + model
(explicit fetch, never silent). Missing binaries -> `ok:false` + hint.

### 4. B-roll (extensions/stock-footage)

```bash
python extensions/stock-footage/fetch.py search --query "<kw>" \
    --provider pexels --orientation portrait --per-page 10
python extensions/stock-footage/fetch.py download --provider pexels \
    --id <id> --out clips/clip_01.mp4
```

Keys from `PEXELS_API_KEY` / `PIXABAY_API_KEY`; absent ->
`{"ok": false, "status": "missing", "hint": ...}` with zero network
calls. Download picks the smallest file meeting `--min-width`
(default 720). Stock clips are optional: skip this stage and let the
render stage produce all visuals when no keys are set.

### 5. Scene plan (scene-plan v2)

Reuse the scene-plan v2 schema from `skills/animation-direction`
(`craft-bridge` scene_manifest v1 + `motion_spec` + `sync_range`):

```json
{"scenes": [{"id": "s1", "sync_range": [0.0, 3.2],
  "visual": {"type": "kinetic_text", "props": {...}},
  "motion_spec": {"easing": "easeOut", "enter": "fade",
                  "exit": "fade", "enter_s": 0.3, "exit_s": 0.3},
  "broll": "clips/clip_01.mp4"}]}
```

One scene per transcript segment/beat. `broll` is a local downloaded
clip path; `visual` covers text/diagram beats the same way as
animation-direction. Validate with
`extensions/remotion-render/plan_check.py` and get plan approval before
rendering (hard gate, same as animation-direction).

### 6. Render

```bash
python extensions/remotion-render/render.py plan.json --workdir out/
```

Remotion renders the scene visuals/overlays. Full 3D scenes route to
`operate-blender`; pure text+b-roll plans may skip render entirely and
go straight to composite.

### 7. Composite (ffmpeg)

```bash
# 9:16 shorts (1080x1920); use 1920x1080 for 16:9, 1080x1080 for 1:1
ffmpeg -i render.mp4 -i narration.wav \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,\
pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles=captions.srt:force_style='Fontsize=14'" \
  -c:v libx264 -c:a aac -shortest short.mp4
```

Build `captions.srt` from ASR segments. Pick aspect per platform:
9:16 Shorts/Reels/TikTok (default), 1:1 feed, 16:9 YouTube.

## Example flow

```bash
W=extensions/voicebox/wrapper.py
python $W doctor                                    # backend up?
python $W generate --text "Three facts about octopi." \
    --voice af_heart --out n/line_01.wav            # per line...
ffmpeg -f concat -safe 0 -i wavlist.txt -c copy narration.wav
python extensions/asr/transcribe.py narration.wav > transcript.json
python extensions/stock-footage/fetch.py search \
    --query "octopus ocean" --orientation portrait > hits.json
python extensions/stock-footage/fetch.py download --id 857195 \
    --out clips/c1.mp4
# agent writes plan.json (scene-plan v2) from transcript + hits
python extensions/remotion-render/plan_check.py plan.json
python extensions/remotion-render/render.py plan.json --workdir out/
ffmpeg -i out/out.mp4 -i narration.wav -vf "scale=1080:1920,subtitles=c.srt" \
    -c:v libx264 -c:a aac -shortest short.mp4
```

## Typed errors per stage

| Stage | Failure | Envelope |
|---|---|---|
| tts | backend down | `status:"missing"` + start hint |
| tts | bad voice/engine | `status:"error"`, `error` detail |
| asr | missing binary/model | `ok:false` + bootstrap hint |
| asr | fetch/decoder failure | `ok:false`, `error:"fetch_error:*"` |
| stock | no API key | `status:"missing"` + `hint`, no network |
| stock | HTTP/timeout | `status:"error"`, `error:"http_error:<code>"` |
| render | plan invalid | `plan_check.py` findings, gate blocks |
| composite | missing input | ffmpeg nonzero exit; surface stderr |

Never fabricate: no fake audio, no fake transcript, no fake clips.
Every stage degrades to a typed error, not a traceback.

## Non-goals

- No auto-publishing or platform upload (YouTube/TikTok APIs).
- No batch mode, watch folder, or scheduling daemon.
- No paid TTS/ASR/stock services; no API keys beyond Pexels/Pixabay.
- No long-form video; 3 minutes max is a hard ceiling.

## Boundaries

- Localhost services only (voicebox, VoiceStudio). Keys stay in env,
  never logged or written to plans.
- Stock clips carry provider license terms; keep `hits[].url` for
  attribution.
- Plan approval gate is mandatory before `render.py` on non-trivial
  plans, same as animation-direction.
