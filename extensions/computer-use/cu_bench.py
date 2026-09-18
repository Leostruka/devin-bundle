#!/usr/bin/env python3
"""Measure per-boundary latencies of the computer-use suite (protocol 4.4).

Prints one JSON object to stdout with p50/p95 and raw samples per boundary:
  startup_subprocess  spawn cost of a real script call (mouse.py position)
  capture_full        mss grab of the primary monitor
  capture_region      mss grab of a 320x240 region
  png_encode          PIL PNG encode of the captured frame
  hints_enum          UIA enum_clickables (focused window)
  input_dispatch      pynput move to current position (no-op move)

Usage: cu_bench.py [--runs N] [--warmup N] [--out FILE] [--dry-run]
"""
import argparse
import io
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

import cu_actions

HERE = os.path.dirname(os.path.abspath(__file__))


def _pct(samples, q):
    s = sorted(samples)
    if not s:
        return None
    k = (len(s) - 1) * q
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return round(s[f] + (s[c] - s[f]) * (k - f), 3)


def _summary(samples):
    return {"p50": _pct(samples, 0.5), "p95": _pct(samples, 0.95),
            "min": round(min(samples), 3), "max": round(max(samples), 3),
            "n": len(samples), "raw_ms": [round(x, 3) for x in samples]}


def _bench(fn, runs, warmup):
    for _ in range(warmup):
        fn()
    out = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        out.append((time.perf_counter() - t0) * 1000.0)
    return out


def _b_startup(mouse_py):
    def f():
        subprocess.run([sys.executable, mouse_py, "position"],
                       capture_output=True, timeout=30)
    return f


def _b_capture_full(sct, mon):
    return lambda: sct.grab(mon)


def _b_capture_region(sct, mon):
    region = {"left": mon["left"], "top": mon["top"],
              "width": min(320, mon["width"]),
              "height": min(240, mon["height"])}
    return lambda: sct.grab(region)


def _b_png_encode(img):
    def f():
        from PIL import Image
        Image.frombytes("RGB", (img.width, img.height),
                        img.rgb).save(io.BytesIO(), "PNG")
    return f


def _b_hints():
    import cu_hints
    return lambda: cu_hints.enum_clickables(scope="focused", timeout=15.0)


def _b_dispatch(ctl):
    pos = ctl.position
    def f():
        ctl.position = pos
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--out", default=None,
                    help="Also write the JSON result to this file")
    ap.add_argument("--dry-run", action="store_true",
                    help="Single pass per boundary; marks dry_run in output")
    args = ap.parse_args()
    runs = 1 if args.dry_run else max(1, args.runs)
    warmup = 1 if args.dry_run else max(0, args.warmup)

    try:
        import mss
        from pynput.mouse import Controller
    except ImportError as e:
        print(json.dumps({"ok": False,
                          "error": f"missing dep: {e} — install requirements.txt"}))
        sys.exit(2)

    boundaries = {}
    errors = {}

    def bench(name, make):
        try:
            boundaries[name] = _summary(_bench(make(), runs, warmup))
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}"
            boundaries[name] = None

    bench("startup_subprocess",
          lambda: _b_startup(os.path.join(HERE, "mouse.py")))

    with mss.MSS() as sct:
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        img = sct.grab(mon)
        bench("capture_full", lambda: _b_capture_full(sct, mon))
        bench("capture_region", lambda: _b_capture_region(sct, mon))
        bench("png_encode", lambda: _b_png_encode(img))

    if sys.platform == "win32":
        bench("hints_enum", _b_hints)
    else:
        boundaries["hints_enum"] = None
        errors["hints_enum"] = "uia requires win32"

    ctl = Controller()
    bench("input_dispatch", lambda: _b_dispatch(ctl))

    result = {
        "ok": True,
        "runs": runs,
        "dry_run": bool(args.dry_run),
        "boundaries": boundaries,
        "meta": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "exe": sys.executable,
            "monitor": {"w": mon["width"], "h": mon["height"],
                        "origin": [mon["left"], mon["top"]]},
            "monitor_count": len(sct.monitors) - 1,
            "measured_at": round(time.time(), 3),
        },
    }
    if errors:
        result["errors"] = errors
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    print(json.dumps(result))


if __name__ == "__main__":
    cu_actions.run_cli(main)
