"""photo_qc — cheap photometric pre-check on an image set.

Before spending a reconstruction run: measure per-frame exposure,
white-balance drift, and vignette spread across the capture set and
emit a go/correct/recapture verdict. Complements image-forensics
(provenance) — this answers "will these photos reconstruct cleanly",
not "is this a real capture".

  python photo_qc.py <dir|glob> -> {"ok", "verdict", "per_image",
    "spread": {exposure, wb, vignette}, "notes"}

Verdict semantics:
  go        -> consistent set, feed the splat/3DGS path directly
  correct   -> moderate photometric drift; run ppisp_runner correction
  recapture -> severe drift (mixed devices/conditions); re-shoot
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

IMG_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")

# spread thresholds (std across the set), tune on real captures
GO = {"exposure": 0.06, "wb": 0.03, "vignette": 0.05}
RECAPTURE = {"exposure": 0.25, "wb": 0.15, "vignette": 0.20}


def _load_rgb(path):
    from PIL import Image
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0


def measure(arr):
    """Per-image photometrics in [0,1]-ish units.

    exposure  : mean luminance (Rec.601)
    wb        : mean(R)-mean(B) gray-world deviation (WB drift proxy)
    vignette  : (corner_mean - center_mean) radial falloff proxy;
                negative values mean corner falloff (real vignetting)
    """
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    h, w = lum.shape
    cy, cx = h // 4, w // 4
    center = lum[cy:h - cy, cx:w - cx].mean()
    corners = np.concatenate([
        lum[:cy, :cx].ravel(), lum[:cy, -cx:].ravel(),
        lum[-cy:, :cx].ravel(), lum[-cy:, -cx:].ravel()])
    return {
        "exposure": float(lum.mean()),
        "wb": float(arr[..., 0].mean() - arr[..., 2].mean()),
        "vignette": float(corners.mean() - center),
    }


def judge(metrics):
    spread = {k: float(np.std([m[k] for m in metrics]))
              for k in ("exposure", "wb", "vignette")}
    if any(spread[k] > RECAPTURE[k] for k in spread):
        verdict = "recapture"
    elif any(spread[k] > GO[k] for k in spread):
        verdict = "correct"
    else:
        verdict = "go"
    return verdict, spread


def scan(paths):
    metrics, notes = [], []
    for p in paths:
        try:
            metrics.append({"file": str(p), **measure(_load_rgb(p))})
        except Exception as e:
            notes.append(f"skip:{p}:{type(e).__name__}")
    if len(metrics) < 2:
        return {"ok": False, "verdict": "inconclusive",
                "notes": notes + ["need >=2 readable images"]}
    verdict, spread = judge(metrics)
    return {"ok": True, "verdict": verdict, "per_image": metrics,
            "spread": spread, "notes": notes}


def collect_paths(target):
    p = Path(target)
    if p.is_dir():
        return [f for f in sorted(p.iterdir())
                if f.suffix.lower() in IMG_EXT]
    return sorted(Path().glob(target))


def main(argv=None):
    ap = argparse.ArgumentParser(description="photometric QC")
    ap.add_argument("target", help="dir or glob")
    args = ap.parse_args(argv)
    print(json.dumps(scan(collect_paths(args.target)),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
