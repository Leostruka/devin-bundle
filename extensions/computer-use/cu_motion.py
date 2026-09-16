#!/usr/bin/env python3
"""Shared action-profile state + motion/timing generators for computer-use.

Profiles:
  fast   — teleport moves, instant typing (legacy behavior, the default)
  smooth — cinematic eased arc (cubic bezier + easeInOutCubic)
  human  — Fitts-law duration, multi-knot bezier, jitter, rare overshoot,
           stochastic keystroke intervals

Precedence: --profile flag > $COMPUTER_USE_PROFILE > session file > "fast".
Session file: <temp>/devin-cu-profile.json
"""
import argparse
import json
import math
import os
import random
import tempfile
import time

PROFILES = ("fast", "smooth", "human")
ENV_VAR = "COMPUTER_USE_PROFILE"


class JsonParser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors still emit one JSON object on stdout."""
    def error(self, message):
        print(json.dumps({"ok": False, "error": f"usage: {message}"}))
        raise SystemExit(2)


def profile_path():
    return os.path.join(tempfile.gettempdir(), "devin-cu-profile.json")


def get_profile(flag=None):
    if flag in PROFILES:
        return flag
    env = os.environ.get(ENV_VAR)
    if env in PROFILES:
        return env
    try:
        with open(profile_path(), encoding="utf-8") as f:
            v = json.load(f).get("profile")
        if v in PROFILES:
            return v
    except Exception:
        pass
    return "fast"


def set_profile(name):
    if name not in PROFILES:
        raise ValueError(f"bad profile {name!r}")
    with open(profile_path(), "w", encoding="utf-8") as f:
        json.dump({"profile": name}, f)


# --- easing -----------------------------------------------------------------

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)


def _bezier(ctrl, t):
    pts = list(ctrl)
    while len(pts) > 1:
        pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
               for a, b in zip(pts, pts[1:])]
    return pts[0]


def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def gen_path(profile, x0, y0, x1, y1, target_w=30.0):
    """Return (points, duration_s). points[0] is never the start; the last
    point is always exactly (x1, y1)."""
    d = _dist((x0, y0), (x1, y1))
    if profile == "fast" or d < 3:
        return [(x1, y1)], 0.0
    if profile == "smooth":
        return _smooth(x0, y0, x1, y1, d)
    return _human(x0, y0, x1, y1, d, target_w)


def _smooth(x0, y0, x1, y1, d):
    dur = min(max(0.25 + 0.35 * math.log2(d / 400 + 1), 0.25), 0.9)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0) / d, (x1 - x0) / d
    off = d * random.uniform(0.08, 0.14) * random.choice((-1, 1))
    ctrl = [(x0, y0), (mx + nx * off, my + ny * off), (x1, y1)]
    n = max(int(dur * 90), 8)
    pts = []
    for i in range(1, n + 1):
        px, py = _bezier(ctrl, ease_in_out_cubic(i / n))
        pts.append((round(px), round(py)))
    pts[-1] = (x1, y1)
    return pts, dur


def _human(x0, y0, x1, y1, d, target_w):
    # Fitts's law (Shannon form): MT = a + b * log2(D/W + 1)
    dur = (0.08 + 0.16 * math.log2(d / max(target_w, 1) + 1))
    dur = min(max(dur * random.gauss(1.0, 0.08), 0.15), 1.6)
    tx, ty, overshot = x1, y1, False
    if d > 300 and random.random() < 0.15:
        ux, uy = (x1 - x0) / d, (y1 - y0) / d
        tx += ux * random.uniform(6, 20)
        ty += uy * random.uniform(6, 20)
        overshot = True
    pad = max(d * 0.12, 40)
    lx, rx = min(x0, tx) - pad, max(x0, tx) + pad
    ly, ry = min(y0, ty) - pad, max(y0, ty) + pad
    ctrl = [(x0, y0)]
    ctrl += [(random.uniform(lx, rx), random.uniform(ly, ry))
             for _ in range(random.randint(1, 3))]
    ctrl.append((tx, ty))
    n = max(int(dur * 110), 10)
    pts = []
    for i in range(1, n + 1):
        px, py = _bezier(ctrl, ease_out_quad(i / n))
        if random.random() < 0.5:
            px += random.gauss(0, 1.2)
            py += random.gauss(0, 1.2)
        pts.append((round(px), round(py)))
    if overshot:  # corrected return to the real target
        back = max(int(dur * 40), 3)
        for i in range(1, back + 1):
            t = ease_out_quad(i / back)
            pts.append((round(tx + (x1 - tx) * t), round(ty + (y1 - ty) * t)))
    pts[-1] = (x1, y1)
    return pts, dur


def play_path(mouse, pts, dur):
    if len(pts) <= 1:
        if pts:
            mouse.position = pts[-1]
        return
    dt = dur / len(pts)
    for p in pts:
        mouse.position = p
        time.sleep(dt)


def pre_click_delay(profile):
    if profile == "human":
        return max(0.03, random.gauss(0.12, 0.04))
    if profile == "smooth":
        return 0.08
    return 0.05


def click_hold(profile, hold_ms=None):
    if hold_ms is not None:
        return max(hold_ms, 0) / 1000
    if profile == "human":
        return min(max(random.gauss(0.07, 0.015), 0.02), 0.2)
    return 0.05


def scroll_gaps(profile, n):
    if profile == "human":
        return [max(0.01, random.gauss(0.07, 0.02)) for _ in range(n)]
    if profile == "smooth":
        return [0.03] * n
    return [0.0] * n


def key_gap(profile):
    """Press→release gap for --key/--keys in non-fast profiles."""
    if profile == "human":
        return max(0.01, random.gauss(0.04, 0.012))
    if profile == "smooth":
        return 0.02
    return 0.0


def type_delays(text, profile, fixed=None):
    """Per-char delays. None = single instant kb.type() call (fast)."""
    if fixed is not None and fixed > 0:
        return [fixed] * len(text)
    if profile == "fast":
        return None
    if profile == "smooth":
        return [0.035] * len(text)
    out = []
    prev = ""
    for ch in text:
        d = random.gauss(0.09, 0.03)
        if ch == prev and ch.strip():
            d *= 0.55
        out.append(max(0.015, d))
        if random.random() < 0.03:
            out[-1] += random.gauss(0.22, 0.07)
        prev = ch
    return out
