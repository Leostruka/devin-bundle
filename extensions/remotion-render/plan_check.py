"""plan_check — pre-render validator for scene-plan v2 (motion).

Runs before the approval gate: catches broken plans at the cheap stage,
never post-render. Checks:

  * sync_range sanity: 0 <= start < end <= audio_duration_s
  * overlap collisions between beats (same screen, one visual at a time
    unless a beat explicitly declares `overlay: true`)
  * readability: beat duration >= words/READ_WPM estimate
  * render budget estimate: frames * RENDER_MS_PER_FRAME

  python plan_check.py plan.json
    -> {"ok": bool, "errors": [...], "warnings": [...],
        "budget": {"frames": N, "est_seconds": F}}
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


READ_WPM = 160.0
RENDER_MS_PER_FRAME = 120.0
OVERLAY_TOLERANCE = 0.0

# Visual prop contract - mirrors PlanComposition.tsx prop types.
# Missing/wrong-typed required props crash Remotion mid-render with a
# cryptic interpolate TypeError; catching them here is the point of
# the gate. Unknown types fall back to KineticText in the template.
_NUM = (int, float)
VISUAL_PROPS = {
    "kinetic_text": {"required": {"text": str},
                     "optional": {"size": _NUM}},
    "diagram_nodes": {"required": {"nodes": list},
                      "optional": {}},
    "counter": {"required": {"to": _NUM},
                "optional": {"label": str}},
    "pan_zoom": {"required": {"src": str},
                 "optional": {"zoom": _NUM}},
}


def _num(v):
    # bool is an int subclass; NaN/Infinity are not finite numbers
    return (isinstance(v, _NUM) and not isinstance(v, bool)
            and math.isfinite(v))


def _type_ok(v, types):
    if not (isinstance(v, types) and not isinstance(v, bool)):
        return False
    return not (isinstance(v, float) and not math.isfinite(v))


def _check_visual_props(bid, vtype, props, errors):
    spec = VISUAL_PROPS.get(vtype)
    if spec is None:
        return  # unknown type: template falls back to KineticText
    for key, types in spec["required"].items():
        if not _type_ok(props.get(key), types):
            errors.append(f"{bid}: visual.props.{key} missing or "
                          f"wrong type for {vtype}")
    for key, types in spec["optional"].items():
        v = props.get(key)
        if v is not None and not _type_ok(v, types):
            errors.append(f"{bid}: visual.props.{key} wrong type "
                          f"for {vtype}")
    if vtype == "diagram_nodes":
        nodes = props.get("nodes")
        if isinstance(nodes, list):
            for ni, n in enumerate(nodes):
                if not isinstance(n, dict) or \
                        not isinstance(n.get("label"), str):
                    errors.append(f"{bid}: nodes[{ni}] needs "
                                  "{label: string}")


def _words(text):
    return len(str(text or "").split())


def check(plan):
    errors, warnings = [], []
    dur = plan.get("audio_duration_s")
    fps = plan.get("fps", 30)
    beats = plan.get("beats", [])
    if not isinstance(beats, list):
        errors.append("beats must be a list")
        beats = []
    if plan.get("version") != 2:
        errors.append("version must be 2 (motion scene-plan)")
    if not _num(dur) or dur <= 0:
        errors.append("audio_duration_s missing or non-positive")
        dur = float("inf")
    if not _num(fps) or fps <= 0:
        errors.append("fps missing or non-positive")
        fps = 30
    ranges = []
    total_frames = 0
    for i, b in enumerate(beats):
        if not isinstance(b, dict):
            errors.append(f"beat{i}: entry must be an object")
            continue
        bid = b.get("id", f"beat{i}")
        sr = b.get("sync_range")
        if not (isinstance(sr, list) and len(sr) == 2
                and all(_num(x) for x in sr)):
            errors.append(f"{bid}: sync_range missing/malformed")
            continue
        s, e = sr
        if not (0 <= s < e):
            errors.append(f"{bid}: bad sync_range {sr}")
            continue
        if e > dur:
            errors.append(f"{bid}: ends {e}s beyond audio {dur}s")
        beat_len = e - s
        vis = b.get("visual", {})
        if not isinstance(vis, dict):
            errors.append(f"{bid}: visual must be an object")
            vis = {}
        props = vis.get("props", {})
        if not isinstance(props, dict):
            props = {}
        _check_visual_props(bid, vis.get("type"), props, errors)
        words = _words(props.get("text") or props.get("label"))
        min_len = words / (READ_WPM / 60.0)
        if words and beat_len < min_len:
            warnings.append(
                f"{bid}: {beat_len:.1f}s < read time {min_len:.1f}s "
                f"for {words} words")
        motion = b.get("motion_spec", {})
        if not isinstance(motion, dict):
            motion = {}
        for k in ("enter", "exit"):
            d = motion.get(f"{k}_s", 0)
            if d and d > beat_len / 2:
                warnings.append(
                    f"{bid}: {k} {d}s exceeds half the beat")
        total_frames += int(beat_len * fps)
        for prev in ranges:
            if s < prev[1] - OVERLAY_TOLERANCE and e > prev[0] \
                    and not b.get("overlay") and not prev[2]:
                errors.append(
                    f"{bid}: overlaps {prev[3]} "
                    f"[{prev[0]:.2f},{prev[1]:.2f}]")
        ranges.append((s, e, b.get("overlay", False), bid))
    budget = {"frames": total_frames,
              "est_seconds": round(total_frames *
                                   RENDER_MS_PER_FRAME / 1000, 1)}
    if total_frames > 30 * 60 * 10:
        warnings.append(f"budget: {total_frames} frames is a long render")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "budget": budget}


def _fail(msg):
    print(json.dumps({"ok": False, "errors": [msg], "warnings": [],
                      "budget": {"frames": 0, "est_seconds": 0}}))
    return 2


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = argv[0] if argv else sys.argv[1]
    try:
        raw = Path(src).read_text(encoding="utf-8")
    except OSError as exc:
        return _fail(f"read_error:{exc}")
    try:
        plan = json.loads(raw)
    except ValueError as exc:
        return _fail(f"json_error:{exc}")
    if not isinstance(plan, dict):
        return _fail("plan must be a JSON object")
    res = check(plan)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
