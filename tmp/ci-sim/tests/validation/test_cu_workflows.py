"""Ticket 05 gate: seeded end-to-end workflow chains over fakes — the
observe -> hint -> dispatch loop must never dispatch on stale state."""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cu_load  # noqa: E402

hints = cu_load.load("cu_hints")
cm = cu_load.load("cu_motion")
ca = cu_load.load("cu_actions")


class FakeMouse:
    def __init__(self):
        self.dispatched = []
        self.held = set()

    def press(self, b):
        self.held.add(b)

    def release(self, b):
        self.held.discard(b)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(hints, "sidecar_path",
                        lambda: str(tmp_path / "hints.json"))
    monkeypatch.setattr(hints, "session_path",
                        lambda: str(tmp_path / "session.json"))
    monkeypatch.setattr(hints, "HINT_TTL_S", 120.0)
    monkeypatch.setattr(hints, "_window_alive", lambda hwnd: True)
    yield


def _observe():
    """Simulate screenshot --hints: one observation, two elements."""
    els = [{"id": "a", "x": 100, "y": 100, "name": "OK", "type": "Button",
            "bounds": [90, 90, 120, 110], "hwnd": 500, "enabled": True},
           {"id": "b", "x": 200, "y": 200, "name": "Cancel", "type": "Button",
            "bounds": [190, 190, 230, 215], "hwnd": 500, "enabled": True}]
    return hints.write_sidecar(els, window={"hwnd": 500, "title": "App"})


def _dispatch_click(mouse, entry):
    """The real dispatch contract: only reached when resolve succeeded."""
    mouse.press("left")
    mouse.release("left")
    mouse.dispatched.append((entry["x"], entry["y"]))


def _try_click(mouse, hint_id, session):
    e, reason = hints.resolve_hint(hint_id, session=session)
    if reason is not None:
        return ca.result("rejected", "physical", error=reason)
    _dispatch_click(mouse, e)
    return ca.result("dispatched", "physical")


def test_observe_then_click_dispatches():
    obs = _observe()
    m = FakeMouse()
    r = _try_click(m, "a", session=obs["session_id"])
    assert r["ok"] is True and r["status"] == "dispatched"
    assert m.dispatched == [(100, 100)]


def test_expired_observation_zero_dispatch():
    obs = _observe()
    m = FakeMouse()
    p = hints.sidecar_path()
    import json
    d = json.load(open(p, encoding="utf-8"))
    d["created_at"] = time.time() - hints.HINT_TTL_S - 1
    json.dump(d, open(p, "w", encoding="utf-8"))
    r = _try_click(m, "a", session=obs["session_id"])
    assert r["status"] == "rejected" and r["error"] == "expired"
    assert m.dispatched == [] and m.held == set()


def test_foreign_session_zero_dispatch():
    _observe()
    m = FakeMouse()
    r = _try_click(m, "a", session="sess-OTHER")
    assert r["status"] == "rejected" and r["error"] == "session"
    assert m.dispatched == []


def test_focus_change_window_gone_zero_dispatch(monkeypatch):
    obs = _observe()
    monkeypatch.setattr(hints, "_window_alive", lambda hwnd: False)
    m = FakeMouse()
    r = _try_click(m, "a", session=obs["session_id"])
    assert r["status"] == "rejected" and r["error"] == "window_gone"
    assert m.dispatched == []


def test_reobserve_generations_monotonic():
    o1 = _observe()
    o2 = _observe()
    assert o2["generation"] == o1["generation"] + 1
    assert o2["observation_id"] != o1["observation_id"]


def test_invalidation_then_reobserve_uses_new_state():
    _observe()
    hints.invalidate_sidecar()
    m = FakeMouse()
    # between observations nothing may dispatch
    r = _try_click(m, "a", session=None)
    assert r["status"] == "rejected"
    obs2 = _observe()
    r = _try_click(m, "b", session=obs2["session_id"])
    assert r["ok"] is True and m.dispatched == [(200, 200)]


def test_unicode_text_plan_bounded():
    """Unicode/IME-adjacent text must produce a bounded interval per char —
    no crashes, no negative/zero cadence."""
    for text in ("héllo wörld", "日本語テスト", "emoji ✓ ñ ü", "àb̃c̃"):
        ds = cm.typing_intervals(
            text,
            medians={"a": 0.1, "e": 0.1},
            fallback=0.15, sigma=0.25, bounds=(0.01, 1.0), seed=1)
        assert len(ds) == len(text)
        assert all(0.01 <= d <= 1.0 for d in ds)


def test_action_accepted_without_visible_effect_is_dispatch_only():
    """A dispatched result must NOT claim verified effect — the contract
    field keeps the difference explicit for the agent."""
    obs = _observe()
    m = FakeMouse()
    r = _try_click(m, "a", session=obs["session_id"])
    assert r["status"] == "dispatched"  # sent, not proven
    assert "verified" != r["status"]


# --- Ticket 15: remaining adversarial cases ------------------------------------

def test_reobserve_stales_prior_hint_ids():
    """Resize/DPI/re-layout analogue: a new observation bumps generation;
    a caller resolving with the OLD generation is rejected as stale."""
    obs1 = _observe()
    obs2 = _observe()  # layout changed -> new snapshot
    m = FakeMouse()
    e, reason = hints.resolve_hint("a", session=obs1["session_id"],
                                   generation=obs1["generation"])
    assert reason == "stale_generation" and e is None
    assert m.dispatched == []
    # caller tracking the current generation resolves fine
    e, reason = hints.resolve_hint("a", session=obs2["session_id"],
                                   generation=obs2["generation"])
    assert reason is None and e["x"] == 100


def test_disabled_element_hint_resolves_but_semantic_rejects():
    """Disabled control: hint resolves (coordinates valid) but semantic
    dispatch must refuse — clicks on disabled elements are blind."""
    els = [{"id": "d", "x": 50, "y": 50, "name": "Off", "type": "Button",
            "bounds": [40, 40, 60, 60], "hwnd": 500, "enabled": False}]
    obs = hints.write_sidecar(els, window={"hwnd": 500})
    e, reason = hints.resolve_hint("d", session=obs["session_id"])
    assert reason is None and e["enabled"] is False
    # dom/uia callers gate on entry["enabled"] -> physical caller decides;
    # semantic path rejection is covered in test_cu_browser_routing.
