"""layad + laya_client + filebool + new profiles.

The daemon is exercised end-to-end over a real localhost socket with a
fake engine — no torch, no weights, no network beyond loopback.
"""
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

LAYA_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA_DIR))

import decision_contract as dc   # noqa: E402
import layad                      # noqa: E402
import laya_client as lc          # noqa: E402
import filebool as fb             # noqa: E402


class FakeEngine:
    """First-criteria-label answers; confidence fixed. The contract
    does the rest."""
    identity = "fake-engine"
    device = "cpu"

    def predict(self, state, questions, **kw):
        key = next(iter(questions))
        label = next(k for k in questions[key]["criteria"]
                     if k != dc.NONE_ID)
        return {"answers": {key: {"choice": label,
                                  "confidence": 0.9,
                                  "distribution": {label: 0.9}}},
                "routing": {"model": "fake"}}


def _req(profile="filebool-v1", cands=None, mode="shadow", rid="r-1"):
    return {"version": 1, "request_id": rid, "profile": profile,
            "mode": mode, "context": {"env_id": "test"},
            "state": {"goal": "contains auth data",
                      "snippets": "file: a.py\n\nx = 1"},
            "candidates": cands or [{"id": "yes"}, {"id": "no"}],
            "deadline_ms": 2000}


@pytest.fixture
def daemon(tmp_path):
    cfg = {"version": 1, "mode": "shadow",
           "profiles": ["filebool-v1", "cmd-risk-v1",
                        "compact-gate-v1", "compact-boundary-v1"],
           "models": {}, "deadline_ms": 2000}
    t = threading.Thread(
        target=layad.serve_socket,
        args=(FakeEngine(), cfg),
        kwargs={"laya_dir": str(tmp_path), "idle_ttl_s": 3600},
        daemon=True)
    t.start()
    info_path = tmp_path / "daemon.json"
    deadline = time.time() + 10
    while not info_path.is_file() and time.time() < deadline:
        time.sleep(0.05)
    info = json.loads(info_path.read_text(encoding="utf-8"))
    yield info


# --- profiles --------------------------------------------------------------

def test_new_profiles_frozen_criteria():
    for prof, key, ids in (
            ("cmd-risk-v1", "risk",
             {"benign", "mutating", "irreversible",
              "egress_or_secret", "ambiguous"}),
            ("compact-gate-v1", "action",
             {"continue", "prune", "fold", "handoff", "clear"}),
            ("compact-boundary-v1", "boundary",
             {"mid_task", "stage_resolved", "task_shifted"}),
            ("filebool-v1", "verdict", {"yes", "no"})):
        q = dc.build_questions(prof, [{"id": i} for i in ids])
        crit = q[key]["criteria"]
        assert set(crit) - {dc.NONE_ID} == ids
        assert crit[dc.NONE_ID]
        # canonical order: __none__ appended last
        assert list(crit)[-1] == dc.NONE_ID


def test_dict_label_descriptions_preserved():
    q = dc.build_questions("filebool-v1",
                           [{"id": "yes"}, {"id": "no"}])
    assert "satisfies" in q["verdict"]["criteria"]["yes"]


def test_profile_requests_validate():
    for prof, cands in (
            ("cmd-risk-v1",
             [{"id": i} for i in
              ("benign", "mutating", "irreversible",
               "egress_or_secret", "ambiguous")]),
            ("compact-gate-v1",
             [{"id": i} for i in
              ("continue", "prune", "fold", "handoff", "clear")])):
        r = _req(profile=prof, cands=cands)
        assert dc.validate_request(r) == []


# --- daemon + client --------------------------------------------------------

def test_recommend_over_socket(daemon):
    rec = lc.recommend(_req(), daemon=daemon)
    assert rec["outcome"] == "suggestion"
    assert rec["candidate_id"] == "yes"
    assert rec["request_id"] == "r-1"


def test_wrong_token_abstains(daemon):
    bad = dict(daemon, auth_token="bogus")
    rec = lc.recommend(_req(), daemon=bad)
    assert rec["outcome"] == "abstain"
    assert "unauthorized" in rec["reason"]


def test_no_daemon_abstains():
    rec = lc.recommend(_req(), daemon=None)
    assert rec["outcome"] == "abstain"
    assert rec["reason"] == "daemon_unavailable"


def test_dead_port_abstains():
    dead = {"port": 1, "auth_token": "x", "pid": -1}
    rec = lc.recommend(_req(), daemon=dead, timeout_s=1.0)
    assert rec["outcome"] == "abstain"


def test_batch_session_order(daemon):
    reqs = [_req(rid=f"b-{i}") for i in range(5)]
    out = lc.batch(reqs, daemon=daemon)
    assert [r["request_id"] for r in out] == [f"b-{i}" for i in range(5)]
    assert all(r["candidate_id"] == "yes" for r in out)


def test_invalid_request_no_socket(daemon):
    bad = _req()
    bad.pop("profile")
    rec = lc.recommend(bad, daemon=daemon)
    assert rec["outcome"] == "abstain"
    assert rec["reason"].startswith("invalid_request")


# --- filebool ---------------------------------------------------------------

def test_filebool_off_mode_abstains(tmp_path):
    prof = tmp_path / "laya" / "profile.json"
    prof.parent.mkdir(parents=True)
    prof.write_text(json.dumps({"mode": "off"}), encoding="utf-8")
    out = fb.ask_laya_filebool([__file__], "has tests",
                               config=str(prof))
    assert out[__file__]["answer"] == "abstain"
    assert out[__file__]["reason"] == "feature_off"


def test_filebool_max_files_guard(tmp_path):
    prof = tmp_path / "laya" / "profile.json"
    prof.parent.mkdir(parents=True)
    prof.write_text(json.dumps({"mode": "off"}), encoding="utf-8")
    with pytest.raises(ValueError, match="too_many_files"):
        fb.ask_laya_filebool(["a"] * 3, "q", max_files=2,
                             config=str(prof))


def test_filebool_glob_and_exclude(tmp_path):
    (tmp_path / "a.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "b.py").write_text("y = 2", encoding="utf-8")
    (tmp_path / "c.txt").write_text("z", encoding="utf-8")
    prof = tmp_path / "laya" / "profile.json"
    prof.parent.mkdir(parents=True)
    prof.write_text(json.dumps({"mode": "off"}), encoding="utf-8")
    out = fb.ask_laya_glob("**/*.py", "q", root=str(tmp_path),
                           exclude=("b.py",), config=str(prof))
    assert len(out) == 1
    assert "a.py" in next(iter(out))


def test_filebool_binary_abstains(tmp_path, monkeypatch):
    blob = tmp_path / "blob.bin"
    blob.write_bytes(b"\x00\x01\x02\x00")
    prof = tmp_path / "laya" / "profile.json"
    prof.parent.mkdir(parents=True)
    prof.write_text(json.dumps({"mode": "shadow",
                                "profiles": ["filebool-v1"],
                                "models": {}}), encoding="utf-8")
    monkeypatch.setattr(lc, "ensure_daemon", lambda *a, **k:
                        {"port": 1, "auth_token": "x", "pid": -1})
    out = fb.ask_laya_filebool([str(blob)], "q", config=str(prof))
    assert out[str(blob)]["answer"] == "abstain"
    assert out[str(blob)]["reason"] == "unreadable"


def test_filebool_maps_replies(tmp_path, monkeypatch):
    f = tmp_path / "a.py"
    f.write_text("import os", encoding="utf-8")
    prof = tmp_path / "laya" / "profile.json"
    prof.parent.mkdir(parents=True)
    prof.write_text(json.dumps({"mode": "shadow",
                                "profiles": ["filebool-v1"],
                                "models": {}}), encoding="utf-8")
    monkeypatch.setattr(lc, "ensure_daemon", lambda *a, **k:
                        {"port": 1, "auth_token": "x", "pid": -1})

    def fake_batch(reqs, daemon=None, timeout_s=10.0):
        rec = dc.make_abstention(reqs[0]["request_id"], "ok")
        rec.update({"outcome": "suggestion", "candidate_id": "no",
                    "mode": "shadow", "profile_version": "filebool-v1",
                    "model_identity": "fake", "reason": "uncalibrated",
                    "context": {}, "adoptable": False})
        return [rec]
    monkeypatch.setattr(lc, "batch", fake_batch)
    out = fb.ask_laya_filebool([str(f)], "q", config=str(prof))
    assert out[str(f)]["answer"] == "no"
