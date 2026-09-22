---
name: operate-spline
description: Use when the user asks to launch, drive, build scenes in, export from, or shut down the Spline desktop app (3D/2D design, Electron). Routes to extensions/spline-operator/wrapper.py, which speaks the app's embedded MCP bridge (ws://127.0.0.1:19692) — structured tool calls, not GUI clicking.
---

# Operate Spline

Drive the installed **Spline** desktop app (Electron, 3D + 2D/"Hana" design tool)
through its official embedded MCP bridge. No computer-use, no UIA, no CDP —
the app itself publishes a tool manifest.

## Anatomy (verified)

- Install: `%LOCALAPPDATA%\Programs\Spline\` — `Spline.exe`, `resources\app.asar`,
  `resources\spline-mcp.cjs` (the bridge), `elevate.exe`.
- `spline-mcp.cjs` = Node script. Hosts a **WebSocket server on
  `ws://127.0.0.1:19692`** (env `HANA_MCP_PORT` overrides) AND an MCP-stdio
  transport. It dies on stdin EOF — the wrapper's keeper daemon handles this.
- The Spline app connects to the bridge as "editor" and pushes a **manifest of
  36 tools**. Agents connect with `{"type":"hello","role":"agent"}` and MUST
  send `Origin: hana-mcp-agent` (allowlist: app.spline.design, localhost, agents).
- Dispatch: `{"type":"call","id":...,"name":...,"args":{...}}` → `{type:"result"|"error"}`.

## Wrapper commands

```bash
W=extensions/spline-operator/wrapper.py

python $W launch [--file path.spline] [--timeout 60]  # bridge daemon + app + wait manifest
python $W status                                       # bridge/editor/pids
python $W tools                                        # manifest w/ descriptions
python $W call 3d_run_code '{"code":"..."}'            # dispatch a tool
python $W kill                                         # clean shutdown (app + bridge + daemon)
```

All output is JSON; exit 0 = ok. `launch` blocks until the editor's manifest
arrives or the timeout expires — never poll without it.

## The tool surface (36 tools, manifest-pushed — always verify with `tools`)

Two domains: `3d_*` (Spline scenes) and `2d_*` (Hana HTML/CSS files).

| Workflow | Tools |
|---|---|
| Build/edit 3D scene | `3d_run_code` (Spline editor DSL — JS alias functions), `3d_get_objects`, `3d_update`-family via run_code |
| Inspect scene | `3d_get_scene`, `3d_analyze_scene`, `3d_get_scene_mcp`, `3d_get_objects` |
| Camera/render | `3d_set_view`, `3d_take_screenshot`, `3d_generate_image`, `3d_generate_3d_model` |
| 2D files | `2d_create_file`, `2d_write_html`, `2d_export_html`, `2d_get_canvas_state`, `2d_review_frame`, `2d_add/update/move/delete/duplicate_objects`, `2d_generate_images`, `2d_edit_image`, `2d_recolor`, `2d_reserve_frames`, `2d_find_space`, `2d_upload_assets`, `2d_resize_frame`, `2d_get_object`, `2d_get_scene` |
| Meta | `3d_load_skill`, `2d_load_skill` — fetch authoring guides (see below); `3d_create_file`, `3d_get_generation`, `3d_set/edit/get_html_content` |

## Mandatory session protocol

1. `launch` once → manifest arrives (36 tools).
2. **Before the first `3d_run_code`: load the 3D authoring contract** —
   `call 3d_load_skill {"name":"authoring-guide"}`, then `authoring-guide-2`,
   then `authoring-guide-3`. The DSL, conventions, and quality bar are in
   those docs, NOT in your training data.
3. For 2D work: `2d_load_skill` `authoring-guide` + `authoring-guide-2`,
   plus `glass`/`3d`/`layer-noise`/`mobile-app`/`interactivity` per design needs.
4. Do NOT call `*_create_file` at task start — scene tools auto-create a file.
5. `kill` when done. Always.

## Boundaries

- Never modify `Spline.exe`, `app.asar`, or `spline-mcp.cjs` — read-only recon.
- Never touch `%APPDATA%`/`%LOCALAPPDATA%` Spline user data.
- `--file` on launch passes the path as a Spline.exe argv (Windows file-open);
  for in-app project ops prefer tool calls after launch.
- If the manifest is absent after `launch`, run `status` — the app may still be
  booting; do not re-launch or spawn duplicates.
