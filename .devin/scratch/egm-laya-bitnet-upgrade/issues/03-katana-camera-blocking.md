# Issue 03: Katana camera blocking (blender-operator + media-tools)

Status: roadmap notes landed in both extension dirs; build is future work.

## Scope

- `blender-operator`: low-poly blocking scene helper + camera track;
  export playblast MP4 plus `camera.json` metadata (per-frame position,
  rotation, focal length, frame range).
- `media-tools`: ingest handoff of playblast + metadata for controlled
  video generation pipelines (Higgsfield Katana / Seedance style).
- Everything headless via the existing TCP exec loop; no new deps without
  approval.
