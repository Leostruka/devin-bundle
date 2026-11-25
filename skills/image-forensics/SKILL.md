---
name: image-forensics
description: Use when checking whether an image is a real camera capture or synthetic/generated, when tagging media provenance before ingestion, when verifying visual evidence for fact-check, or when validating that ai3d-gen source photos are real captures before splatting. Covers PRNU noise-residual forensics, EXIF/XMP/C2PA first pass, and PCE scoring via extensions/image-forensics.
---

# Image Forensics

Cheap image provenance: real-vs-synthetic plus "which camera took this".
Route: `extensions/image-forensics/verdict.py` — JSON contract
`{ok, verdict, pce, metadata_flags, notes}`.

## Evidence ordering (always in this order)

1. **Metadata first pass** — `metadata.py`: EXIF/XMP/C2PA report.
   Generator tags (`stable diffusion`, `dall-e`, ...) or a C2PA manifest
   are fast signals. Absence of EXIF is NOT evidence of synthesis:
   metadata dies on screenshot/re-upload; pixel noise does not.
2. **Noise residual** — `prnu.residual`: denoise (wavelet via PyWavelets
   when installed, Gaussian fallback) and subtract; the remainder is the
   fingerprint candidate.
3. **Reference pattern** — `verdict.py --build-ref dir/ --out ref.npy`
   averages residuals of N flat-ish real photos from one device.
4. **PCE score** — `prnu.pce`: peak-to-correlation-energy of residual vs
   reference. Goljan's empirical band ~50-60 discriminates; calibrate on
   the local dataset, never treat thresholds as universal.
5. **Verdict**: `real_capture` / `synthetic` / `inconclusive` /
   `no_reference` + flags + notes.

## Abstain rules

- Residual energy below the denoiser floor (flat or heavily recompressed
  input) -> `inconclusive`, note `low_residual_energy`.
- PCE is shape-bound: downscaled inputs never match a full-res ref.
  WhatsApp normalizes the long edge to 1280 but PRESERVES aspect ratio
  (4:3 devices -> 1280x960, 16:9 -> 1280x720). Build a resolution-matched
  ref by downscaling flat captures before averaging. Measured 2026-11-25
  (VISION D02/D15 natWA, n=12 each): per-image stochastic survival -
  ~43 is a working abstain threshold at 1280x960; below it devices are
  indistinguishable (75% of iPhone4s natWA die vs 17% of iPhone6).
  Held-out validation on never-calibrated devices (same dataset,
  `.devin/scratch/prnu-vision/heldout-2026-11-25.json`): nat detection
  validated - D05 mean 966/min 294 and D24 mean 1078/min 734 vs
  cross-device floor max 38.7 (7.6x+ margin). natWA marginal as
  predicted: D05 mean 232 but min 24.6 falls INSIDE the floor range
  (max 29.4); D24 (16:9) mean 44.4 hovers at the abstain threshold.
  Per-image abstain is not optional for natWA; 16:9-crop devices are
  near-unclassifiable after WhatsApp.
- Heavy crop/resize/recompression weakens the signal; say so in notes.
- Never claim provenance from a single signal: combine metadata flags +
  residual + PCE. For publication, pair with `fact-check`.
- No camera reference available -> `no_reference`; build one or abstain.
- JPEG-domain caveat (measured 2026-11-09, see
  `.devin/research/2026-11-09-if-heldout-eval.md`): a ref built from
  camera JPEGs cannot reliably distinguish OTHER JPEGs - the shared
  quantization signature dominates the residual and synthetic JPEGs
  score real_capture at default thresholds. Prefer lossless camera
  originals (PNG/TIFF) for refs; when only JPEGs exist, raise
  `--pce-real` per-domain and validate with `eval_set.py` first.

## Commands

```bash
python extensions/image-forensics/verdict.py shot.jpg --ref ref.npy
python extensions/image-forensics/verdict.py --build-ref known_phone/ --out ref.npy
python extensions/image-forensics/verdict.py --build-ref known_phone/ --out ref_small.npy --resize 1280x960
python extensions/image-forensics/metadata.py shot.jpg
```

## Integrations

- `ai3d-gen` preflight: source images should verify as real captures
  before the splat pipeline (synthetic inputs break PRNU assumptions).
- `fact-check`: visual-evidence tagging.
- PPISP (`extensions/ppisp-prep`) models complementary per-camera
  photometrics (exposure/vignette/CRF) — provenance vs correction answer
  different questions; do not conflate.
