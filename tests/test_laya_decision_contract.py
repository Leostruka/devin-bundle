"""L01 — closed decision contract (no model).

validate_request/validate_recommendation enforce the §5.1 envelope:
unique candidate ids, __none__ reserved, <=8 candidates, echo-context
matching for provenance, numbers that are real numbers (never NaN/Inf,
never bool-as-number), and feature-off semantics. Nothing here spawns
a subprocess or reads weights — mode: off is a complete no-op.
"""
import json
import math
import sys
from pathlib import Path

import pytest

LAYA_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA_DIR))

import decision_contract as dc  # noqa: E402


@pytest.fixture
def req():
    return {
        "version": 1,
        "request_id": "d-17",
        "profile": "ui-target-v1",
        "mode": "shadow",
        "language": "pt",
        "context": {"env_id": "vm-a", "instance_id": "i-3",
                    "observation_id": "obs-17"},
        "state": {"goal": "Abrir as configurações de áudio"},
        "candidates": [
            {"id": "as", "role": "Button", "name": "Áudio",
             "scope": "Configurações"},
            {"id": "ad", "role": "Button", "name": "Vídeo",
             "scope": "Configurações"},
        ],
        "deadline_ms": 1000,
    }


def _resp(req, **over):
    r = {"ok": True, "version": 1, "request_id": req["request_id"],
         "outcome": "suggestion", "candidate_id": "as",
         "context": dict(req.get("context") or {}),
         "raw_confidence": 0.72, "raw_top_probability": 0.93,
         "calibrated_probability": None, "calibration_id": None,
         "mode": "shadow", "adoptable": False, "reason": "uncalibrated",
         "model_identity": "approved-local-snapshot",
         "profile_version": "ui-target-v1"}
    r.update(over)
    return r


# --- request ---------------------------------------------------------------

def test_valid_request(req):
    assert dc.validate_request(req) == []


def test_request_requires_version_and_id(req):
    for k in ("version", "request_id", "profile", "mode",
              "candidates"):
        q = dict(req)
        q.pop(k)
        assert dc.validate_request(q), f"missing {k} accepted"


def test_mode_closed_set(req):
    for bad in ("on", "auto", True, 1):
        q = dict(req, mode=bad)
        assert dc.validate_request(q)
    for ok in ("off", "shadow", "assist"):
        assert dc.validate_request(dict(req, mode=ok)) == []


def test_duplicate_candidate_ids_rejected(req):
    req["candidates"].append(dict(req["candidates"][0]))
    assert "duplicate_candidate_id" in \
        ";".join(dc.validate_request(req))


def test_none_sentinel_reserved(req):
    req["candidates"].append(
        {"id": "__none__", "role": "x", "name": "x", "scope": "x"})
    assert "reserved_candidate_id" in \
        ";".join(dc.validate_request(req))


def test_candidate_limit_eight(req):
    req["candidates"] = [
        {"id": f"c{i}", "role": "Button", "name": f"n{i}",
         "scope": "s"} for i in range(9)]
    assert "too_many_candidates" in \
        ";".join(dc.validate_request(req))
    req["candidates"] = req["candidates"][:8]
    assert dc.validate_request(req) == []


def test_candidate_fields(req):
    req["candidates"][0]["id"] = ""
    assert dc.validate_request(req)
    req["candidates"][0]["id"] = 7
    assert dc.validate_request(req)


def test_deadline_positive_int(req):
    for bad in (0, -1, "1000", 1.5, True):
        assert dc.validate_request(dict(req, deadline_ms=bad))


def test_state_allowlist_and_no_secrets(req):
    for key in ("argv", "command", "sql", "token", "password",
                "cookie", "secret", "credential"):
        q = dict(req)
        q["state"] = {"goal": "g", key: "x"}
        errs = ";".join(dc.validate_request(q))
        assert "state_field_forbidden" in errs, key


def test_state_values_bounded(req):
    q = dict(req)
    q["state"] = {"goal": "g", "page_text": "x" * 100001}
    assert dc.validate_request(q)
    q["state"] = {"goal": float("nan")}
    assert dc.validate_request(q)      # NaN rejected
    q["state"] = {"goal": float("inf")}
    assert dc.validate_request(q)      # Inf rejected
    q["state"] = {"goal": {"nested": "blob"}}
    assert dc.validate_request(q)      # no blobs


def test_bool_is_not_a_number(req):
    q = dict(req)
    q["state"] = {"goal": "g", "confidence_hint": True}
    assert dc.validate_request(q)


# --- recommendation ---------------------------------------------------------

def test_valid_recommendation(req):
    assert dc.validate_recommendation(_resp(req), req) == []


def test_unknown_candidate_cannot_be_adopted(req):
    r = _resp(req, candidate_id="invented")
    errs = ";".join(dc.validate_recommendation(r, req))
    assert "candidate_not_in_request" in errs


def test_none_outcome_is_abstention(req):
    r = _resp(req, outcome="abstain", candidate_id="__none__",
              reason="no_match")
    assert dc.validate_recommendation(r, req) == []


def test_foreign_request_rejected(req):
    r = _resp(req, request_id="d-999")
    assert "request_id_mismatch" in \
        ";".join(dc.validate_recommendation(r, req))


def test_context_echo_must_match(req):
    r = _resp(req)
    r["context"]["instance_id"] = "i-OTHER"
    assert "context_mismatch" in \
        ";".join(dc.validate_recommendation(r, req))


def test_confidence_fields_real_numbers(req):
    for bad in (float("nan"), float("inf"), "0.9", True, -0.1, 1.5):
        r = _resp(req, raw_confidence=bad)
        assert dc.validate_recommendation(r, req), bad


def test_outcome_closed_set(req):
    for bad in ("allow", "execute", "yes"):
        assert dc.validate_recommendation(
            _resp(req, outcome=bad), req)


def test_profile_version_matches(req):
    r = _resp(req, profile_version="other-profile")
    assert "profile_mismatch" in \
        ";".join(dc.validate_recommendation(r, req))


# --- questions + abstention -------------------------------------------------

def test_build_questions_ui_target(req):
    q = dc.build_questions("ui-target-v1", req["candidates"])
    t = q["target"]
    assert t["type"] == "choice"
    assert set(t["criteria"]) == {"as", "ad", "__none__"}
    assert "untrusted" in t["instructions"]
    import laya_cli
    assert laya_cli.check_questions(q) == []


def test_build_questions_closed_profiles():
    q = dc.build_questions("issue-category-v1", [])
    crit = q["category"]["criteria"]
    assert "bug" in crit and "__none__" in crit
    with pytest.raises(ValueError, match="unknown_profile"):
        dc.build_questions("made-up", [])


def test_build_questions_rejects_over_limit():
    cands = [{"id": f"c{i}", "role": "r", "name": "n", "scope": "s"}
             for i in range(9)]
    with pytest.raises(ValueError):
        dc.build_questions("ui-target-v1", cands)


def test_make_abstention():
    a = dc.make_abstention("d-1", "queue_full")
    assert a["outcome"] == "abstain"
    assert a["adoptable"] is False
    assert a["request_id"] == "d-1"


# --- config: feature off is a complete no-op ---------------------------------

def test_mode_off_does_nothing():
    cfg = dc.load_config(None)          # missing file -> defaults
    assert cfg["mode"] == "off"
    assert cfg["calibration"] is None
    assert dc.enabled(cfg) is False


def test_mode_off_never_spawns(tmp_path):
    """enabled() is the ONLY gate callers need: off/unknown/absent all
    mean 'do nothing' — no engine import, no weight read."""
    cfg = dc.load_config(None)
    assert dc.enabled(cfg) is False
    assert dc.enabled({"mode": "shadow"}) is True
    assert dc.enabled({"mode": "bogus"}) is False
