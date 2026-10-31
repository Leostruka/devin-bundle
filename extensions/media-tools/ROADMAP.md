# media-tools roadmap

## Katana camera-blocking ingest (queued, spec: `.devin/scratch/egm-laya-bitnet-upgrade/`)

Consume `blender-operator` playblast + `camera.json` handoff for controlled
video generation (Higgsfield Katana / Seedance style):

- `ingest_playblast(mp4, camera_json)`: validate metadata (frame range,
  transforms, focal length) and stage a video-gen job bundle.
- Metadata surfaced to downstream tools unchanged; media-tools adds fx or
  conversion only when requested.

Constraints: stdlib-first, no cloud calls from this extension, secrets never
in repo.
