"""verdict — combine metadata + residual + PCE into a provenance call.

CLI contract (JSON on stdout, like other bundle extensions):

  python verdict.py IMAGE [--ref REF.npy] [--pce-real 50] [--pce-synth 10]
    -> {"ok": true, "verdict": "real_capture|synthetic|inconclusive|
        no_reference", "pce": float|null, "metadata_flags": [...],
        "notes": [...]}

  python verdict.py --build-ref DIR --out ref.npy   (reference builder)

Rules (see skills/image-forensics): never claim provenance from a
single signal; residual energy below the denoiser floor abstains;
PCE thresholds are dataset-calibrated, not universal.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata as md          # noqa: E402
import prnu                    # noqa: E402

PCE_REAL = 50.0
PCE_SYNTH = 10.0
ENERGY_FLOOR = 0.003


def judge(image_path, ref_path=None, pce_real=PCE_REAL,
          pce_synth=PCE_SYNTH):
    out = {"ok": True, "verdict": "inconclusive", "pce": None,
           "metadata_flags": [], "notes": []}
    rep = md.report(image_path)
    out["metadata_flags"] = rep["flags"]
    if rep.get("c2pa_manifest"):
        out["notes"].append("c2pa_manifest_present")
    if "generator_software_tag" in rep["flags"] \
            or "generator_string_in_container" in rep["flags"]:
        out["verdict"] = "synthetic"
        out["notes"].append("metadata_generator_signal")
        return out
    try:
        arr = prnu.load_gray(image_path)
    except Exception as e:
        return {"ok": False, "verdict": "inconclusive", "pce": None,
                "metadata_flags": rep["flags"],
                "notes": [f"load_error:{type(e).__name__}"]}
    res = prnu.residual(arr)
    energy = prnu.residual_energy(res)
    if energy < ENERGY_FLOOR:
        out["verdict"] = "inconclusive"
        out["notes"].append(f"low_residual_energy:{energy:.5f}")
        return out
    if ref_path is None:
        out["verdict"] = "no_reference"
        out["notes"].append("residual_ok_but_no_camera_reference")
        return out
    try:
        ref = _load_ref(ref_path, arr.shape)
    except (OSError, ValueError) as e:
        out["notes"].append(f"ref_error:{e}")
        return out
    score = prnu.pce(res, ref)
    out["pce"] = score
    if score >= pce_real:
        out["verdict"] = "real_capture"
    elif score <= pce_synth:
        out["verdict"] = "synthetic"
    else:
        out["verdict"] = "inconclusive"
        out["notes"].append("pce_between_thresholds")
    return out


def _load_ref(ref_path, shape):
    import numpy as np
    ref = np.load(ref_path)
    if ref.shape != shape:
        raise ValueError(
            f"ref shape {ref.shape} != image {shape}; "
            "crop/resize images to the reference geometry first")
    return ref


def build_ref(dir_path, out_path):
    import numpy as np
    arrays = []
    for f in sorted(Path(dir_path).iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif",
                                ".tiff", ".bmp", ".webp"):
            try:
                arrays.append(prnu.load_gray(f))
            except Exception:
                continue
    ref = prnu.build_reference(arrays)
    np.save(out_path, ref)
    return {"ok": True, "images": len(arrays), "ref": str(out_path)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="PRNU provenance verdict")
    ap.add_argument("image", nargs="?")
    ap.add_argument("--ref")
    ap.add_argument("--pce-real", type=float, default=PCE_REAL)
    ap.add_argument("--pce-synth", type=float, default=PCE_SYNTH)
    ap.add_argument("--build-ref")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    if args.build_ref:
        print(json.dumps(build_ref(args.build_ref, args.out or "ref.npy"),
                         ensure_ascii=False))
        return 0
    if not args.image:
        ap.error("image path required (or --build-ref)")
    print(json.dumps(judge(args.image, args.ref, args.pce_real,
                           args.pce_synth), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
