#!/usr/bin/env python3
"""P4b: laya shadow-mode latency for ui-target-v1 decisions.

Run under the laya venv:
  extensions\\laya-tools\\.venv\\Scripts\\python.exe p4_laya.py

Measures what an assist/shadow path would actually cost: engine build
(once per worker process) + steady-state recommend() latency over a
closed set of 8 candidates. Weights resolve from the local HF cache
(offline flags inside load_engine) — no download, no adoption. mode is
'off' in the request so nothing can be adopted regardless.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYA = HERE.parents[2] / "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA))

import decision_contract as dc  # noqa: E402
import laya_worker  # noqa: E402

CANDS = [
    {"id": f"h{i}", "role": r, "name": n, "scope": "notepad"}
    for i, (r, n) in enumerate([
        ("menuitem", "File"), ("menuitem", "Edit"),
        ("menuitem", "View"), ("button", "Settings"),
        ("button", "Minimize"), ("button", "Maximize"),
        ("button", "Close"), ("tabitem", "Untitled")])
]


def make_req(i):
    return {
        "version": dc.VERSION,
        "request_id": f"p4-{i}",
        "profile": "ui-target-v1",
        "mode": "shadow",
        "context": {"env_id": "host", "instance_id": "p4",
                    "observation_id": f"obs-{i}",
                    "capabilities_digest": "x", "policy_digest": "y"},
        "state": {"goal": "open the settings page"},
        "candidates": CANDS,
        "deadline_ms": 1000,
    }


def main():
    out = {"ok": True}
    t = time.monotonic()
    try:
        engine = laya_worker.load_engine({}, device="cpu")
    except Exception as e:
        print(json.dumps({"ok": False, "stage": "load_engine",
                          "error": f"{type(e).__name__}: {e}"}))
        return
    out["engine_build_s"] = round(time.monotonic() - t, 2)

    lat, recs = [], []
    for i in range(6):
        t = time.monotonic()
        rec = laya_worker.recommend(make_req(i), engine)
        lat.append((time.monotonic() - t) * 1000)
        recs.append({"outcome": rec.get("outcome"),
                     "candidate_id": rec.get("candidate_id"),
                     "reason": rec.get("reason"),
                     "model": rec.get("model_identity")})
    out["first_predict_ms"] = round(lat[0], 1)
    steady = sorted(lat[1:])
    out["steady_p50_ms"] = round(steady[len(steady) // 2], 1)
    out["steady_max_ms"] = round(steady[-1], 1)
    out["recs"] = recs
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
