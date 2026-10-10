# ISSUE 04, Animation Direction: narration → scene plan → code-rendered motion

Status: planned (research done) · Source: IG `DeNUYLkRWsz` (@matheusolivsilv) · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- Reel pipeline: narrated video → timestamped+semantic transcript → frame analysis → **scene plan synced to narration** → human approval gate → generated React code rendered by **Remotion** → composited over recording. Code controls every element's appear/move/duration.
- Value: agent becomes a motion-graphics director: "explain X" → synced b-roll/infographic animation without touching a video editor; corrections happen at the cheap plan stage, not post-render.

## Pipeline (extracted)

1. **Enrich**: ASR + timestamps + semantic beats (what concept each segment explains). Local ASR proven this session: yt-dlp + whisper.cpp `ggml-base` (PT-BR OK), package as `extensions/asr/`.
2. **Analyze**: keyframe extraction (ffmpeg scene-select) + multimodal reasoning over frames → what visuals should appear.
3. **Plan**: scene manifest v2 (motion): per beat → `{visual, motion_spec (easing/enter/exit/duration), sync_range}`.
4. **GATE**: render nothing until plan approved (ask_user_question / ledger sign-off). Core of the skill, mirrors our `gates` discipline.
5. **Render**: plan → Remotion React components → `npx remotion render` → frames.
6. **Composite**: overlay on source video via ffmpeg `timeline.py` (Issue 03 dependency).

## Brain (Skill)

- **New `animation-direction` skill**: motion vocabulary (easings, entrances, holds, transitions, timing budgets), beat→visual mapping rules, scene-plan schema, the mandatory plan gate, when Remotion vs After-Effects-JSX vs Blender paths apply (default: Remotion; Blender for 3D via operate-blender; AE only if user has it).
- Composition sync rules: text ≤ N words on screen, beat duration ≥ read time, avoid motion during cuts.

## Muscle (Extension)

- `extensions/asr/`, wrap the proven yt-dlp + whisper.cpp flow: `transcribe.py url|file → {text, segments[{start,end,text}]}`; model cache dir; base→small upgrade flag.
- `extensions/remotion-render/`, scaffold: plan JSON → Remotion project template → render → frames/alpha mov. Requires Node + `npx remotion`; ship template components (kinetic text, diagram nodes, counters, image pan/zoom).
- `plan_check.py`, pre-render validator: durations vs audio, overlap collisions, budget estimate → feeds the approval gate artifact.

## Step-by-step (on authorization)

1. `extensions/asr/` packaging (binaries + model bootstrap script like laya-tools `bootstrap.py`).
2. Scene-plan v2 schema (extends Issue 03 manifest with `motion_spec` + `sync_range`).
3. Remotion template + renderer for 3 primitive visuals; golden-frame tests.
4. `plan_check` + gate wiring; then ffmpeg composite path (Issue 03 `timeline.py`).
5. End-to-end: 30s narrated clip → plan → approve → rendered composite.
6. Write `animation-direction` SKILL.md.

## Non-goals

No After Effects dependency (optional renderer), no paid TTS/ASR APIs, no auto-publishing, plan approval is a hard gate, always.
