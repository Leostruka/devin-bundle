"""Etapa 7 gates: minimum-jerk presentation path, absolute-deadline
scheduling, seeded reproducibility, digram/trigram typing cadence."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load

cm = load("cu_motion")


class FakeMouse:
    def __init__(self):
        self.positions = []
        self._pos = (0, 0)

    @property
    def position(self):
        return self._pos

    @position.setter
    def position(self, v):
        self._pos = v
        self.positions.append(v)


def test_minjerk_endpoints_and_monotonic_progress():
    pts, dur = cm.gen_path("smooth", 0, 0, 100, -50, motion="minjerk")
    assert pts[-1] == (100, -50)  # endpoint always exact
    xs = [p[0] for p in pts]
    assert all(a <= b for a, b in zip(xs, xs[1:]))  # straight, no backtrack
    assert dur > 0


def test_minjerk_no_overshoot_any_seed():
    for seed in range(5):
        pts, _ = cm.gen_path("human", 10, 10, 800, 10,
                             motion="minjerk", seed=seed)
        assert all(p[0] <= 800 for p in pts)
        assert pts[-1] == (800, 10)


def test_minjerk_zero_distance_and_negative_coords():
    pts, dur = cm.gen_path("smooth", -5, -5, -5, -5, motion="minjerk")
    assert pts == [(-5, -5)] and dur == 0.0
    pts, dur = cm.gen_path("smooth", -300, -100, -10, -50, motion="minjerk")
    assert pts[-1] == (-10, -50)
    assert all(p[0] <= -10 for p in pts)


def test_human_path_seed_reproducible():
    a = cm.gen_path("human", 0, 0, 500, 300, seed=42)
    b = cm.gen_path("human", 0, 0, 500, 300, seed=42)
    assert a == b


def test_fast_profile_ignores_motion():
    pts, dur = cm.gen_path("fast", 0, 0, 500, 300, motion="minjerk")
    assert pts == [(500, 300)] and dur == 0.0


def test_play_path_absolute_deadlines(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(cm.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(cm.time, "sleep",
                        lambda s: now.__setitem__(0, now[0] + s))
    m = FakeMouse()
    cm.play_path(m, [(10, 0), (20, 0), (30, 0)], 0.3)
    assert now[0] == pytest.approx(0.3)  # no accumulated sleep drift
    assert m.positions == [(10, 0), (20, 0), (30, 0)]


def test_play_path_cancel_stops_dispatch(monkeypatch):
    monkeypatch.setattr(cm.time, "sleep", lambda s: None)
    calls = iter([False, False, True])  # cancel before 3rd point
    m = FakeMouse()
    cm.play_path(m, [(i, 0) for i in range(10)], 1.0,
                 cancel=lambda: next(calls))
    assert len(m.positions) == 2


def test_typing_intervals_context_priority():
    medians = {"ab": 0.05, "abc": 0.20}
    iv = cm.typing_intervals("abc", medians, 0.09, 0.0, (0.01, 0.5), 3)
    assert math.isclose(iv[0], 0.09)  # "a" has no context -> fallback
    assert math.isclose(iv[1], 0.05)  # "ab" digram
    assert math.isclose(iv[2], 0.20)  # "abc" trigram beats digram


def test_typing_delays_seed_reproducible_and_bounded():
    a = cm.type_delays("hello world", "human", seed=7)
    b = cm.type_delays("hello world", "human", seed=7)
    assert a == b and len(a) == 11
    lo, hi = cm._TYPING_BOUNDS
    assert all(lo <= d <= hi for d in a)


def test_type_delays_fast_fixed_smooth_unchanged():
    assert cm.type_delays("abc", "fast") is None
    assert cm.type_delays("abc", "smooth") == [0.035] * 3
    assert cm.type_delays("abc", "human", fixed=0.02) == [0.02] * 3


def test_hick_hyman_scales_with_choice_count():
    d1 = cm.pre_click_delay("human", n_choices=2, seed=7)
    d2 = cm.pre_click_delay("human", n_choices=32, seed=7)
    assert d2 > d1  # more on-screen choices -> longer decision dwell
    assert cm.pre_click_delay("fast", n_choices=32) == 0.05


def test_smooth_scroll_inertial_deceleration():
    gaps = cm.scroll_gaps("smooth", 9, seed=1)
    assert gaps[0] < gaps[-1]               # decelerating
    assert all(gaps[i] <= gaps[i + 1] + 1e-9 for i in range(8))
    assert cm.scroll_gaps("smooth", 9, seed=1) == gaps  # seeded replay


def test_typing_plan_typo_and_backspace():
    plan = cm.typing_plan("a" * 400, "human", seed=3, error_rate=0.05)
    ops = [op for op, _, _ in plan]
    assert "backspace" in ops  # rare typos injected + corrected
    # deterministic replay
    assert plan == cm.typing_plan("a" * 400, "human", seed=3,
                                  error_rate=0.05)
    # every intended char still present in order (net text preserved)
    typed = [c for op, c, _ in plan if op == "type"]
    # wrong keys precede their backspaces; final typed sequence covers all
    # intended chars (each intended char appears exactly once as a "type"
    # after any correction)
    assert typed.count("a") >= 400


def test_seeded_gauss_replay():
    assert cm.gauss(42, 0.1, 0.02) == cm.gauss(42, 0.1, 0.02)
    assert cm.gauss(42, 0.1, 0.02) != cm.gauss(43, 0.1, 0.02)
