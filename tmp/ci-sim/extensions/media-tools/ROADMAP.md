# media-tools roadmap

## Katana camera-blocking ingest (implemented, spec: `.devin/scratch/egm-laya-bitnet-upgrade/`)

Canonical owner: `.devin/issues/MILESTONE_2_13_camera_blocking.md`.
This addendum's ingest helper is shipped: `playblast_ingest.py` validates a
Blender playblast (MP4 + `camera.json`) and emits a local handoff job
descriptor for camera-preserving repaint pipelines (Higgsfield Katana /
Seedance class). Stdlib only; no external calls.

- `ingest_playblast(mp4, camera_json=None, out=None, preview=None,
  beats_per_second=1)`: `ffprobe` the MP4, validate `camera.json` schema
  (fps, frame_start/end, per-frame `matrix_world`/`location`/
  `rotation_euler`/`lens`), and check metadata/probe agreement
  (fps +/-0.5, frames +/-2, resolution +/-4). Mismatch or missing files raise
  typed errors; an existing output is never overwritten.
- Descriptor: `kind: "camera-blocking-handoff"` with probed video facts,
  camera summary and a `prompt_template` of timed beats (per-timestamp
  camera pose sampled at `--beats-per-second`). `target.external_call`
  is `false` - staging only, no video-gen service is invoked.
- Metadata surfaced to downstream tools unchanged; media-tools adds fx or
  conversion only when requested.

CLI:

```
python playblast_ingest.py <playblast.mp4> [--camera camera.json]
    [--preview preview.png] [--out handoff.json] [--beats-per-second 1]
```

Constraints: stdlib-first, requires `ffprobe` (`FFPROBE_EXE` or PATH), no
cloud calls from this extension, secrets never in repo. Pending: actual
submission to an external Katana/Seedance endpoint is not implemented and
not claimed.
