# ISSUE 05: PPISP camera-model inversion for clean 3D reconstruction

Status: planned (research done) · Source: transcript (user-provided) + NVIDIA `nv-tlabs/ppisp` (research.nvidia.com/labs/sil/projects/ppisp) · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- Transcript describes NVIDIA's **PPISP** (Physically-Plausible ISP): instead of fixing the scene, the model learns how each camera distorted each frame, then inverts it. Verified upstream:
  - **Exposure compensation** (per-frame), **vignetting** (radial falloff, per-camera), **color correction** via chromaticity homography (WB drift, per-frame), **CRF** nonlinear tone mapping (per-camera).
  - A **controller** trained on input views predicts per-frame corrections for novel views (analogous to auto-exposure/AWB), freezing scene params during distillation.
  - Result: photometric inconsistencies stop being baked into geometry as floaters/ghosts; clean 3DGS/NeRF from ordinary phone captures.
- Value: direct upgrade to `ai3d-gen`/gsplat intake quality and to Issue 02 (PRNU is per-sensor too; PPISP models complementary per-camera effects). Also a capture-preprocessing gate: score input-photo photometric variance before spending a reconstruction run.

## Brain (Skill)

- **Update `ai3d-gen`**: add photometric-QC stage before splatting, variance flags (exposure/WB spread across set), recommend PPISP correction pass when capture mixing devices/conditions.
- **Touch `image-forensics`** (Issue 02): PRNU fingerprint vs PPISP-modeled vignette/CRF are complementary camera models; document which signal answers which question (provenance vs photometric correction).
- Optional `radiance-prep` notes inside `ai3d-gen`: when to re-capture vs correct.

## Muscle (Extension)

`extensions/ppisp-prep/` (Python, venv like laya-tools):

- `photo_qc.py`: cheap pre-check on an image set, exposure/WB/vignette spread report → `go / correct / recapture` verdict JSON.
- `ppisp_runner.py`: wrap `nv-tlabs/ppisp` (upstream code, check its license at clone time): train PPISP+controller on the capture set, emit corrected frames + per-camera report (exposure/vignette/color/CRF plots upstream already generates).
- Downstream hook: corrected set feeds the existing `ai3d-gen` 3DGS/ComfyUI path.

## Step-by-step (on authorization)

0. Clone `nv-tlabs/ppisp`, verify license + env requirements (torch, CUDA optional); read upstream training entry points.
1. `photo_qc.py` on a real mixed-device photo set; calibrate variance thresholds.
2. `ppisp_runner.py` end-to-end on the same set; gate: corrected render vs raw render floaters visible diff + upstream metrics.
3. Wire into `ai3d-gen` intake (skill edit); document camera-mix guidance.
4. Held-out check (Rule 15): fresh capture set, measure reconstruction-quality delta.

## Non-goals

No reimplementation of the PPISP network, no NeRF training infra beyond upstream defaults, no GPU mandate (CPU fallback slow path acceptable for prep stage).
