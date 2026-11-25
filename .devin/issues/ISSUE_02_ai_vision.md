# ISSUE 02: Cognitive Vision (image provenance & PRNU forensics)

Status: resolved 2026-11-25 (all 5 steps done; held-out validated on never-calibrated VISION devices) · Source: IG `DeRX9KpJPlT` (@plattipusofficial) + Lukáš/Fridrich/Goljan 2006 + Corvi et al. ICASSP 2023 · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- Reel method: every camera stamps **PRNU** (photo-response non-uniformity, per-pixel silicon variance) on captures; synthetic images have none. Metadata/"AI info" labels die on screenshot; pixel noise doesn't.
- Value: agent gains a cheap provenance check, real-vs-synthetic plus "which camera took this", used by `ai3d-gen`/gsplat intake (splats need real photos), `fact-check` (visual evidence), media ingestion (trust tagging).

## Method pipeline (literature)

1. **Metadata first pass**: EXIF/XMP/C2PA. Fast verdict when present; absence ≠ synthetic.
2. **Noise residual**: wavelet denoising (Mihcak/BDWT) or guided/Wiener filter → extract high-freq residual = fingerprint candidate.
3. **Reference pattern**: camera PRNU from N flat-ish real photos (averaged residuals).
4. **PCE score**: peak-to-correlation-energy of residual × reference; empirical threshold (Goljan: PCE ~50-60 discriminates; calibrate locally).
5. Verdict: `real_capture` / `synthetic` / `inconclusive` + confidence + which camera.

## Brain (Skill)

- **New `image-forensics` skill**: when-to-use, evidence ordering (metadata→residual→PCE→verdict), threshold semantics (PCE is dataset-calibrated, not universal), abstain rules (heavy recompression/crop = weaker signal), never claim provenance from a single signal; combine with `fact-check` for publication.
- **Touch `ai3d-gen`**: preflight check "source images verified real captures" before splat pipeline.

## Muscle (Extension)

`extensions/image-forensics/` (Python):

- `metadata.py`: EXIF/XMP/C2PA report (Pillow + piexif; C2PA via `c2pa-python` if viable, else flag-only).
- `prnu.py`: residual extractor (PyWavelets denoise), reference builder (`build_ref dir/` outputs `ref.npy`), `pce_score(img, ref)`.
- `verdict.py` CLI: `{ok, verdict, pce, metadata_flags, notes}` JSON contract like other extensions.
- Deps: numpy, PyWavelets, opencv-headless, Pillow; venv'd like `laya-tools`.

## Step-by-step (on authorization)

1. Implement residual + PCE core; unit-test on synthetic fixtures (known camera-phone set + generated set).
2. Build reference patterns for 2-3 known devices; validate PCE separation (real >> synthetic).
3. `verdict.py` combine signals; abstain when residual energy below noise floor.
4. Held-out validation per Rule 15: fresh image set, no calibration leakage; record metrics in refinement log.
5. Write `image-forensics` SKILL.md; link from `ai3d-gen` preflight + `fact-check`.

## Datasets (trusted sources, 2026-11-13)

- **VISION** (LESC lab, Univ. of Florence; EURASIP J. Inf. Security 2017,
  peer-reviewed open access): 34,427 images + 1,914 videos, 35 portable
  devices / 11 brands. Per-device dirs `D01..D35`; `images/flat/` subdirs
  are flat-field captures = ideal reference builders; native + social
  (FB/YT/WhatsApp) versions cover the recompression regime our
  false-positive finding needs. Download: `wget -i
  https://lesc.dinfo.unifi.it/VISION/VISION_files.txt` (license:
  research use, cite the paper). Errata: 5 misplaced social videos
  listed on the datasets page.
- **Dresden Image Database** (Agilbert/Goljan lineage): the original
  PRNU benchmark (~70 devices, flat/natural split); canonical but the
  primary host has been intermittently offline - VISION is the
  reliable fetch today. ISPL Polimi republishes derived PRNU refs:
  `github.com/polimi-ispl/cnn-fast-sdi` `utility_dataset.py` shows the
  `prnu_flat_<dev>.npy` convention and the Dresden/VISION device lists.
- **Code**: Binghamton DDE hosts the reference implementation
  (`dde.binghamton.edu/download/camera_fingerprint`) - getFingerprint,
  PCE, NoiseExtractFromImage, consistent with the large-scale Goljan
  test. `github.com/polimi-ispl/prnu-python` is the Python port our
  `prnu.py` already follows.

First real calibration run (2026-11-13, subset in
`.devin/scratch/prnu-vision/`, gitignored): D02_iPhone4s + D15_iPhone6,
8 flat refs each, held-out nat + natWA.

| comparison | PCE | verdict |
|---|---|---|
| D02 nat vs ref_D02 | 68-266 (7/8 real, 1 abstain) | correct |
| D15 nat vs ref_D15 | 110-1391 (3/3 real) | correct |
| D02 nat vs ref_D15 | 9-17 | correctly rejected |
| D15 nat vs ref_D02 | 15-21 | correctly rejected |
| D02 natWA vs ref_D02 | abstain (residual below floor) | correct abstain |

Same-device vs cross-device separation ~4x at default threshold 50;
WhatsApp recompression kills the residual so the tool abstains instead
of guessing - matches the documented abstain rules. Server
rate-limits parallel fetches (503) - download sequentially with
`--retry`. Ref builder caveat: `--build-ref` swallows per-image load
errors and reports `empty image set` when all fail - a 206-byte 503
page looks like a jpg until PIL rejects it.

## Progress (2026-11-09 audit)

- Landed: `extensions/image-forensics/` (metadata.py, prnu.py, verdict.py) + `skills/image-forensics/SKILL.md` + tests/test_image_forensics.py (10 tests, green)
- DONE 2026-11-09 (partial): `eval_set.py` held-out harness shipped (labeled real/synth dirs -> per-class verdict distribution + decided accuracy + coverage; thresholds stay CLI inputs so calibration and held-out never share constants). First real-data run: webcam JPEG ref (4 imgs) vs held-out frames - real 3/3 correct BUT synth JPEG frames false-positive (PCE 130-187 > default 50) - ref residual dominated by shared JPEG quant signature, not isolating sensor PRNU. Full writeup: `.devin/research/2026-11-09-if-heldout-eval.md`. Still pending: larger multi-session/device dataset for threshold calibration
- DONE 2026-11-17 (partial): dataset expanded to 3 devices - added D03_Huawei_P9 (8 flat refs + 8 nat, ~188MB total now in `.devin/scratch/prnu-vision/`, gitignored). ref_D03.npy built clean (8/8 images). **Cross-brand calibration finding**: all 8 D03 nat score PCE 18.8-34.3 vs ref_D03 -> verdict inconclusive at default threshold 50. Same-device signal sits ~1.5-4x above the documented cross-device floor (9-21 from D02<->D15 runs), so a per-device threshold near 25 would still separate; default 50 is iPhone-calibrated, confirming PCE universality is a myth per the skill doc. Cross-device PCE is geometry-blocked by design (refs are resolution-bound; ref_error note emitted, not fake-low PCE). Implication for threshold calibration: collect per-device PCE distributions, not one global threshold.
- DONE 2026-11-25 (partial): per-device calibration run over the full
  VISION subset (script `.devin/scratch/si-20261125/prnu_device_calibration.py`,
  artifact `.devin/scratch/prnu-vision/calibration-2026-11-25.json`).
  Real cross-device floors now measured for D02<->D15 (both 2448x3264):
  - D02: nat 68.8-265.9 (n=7) vs D15-nat floor 8.8-30.1 -> threshold 45.5
    (geometric mean of floor max and nat min; 2.3x separation).
  - D15: nat 110.3-1391.5 (n=8) vs D02-nat floor 8.8-35.2 -> threshold
    62.3 (3.1x separation).
  - D03: nat 18.8-34.3 (n=8); cross floor geometry-blocked (2976x3968
    vs both refs) -> fallback 9.4 = inside the documented floor range,
    so D03 stays genuinely inconclusive for attribution; needs more
    flat refs to strengthen the reference pattern, not a lower
    threshold.
  - Data quality: 5 files fail `load_gray` ("cannot identify image
    file") - D02 nat_0008 + all 4 D02 natWA + all 4 D15 natWA. Corrupt
    in the local copy; natWA distribution unmeasurable until re-fetched.
  - Verdict: per-device thresholds are real (45-62 for iPhones) and the
    50 default is coincidentally mid-range; PCE universality stays
    refuted. Still pending user-gated work: re-fetch corrupt natWA
    files; held-out step 4 needs fresh captures outside this subset.
- DONE 2026-11-25 (partial, cont.): corruption triage + first natWA
  measurement (artifact `calibration-natwa-2026-11-25.json`, script
  `.devin/scratch/si-20261125/prnu_natwa_calibration.py`).
  - D02 nat_0008 + 4 natWA were 199-byte HTTP 503 pages (rate-limit
    casualties, the documented fetch caveat); re-fetched sequentially
    with retry - all load now.
  - D15 natWA corruption was a FALSE report - all 4 load + residual
    fine (valid JPEG FFD8..FFD9). Real blocker was geometry, not data.
  - natWA is WhatsApp-downscaled 960x1280 vs 2448x3264 refs -> PCE
    geom-blocked by design. Fix: resolution-matched refs built by
    downscaling flat images (LANCZOS) - new artifacts
    `ref_D02_natwa.npy`, `ref_D15_natwa.npy`.
  - FIRST natWA numbers (n=4, then thickened to n=12 per device -
    VISION hosts ~100 natWA each, fetched 0005-0012 sequentially):
    - D02 n=12: [21.8-27.2]x9 overlap floor [21.8-35.0] completely,
      but 3 outliers 43.3/91.0/132.3 clear floor max - WhatsApp
      survival is per-image stochastic: 25% retain attributable
      signal, 75% correctly abstain.
    - D15 n=12: [28.4, 29.0] below floor max 42.5; 43.1 at edge;
      65.4-537.9 x9 clearly above - 83% attributable.
    - Working abstain threshold at 960x1280: ~43 (above both floor
      maxima 35.0/42.5); below it the two devices are
      indistinguishable.
  - Still pending: held-out step 4 needs fresh captures outside this
    subset (user-gated).
- DONE 2026-11-25 (step 4, dataset-fresh substitute): held-out
  validation on devices NEVER in calibration (D05_Apple_iPhone5c +
  D24_Xiaomi_RedmiNote3, 8 flat+8 nat+8 natWA each, fetched from VISION;
  script `.devin/scratch/si-20261125/prnu_heldout_eval.py`, artifact
  `.devin/scratch/prnu-vision/heldout-2026-11-25.json`). Floor pools
  shape-matched: nat floors from D02/D15 nat, natWA floors shape-aware.
  - nat VALIDATED: D05 mean 966/min 294, D24 mean 1078/min 734 vs
    cross-device floor max 38.7 (mean 30.6). Minimum-margin 7.6x -
    per-device detection generalizes to never-calibrated devices.
  - natWA marginal as predicted: D05 mean 232 but min 24.6 falls INSIDE
    the floor range (max 29.4) - per-image abstain confirmed necessary,
    not optional.
  - NEW correction: WhatsApp does NOT normalize to fixed 960x1280 - it
    scales the long edge to 1280 preserving aspect ratio (4:3 -> 1280x960,
    16:9 -> 1280x720). D24 natWA shape is 1280x720.
  - 16:9 natWA near-unclassifiable: D24 natWA mean only 44.4 (vs 4:3
    D05 mean 232) - hovers at the ~43 abstain threshold. Aspect ratio
    materially affects survival.
  - SKILL.md abstain rules updated with all of the above.
  - Remaining user-gated: fresh physical captures (own devices) would
    strengthen but are no longer blocking - core detection validated.

## Non-goals

No deepfake-face classifiers, no SaaS detection APIs, no GPU requirement. Rust port only if batch throughput demands (ADR-003).
