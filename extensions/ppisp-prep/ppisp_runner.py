"""ppisp_runner — wrap NVIDIA nv-tlabs/ppisp for correction passes.

PPISP learns per-camera distortion (exposure, vignette, chromaticity
homography / WB drift, CRF tone mapping) and inverts it so photometric
inconsistencies stop baking into geometry as floaters/ghosts.

We do NOT vendor or reimplement the network. `doctor()` reports what is
present; `run()` drives the upstream checkout's own training entry
points. License is verified at clone time — read upstream LICENSE and
record it before first use (ppisp_upstream/LICENSE).

  python ppisp_runner.py doctor
  python ppisp_runner.py run <images_dir> --out corrected/ [--steps N]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_UPSTREAM = HERE / "ppisp_upstream"
ENV_VAR = "PPISP_DIR"


def upstream_dir():
    p = os.environ.get(ENV_VAR)
    return Path(p) if p else DEFAULT_UPSTREAM


def _license_kind(path):
    lic = path / "LICENSE"
    if not lic.exists():
        lic = path / "LICENSE.md"
    if not lic.exists():
        return "missing"
    text = lic.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
    if "apache" in text:
        return "apache-2.0"
    if "mit license" in text or "permission is hereby granted" in text:
        return "mit"
    if "nvidia" in text and "license" in text:
        return "nvidia-custom:review-required"
    return "unrecognized:review-required"


def doctor():
    up = upstream_dir()
    torch = None
    try:
        import torch  # noqa
        torch = True
    except ImportError:
        torch = False
    return {
        "upstream": str(up),
        "present": (up / "README.md").exists() or any(up.glob("*.py")),
        "license": _license_kind(up) if up.exists() else "absent",
        "torch": torch,
        "cuda": shutil.which("nvidia-smi") is not None,
        "hint": None if up.exists() else
            f"git clone https://github.com/nv-tlabs/ppisp {up} "
            "or set PPISP_DIR",
    }


def run(images_dir, out_dir, steps=None, extra=None):
    d = doctor()
    if not d["present"]:
        return {"ok": False, "error": "upstream_missing",
                "hint": d["hint"]}
    if d["license"] in ("missing", "unrecognized:review-required"):
        return {"ok": False, "error": "license_unverified",
                "license": d["license"]}
    up = upstream_dir()
    entry = None
    for cand in ("train.py", "scripts/train.py", "ppisp/train.py"):
        if (up / cand).exists():
            entry = up / cand
            break
    if entry is None:
        return {"ok": False, "error": "entrypoint_not_found",
                "hint": "read upstream README for the training entry"}
    argv = [sys.executable, str(entry), "--data", str(images_dir),
            "--out", str(out_dir)]
    if steps:
        argv += ["--steps", str(steps)]
    argv += list(extra or [])
    p = subprocess.run(argv, cwd=up, capture_output=True, text=True)
    return {"ok": p.returncode == 0, "exit": p.returncode,
            "out": str(out_dir), "stdout": p.stdout[-2000:],
            "stderr": p.stderr[-2000:]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="PPISP correction runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    pr = sub.add_parser("run")
    pr.add_argument("images_dir")
    pr.add_argument("--out", required=True)
    pr.add_argument("--steps", type=int)
    args = ap.parse_args(argv)
    if args.cmd == "doctor":
        print(json.dumps(doctor(), indent=2))
    else:
        print(json.dumps(run(args.images_dir, args.out, args.steps),
                         indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
