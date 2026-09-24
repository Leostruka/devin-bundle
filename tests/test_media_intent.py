"""L08 — creative preset suggestions without pixel judgment.

Explicit names win; the model classifies text against the existing
catalog only. Output is a workflow destination or existing preset id —
never params, output files, camera, overwrite or delete.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "media-tools"))
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import intent                   # noqa: E402
import decision_contract as dc  # noqa: E402

PRESETS = ["halftone", "ascii", "grainrad", "crosshatch", "dots"]


def _reply(req, choice):
    return {"ok": True, "version": 1,
            "request_id": req["request_id"],
            "outcome": "suggestion" if choice != "__none__" else "abstain",
            "candidate_id": choice, "context": {},
            "raw_confidence": 0.7, "raw_top_probability": 0.7,
            "calibrated_probability": None, "calibration_id": None,
            "mode": req["mode"], "adoptable": False,
            "reason": "uncalibrated", "model_identity": "fake",
            "profile_version": req["profile"]}


class FakeClient:
    def __init__(self, intent="stylize_image", preset="halftone"):
        self.calls = []
        self._intent, self._preset = intent, preset

    def recommend(self, request):
        self.calls.append(request)
        if request["profile"] == "media-intent-v1":
            return _reply(request, self._intent)
        return _reply(request, self._preset)


# --- explicit resolution --------------------------------------------------------

def test_explicit_effect_is_preserved():
    assert intent.resolve_explicit("halftone",
                                   {"halftone", "ascii"}) == "halftone"


def test_resolve_explicit_no_inference():
    assert intent.resolve_explicit("halfton", {"halftone"}) is None
    assert intent.resolve_explicit("HALFTONE", {"halftone"}) is None
    assert intent.resolve_explicit("", {"halftone"}) is None


def test_explicit_name_in_text_wins_no_model():
    c = FakeClient()
    out = intent.suggest(c, "make it crosshatch please", PRESETS)
    assert c.calls == []
    assert out["candidate_id"] == "crosshatch"
    assert out["reason"] == "explicit_name"


# --- intent -> preset flow ---------------------------------------------------------

def test_two_stage_suggests_existing_preset():
    c = FakeClient("stylize_image", "ascii")
    out = intent.suggest(c, "retro terminal look", PRESETS)
    assert out["outcome"] == "suggestion"
    assert out["candidate_id"] == "ascii"
    assert out["intent"] == "stylize_image"
    assert [r["profile"] for r in c.calls] == \
        ["media-intent-v1", "media-preset-v1"]


def test_workflow_destination_returns_intent():
    c = FakeClient(intent="diagram")
    out = intent.suggest(c, "flowchart of the pipeline", PRESETS)
    assert out["candidate_id"] == "diagram"
    assert len(c.calls) == 1          # preset stage not needed


def test_result_has_no_execution_fields():
    out = intent.suggest(FakeClient(), "gritty photo", PRESETS)
    for banned in ("output", "path", "params", "camera",
                   "overwrite", "delete", "args"):
        assert banned not in out


def test_preset_outside_catalog_abstains():
    out = intent.suggest(FakeClient(preset="deepfry"), "x", PRESETS)
    assert out["outcome"] == "abstain"
    # candidate not in the request's closed set -> reply invalid
    assert out["reason"] == "invalid_reply"


def test_no_presets_abstains():
    out = intent.suggest(FakeClient(), "x", [])
    assert out["outcome"] == "abstain"
    assert out["reason"] == "no_presets_available"


def test_intent_abstain_short_circuits():
    c = FakeClient(intent="__none__")
    out = intent.suggest(c, "???", PRESETS)
    assert out["outcome"] == "abstain"
    assert len(c.calls) == 1
