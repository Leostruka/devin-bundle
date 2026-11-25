# ISSUE 05: PPISP camera-model inversion for clean 3D reconstruction

Status: implemented + synthetic-validated 2026-11-25 (steps 0-3 done; step 4 real-capture held-out user-gated - needs physical captures + COLMAP) · Source: transcript (user-provided) + NVIDIA `nv-tlabs/ppisp` (research.nvidia.com/labs/sil/projects/ppisp) · Ledger: `.devin/research/4_fronts_recon.md`

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
   - DONE 2026-11-17 (remote verification, no local clone yet): Apache-2.0, 474 stars, Python. Layout: `ppisp/` package + `tests/` + pyproject/setup.py. Env reality: torch runtime dep AND a compiled CUDA extension via `torch.utils.cpp_extension` - upstream recommends `pip install . --no-build-isolation` so the kernel builds against the local torch ABI. Not "CUDA optional": the differentiable kernel requires a CUDA build toolchain (nvcc) + GPU for training. Training entry point documented in README (controller distillation loop). Local clone still needed for step 2 e2e.
1. `photo_qc.py` on a real mixed-device photo set; calibrate variance thresholds.
2. `ppisp_runner.py` end-to-end on the same set; gate: corrected render vs raw render floaters visible diff + upstream metrics.
3. Wire into `ai3d-gen` intake (skill edit); document camera-mix guidance.
4. Held-out check (Rule 15): fresh capture set, measure reconstruction-quality delta.

## Progress (2026-11-09 audit)

- Landed: `extensions/ppisp-prep/` (photo_qc.py, ppisp_runner.py) + tests/test_ppisp_prep.py (10 tests, green) + ai3d-gen SKILL.md intake wiring (step 3)
- DONE 2026-11-09 (partial): `photo_qc.py` live-verified on real captures - scan series `_scan_h*.jpg` (7 same-session webcam frames) -> verdict `go` (exposure spread 0.005, wb 0.0, vignette 0.004); mixed 30-image dir -> `correct` (exposure 0.137, vignette 0.131 - moderate drift correctly flagged). Thresholds behave as documented on real data
- DONE 2026-11-25 (partial): upstream cloned to
  `.devin/scratch/ppisp_upstream` (depth 1, Apache-2.0 verified on
  disk; kept out of `extensions/` because audit contract checks scan
  vendored trees; the runner resolves it via `PPISP_DIR` env or the
  default `extensions/ppisp-prep/ppisp_upstream` path, the latter now
  gitignored).
  **Env blocker pinned**: local torch is `2.15.0+cpu`
  (cuda.is_available False) and upstream `setup.py` builds a
  `CUDAExtension` unconditionally.
- DONE 2026-11-25: env blocker CRACKED via userland WSL2 path, zero
  admin installs, zero Windows-env mutation (full recipe in ledger
  iteration 25): torch 2.13.0+cu129 in venv + CUDA 12.9 toolkit from 6
  repo .debs extracted userland (~42MB, no 5.8GB runfile). ppisp 1.3.0
  CUDA extension built for sm_86; upstream pytest suite 235/235 PASSED
  on the real RTX 3050 (kernel-vs-torch equivalence, gradcheck,
  regularization). Windows-side blocker re-pinned: no MSVC present at
  all (vswhere empty) - WSL2 is the supported path.
- ppisp_runner redesign (same day): upstream is a LIBRARY (no train.py
  exists) - run() now errors honestly `integration_required`; smoke()
  drives upstream's pytest suite; doctor() reports torch_cuda +
  ppisp_importable + upstream_kind. Tests updated 12/12.
- DONE 2026-11-25 (step 2, synthetic validation): integration harness
  `extensions/ppisp-prep/synth_harness.py` - gsplat + ppisp in one
  training loop in WSL2. Evidence matrix (novel-view PSNR delta vs
  baseline, positive = ppisp better; raw = scene cleanliness,
  corrected = controller-inference output):
  - strong corruption (expo U(0.7,1.4), wb +-10%, vig 0.35), 4 seeds:
    corrected +2.12/+1.39/+2.30/+2.59 (mean +2.10dB, min +1.39),
    raw +1.14/+1.31/+2.22/+1.82. 3/4 clear the 2dB gate, ALL positive
    - reliable win at strong variation.
  - control (zero corruption): raw +0.30, corrected +1.07 - ppisp does
    NOT hurt clean training (safety for the ai3d-gen wiring).
  - realistic drift (expo U(0.9,1.1), wb +-3%, vig 0.15), 3 seeds:
    corrected +0.80 / -1.20 / +1.64 (mean +0.41), raw +0.51 / -1.66 /
    +1.04. HIGH VARIANCE, one negative - the strong-corruption benefit
    does NOT transfer reliably to mild drift.
  Recommendation sharpened: wire ppisp when capture sets show strong
  per-frame appearance variation (photo_qc spread large / mixed-device
  / outdoor changing light); for mild uniform drift the benefit is a
  seed lottery around zero. photo_qc's role as the gating instrument
  is thereby confirmed as necessary, not optional.
  Protocol + artifacts: `.devin/scratch/si-20261125/synth_ppisp_*.json`,
  ledger iterations 25-26b. Remaining for full step 2: real multi-view
  capture validation (user captures + COLMAP; DTU substitute declined -
  format adaptation cost vs marginal evidence over the proven causal
  claim).
- DONE 2026-11-25 (step-1 calibration evidence, VISION): photo_qc run
  over 5 devices x (flat, nat) sets (artifact
  `.devin/scratch/prnu-vision/photoqc-calibration-2026-11-25.json`).
  - Flat (controlled uniform-field, closest proxy to ideal capture
    series): 3/5 `go` (D02/D03/D05, all spreads well inside GO), 2/5
    marginal `correct` on wb alone (D15 0.032 vs 0.03 threshold; D24
    0.065). Consistent with PPISP's thesis: real devices drift even in
    controlled series, correction is genuinely needed. Thresholds NOT
    changed: the measured behavior is plausible discrimination, not
    threshold error.
  - Nat (varied scenes, off-design negative control): all `correct`,
    none `recapture`/`go`. Vignette spread is the strongest channel
    (flat 0.001-0.015 vs nat 0.083-0.18, 10-50x separation) but on
    varied scenes it measures SCENE consistency, not lens falloff -
    semantics documented as a proxy, confirmed behaving as such.
  - `recapture` verdict untriggered: no pathological series in evidence
    base; remains validated only by unit fixtures.
- Step-4 held-out protocol designed (Rule 15, recorded for the e2e
  run once env lands):
  - Capture: fresh phone set (>=20 frames, mixed lighting) NOT used for
    photo_qc threshold calibration - calibration data and held-out data
    must not share frames.
  - Split: even-numbered frames -> PPISP training input; odd frames ->
    held-out evaluation views (never seen by the controller).
  - Metrics: (a) upstream's own reports (exposure/vignette/color/CRF
    per-camera parameters), (b) photometric consistency delta: std of
    per-frame exposure+WB residuals over held-out views, corrected vs
    raw, (c) downstream: 3DGS render of the corrected set vs raw set on
    the same held-out views, floaters/PSNR delta.
  - Gate: pass = held-out photometric variance drops >=30% after
    correction AND the corrected reconstruction renders on the real
    set; abstain = upstream training fails or delta <10% (weak signal,
    needs more frames not a lower bar).

## Non-goals

No reimplementation of the PPISP network, no NeRF training infra beyond upstream defaults, no GPU mandate (CPU fallback slow path acceptable for prep stage).
