"""eval_set - held-out provenance eval over labeled image dirs.

Rule 15 harness for ISSUE_02 step 4: run verdict.judge over
--real-dir (expected real_capture) and --synth-dir (expected
synthetic), then report per-class verdict distribution plus decided
accuracy. Thresholds stay inputs so calibration runs and held-out runs
never share tuned constants by accident.

  python eval_set.py --real DIR --synth DIR --ref ref.npy
      [--pce-real 50] [--pce-synth 10] [--limit N] [--json]

-> {"ok": bool, "classes": {"real": {...}, "synthetic": {...}},
    "decided_accuracy": float|null, "coverage": float,
    "errors": [...]}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import verdict as vd          # noqa: E402

from forensics_envelope import _stamp, _dumps


IMG_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp",
           ".webp")
VERDICTS = ("real_capture", "synthetic", "inconclusive",
            "no_reference", "ref_error")


def _images(d):
    return sorted(f for f in Path(d).iterdir()
                  if f.suffix.lower() in IMG_EXT) \
        if Path(d).is_dir() else []


def _class_report(expected, files, ref, pce_real, pce_synth, limit):
    counts = {v: 0 for v in VERDICTS}
    counts["load_error"] = 0
    n = 0
    for f in files[:limit] if limit else files:
        n += 1
        try:
            r = vd.judge(str(f), ref, pce_real, pce_synth)
        except Exception:
            counts["load_error"] += 1
            continue
        if any(str(n).startswith("ref_error:") for n in
               r.get("notes", [])):
            counts["ref_error"] += 1
            continue
        v = r.get("verdict", "inconclusive")
        counts[v if v in counts else "inconclusive"] += 1
    correct = counts[expected]
    decided = n - counts["inconclusive"] - counts["no_reference"] \
        - counts["load_error"] - counts["ref_error"]
    return {"expected": expected, "n": n, "verdicts": counts,
            "correct": correct, "decided": decided}


def evaluate(real_dir, synth_dir, ref=None, pce_real=vd.PCE_REAL,
             pce_synth=vd.PCE_SYNTH, limit=None):
    errors = []
    real_files = _images(real_dir)
    synth_files = _images(synth_dir)
    if not real_files:
        errors.append(f"real_dir empty or missing: {real_dir}")
    if not synth_files:
        errors.append(f"synth_dir empty or missing: {synth_dir}")
    out = {"ok": not errors, "classes": {}, "errors": errors}
    if errors:
        return out
    for expected, files in (("real_capture", real_files),
                            ("synthetic", synth_files)):
        out["classes"]["real" if expected == "real_capture"
                       else "synthetic"] = _class_report(
            expected, files, ref, pce_real, pce_synth, limit)
    decided = sum(c["decided"] for c in out["classes"].values())
    correct = sum(c["correct"] for c in out["classes"].values())
    total = sum(c["n"] for c in out["classes"].values())
    out["decided_accuracy"] = (correct / decided) if decided else None
    out["coverage"] = (decided / total) if total else 0.0
    return out


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(
        description="held-out real-vs-synthetic provenance eval")
    ap.add_argument("--real", required=True, help="dir of real captures")
    ap.add_argument("--synth", required=True,
                    help="dir of synthetic/generated images")
    ap.add_argument("--ref", default=None, help="camera ref.npy")
    ap.add_argument("--pce-real", type=float, default=vd.PCE_REAL)
    ap.add_argument("--pce-synth", type=float, default=vd.PCE_SYNTH)
    ap.add_argument("--limit", type=int, default=None,
                    help="max images per class (smoke runs)")
    args = ap.parse_args(argv)
    res = evaluate(args.real, args.synth, args.ref,
                   args.pce_real, args.pce_synth, args.limit)
    print(_dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
