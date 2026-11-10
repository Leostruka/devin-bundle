# R7-10 / GH #443 - raea vs Remotion render backend spike

Source: reel `DfgQMGEKGJG` (shane.shinyobjectz), survey row:
`.devin/research/2026-11-10-reels-batch7-survey.md` line 28 claims
"raea (Render Anything Engine): Rust+Bevy+Dioxus, React/TS
compositions on local GPU, raea render/play/cut/check, agent skills
installer, 10-20x vs Remotion claim". The transcript itself is a
song/monologue; the useful spec comes from primary sources below.

## What raea is (verified)

Primary sources:

- Repo: https://github.com/shinyobjectz/raea
- Docs: https://raea.io/docs/ , https://raea.io/llms.txt
- Bundled agent skill: https://github.com/shinyobjectz/raea/blob/main/sdk/skills/raea/SKILL.md

raea is the "Render Anything Engine": compositions written in
React/TypeScript (same `useCurrentFrame` / `Composition` /
`interpolate` API shape Remotion uses) drawn frame-by-frame by a
native GPU engine built on Bevy (Rust). CLI verbs include
`raea render` (MP4/PNG/frame dir, headless), `raea cut` (cut footage
by spoken words), `raea check` (clipped text, low contrast, unsafe
areas, freezes, loudness), `raea play` / `raea export-game` (games),
`raea sao` / `raea tokensynth` (foley/instrument audio). Build
requires Rust + bun + CMake. Runs locally, no account. The 10-20x
speed claim vs Remotion is vendor marketing (raea.io homepage:
renders on GPU "instead of screenshotting a browser"), not
independently benchmarked.

## Comparison vs current pipeline

Current pipeline (`skills/animation-direction/SKILL.md`):
narration -> `extensions/asr/transcribe.py` -> scene-plan v2 ->
`plan_check.py` gate -> `render.py` materializes
`templates/remotion-project/` -> `npx remotion render` ->
`composite.py` ffmpeg overlay (narration audio preserved, alpha
`.mov` / `--fit contain` PiP).

| Axis | Remotion (current) | raea |
|---|---|---|
| Composition model | React/TS, frame function | React/TS, frame function (API clone) |
| Render path | headless Chromium screenshot per frame + ffmpeg | native GPU draw + hardware encode |
| Speed | browser-bound | claimed 10-20x faster (vendor claim, unverified) |
| Maturity/ecosystem | established, large docs/community | new, single-author repo, Bevy 0.20 pin |
| Install | npx/node only | Rust toolchain + bun + CMake + platform deps |
| Validation hooks | none built in (bundle has plan_check.py) | `raea check` (clipped text, contrast, freezes, loudness) |
| Footage cutting | none | `raea cut` by transcript words |
| Extras | video only | games, 3D (glTF, splats), audio synth |
| Agent fit | works via CLI today | designed agent-first (frames queryable as data, ships own SKILL.md) |

Fit to this bundle: the plan-gate architecture (corrections at plan
stage, never post-render) transfers directly - scene-plan v2 would
materialize into a raea composition instead of the Remotion template.
`raea check` overlaps `plan_check.py`'s role but at render time
rather than plan time, which is complementary. `raea cut` overlaps
`extensions/asr` + composite timing, only useful if source footage
cutting enters scope.

## Recommendation: hybrid, Remotion stays default

- Keep Remotion as the default backend: zero new toolchain, mature,
  templates already exist (`templates/remotion-project/`).
- Add raea as an optional backend behind `render.py` (a
  `--backend raea` materializer + template), gated on a local
  toolchain probe (Rust/bun/CMake present). Value: render-speed for
  long reels, `raea check` as a post-render quality gate.
- Do not switch: single-author project risk, heavy native build on
  Windows CI, and the 10-20x claim is unverified. Spike cost is
  bounded (one template dir + backend branch in render.py).
- Revisit if/when raea gains a binary release or the bundle needs
  its game/3D lanes.
