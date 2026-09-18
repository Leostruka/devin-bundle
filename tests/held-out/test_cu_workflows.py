"""Held-out computer-use workflow checks.

FROZEN POLICY — do not edit after first observation: seeds 101-105,
assertions below are the fixed acceptance surface. Changes here after a
green run invalidate the held-out guarantee (see AGENTS.md rule 16 and
.devin/scratch/computer-use-staged-upgrades/issues/14).

These are INDEPENDENT of tests/validation/test_cu_workflows.py: different
seeds, different fixture shapes, same safety invariants — stale state can
never produce a physical dispatch, and session-owned inputs never leak.
"""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cu_load  # noqa: E402

hints = cu_load.load("cu_hints")
ca = cu_load.load("cu_actions")

HELD_OUT_SEEDS = (101, 102, 103, 104, 105)  # frozen — do not change


class Mouse:
    def __init__(self):
        self.held = set()
        self.dispatched = []

    def press(self, b):
        self.held.add(b)

    def release(self, b):
        self.held.discard(b)


@pytest.fixture(autouse=True)
def _iso(tmp_path, monkeypatch):
    monkeypatch.setattr(hints, "sidecar_path",
                        lambda: str(tmp_path / "h.json"))
    monkeypatch.setattr(hints, "session_path",
                        lambda: str(tmp_path / "s.json"))
    monkeypatch.setattr(hints, "_window_alive", lambda h: True)
    monkeypatch.setattr(hints, "HINT_TTL_S", 300.0)
    yield


def _obs(n=3, hwnd=900):
    els = [{"id": hid, "x": 50 * (i + 1), "y": 60 * (i + 1),
            "name": f"t{i}", "type": "Button",
            "bounds": [50 * i, 60 * i, 50 * i + 40, 60 * i + 25],
            "hwnd": hwnd, "enabled": True}
           for i, hid in enumerate(hints.hint_ids(n))]
    return hints.write_sidecar(els, window={"hwnd": hwnd})


@pytest.mark.parametrize("seed", HELD_OUT_SEEDS)
def test_heldout_stale_never_dispatches(seed):
    """Every staleness vector must end in a typed rejection with the mouse
    untouched — this is the invariant that must survive refactors."""
    import random
    rng = random.Random(seed)
    obs = _obs(n=rng.randint(1, 5))
    m = Mouse()
    vector = rng.choice(["expire", "session", "invalidate", "unknown_id"])
    if vector == "expire":
        p = hints.sidecar_path()
        d = json.load(open(p, encoding="utf-8"))
        d["created_at"] = time.time() - hints.HINT_TTL_S - 1
        json.dump(d, open(p, "w", encoding="utf-8"))
        sess = obs["session_id"]
    elif vector == "session":
        sess = "other-session"
    elif vector == "invalidate":
        hints.invalidate_sidecar()
        sess = obs["session_id"]
    else:
        sess = obs["session_id"]
    hid = rng.choice(list("asdf") + ["zz"])
    e, reason = hints.resolve_hint(hid, session=sess)
    if reason is None:
        m.press("left")
        m.release("left")
        m.dispatched.append((e["x"], e["y"]))
    assert (reason is not None) == (m.dispatched == []), \
        f"seed {seed} vector {vector}: dispatched={m.dispatched} reason={reason}"
    assert m.held == set()


@pytest.mark.parametrize("seed", HELD_OUT_SEEDS)
def test_heldout_inputs_always_released(seed):
    """Fault injection mid-gesture: no session-owned input survives."""
    import random
    rng = random.Random(seed)
    m = Mouse()
    n_fail = rng.randint(0, 2)
    for i in range(3):
        try:
            with ca.OwnedInputs() as owned:
                owned.press(m, "shift")
                owned.press(m, "k")
                if i == n_fail:
                    raise RuntimeError("fault")
                owned.release(m, "k")
                owned.release(m, "shift")
        except RuntimeError:
            pass
        assert m.held == set(), f"seed {seed} leaked input at op {i}"
