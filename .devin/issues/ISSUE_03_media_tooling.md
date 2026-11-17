# ISSUE 03: Advanced Media Tooling, consume storytold engines (MCP/CLI/crates), build only gaps

Status: in-progress · Source: `github.com/storytold` (44 repos) · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- storytold's craft suite is **agent-native by design**: every UI action is a typed command in one registry; the same commands dispatch via CLI, a JSON control channel, and a built-in **MCP server**. Verified:
  - `filmcraft`: 650+ engine commands, `filmcraft-cli commands` lists them, `filmcraft-cli mcp` runs headless MCP. Cut/trim/grade/mix/export, keyframed DSP, real text engine. License MIT OR Apache-2.0.
  - `photocraft`: 500+ commands, `photocraft-cli run` headless open/edit/save, JSON channel + MCP server. Real PSD read/write (standalone `photocraft-psd` crate), layered TIFF, OpenEXR, Affinity read. License MIT OR Apache-2.0.
  - `spark`: npm `@sparkjsdev/spark`, MIT; gsplat render/edit for `ai3d-gen` previews.
  - `craft-libs`: shared Rust crates consumable via git dep (MIT/Apache).
- Decision (user): **use their engines where licensing permits; build only the seam and the gaps.** No wheel reinvention: our `compose`/`timeline` ideas mostly map to existing photocraft/filmcraft commands.

## Inventário agent-nativo (verificado nos READMEs)

Todo app craft expõe o mesmo trio: **CLI + JSON control channel + MCP server**.

| App | Equivale a | Comandos / acesso |
|---|---|---|
| filmcraft | Premiere | 650+ cmds, `filmcraft-cli mcp` (headless) |
| photocraft | Photoshop | 500+ cmds, `photocraft-cli run`, MCP |
| vectorcraft | Illustrator | cmd API + `--control 7979` + MCP |
| wordcraft | Word | 389 cmds, MCP + CLI ("Built for agents") |
| pdfcraft | Acrobat | `pdfcraft-cli` combine/extract/split/render/text |
| gridcraft | Excel | MCP + CLI + `--control` JSON channel |
| deckcraft | PowerPoint | 200+ cmds, CLI + JSON + MCP |
| cadcraft | AutoCAD | MCP badge, agents/CLI |
| lightcraft | Lightroom | "drivable end to end by AI agents over MCP", JSON-lines channel |
| soundcraft | Pro Tools | cmds via menus/CLI/JSON/MCP |
| spark | gsplat renderer | npm `@sparkjsdev/spark` |
| craft-libs | shared codecs (RAW etc.) | crates via git dep |

## Absorção proposta

| Capability | Consume (primary) | Build only if gap |
|---|---|---|
| Video timeline edit | filmcraft MCP (`filmcraft-cli mcp`) or CLI | manifest→command mapper |
| Image layers / PSD | photocraft MCP/CLI | same mapper |
| Vector drawing | vectorcraft MCP/`--control` | same mapper |
| Docs/sheets/slides/PDF | word/grid/deck/pdf-craft CLIs + MCP | same mapper |
| CAD / audio / photo-dev | cad/sound/light-craft MCP | on demand |
| gsplat render/preview | `spark` npm + three.js viewer | `spark-view` static preview page |
| Scene staging before generation | artcraft concept | `scene_manifest.json` (ours, cross-engine contract) |
| RAW/codec needs | craft-libs crates via git dep | promote only when needed |

## Brain (Skill)

- **Update `media-tools` / `creative-engineering`**: manifest-first authoring stays, but dispatch targets change: prefer filmcraft/photocraft MCP commands; document command discovery (`filmcraft-cli commands`, `photocraft-cli` equivalents) and JSON channel protocol. `mcp-governance` applies, lazy-enable per task (Rule: MCP context tax).
- Routing: `media-tools/intent.py` (laya) picks filmcraft vs photocraft vs manifest path.

## Muscle (Extension)

`extensions/craft-bridge/` (thin, not a new engine):

- `bridge.py`: spawn/attach to any `*-cli mcp` or `--control` channel across the suite; normalized `run_command(app, command_id, params)` + `list_commands(app)` (uniform registry across all 10 apps).
- `scene_manifest.py`: our JSON scene/timeline spec → command sequences routed to the right craft engine (the cross-engine contract Issue 04 also consumes).
- `spark-view/`: static three.js + spark page rendering `.PLY/.SPZ` for `ai3d-gen` output checks.
- Gap-fillers only after command audit: whatever ops the registries lack (our existing fx pipeline already covers stylistic work).

## Step-by-step (on authorization)

0. **Repo exploration pass**: enumerate all 44 `storytold` repos via GitHub API; triage into craft-apps / shared-libs (craft-libs) / ML-audio / legacy-capture / infra; shallow-clone the craft suite + craft-libs; inspect actual crate layout, command registries, MCP/CLI entry points, build requirements per repo. README claims get verified against source before committing to consume.
   - DONE 2026-11-17 (enumeration + triage): 82 public repos verified via `gh api` (org grew from 44). Full categorized table + license audit in `.devin/research/2026-11-17-storytold-repo-triage.md`. Source spot-check: filmcraft ships `.mcp.json` + Cargo workspace; consume-first set identified (photocraft/filmcraft/vectorcraft/lightcraft/effectcraft/gridcraft/deckcraft, all Apache-2.0).
   - DONE 2026-11-17 (source probe, `.devin/scratch/storytold-probe/`): shallow clones confirm the architecture. filmcraft = workspace with 31 crates + `apps/{filmcraft,filmcraft-cli,filmcraft-web}`; `.mcp.json` wires `target/release/filmcraft-cli mcp --bridge|--demo`; commands dispatch via `CommandSpec {id,label,menu,shortcut,params,enabled,run}` registry + `find(id)` - ~200-260 registered commands in `crates/engine` alone across 15 `commands()` providers. `run <script.jsonl>` accepts `{"id","params"}` lines directly - our `scene_manifest` maps 1:1. craft-libs = 176-crate workspace (aaf/aep/affinity/captions/control-protocol/format crates per app).
   - DONE 2026-11-17 (live CLI verify): official release binary `filmcraft-0.20.1-windows-x64-portable.zip` runs on this machine - NO local build needed. `filmcraft-cli commands --json` returns **718 commands** (claim was 650+). `mcp --demo` spawns and speaks MCP JSON-RPC (rejects malformed init with proper error). Step 1 for filmcraft is verified-complete; releases exist for windows-x64/arm64, linux (deb/AppImage/flatpak), freebsd - same pattern likely covers other craft apps.
1. Install/build the craft CLIs needed (filmcraft, photocraft, word/pdf/grid/deck-craft; cargo or releases); verify headless commands + `*-cli mcp` spawn on this machine.
   - Prefer official release binaries over cargo builds (verified 2026-11-17); `cargo build --release` exists as fallback (toolchain present, deps fetched OK before disk-full abort).
2. Audit command catalogs vs needed ops; produce `ops_matrix.md` (coverage map per app).
   - DONE 2026-11-17 (filmcraft): `ops_matrix.md` carries the live 718-command catalog audit - all needed timeline/edit/mixer/export/captions ops present; motion/position/scale map through `effects.apply`/`effects.setParam` + keyframes; true gaps = no warp-stabilizer analog, proxy = presets-only.
3. `bridge.py` + mcp_config entries (lazy-enabled); smoke: open→edit→export a PSD and cut+export a video clip via commands only.
   - DONE 2026-11-17 (contract fix, PRs #674/#676/#678/#684): bridge previously emitted a nonexistent `run --command --params` argv. Corrected to the verified contract - `run_command` -> `exec <id> <json>`, `run_script`/`script` subcommand -> `run -` JSONL batch, `list_commands` -> `commands [filter] --json`, `McpClient` -> `mcp` stdio JSON-RPC (17 tools live-verified: command_run/batch/list, doc/sequence/project_inspect, media_import, render_frame/preview, ui_*). `ops_map.json` seam ids corrected against the 718-command catalog (7 invented ids fixed). Remaining: mcp_config entries, PSD/video smoke.
4. `scene_manifest` schema v1 + mapper to filmcraft/photocraft command sequences; golden-output tests.
5. `spark-view` preview for splat assets.
6. Update skills (`media-tools`, `creative-engineering`, `mcp-lazy-enablement` entry).

## Progress (2026-11-09 audit)

- Landed: `extensions/craft-bridge/` (bridge.py, ops_matrix.md, scene_manifest.py, spark-view) + tests/test_craft_bridge.py (15 tests, green); media-tools skill references craft engines
- 2026-11-17: filmcraft steps 0-3 verified against release binary; bridge contract corrected end-to-end
- Pending: mcp_config entries + PSD/video smoke (step 3 remainder), steps 4-6 (golden-output tests, spark-view preview check on this machine)

## Non-goals

No reimplementation of compositor/timeline engines, no forking craft apps, no GUI automation. Fallback order if a command gap persists: craft-libs crate → ffmpeg/Pillow gap-filler in `media-tools`.
