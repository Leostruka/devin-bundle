"""L07 — contextual labels on tool outputs, never authority over them.

annotate() attaches context_suggestion as an EXTRA field. Exit codes,
status, stderr text and provenance pass through byte-identical — the
model can never turn a failed process green or hide an error.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import output_context as oc     # noqa: E402
import decision_contract as dc  # noqa: E402

LABELS = set(dc._PROFILES["output-context-v1"][2])


def test_classifier_cannot_turn_failed_process_green():
    result = oc.annotate({"exit_code": 1, "status": "failed"},
                         {"choice": "warning_only"})
    assert result["exit_code"] == 1
    assert result["status"] == "failed"


def test_annotate_preserves_every_original_field():
    original = {"exit_code": 2, "status": "failed",
                "stderr": "EACCES denied", "tool": "exec",
                "blob": "x" * 9999}
    out = oc.annotate(original, {"choice": "runtime_failure"})
    for k, v in original.items():
        assert out[k] == v          # untouched, not truncated
    assert out["context_suggestion"]["label"] == "runtime_failure"


def test_annotate_does_not_mutate_input():
    original = {"exit_code": 0}
    oc.annotate(original, {"choice": "warning_only"})
    assert "context_suggestion" not in original


def test_unknown_label_falls_back_to_none():
    out = oc.annotate({"exit_code": 1},
                      {"choice": "everything_is_fine"})
    assert out["context_suggestion"]["label"] == "__none__"


def test_recommendation_shape_accepted():
    out = oc.annotate({"exit_code": 0},
                      {"candidate_id": "warning_only",
                       "raw_confidence": 0.7})
    assert out["context_suggestion"]["label"] == "warning_only"
    assert out["context_suggestion"]["confidence"] == 0.7


def test_non_dict_suggestion_is_none():
    out = oc.annotate({"exit_code": 0}, "nonsense")
    assert out["context_suggestion"]["label"] == "__none__"


# --- normalize -----------------------------------------------------------------

def test_normalize_extracts_authoritative_fields():
    n = oc.normalize({"tool": "exec", "op": "run", "exit_code": 1,
                      "status": "failed", "stderr": "boom",
                      "provenance": {"source": "ci"}})
    assert n["tool_name"] == "exec"
    assert n["exit_code"] == 1
    assert n["status"] == "failed"
    assert n["provenance"] == {"source": "ci"}


def test_normalize_bounds_excerpt():
    n = oc.normalize({"stderr": "e" * 50000, "stdout": "o" * 50000})
    assert len(n["excerpt"]) <= 4000


def test_normalize_content_is_data_not_execution():
    """Source content (even code) is a bounded string field only."""
    n = oc.normalize({"stdout": "raise SystemExit(1)"})
    assert isinstance(n["excerpt"], str)
    assert "raise" in n["excerpt"]


# --- suggest (model round trip) --------------------------------------------------

class FakeClient:
    def __init__(self, choice="runtime_failure"):
        self.calls = []
        self._choice = choice

    def recommend(self, request):
        self.calls.append(request)
        return {"ok": True, "version": 1,
                "request_id": request["request_id"],
                "outcome": "suggestion", "candidate_id": self._choice,
                "context": {}, "raw_confidence": 0.6,
                "raw_top_probability": 0.6,
                "calibrated_probability": None, "calibration_id": None,
                "mode": "shadow", "adoptable": False,
                "reason": "uncalibrated", "model_identity": "fake",
                "profile_version": "output-context-v1"}


def test_suggest_attaches_label():
    c = FakeClient("warning_only")
    out = oc.suggest(c, {"exit_code": 0, "stderr": "deprecated warn"})
    assert out["context_suggestion"]["label"] == "warning_only"
    assert c.calls[0]["profile"] == "output-context-v1"
    # candidates are the closed label set
    ids = {cd["id"] for cd in c.calls[0]["candidates"]}
    assert ids == LABELS


def test_suggest_invalid_reply_still_preserves_result():
    class Bad(FakeClient):
        def recommend(self, request):
            r = super().recommend(request)
            r["candidate_id"] = "made_up_label"
            return r
    out = oc.suggest(Bad(), {"exit_code": 1, "status": "failed"})
    assert out["exit_code"] == 1
    assert out["context_suggestion"]["label"] == "__none__"
