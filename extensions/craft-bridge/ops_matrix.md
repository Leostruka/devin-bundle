# Craft suite ops matrix (verified 2026-10 via gh api users/storytold/repos)

All craft apps: Rust, Apache-2.0 (dual MIT/Apache for filmcraft/photocraft
per READMEs). spark: TypeScript, MIT (`@sparkjsdev/spark`).
Every app exposes `<app>-cli commands` / `exec` / `run` / `mcp`
(`exec` = one-shot, `run` = batch JSONL); several add `--control <port>`
JSON-lines channel.

| App | Domain | CLI | Channels | Consume for |
|---|---|---|---|---|
| filmcraft | video timeline | filmcraft-cli | cli, mcp | cut/trim/grade/mix/export, keyframed DSP |
| photocraft | image layers | photocraft-cli | cli, mcp | PSD read/write, layered TIFF, OpenEXR, Affinity read |
| vectorcraft | vector drawing | vectorcraft-cli | cli, mcp, --control 7979 | Illustrator-style ops |
| wordcraft | documents | wordcraft-cli | cli, mcp | 389 cmds ("built for agents") |
| pdfcraft | pdf | pdfcraft-cli | cli | combine/extract/split/render/text |
| gridcraft | spreadsheets | gridcraft-cli | cli, mcp, --control | Excel-style ops |
| deckcraft | slides | deckcraft-cli | cli, mcp, json | 200+ cmds |
| cadcraft | cad | cadcraft-cli | mcp, cli | AutoCAD-style ops |
| lightcraft | photo develop | lightcraft-cli | mcp, json-lines | RAW dev, agent-drivable end to end |
| soundcraft | audio | soundcraft-cli | cli, mcp, json | Pro-Tools-style ops |
| artcraft | concept/staging | (suite member) | - | scene staging concepts only |
| spark | gsplat render | npm @sparkjsdev/spark | js api | .PLY/.SPZ preview (see spark-view/) |
| craft-libs | shared codecs | cargo git dep | crates | RAW/codecs when an app misses a need |

### filmcraft live catalog (718 commands, verified 2026-11-17 on release 0.20.1)

Domain histogram: graphics 83, file 57, clip 57, timeline 57, sequence 51,
project 40, edit 39, multicam 35, markers 33, trim 24, captions 23,
mixer 20, export 19, media 17, effects 16, shortcuts 16, playhead 14,
transcript 14, masks 12, mediaBrowser 10.

Confirmed coverage: razor, ripple (5), slip (5), slide (5), roll, nest (3),
rateStretch, clip.synchronize, transitions (6), lumetri.* (8: presets,
setInputLut, setLook, applyMatch, exportCube), sequence.colorSettings,
mixer.* (24 incl. setKeyframe), effects.*Keyframe (8), export.presets.* +
sequence.render* (8), multicam.* (35), captions + transcript (37 total).

Mapping caveat: motion/position/scale/opacity/blend have no dedicated
commands - they dispatch through `effects.apply` + `effects.setParam` +
keyframe ops. scene_manifest must target effect-param paths, not verb ids.

True gaps: no warp-stabilizer analog; proxy workflow is presets-only
(`media.proxyPresets`, no create/attach).

ops_map.json seam vocabulary verified against this catalog
(2026-11-17): cut->timeline.razor, grade->lumetri.applyPreset,
mix->clipMixer.set, export->export.quick, text->graphics.newText,
layer->file.newAdjustmentLayer, render->sequence.renderInToOut;
trim/open/save ids exist verbatim. Seven prior ids (timeline.cut,
color.grade, audio.mix, file.export, text.insert, layer.add,
render.frame) did not exist and were corrected.

## Coverage vs our needs

| Need | Covered by | Gap filler |
|---|---|---|
| Video timeline edit | filmcraft commands | manifest->command mapper (ours) |
| Image layers / PSD | photocraft commands | same mapper |
| Vector | vectorcraft | same mapper |
| Docs/sheets/slides/PDF | word/grid/deck/pdf CLIs | same mapper |
| CAD/audio/photo-dev | cad/sound/light | on demand |
| gsplat preview | spark + three.js | spark-view/ static page (ours) |
| Scene staging contract | none upstream | scene_manifest.py (ours) |
| Stylistic FX | none needed | extensions/media-tools (existing) |

## Non-goals

No engine reimplementation, no forking craft apps, no GUI automation.
Fallback order on a command gap: craft-libs crate -> ffmpeg/Pillow
gap-filler in media-tools.
