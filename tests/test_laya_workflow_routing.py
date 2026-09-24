"""L06 — routing/triage assist without a competing router.

Explicit triggers always win; the model only sees requests with NO
explicit skill. Two stages: family (closed labels) -> <=8 real catalog
entries -> suggested name. The decision path performs zero side
effects.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import workflow_routing as wr   # noqa: E402

CLI = ROOT / "extensions" / "laya-tools" / "laya_cli.py"


def _catalog():
    return [
        {"id": "ask-bundle", "purpose": "route vague requests"},
        {"id": "debugging", "purpose": "diagnose and fix bugs in code"},
        {"id": "tdd", "purpose": "test driven code workflow"},
        {"id": "operate-spline", "purpose": "spline 3d design scenes"},
        {"id": "data-analyst", "purpose": "sql database query charts"},
        {"id": "research", "purpose": "investigate primary sources"},
        {"id": "jira", "purpose": "jira issue triage operations"},
        {"id": "intake", "purpose": "triage sizing issues"},
        {"id": "handoff", "purpose": "compact conversation context"},
    ]


def _reply(req, choice):
    return {"ok": True, "version": 1,
            "request_id": req["request_id"],
            "outcome": "suggestion" if choice != "__none__" else "abstain",
            "candidate_id": choice, "context": {},
            "raw_confidence": 0.8, "raw_top_probability": 0.8,
            "calibrated_probability": None, "calibration_id": None,
            "mode": req["mode"], "adoptable": False,
            "reason": "uncalibrated", "model_identity": "fake",
            "profile_version": req["profile"]}


class FakeClient:
    def __init__(self, family="development", skill="tdd"):
        self.calls = []
        self._family, self._skill = family, skill

    def recommend(self, request):
        self.calls.append(request)
        if request["profile"] == "skill-family-v1":
            return _reply(request, self._family)
        return _reply(request, self._skill)


# --- explicit triggers ----------------------------------------------------------

def test_explicit_skill_bypasses_model():
    assert wr.requires_model(explicit_skill="jira",
                             candidates=["jira", "intake"]) is False


def test_no_explicit_skill_may_use_model():
    assert wr.requires_model(explicit_skill=None) is True
    assert wr.requires_model(explicit_skill="") is True
    assert wr.requires_model(explicit_skill="   ") is True


# --- catalog + families ---------------------------------------------------------

def test_catalog_from_manifest_shape():
    cat = wr.load_catalog({"skills": [
        {"name": "a", "purpose": "p"}, {"name": "b"}]})
    assert [c["id"] for c in cat] == ["a", "b"]


def test_family_shortlist_capped_and_ordered():
    cat = [{"id": f"dev-{i}", "purpose": "code fix"} for i in range(12)]
    s = wr.shortlist("development", cat)
    assert len(s) == 8
    assert s[0]["id"] == "dev-0"


def test_assign_family_never_guesses():
    assert wr.assign_family({"id": "x", "purpose": "zzz qqq"}) \
        == "assistance"


# --- two-stage recommend ---------------------------------------------------------

def test_two_stage_returns_catalog_name():
    c = FakeClient("development", "tdd")
    out = wr.recommend(c, _catalog(), "write tests for the parser")
    assert out["outcome"] == "suggestion"
    assert out["candidate_id"] == "tdd"
    assert out["family"] == "development"
    assert [r["profile"] for r in c.calls] == \
        ["skill-family-v1", "skill-pick-v1"]
    # stage-2 request carried only real catalog entries, <=8
    assert len(c.calls[1]["candidates"]) <= 8
    ids = {e["id"] for e in _catalog()}
    assert all(cd["id"] in ids for cd in c.calls[1]["candidates"])


def test_family_abstain_short_circuits():
    c = FakeClient(family="__none__")
    out = wr.recommend(c, _catalog(), "???")
    assert out["outcome"] == "abstain"
    assert len(c.calls) == 1


def test_skill_outside_catalog_abstains():
    out = wr.recommend(FakeClient("development", "nonexistent"),
                       _catalog(), "x")
    assert out["outcome"] == "abstain"


def test_decision_path_has_no_side_effects():
    import inspect
    src = inspect.getsource(wr)
    for banned in ("mcp_call_tool", "gh ", "subprocess", "Popen",
                   "issue edit", "worklog"):
        assert banned not in src


# --- CLI recommend entrypoint ----------------------------------------------------

def test_cli_recommend_off_abstains_without_spawn(tmp_path):
    """mode off (missing config) -> abstain JSON, exits fast, no worker."""
    r = subprocess.run(
        [sys.executable, str(CLI), "recommend",
         "--profile", "skill-family-v1", "--goal", "fix a bug",
         "--config", str(tmp_path / "absent.json")],
        capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["outcome"] == "abstain"
    assert out["reason"] == "feature_off"
