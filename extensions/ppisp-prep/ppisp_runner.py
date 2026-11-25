"""ppisp_runner — wrap NVIDIA nv-tlabs/ppisp for correction passes.

PPISP learns per-camera distortion (exposure, vignette, chromaticity
homography / WB drift, CRF tone mapping) and inverts it so photometric
inconsistencies stop baking into geometry as floaters/ghosts.

We do NOT vendor or reimplement the network. `doctor()` reports what is
present; `run()` drives the upstream checkout's own training entry
points. License is verified at clone time — read upstream LICENSE and
record it before first use (ppisp_upstream/LICENSE).

  python ppisp_runner.py doctor
  python ppisp_runner.py smoke
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

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "ppisp-prep"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    if isinstance(payload, list):
        payload = {"ok": True, "items": payload}
    return json.dumps(_stamp(payload), **kw)


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
    torch_cuda = None
    try:
        import torch as _t  # noqa
        torch = True
        torch_cuda = bool(_t.cuda.is_available())
    except ImportError:
        torch = False
    ppisp_importable = None
    try:
        import ppisp  # noqa
        ppisp_importable = True
    except ImportError:
        ppisp_importable = False
    except Exception:
        ppisp_importable = "error"
    return {
        "upstream": str(up),
        "upstream_kind": "library",
        "present": (up / "README.md").exists() or any(up.glob("*.py")),
        "license": _license_kind(up) if up.exists() else "absent",
        "torch": torch,
        "torch_cuda": torch_cuda,
        "ppisp_importable": ppisp_importable,
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
    return {
        "ok": False,
        "error": "integration_required",
        "detail": "upstream ppisp is a library: a differentiable module "
                  "integrated into a radiance-field training loop "
                  "(3DGS/NeRF), with no standalone train entry. "
                  "Correction requires the reconstruction-pipeline "
                  "integration milestone (poses via COLMAP + gsplat "
                  "training with the ppisp module in the loop).",
        "hint": "run `ppisp_runner.py smoke` to validate the built "
                "kernel on this host via upstream's own test suite",
    }


def smoke():
    """Validate the built kernel via upstream's own pytest suite."""
    d = doctor()
    if not d["present"]:
        return {"ok": False, "error": "upstream_missing",
                "hint": d["hint"]}
    if d["license"] in ("missing", "unrecognized:review-required"):
        return {"ok": False, "error": "license_unverified",
                "license": d["license"]}
    up = upstream_dir()
    argv = [sys.executable, "-m", "pytest", "tests", "-x", "-q"]
    try:
        timeout = int(os.environ.get("PPISP_TIMEOUT", "1800"))
    except ValueError:
        timeout = 1800
    try:
        p = subprocess.run(argv, cwd=up, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"upstream_timeout:{timeout}s"}
    except OSError as e:
        return {"ok": False, "error": f"spawn_failed:{e}"}
    tail = (p.stdout.strip().splitlines() or [""])[-1]
    return {"ok": p.returncode == 0, "exit": p.returncode,
            "summary": tail[-400:],
            "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="PPISP correction runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("smoke")
    pr = sub.add_parser("run")
    pr.add_argument("images_dir")
    pr.add_argument("--out", required=True)
    pr.add_argument("--steps", type=int)
    args = ap.parse_args(argv)
    if args.cmd == "doctor":
        res = doctor()
    elif args.cmd == "smoke":
        res = smoke()
    else:
        res = run(args.images_dir, args.out, args.steps)
    print(_dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
