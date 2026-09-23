"""L04 — Laya suggests computer-use targets; it never executes.

Shadow-only plumbing: observed elements -> <=8 closed candidates ->
worker recommendation -> sanitized log. adoptable() is the single gate
any future assist path must pass: every binding field must match the
CURRENT context and the reply must carry mode=assist + adoptable.
A wrong model with max confidence still cannot cause an action —
there is no execution path in this module.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "computer-use"))
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import cu_decision as cd          # noqa: E402
import decision_contract as dc    # noqa: E402

CTX = {"env_id": "vm-a", "instance_id": "i-3", "observation_id": "o-1",
       "capabilities_digest": "capd", "policy_digest": "pold"}


def _els():
    return [{"id": "as", "role": "Button", "name": "Áudio",
             "scope": "Config", "enabled": True},
            {"id": "ad", "role": "Button", "name": "Vídeo",
             "scope": "Config", "enabled": True},
            {"id": "ax", "role": "Button", "name": "Disabled",
             "scope": "Config", "enabled": False}]


class FakeClient:
    def __init__(self, reply=None):
        self.calls = []
        self._reply = reply

    def recommend(self, request):
        self.calls.append(request)
        if self._reply is not None:
            return self._reply
        return {"ok": True, "version": 1,
                "request_id": request["request_id"],
                "outcome": "suggestion", "candidate_id": "as",
                "context": dict(request.get("context") or {}),
                "raw_confidence": 0.9, "raw_top_probability": 0.9,
                "calibrated_probability": None, "calibration_id": None,
                "mode": request["mode"], "adoptable": False,
                "reason": "uncalibrated", "model_identity": "fake",
                "profile_version": "ui-target-v1"}


# --- candidates --------------------------------------------------------------

def test_elements_to_candidates_filters_disabled():
    cands = cd.build_candidates(_els())
    assert [c["id"] for c in cands] == ["as", "ad"]


def test_candidates_capped_at_eight():
    els = [{"id": f"e{i}", "role": "Button", "name": f"n{i}",
            "enabled": True} for i in range(12)]
    assert len(cd.build_candidates(els)) == 8


def test_candidate_ids_unique_stable():
    cands = cd.build_candidates(_els() + _els())
    ids = [c["id"] for c in cands]
    assert len(ids) == len(set(ids))


# --- exact match --------------------------------------------------------------

def test_exact_match_never_calls_model():
    client = FakeClient()
    out = cd.suggest(client, CTX, "Áudio", _els())
    assert client.calls == []
    assert out["outcome"] == "suggestion"
    assert out["candidate_id"] == "as"
    assert out["reason"] == "exact_match"


def test_zero_candidates_abstains_without_model():
    client = FakeClient()
    out = cd.suggest(client, CTX, "anything", [])
    assert client.calls == []
    assert out["outcome"] == "abstain"
    assert out["reason"] == "no_candidates"


# --- shadow suggest -------------------------------------------------------------

def test_shadow_suggestion_logged_and_sanitized(tmp_path):
    log = tmp_path / "decisions.jsonl"
    client = FakeClient()
    out = cd.suggest(client, CTX, "open audio", _els(), log_path=log)
    assert out["outcome"] == "suggestion"
    rec = json.loads(log.read_text().splitlines()[0])
    assert rec["candidate_id"] == "as"
    assert "open audio" not in json.dumps(rec)   # goal text not logged
    assert rec["mode"] == "shadow"


def test_wrong_model_max_confidence_cannot_execute(tmp_path):
    """Model deliberately wrong with score 1.0: output has no action
    path and adoptable() refuses it in shadow mode."""
    bad = {"ok": True, "version": 1, "request_id": None,
           "outcome": "suggestion", "candidate_id": "ad",
           "context": dict(CTX), "raw_confidence": 1.0,
           "raw_top_probability": 1.0, "calibrated_probability": 1.0,
           "calibration_id": "c", "mode": "shadow", "adoptable": True,
           "reason": "x", "model_identity": "evil",
           "profile_version": "ui-target-v1"}

    class Evil(FakeClient):
        def recommend(self, request):
            self.calls.append(request)
            return dict(bad, request_id=request["request_id"])
    out = cd.suggest(Evil(), CTX, "open audio settings", _els())
    assert "execute" not in out and "action" not in out
    assert cd.adoptable(out, CTX) is False       # shadow != assist


def test_foreign_reply_becomes_abstain(tmp_path):
    class Foreign(FakeClient):
        def recommend(self, request):
            r = super().recommend(request)
            r["request_id"] = "d-FORGED"
            return r
    out = cd.suggest(Foreign(), CTX, "open audio", _els())
    assert out["outcome"] == "abstain"


# --- adoptable gate ---------------------------------------------------------------

def _rec(**over):
    r = {"outcome": "suggestion", "candidate_id": "as",
         "adoptable": True, "mode": "assist", "context": dict(CTX)}
    r.update(over)
    return r


def test_stale_suggestion_is_rejected():
    assert cd.adoptable({"observation_id": "old"},
                        {"observation_id": "new"}) is False


def test_adoptable_requires_every_binding_field():
    for f in CTX:
        ctx = dict(CTX)
        ctx[f] = "stale"
        assert cd.adoptable(_rec(), ctx) is False, f
    assert cd.adoptable(_rec(), CTX) is True


def test_adoptable_requires_assist_and_flag():
    assert cd.adoptable(_rec(mode="shadow"), CTX) is False
    assert cd.adoptable(_rec(adoptable=False), CTX) is False
    assert cd.adoptable(_rec(outcome="abstain"), CTX) is False


def test_adoptable_rejects_missing_fields():
    rec = _rec()
    del rec["context"]["policy_digest"]
    assert cd.adoptable(rec, CTX) is False
