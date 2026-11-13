#!/usr/bin/env python3
"""fit_calibration - fit probability maps over FROZEN captures.

Reads frozen manifests (gold labels + recorded worker replies), keeps
decided cases (outcome == "suggestion"), and fits calibration maps:

  - platt: 2-parameter logistic on raw_confidence (same parameterization
    as laya_worker._calibrated: sigmoid(a*x + b))
  - table: isotonic (PAVA) fit emitted as sorted [x, y] points; the
    worker's table kind linearly interpolates between them

Train manifests and held-out manifests are separate flags so the same
script produces honest held-out numbers. This tool never calls an
engine, never writes profiles, and never flips a mode - its output is
a review artifact for the deliberate activation checklist.

  python fit_calibration.py \
      --manifest ../../.devin/evals/laya/<p>/manifest.frozen.json \
      --heldout ../../.devin/evals/laya/<p>/manifest.heldout.frozen.json \
      --map all
"""
from __future__ import annotations

import argparse
import json
import math
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
    return {"bundle": _bundle_version(), "wrapper": "laya-tools"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def _sigmoid(z):
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))


def _decided_cases(manifest_path):
    """[(x, y, case_id)] for decided cases: x = raw_confidence,
    y = 1 iff candidate_id == gold."""
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(
            data.get("cases"), list):
        raise ValueError("manifest_not_object_or_cases_not_list")
    out = []
    for c in data["cases"]:
        if not isinstance(c, dict):
            continue
        rep = c.get("reply") or {}
        if rep.get("outcome") != "suggestion":
            continue
        x = rep.get("raw_confidence")
        if not isinstance(x, (int, float)) or isinstance(x, bool):
            continue
        y = 1 if rep.get("candidate_id") == c.get("gold") else 0
        out.append((float(x), y, c.get("case_id", "?")))
    return out, len(data.get("cases", []))


def fit_platt(xs, ys):
    """Newton-Raphson logistic fit of y ~ sigmoid(a*x + b)."""
    a, b = 1.0, 0.0
    for _ in range(60):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys):
            p = _sigmoid(a * x + b)
            w = max(p * (1 - p), 1e-6)
            r = p - y
            g0 += r * x
            g1 += r
            h00 += w * x * x
            h01 += w * x
            h11 += w
        h00 += 1e-6
        h11 += 1e-6
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        da = (h11 * g0 - h01 * g1) / det
        db = (h00 * g1 - h01 * g0) / det
        a -= da
        b -= db
        if abs(da) + abs(db) < 1e-9:
            break
    return a, b


def _pava_table(xs, ys):
    """Isotonic regression via pool-adjacent-violators.

    Returns sorted [[x, yhat], ...] at observed x positions; the
    worker's table kind interpolates linearly between points."""
    order = sorted(zip(xs, ys))
    blocks = []  # [count, sum_y, [(x, y), ...]]
    for x, y in order:
        blocks.append([1, float(y), [(x, float(y))]])
        while len(blocks) >= 2:
            b2, b1 = blocks[-1], blocks[-2]
            if b1[1] / b1[0] <= b2[1] / b2[0] + 1e-12:
                break
            blocks[-2:] = [[b1[0] + b2[0], b1[1] + b2[1],
                            b1[2] + b2[2]]]
    pts = []
    for _, s, members in blocks:
        yhat = s / len(members)
        for x, _ in members:
            pts.append([round(x, 6), round(yhat, 6)])
    dedup = []
    for p in pts:
        if dedup and dedup[-1] == p:
            continue
        dedup.append(p)
    return dedup


def _table_fn(points):
    pts = sorted(points)

    def f(x):
        if x <= pts[0][0]:
            return pts[0][1]
        if x >= pts[-1][0]:
            return pts[-1][1]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]
    return f


def _platt_fn(a, b):
    return lambda x: _sigmoid(a * x + b)


def adoption_curve(fn, cases, total, thresholds):
    """cases: [(x, y, id)] decided; total: all cases incl. abstains."""
    rows = []
    for t in thresholds:
        adopted = [(x, y) for x, y, _ in cases if fn(x) >= t]
        n = len(adopted)
        correct = sum(y for _, y in adopted)
        rows.append({
            "threshold": t,
            "adopted": n,
            "adopted_correct": correct,
            "adopted_accuracy": round(correct / n, 4) if n else None,
            "coverage": round(n / total, 4) if total else None,
        })
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", action="append", required=True,
                   help="Frozen manifest for TRAINING (repeatable)")
    p.add_argument("--heldout", action="append", default=[],
                   help="Frozen manifest for held-out eval (repeatable)")
    p.add_argument("--map", choices=["platt", "table", "all"],
                   default="all")
    p.add_argument("--thresholds", default="0.5,0.6,0.7,0.8,0.9,0.95")
    p.add_argument("--out", help="Write JSON report to this path")
    p.add_argument("--emit-block", metavar="PROFILE",
                   help="Print a calibration-block skeleton for PROFILE "
                        "using the --map choice (requires --threshold)")
    p.add_argument("--threshold", type=float, default=0.9,
                   help="Threshold for --emit-block")
    p.add_argument("--cardinality", type=int, default=0,
                   help="Candidate cardinality for --emit-block")
    args = p.parse_args(argv)

    train, train_total = [], 0
    try:
        for m in args.manifest:
            cases, total = _decided_cases(m)
            train += cases
            train_total += total
        heldout_sets = []
        for m in args.heldout:
            cases, total = _decided_cases(m)
            heldout_sets.append({"manifest": m, "cases": cases,
                                 "total": total})
    except (OSError, ValueError) as exc:
        print(_dumps({"ok": False,
                          "reason": f"manifest_unreadable:{exc}"}))
        return 1

    if len(train) < 5:
        print(_dumps({"ok": False,
                          "reason": "too_few_decided_train_cases",
                          "n": len(train)}))
        return 1

    xs = [x for x, _, _ in train]
    ys = [y for _, y, _ in train]
    thresholds = [float(t) for t in args.thresholds.split(",")
                  if t.strip()]

    maps = {}
    if args.map in ("platt", "all"):
        a, b = fit_platt(xs, ys)
        maps["platt"] = {"kind": "platt", "a": round(a, 6),
                         "b": round(b, 6),
                         "_fn": _platt_fn(a, b)}
    if args.map in ("table", "all"):
        pts = _pava_table(xs, ys)
        maps["table"] = {"kind": "table", "points": pts,
                         "_fn": _table_fn(pts)}

    report = {"ok": True, "train": {"decided": len(train),
                                    "cases": train_total},
              "maps": {}}
    for name, m in maps.items():
        fn = m["_fn"]
        entry = {"map": {k: v for k, v in m.items() if k != "_fn"}}
        entry["train_curve"] = adoption_curve(fn, train, train_total,
                                              thresholds)
        entry["heldout"] = [{
            "manifest": h["manifest"],
            "decided": len(h["cases"]), "cases": h["total"],
            "curve": adoption_curve(fn, h["cases"], h["total"],
                                    thresholds)}
            for h in heldout_sets]
        report["maps"][name] = entry

    if args.emit_block:
        kind = "platt" if args.map == "platt" else \
            ("table" if args.map == "table" else "platt")
        m = maps[kind]
        block = {
            "id": f"{args.emit_block}-cal-<date>",
            "checkpoint_sha256": "<digest of approved checkpoint>",
            "profile": args.emit_block,
            "locale": "en",
            "data_source": "<eval dir>",
            "evaluation_id": "<eval ids used>",
            "threshold": args.threshold,
            "cardinality": args.cardinality,
            "map": {k: v for k, v in m.items() if k != "_fn"},
        }
        report["emit_block"] = block

    txt = _dumps(report, indent=1)
    if args.out:
        Path(args.out).write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
