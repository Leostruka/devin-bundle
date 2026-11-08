# image-forensics held-out eval - first real-data run (2026-11-09)

Rule 15 step for ISSUE_02. Synthetic-fixture tests had shown clean
PCE separation; this run tests real camera JPEGs vs code-rendered
synthetic frames. Harness: `extensions/image-forensics/eval_set.py`.

## Protocol (no calibration leakage)

- REF: 4 webcam JPEGs `_scan_h{40,80,120,160}.jpg` (640x360,
  sequential heights, same session) -> `ref.npy` via `--build-ref`
- REAL held-out: `_scan_h{200,240,280}.jpg` - never in ref
- SYNTH: 10 frames extracted from Remotion renders
  (`anim-e2e/final-narrated.mp4`, `render-proof.mp4`) - pure digital
  content, zero camera pixels. 5 at 640x360, 5 at 1920x1080.
- Thresholds: defaults `pce_real=50`, `pce_synth=10`.

Contamination note: first synth attempt used camera-project proof
PNGs which embed camera frames - correctly scored real_capture;
replaced with pure-render frames.

## Results

| class | n | real_capture | synthetic | inconclusive | decided_acc |
|---|---|---|---|---|---|
| real held-out | 3 | 3 | 0 | 0 | 1.00 |
| synth 640x360 | 5 | **5** | 0 | 0 | 0.00 |
| synth 1920x1080 | 5 | 0 | 0 | 5 | abstain |

PCE values: real ~628-635; synth-JPEG ~130-187; synth-PNG-source
frames hit `low_residual_energy` floor -> inconclusive (correct
abstain per design).

## Finding

Default `PCE_REAL=50` false-positives on JPEG-domain synthetic
content: rendered frames re-encoded as JPEG score 130-187 against a
ref built from 4 same-encoder webcam JPEGs. The ref residual is
dominated by the shared JPEG quantization signature, not isolating
sensor PRNU - all JPEGs correlate with it.

Separation DOES exist on this data: real ~630 vs synth ~130-190
(3.3-4.8x gap). `pce_real=300` would classify correctly here, but
that is post-hoc tuning on n=3 - not a fix, a demonstration that
thresholds are per-domain as documented.

## Recommendations

1. `verdict.py`/`eval_set.py`: surface `ref_error` notes as their own
   bucket (shape-mismatched images currently fold into inconclusive).
2. Document JPEG-domain caveat in SKILL.md: PRNU ref built from
   camera JPEGs cannot distinguish other JPEGs; prefer lossless
   captures for ref, or require PNG/TIFF camera originals.
3. Optional hardening: high-pass residual to suppress 8x8 DCT-grid
   correlation before PCE (research item, not implemented).
4. Re-run held-out with >=10 ref images across sessions/devices
   when a proper dataset is assembled (still pending external data).

Artifacts (local only, personal camera frames - not committed):
`.devin/scratch/if-eval/{ref,real,synth}/`, `ref.npy`.
