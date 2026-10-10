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
import sys
from pathlib import Path

READ_WPM = 160.0
RENDER_MS_PER_FRAME = 120.0
OVERLAY_TOLERANCE = 0.0


def _words(text):
    return len(str(text or "").split())


def check(plan):
    errors, warnings = [], []
    dur = plan.get("audio_duration_s")
    fps = plan.get("fps", 30)
    beats = plan.get("beats", [])
    if plan.get("version") != 2:
        errors.append("version must be 2 (motion scene-plan)")
    if not isinstance(dur, (int, float)) or dur <= 0:
        errors.append("audio_duration_s missing or non-positive")
        dur = float("inf")
    ranges = []
    total_frames = 0
    for i, b in enumerate(beats):
        bid = b.get("id", f"beat{i}")
        sr = b.get("sync_range")
        if not (isinstance(sr, list) and len(sr) == 2
                and all(isinstance(x, (int, float)) for x in sr)):
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
        words = _words(vis.get("props", {}).get("text") or
                       vis.get("props", {}).get("label"))
        min_len = words / (READ_WPM / 60.0)
        if words and beat_len < min_len:
            warnings.append(
                f"{bid}: {beat_len:.1f}s < read time {min_len:.1f}s "
                f"for {words} words")
        motion = b.get("motion_spec", {})
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


def main(argv=None):
    plan = json.loads(Path(argv[0] if argv else sys.argv[1])
                      .read_text(encoding="utf-8"))
    print(json.dumps(check(plan), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
