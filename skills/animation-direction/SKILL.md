---
name: animation-direction
description: Use when turning narrated video/audio into synced code-rendered motion graphics — narration -> timestamped transcript -> scene plan -> approval gate -> Remotion render -> ffmpeg composite. Covers the motion vocabulary, beat-to-visual mapping, scene-plan v2 schema, and the mandatory plan gate via extensions/asr + extensions/remotion-render.
---

# Animation Direction

Motion-graphics direction without a video editor: "explain X" -> synced
b-roll/infographic animation. Corrections happen at the cheap plan
stage, never post-render.

## VIDEO.md (durable brief, written first)

Every piece starts as `VIDEO.md` in the output directory, the single
source of truth that survives context compaction: goal, audience,
aspect/duration, copy, timed shot list, palette/type, motion direction,
sound, assets, constraints, approval state, and build notes. The plan
derives from it; corrections update it; the render is accountable to it.
A piece without VIDEO.md is improvised, and improvisation is where slop
comes from. Before the approval gate, check the plan against
`reference/slop-video-patterns.md` - a plan containing a listed
anti-pattern is not ready.

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
unless `overlay: true`; no motion during narration cuts. Audio/visual
offsets are allowed at cut boundaries (J-cut: audio leads the next
visual; L-cut: audio outlives the visual) -- the prohibition is on
motion *during* the narration cut itself.

## Preview and fix loop (before any MP4 render)

Rendering is the expensive step; everything before it should be cheap.

1. **Preview in the browser, not in your head.** Serve the unrendered
   composition (Remotion Studio: `npx remotion studio` in the generated
   project) so the reviewer can play and scrub the real timing. A plan
   approved only as JSON gets rejected as video.
2. **Timestamped notes, batched by scene.** Reviewer feedback is collected
   as `{timecode, scene_id, text}` notes and grouped per scene before any
   edit. Classify each note: small fix (copy, font size, dimensions,
   colors, timings) or design change (layout, structure, new scenes).
3. **Small fixes go to the scoped fixer.** The `video-fixer` agent profile
   applies small fixes only and bounces design changes back. Design
   changes return to the plan stage and re-enter the approval gate -
   they are never smuggled into the fix loop.
4. **Verify by measurement first.** DOM geometry, exact beat/cut times,
   font and color values, viewport behavior, asset dimensions. Screenshots
   are the fallback for questions measurement cannot answer (composition
   feel, overlap artifacts), and when needed they are cropped to the
   region in question, never full-frame dumps.
5. **Render MP4 only after explicit approval** of the previewed result,
   recorded in VIDEO.md's approval state. "Looks good so far" in chat is
   not approval.

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
- Plan contract is the scene-plan schema v2 (`motion_spec` +
  `sync_range`).
