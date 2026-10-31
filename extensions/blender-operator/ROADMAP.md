# blender-operator roadmap

## Katana camera blocking (queued, spec: `.devin/scratch/egm-laya-bitnet-upgrade/`)

Add a low-poly camera-blocking helper on top of the existing TCP exec loop:

- `blocking_scene(primitives)`: build a minimal low-poly set (boxes/planes)
  for shot blocking.
- `camera_track(keys)`: keyframed camera with per-frame position, rotation,
  focal length.
- `export_playblast(path)`: viewport playblast to MP4 plus `camera.json`
  metadata (frame range, per-frame transform, lens) for controlled video
  pipelines (Higgsfield Katana / Seedance style).

Constraints: headless only, no new deps without approval, output to temp or
explicit paths.
