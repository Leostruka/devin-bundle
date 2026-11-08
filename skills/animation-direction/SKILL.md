---
name: animation-direction
description: Use when turning narrated video/audio into synced code-rendered motion graphics — narration -> timestamped transcript -> scene plan -> approval gate -> Remotion render -> ffmpeg composite. Covers the motion vocabulary, beat-to-visual mapping, scene-plan v2 schema, and the mandatory plan gate via extensions/asr + extensions/remotion-render.
---

# Animation Direction

Motion-graphics direction without a video editor: "explain X" -> synced
b-roll/infographic animation. Corrections happen at the cheap plan
stage, never post-render.

## Pipeline

1. **Enrich** — `extensions/asr/transcribe.py url|file` (yt-dlp +
   whisper.cpp, offline) -> `{text, segments[{start,end,text}]}`;
   bootstrap via `extensions/asr/bootstrap.py` (explicit fetch only).
2. **Analyze** — keyframes (ffmpeg scene-select) + semantic beats: what
   concept each segment explains.
3. **Plan** — scene-plan v2 per beat:
   `{id, sync_range:[s,e], visual:{type,props},
     motion_spec:{easing,enter,exit,enter_s,exit_s}, overlay?}`.
4. **GATE (hard)** — render nothing until the plan is approved:
   `plan_check.py` output + `ask_user_question`/ledger sign-off.
5. **Render** — `extensions/remotion-render/render.py plan.json
   --workdir out/` -> Remotion project -> `npx remotion render`.
6. **Composite** - `extensions/remotion-render/composite.py source
   overlay -o out.mp4 [--fit frame|contain] [--pos x:y] [--mix]`:
   source audio (narration) preserved by default, `--mix` amixes
   overlay audio; alpha `.mov` renders overlay full-frame, mp4
   renders use `--fit contain` PiP/lower-third. Per-beat `sync_range`
   timing: render each beat clip separately and concat, or one
   full-length plan - composite handles whole inputs only.

## Motion vocabulary

- Easings: `linear` (data/tickers), `spring` (emphasis, diagrams),
  `easeOut` (default entrances).
- Entrances: `fade` (default), `slideUp` (titles/steps), `scale`
  (callouts), `none` (cuts). Exits default `fade`, `none` on cut.
- Timing budgets: entrance <= 0.5s and <= half the beat; holds >= 1.5s
  for text; transitions only between narration cuts.
- Direction grammar (the part that reads as directed, not tweened):
  `anticipation` (small counter-move before the main move), `release`
  (the move itself, faster than the anticipation), `smear frame`
  (stretch the element along the path of travel for 1-2 frames on fast
  moves), and negative space as a tool - hold empty space around the
  subject instead of filling every frame.

## Beat -> visual mapping

| Beat | visual.type | props contract |
|---|---|---|
| Claim / definition | `kinetic_text` | `{text: str, size?: num}` - <= ~12 words |
| Process / sequence | `diagram_nodes` | `{nodes: [{label: str}, ...]}` - stagger 6f |
| Number / metric | `counter` | `{to: num, label?: str}` - count up ~1s |
| Screenshot / asset | `pan_zoom` | `{src: str, zoom?: num}` - slow zoom 1.0->~1.15 |

`plan_check.py` enforces this contract (missing/wrong-typed required
props = error before the gate); unknown types fall back to
KineticText. Bool is not a number - `to: true` fails the check.

Sync rules: beat duration >= read time (160 WPM); one visual on screen
unless `overlay: true`; no motion during narration cuts.

## Renderer selection

Default **Remotion** (this extension). Blender via `operate-blender`
when the visual is 3D. After-Effects JSX only if the user already has
AE. No paid TTS/ASR services; plan approval is a hard gate, always.

## Files

- `extensions/asr/` — transcribe + bootstrap.
- `extensions/remotion-render/` — `plan_check.py` (pre-gate validator:
  sync_range vs audio, overlap collisions, read-time + budget warnings),
  `render.py` (materialize template + render), `composite.py` (ffmpeg
  overlay onto source, narration-first audio), `templates/remotion-project/`
  (Root + PlanComposition + primitives).
- Plan contract extends `craft-bridge` scene_manifest v1 with
  `motion_spec` + `sync_range` (v2).
