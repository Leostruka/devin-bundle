"""L03 — evaluation metrics over FROZEN captures.

Metrics are pure functions tested with known vectors. evaluate()
consumes a frozen manifest (requests + gold labels + recorded replies)
and never calls an engine, never dispatches tools, never reads
production data, never flips a flag.
"""
import json
import sys
from pathlib import Path

import pytest

LAYA_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA_DIR))

import eval_decisions as ed  # noqa: E402


def _req(rid, cand_ids=("a", "b")):
    return {"version": 1, "request_id": rid, "profile": "ui-target-v1",
            "mode": "shadow",
            "candidates": [{"id": c} for c in cand_ids],
            "deadline_ms": 1000}


def _reply(req, choice, conf=0.9):
    return {"ok": True, "version": 1,
            "request_id": req["request_id"],
            "outcome": "abstain" if choice == "__none__" else "suggestion",
            "candidate_id": choice, "context": req.get("context") or {},
            "raw_confidence": conf, "raw_top_probability": conf,
            "calibrated_probability": None, "calibration_id": None,
            "mode": "shadow", "adoptable": False, "reason": "x",
            "model_identity": "m", "profile_version": "ui-target-v1"}


def _case(rid, gold, choice=None, cands=("a", "b")):
    req = _req(rid, cands)
    reply = _reply(req, choice if choice is not None else gold)
    return {"case_id": rid, "gold": gold, "request": req,
            "reply": reply}


# --- wilson -------------------------------------------------------------------

def test_wilson_empty_and_perfect_are_distinct():
    assert ed.wilson_lower(0, 0) == 0.0
    assert 0.99 < ed.wilson_lower(300, 300) < 1.0


def test_wilson_monotonic_in_successes():
    assert ed.wilson_lower(9, 10) > ed.wilson_lower(1, 10)
    assert ed.wilson_lower(50, 100) > ed.wilson_lower(5, 10)


def test_wilson_bounds():
    assert 0.0 <= ed.wilson_lower(0, 10) < ed.wilson_lower(10, 10) <= 1.0


# --- score_case -----------------------------------------------------------------

def test_correct_case():
    s = ed.score_case(_case("c1", "a"))
    assert s["outcome"] == "correct"


def test_wrong_case():
    s = ed.score_case(_case("c1", "a", choice="b"))
    assert s["outcome"] == "wrong"


def test_abstain_on_gold_is_missed():
    s = ed.score_case(_case("c1", "a", choice="__none__"))
    assert s["outcome"] == "abstained"


def test_correct_abstention():
    s = ed.score_case(_case("c1", "__none__", choice="__none__"))
    assert s["outcome"] == "correct_abstain"


def test_shortlist_miss_detected():
    c = _case("c1", "z")          # gold not among a/b
    s = ed.score_case(c)
    assert s["outcome"] == "shortlist_miss"


# --- evaluate -----------------------------------------------------------------

def test_evaluate_counts():
    cases = [_case("c1", "a"),                       # correct
             _case("c2", "a", choice="b"),           # wrong
             _case("c3", "a", choice="__none__"),    # abstained
             _case("c4", "__none__", choice="__none__"),  # correct_abstain
             _case("c5", "z")]                       # shortlist_miss
    rep = ed.evaluate(cases, name="B1")
    assert rep["total"] == 5
    assert rep["correct"] == 1
    assert rep["wrong"] == 1
    assert rep["abstained"] == 1
    assert rep["correct_abstain"] == 1
    assert rep["shortlist_miss"] == 1
    # accuracy counts decided cases only (correct+wrong)
    assert rep["decided"] == 2
    assert rep["accuracy"] == pytest.approx(0.5)
    assert rep["coverage"] == pytest.approx(2 / 4)
    # abstention accuracy: correct_abstain / all-abstain-gold cases
    assert "wilson_accuracy_low" in rep


def test_evaluate_deterministic_bytes():
    cases = [_case("c1", "a"), _case("c2", "a", choice="b")]
    a = ed.evaluate(cases, name="x")
    b = ed.evaluate(list(cases), name="x")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_evaluate_empty():
    rep = ed.evaluate([], name="empty")
    assert rep["total"] == 0 and rep["accuracy"] is None


# --- compare -----------------------------------------------------------------

def test_compare_reports():
    cases = [_case("c1", "a"), _case("c2", "a", choice="b")]
    b0 = ed.evaluate(cases, name="B0")
    better = [_case("c1", "a"), _case("c2", "a")]
    b1 = ed.evaluate(better, name="B1")
    cmp = ed.compare(b0, b1)
    assert cmp["accuracy_delta"] == pytest.approx(0.5)
    assert cmp["names"] == ["B0", "B1"]


# --- manifest CLI (frozen capture only) ---------------------------------------

def test_evaluate_manifest_cli(tmp_path, capsys):
    manifest = tmp_path / "frozen.json"
    manifest.write_text(json.dumps({
        "version": 1, "frozen": True,
        "cases": [_case("c1", "a"), _case("c2", "a", choice="b")],
    }), encoding="utf-8")
    out = tmp_path / "result.json"
    rc = ed.main(["--manifest", str(manifest), "--mode", "evaluate",
                  "--out", str(out), "--name", "B1"])
    assert rc == 0
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["total"] == 2 and rep["correct"] == 1
    # pure JSON on stdout
    json.loads(capsys.readouterr().out)


def test_manifest_not_frozen_rejected(tmp_path):
    manifest = tmp_path / "live.json"
    manifest.write_text(json.dumps({"version": 1, "cases": []}))
    rc = ed.main(["--manifest", str(manifest), "--mode", "evaluate",
                  "--out", str(tmp_path / "r.json")])
    assert rc != 0
