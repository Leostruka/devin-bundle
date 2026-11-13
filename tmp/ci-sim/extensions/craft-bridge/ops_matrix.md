# Craft suite ops matrix (verified 2026-10 via gh api users/storytold/repos)

All craft apps: Rust, Apache-2.0 (dual MIT/Apache for filmcraft/photocraft
per READMEs). spark: TypeScript, MIT (`@sparkjsdev/spark`).
Every app exposes the trio: `<app>-cli commands` / `run` / `mcp`;
several add `--control <port>` JSON-lines channel.

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
