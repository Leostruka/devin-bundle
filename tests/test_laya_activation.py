"""L10 — assist promotion only with compatible calibration.

mode=assist demands calibration+evaluation IDs matching the pinned
snapshot, profile, locale, cardinality and data source. Any mismatch
degrades the worker to shadow (never blocked, never authorized).
raw_confidence never participates in authorization. off shuts down
only the worker — data and models stay.
"""
import io
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import decision_contract as dc  # noqa: E402
import laya_worker              # noqa: E402

MODEL_SHA = "a" * 64


def _cfg(mode="assist", **kw):
    c = {"version": 1, "mode": mode,
         "profiles": ["ui-target-v1"],
         "models": {"m": {"path": "C:/x/m", "sha256": MODEL_SHA,
                          "identity": "snap"}},
         "calibration": {"id": "cal-1", "threshold": 0.6,
                         "checkpoint_sha256": MODEL_SHA,
                         "profile": "ui-target-v1", "locale": "en",
                         "cardinality": 3, "data_source": "ds-9",
                         "evaluation_id": "eval-1",
                         "map": {"kind": "identity"}},
         "device": "cpu", "deadline_ms": 1000}
    c.update(kw)
    return c


def _req(mode="assist"):
    return {"version": 1, "request_id": "d-1", "profile":
            "ui-target-v1", "mode": mode, "context": {},
            "state": {"goal": "g"},
            "candidates": [{"id": "a"}, {"id": "b"}],
            "deadline_ms": 5000}


class E:
    identity = "snap"
    device = "cpu"

    def predict(self, s, q):
        return {"answers": {"target": {"choice": "a",
                                       "confidence": 0.8}},
                "routing": {"model": "m"}}


def _serve(cfg, requests):
    reader = io.StringIO("".join(json.dumps(
        {"version": 1, "request": r}) + "\n" for r in requests))
    writer = io.StringIO()
    laya_worker.serve(reader, writer, E(), cfg)
    return [json.loads(l) for l in writer.getvalue().splitlines()
            if l.strip()]


# --- activation gate ------------------------------------------------------------

def test_assist_without_calibration_degrades_to_shadow():
    cfg = _cfg()
    cfg["calibration"] = None
    assert dc.activation_errors(cfg)
    assert dc.effective_mode(cfg) == "shadow"


def test_full_compatible_calibration_allows_assist():
    assert dc.activation_errors(_cfg()) == []
    assert dc.effective_mode(_cfg()) == "assist"


def test_checkpoint_mismatch_degrades():
    cfg = _cfg()
    cfg["calibration"]["checkpoint_sha256"] = "b" * 64
    assert dc.effective_mode(cfg) == "shadow"


def test_profile_mismatch_degrades():
    cfg = _cfg()
    cfg["calibration"]["profile"] = "other-profile"
    assert dc.effective_mode(cfg) == "shadow"


def test_cardinality_beyond_limit_degrades():
    cfg = _cfg()
    cfg["calibration"]["cardinality"] = 9
    assert dc.effective_mode(cfg) == "shadow"


def test_missing_evaluation_id_degrades():
    cfg = _cfg()
    del cfg["calibration"]["evaluation_id"]
    assert dc.effective_mode(cfg) == "shadow"


def test_off_and_shadow_modes():
    assert dc.effective_mode({"mode": "off"}) == "off"
    assert dc.effective_mode({"mode": "shadow"}) == "shadow"
    assert dc.effective_mode({"mode": "bogus"}) == "off"


# --- calibrated serving ------------------------------------------------------------

def test_assist_applies_calibration_and_marks_adoptable():
    cfg = _cfg()
    cfg["calibration"]["threshold"] = 0.5   # raw 0.8 clears it
    [r] = _serve(cfg, [_req("assist")])
    assert r["outcome"] == "suggestion"
    assert r["calibrated_probability"] == pytest.approx(0.8)
    assert r["calibration_id"] == "cal-1"
    assert r["adoptable"] is True
    assert r["reason"] == "calibrated"


def test_below_threshold_not_adoptable():
    cfg = _cfg()
    cfg["calibration"]["threshold"] = 0.95
    [r] = _serve(cfg, [_req("assist")])
    assert r["outcome"] == "suggestion"
    assert r["adoptable"] is False


def test_raw_confidence_never_authorizes():
    """confidence 1.0 without calibration: adoptable stays False."""
    cfg = _cfg(mode="shadow")
    cfg["calibration"] = None

    class MaxConf(E):
        def predict(self, s, q):
            return {"answers": {"target": {"choice": "a",
                                           "confidence": 1.0}}}
    reader = io.StringIO(json.dumps(
        {"version": 1, "request": _req("assist")}) + "\n")
    writer = io.StringIO()
    laya_worker.serve(reader, writer, MaxConf(), cfg)
    r = json.loads(writer.getvalue().splitlines()[0])
    assert r["adoptable"] is False
    assert r["calibrated_probability"] is None


def test_shadow_request_on_assist_worker_stays_shadow():
    [r] = _serve(_cfg(), [_req("shadow")])
    assert r["adoptable"] is False
    assert r["mode"] == "shadow"
