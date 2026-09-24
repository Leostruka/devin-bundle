"""L05 — Laya recommends an existing Spline tool; never calls it.

Two-stage narrowing: domain (closed labels) -> shortlist of REAL
manifest tools -> suggestion referencing only a tool present in that
exact manifest (pinned by manifest_hash). Read-only: no launch, no
kill, no export, no generated code into 3d_run_code.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "spline-operator"))
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))

import decision as sd           # noqa: E402
import decision_contract as dc  # noqa: E402


def _manifest():
    return {"tools": [
        {"name": "3d_add_primitive", "description": "add a 3D shape",
         "inputSchema": {"type": "object"}},
        {"name": "3d_run_code", "description": "run js in scene",
         "inputSchema": {"type": "object"}},
        {"name": "2d_draw_path", "description": "draw vector path"},
        {"name": "inspect_scene", "description": "list objects"},
        {"name": "export_png", "description": "render to png"},
    ], "editor": {"id": "ed-1"}, "scene": {"id": "sc-9"}}


def _reply(req, choice):
    return {"ok": True, "version": 1,
            "request_id": req["request_id"],
            "outcome": "suggestion" if choice != "__none__" else "abstain",
            "candidate_id": choice, "context": req.get("context") or {},
            "raw_confidence": 0.8, "raw_top_probability": 0.8,
            "calibrated_probability": None, "calibration_id": None,
            "mode": req["mode"], "adoptable": False,
            "reason": "uncalibrated", "model_identity": "fake",
            "profile_version": req["profile"]}


class FakeClient:
    """Replies per-request by profile: domain first, tool second."""
    def __init__(self, domain="scene_3d", tool="3d_add_primitive"):
        self.calls = []
        self._domain = domain
        self._tool = tool

    def recommend(self, request):
        self.calls.append(request)
        if request["profile"] == "spline-domain-v1":
            return _reply(request, self._domain)
        return _reply(request, self._tool)


# --- manifest digest + matching ----------------------------------------------

def test_manifest_digest_stable_and_sensitive():
    d1 = sd.manifest_digest(_manifest())
    assert d1 == sd.manifest_digest(_manifest())
    m2 = _manifest()
    m2["tools"].pop()
    assert sd.manifest_digest(m2) != d1


def test_foreign_manifest_suggestion_is_not_usable():
    assert sd.manifest_matches({"manifest_hash": "old"}, "current") \
        is False


def test_manifest_matches_requires_both_sides():
    cur = sd.manifest_digest(_manifest())
    assert sd.manifest_matches({"manifest_hash": cur}, cur) is True
    assert sd.manifest_matches({"manifest_hash": cur}, "") is False
    assert sd.manifest_matches({}, cur) is False


# --- shortlist -----------------------------------------------------------------

def test_domain_shortlist_filters_real_tools():
    m = _manifest()
    s3 = sd.shortlist("scene_3d", m)
    assert "3d_add_primitive" in s3 and "3d_run_code" in s3
    assert "export_png" not in s3
    assert set(s3) <= {t["name"] for t in m["tools"]}


def test_shortlist_unknown_domain_empty():
    assert sd.shortlist("quantum", _manifest()) == []


def test_shortlist_preserves_manifest_order():
    m = _manifest()
    assert sd.shortlist("export", m) == ["export_png"]


# --- recommend flow --------------------------------------------------------------

def test_recommend_two_stage_returns_existing_tool():
    client = FakeClient(domain="scene_3d", tool="3d_add_primitive")
    out = sd.recommend(client, _manifest(), "add a cube")
    assert out["outcome"] == "suggestion"
    assert out["candidate_id"] == "3d_add_primitive"
    assert out["manifest_hash"] == sd.manifest_digest(_manifest())
    assert [c["profile"] for c in client.calls] == \
        ["spline-domain-v1", "spline-tool-v1"]


def test_recommend_never_carries_generated_code():
    client = FakeClient(tool="3d_run_code")
    out = sd.recommend(client, _manifest(), "make it spin")
    blob = json.dumps(out)
    assert "code" not in out
    assert "args" not in out            # no fabricated call args
    assert "def " not in blob and "function" not in blob


def test_domain_abstain_short_circuits():
    client = FakeClient(domain="__none__")
    out = sd.recommend(client, _manifest(), "???")
    assert out["outcome"] == "abstain"
    assert len(client.calls) == 1       # tool stage never ran


def test_tool_outside_manifest_is_abstain():
    client = FakeClient(tool="hacked_tool")
    out = sd.recommend(client, _manifest(), "x")
    assert out["outcome"] == "abstain"


def test_empty_shortlist_abstains():
    m = {"tools": [{"name": "export_png", "description": "x"}],
         "editor": {}, "scene": {}}
    client = FakeClient(domain="scene_3d")
    out = sd.recommend(client, m, "add cube")
    assert out["outcome"] == "abstain"
    assert len(client.calls) == 1


def test_no_launch_no_kill_no_export_permission():
    """The module exposes no lifecycle/execution verbs."""
    for banned in ("launch", "kill", "export", "call", "run"):
        assert not hasattr(sd, f"cmd_{banned}")
    src = Path(sd.__file__).read_text(encoding="utf-8")
    assert "cmd_launch" not in src and "cmd_kill" not in src
    assert "_agent_session" not in src or "fetch" in src
