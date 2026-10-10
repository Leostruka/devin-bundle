# ISSUE 02: Cognitive Vision (image provenance & PRNU forensics)

Status: planned (research done) · Source: IG `DeRX9KpJPlT` (@plattipusofficial) + Lukáš/Fridrich/Goljan 2006 + Corvi et al. ICASSP 2023 · Ledger: `.devin/research/4_fronts_recon.md`

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

## Non-goals

No deepfake-face classifiers, no SaaS detection APIs, no GPU requirement. Rust port only if batch throughput demands (ADR-003).
