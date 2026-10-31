# Issue 03: Katana camera blocking (blender-operator + media-tools)

Status: implemented locally. Canonical owner remains
`.devin/issues/MILESTONE_2_13_camera_blocking.md`; this is its
camera-metadata addendum - no duplicate presets were created.

## Shipped

- `blender-operator/camera_blocking.py` + `presets/blockout.py`,
  `camera_rig.py`, `playblast.py`: isolated factory-startup blender server
  (owned pid + nonce), orbit/dolly camera track, playblast MP4 +
  `<name>.camera.json` + preview PNG.
- `media-tools/playblast_ingest.py`: ffprobe + camera.json agreement
  validation -> `<name>.handoff.json` (`kind: camera-blocking-handoff`,
  `external_call: false`).
- Smoke evidence: controller run `.devin/scratch/egm-smoke-controller/`
  (shot.mp4 h264 480x270 @24fps 24 frames, shot.camera.json,
  shot.handoff.json). Earlier `.devin/scratch/egm-smoke-l4/` kept as
  historical evidence.

## Open

- No external Katana/Seedance submission - the handoff descriptor is a
  local staging artifact only; do not describe this as an end-to-end
  external service.
