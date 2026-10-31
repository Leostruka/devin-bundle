# blender-operator roadmap

## Katana camera blocking (implemented, spec: `.devin/scratch/egm-laya-bitnet-upgrade/`)

Canonical owner: `.devin/issues/MILESTONE_2_13_camera_blocking.md`.
This is an addendum for camera metadata, not a parallel implementation plan.

Shipped: `camera_blocking.py` orchestrates the full pipeline on top of the
existing TCP exec loop - it spawns its own `blender -b --factory-startup`
server on a dedicated port (default 19713), runs the presets, and shuts down
ONLY the process it spawned (pid + pinned nonce ownership checks; user
scenes and foreign servers are never touched):

- `presets/blockout.py`: minimal low-poly blocking set.
- `presets/camera_rig.py`: keyframed camera on `orbit` or `dolly` path -
  per-frame position, rotation, focal length.
- `presets/playblast.py`: viewport playblast to MP4 plus `<name>.camera.json`
  metadata (frame range, per-frame `matrix_world`/`location`/
  `rotation_euler`/`lens`) and a preview PNG.
- Handoff: the result is ingested via `media-tools/playblast_ingest.py`
  into a `<name>.handoff.json` descriptor for controlled video pipelines
  (Higgsfield Katana / Seedance style). No external service is contacted.

CLI:

```
python camera_blocking.py --out DIR [--name shot] [--fps 24] [--frames 48]
    [--width 640 --height 360] [--path orbit|dolly] [--radius 12]
    [--cam-height 5] [--lens 35] [--engine BLENDER_WORKBENCH|BLENDER_EEVEE_NEXT]
    [--port 19713] [--exe PATH] [--beats-per-second 1] [--force] [--keep-server]
```

Validated bounds live in `camera_blocking.LIMITS` (fps 1-120, frames 2-480,
16-4096 px, etc.). Smoke evidence: `.devin/scratch/egm-smoke-controller/`
(shot.mp4 h264 480x270 @24fps 24 frames + shot.camera.json +
shot.handoff.json); earlier `.devin/scratch/egm-smoke-l4/` kept as
historical evidence.

Constraints: headless only, no new deps without approval, output to temp or
explicit paths. Pending: no external Katana/Seedance submission exists -
the handoff descriptor marks `external_call: false`.
