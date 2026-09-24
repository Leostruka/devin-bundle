"""L09 — knowledge labels on extracted spans; never fabricates.

attach() returns an ANNOTATED COPY: source_hash/quote/lines pass
through untouched, the label lives under a separate `annotation` key
marked confirmed=False. Unconfirmed suggestions stay out of the
factual base; writes/merges still go through existing approval.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import knowledge_labels as kl   # noqa: E402
import decision_contract as dc  # noqa: E402


@pytest.fixture
def span():
    return {"source_hash": "abc123", "quote": "deadline is Friday",
            "lines": [10, 11], "source": "meeting-notes.md"}


# --- attach ------------------------------------------------------------------

def test_label_keeps_original_evidence(span):
    labelled = kl.attach(span, "concept")
    assert labelled["source_hash"] == span["source_hash"]
    assert labelled["quote"] == span["quote"]
    assert labelled["lines"] == span["lines"]


def test_attach_never_mutates_input(span):
    kl.attach(span, "entity")
    assert "annotation" not in span


def test_annotation_is_unconfirmed_and_separate(span):
    labelled = kl.attach(span, "entity")
    assert labelled["annotation"]["label"] == "entity"
    assert labelled["annotation"]["confirmed"] is False
    assert labelled["annotation"]["source"] == "laya"


def test_label_outside_ontology_rejected(span):
    with pytest.raises(ValueError, match="label_not_in_ontology"):
        kl.attach(span, "made_up_label")


def test_span_without_provenance_rejected():
    with pytest.raises(ValueError, match="span_provenance_missing"):
        kl.attach({"quote": "orphan text"}, "concept")
    with pytest.raises(ValueError, match="span_provenance_missing"):
        kl.attach({"source_hash": "abc"}, "concept")   # no quote


def test_attach_with_confidence(span):
    labelled = kl.attach(span, "concept", confidence=0.8)
    assert labelled["annotation"]["confidence"] == 0.8


# --- suggest (worker round trip) ------------------------------------------------

class FakeClient:
    def __init__(self, choice="concept"):
        self.calls = []
        self._choice = choice

    def recommend(self, request):
        self.calls.append(request)
        return {"ok": True, "version": 1,
                "request_id": request["request_id"],
                "outcome": "suggestion", "candidate_id": self._choice,
                "context": {}, "raw_confidence": 0.75,
                "raw_top_probability": 0.75,
                "calibrated_probability": None, "calibration_id": None,
                "mode": "shadow", "adoptable": False,
                "reason": "uncalibrated", "model_identity": "fake",
                "profile_version": "knowledge-label-v1"}


def test_suggest_attaches_label(span):
    out = kl.suggest(FakeClient("concept"), span)
    assert out["annotation"]["label"] == "concept"
    assert out["annotation"]["confirmed"] is False
    assert out["quote"] == "deadline is Friday"


def test_suggest_candidates_are_ontology_labels(span):
    c = FakeClient("entity")
    kl.suggest(c, span)
    ids = {cd["id"] for cd in c.calls[0]["candidates"]}
    assert ids <= kl.ONTOLOGY


def test_suggest_invalid_reply_leaves_span_unlabelled(span):
    class Bad(FakeClient):
        def recommend(self, request):
            r = super().recommend(request)
            r["candidate_id"] = "hallucinated"
            return r
    out = kl.suggest(Bad(), span)
    assert "annotation" not in out or \
        out["annotation"]["label"] not in ("hallucinated",)


def test_no_persistence_no_writes(tmp_path, span):
    """attach/suggest write nothing: no files appear, span unchanged."""
    before = set(Path(ROOT).rglob("*"))
    kl.attach(span, "concept")
    kl.suggest(FakeClient(), span)
    assert set(Path(ROOT).rglob("*")) == before
    assert "annotation" not in span
