"""Gate for C09: re-observe effects — an ACK is never success.

verify_effect(action, before, after, predicate) demands the SAME
instance and a LATER observation; closed predicates only; a visual
change is evidence, not task completion.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_backend = load("cu_backend")
cu_qmp_backend = load("cu_qmp_backend")


def _meta(instance="i-1", ns=1, sha="a"):
    return {"instance_id": instance, "monotonic_ns": ns,
            "frame_sha256": sha}


def _frame(rgb=b"\x00" * 12, w=2, h=2):
    return cu_qmp_backend.Frame(rgb, w, h)


# --- result_from_ack: transport only ------------------------------------------------

def test_ack_is_not_effect_verification():
    r = cu_backend.result_from_ack({"return": {}}, request_id="r1")
    assert r["status"] == "dispatched"
    assert "verification" not in r


def test_ack_carries_request_id_and_payload():
    r = cu_backend.result_from_ack({"return": {"x": 1}},
                                   request_id="r9")
    assert r["request_id"] == "r9"
    assert r["ack"] == {"x": 1}


# --- verify_effect preconditions ------------------------------------------------------

def test_verify_requires_same_instance():
    r = cu_backend.verify_effect(
        {"cmd": "click"},
        {"meta": _meta(instance="i-1")},
        {"meta": _meta(instance="i-2", ns=2, sha="b")},
        {"kind": "frame_changed"})
    assert r["verified"] is False
    assert "instance" in r["reason"]


def test_verify_requires_later_observation():
    r = cu_backend.verify_effect(
        {"cmd": "click"},
        {"meta": _meta(ns=10)},
        {"meta": _meta(ns=5)},
        {"kind": "frame_changed"})
    assert r["verified"] is False
    assert "stale" in r["reason"] or "order" in r["reason"]


def test_verify_requires_predicate():
    r = cu_backend.verify_effect(
        {}, {"meta": _meta()}, {"meta": _meta(ns=2, sha="b")}, None)
    assert r["verified"] is False


# --- closed predicates ---------------------------------------------------------------

def test_frame_changed_is_evidence_not_done():
    """Pixels differing = evidence the screen moved. It is NOT proof the
    intended action worked — status 'evidence', verified False."""
    r = cu_backend.verify_effect(
        {"cmd": "click"},
        {"meta": _meta(), "frame": _frame()},
        {"meta": _meta(ns=2, sha="b"), "frame": _frame(b"\x01" * 12)},
        {"kind": "frame_changed"})
    assert r["status"] == "evidence"
    assert r["verified"] is False
    assert r["predicate_satisfied"] is True


def test_frame_unchanged_satisfies_nothing():
    r = cu_backend.verify_effect(
        {"cmd": "click"},
        {"meta": _meta(), "frame": _frame()},
        {"meta": _meta(ns=2), "frame": _frame()},
        {"kind": "frame_changed"})
    assert r["predicate_satisfied"] is False


def test_region_changed_ignores_animation_elsewhere():
    """Animation in another rect must not satisfy a region predicate —
    the 'splash still animating' false positive."""
    before = _frame(b"\x00" * 12, 2, 2)
    after = _frame(b"\x00" * 6 + b"\xff" + b"\x00" * 5, 2, 2)
    # pixel (1,1) changed; predicate watches (0,0)-(1,0) row
    r = cu_backend.verify_effect(
        {"cmd": "click"},
        {"meta": _meta(), "frame": before},
        {"meta": _meta(ns=2, sha="b"), "frame": after},
        {"kind": "region_changed", "x": 0, "y": 0, "w": 1, "h": 1})
    assert r["predicate_satisfied"] is False


def test_region_changed_satisfied_in_region():
    before = _frame(b"\x00" * 12, 2, 2)
    after = _frame(b"\xff" * 3 + b"\x00" * 9, 2, 2)
    r = cu_backend.verify_effect(
        {"cmd": "click"},
        {"meta": _meta(), "frame": before},
        {"meta": _meta(ns=2, sha="b"), "frame": after},
        {"kind": "region_changed", "x": 0, "y": 0, "w": 1, "h": 1})
    assert r["predicate_satisfied"] is True


def test_dom_field_predicate_unavailable_is_honest():
    """No guest DOM/UIA source exists yet (C10+) — the predicate must
    report source_unavailable, never fabricate a comparison."""
    r = cu_backend.verify_effect(
        {"cmd": "type"},
        {"meta": _meta(), "frame": _frame()},
        {"meta": _meta(ns=2, sha="b"), "frame": _frame(b"\x01" * 12)},
        {"kind": "field_equals", "source": "dom",
         "field": "value", "equals": "x"})
    assert r["verified"] is False
    assert "unavailable" in r["reason"]


def test_unknown_predicate_rejected():
    r = cu_backend.verify_effect(
        {}, {"meta": _meta()}, {"meta": _meta(ns=2)}, {"kind": "magic"})
    assert r["verified"] is False
    assert "predicate" in r["reason"]


# --- CLI wiring: --verify on remote ops ------------------------------------------------

def test_remote_click_with_verify_attaches_evidence(tmp_path,
                                                    monkeypatch,
                                                    capsys):
    frames = [_frame(b"\x00" * 12, 2, 2), _frame(b"\xff" * 12, 2, 2)]
    metas = [{"backend": "qmp", "instance_id": "i-1",
              "monotonic_ns": 1, "frame_sha256": "a",
              "origin_px": [0, 0]},
             {"backend": "qmp", "instance_id": "i-1",
              "monotonic_ns": 2, "frame_sha256": "b",
              "origin_px": [0, 0]}]

    class FakeBackend:
        env_dir = tmp_path / "env"
        calls = {"observe": 0}

        def observe(self):
            i = self.calls["observe"]
            self.calls["observe"] += 1
            return frames[min(i, 1)], metas[min(i, 1)]

        def send_events(self, events):
            return {"dispatched": len(events)}

    (tmp_path / "env").mkdir()
    reg = tmp_path / "envs"
    reg.mkdir()
    (reg / "devin-linux.json").write_text(json.dumps(
        {"env_id": "devin-linux", "provider": "qemu"}))
    monkeypatch.setenv("CU_ENV_ROOT", str(reg))
    cb = load("cu_backend")
    monkeypatch.setattr(cb, "open_backend",
                        lambda target: FakeBackend())
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "click", "1", "1",
                         "--env", "devin-linux", "--verify"])
    mouse.main()
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is True
    assert out["status"] == "dispatched"  # ACK still not promoted
    assert out["verification"]["status"] == "evidence"
    assert out["verification"]["predicate_satisfied"] is True
