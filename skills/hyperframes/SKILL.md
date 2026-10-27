---
name: hyperframes
description: Use when turning HTML/data-attribute animations into MP4 video (kinetic text, web-native motion graphics, DOM-driven scenes). Routes to extensions/hyperframes/wrapper.py, a whitelist passthrough to the hyperframes CLI over npx (Node >= 22 + FFmpeg required).
triggers: [user, model]
---

# Hyperframes

HTML-native animation to MP4 via `extensions/hyperframes/wrapper.py` --
thin passthrough to `hyperframes` over `npx -y hyperframes@latest`.
Animations are declared in HTML with data attributes; no React, no
bundler project required.

## Requirements

- Node.js >= 22 with `npx` (or `hyperframes` on PATH).
- FFmpeg on PATH for MP4 encode.
- Missing toolchain reports `status: missing` -- never fabricate.

## Commands

```bash
W=extensions/hyperframes/wrapper.py

python $W doctor                                   # node>=22, npx, ffmpeg, invoker
python $W init [dir]                               # scaffold a project
python $W render <project> [--output out.mp4] \
    [--fps 30] [--duration 10] [--width 1920] [--height 1080]
python $W render --input <project> [--output out.mp4]
```

`render` requires a positional project path or `--input`. Only
whitelisted flags (`--input --output --fps --duration --width --height`)
are forwarded; anything else is rejected as flag injection. Render
timeout is 600s; other commands 60s.

## Workflow

1. `doctor` once per session; confirm `node_ok` and invoker.
2. `init` a project dir or point `render` at an existing one.
3. `render` to MP4; check envelope `status` and `exit_code`.

## hyperframes vs remotion-render

- `hyperframes`: HTML + data attributes, web-native; best for quick
  kinetic text / DOM animations without a React toolchain.
- `extensions/remotion-render`: React/Remotion compositions; heavier,
  programmatic scenes driven by the animation-direction plan schema.
Choose hyperframes when the source is plain HTML; remotion-render when
the scene needs the React composition model.

## Boundaries

- Whitelisted subcommands (`doctor init render`) and flags only.
- No arbitrary CLI flag injection; no shell.
- Output bounded at 1 MiB per stream.
