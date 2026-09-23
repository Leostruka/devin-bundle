"""L02 — isolated offline worker + stdio client.

serve() speaks versioned JSON-lines over stdio: one request envelope in,
one recommendation out, diagnostics strictly on stderr. The engine is
built ONCE per worker and reused. CI uses a fake engine — no torch, no
weights, no network.
"""
import io
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

LAYA_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "laya-tools"
sys.path.insert(0, str(LAYA_DIR))

import decision_contract as dc   # noqa: E402
import laya_worker               # noqa: E402
from decision_client import DecisionClient  # noqa: E402


REQ = {
    "version": 1,
    "request_id": "d-1",
    "profile": "ui-target-v1",
    "mode": "shadow",
    "context": {"env_id": "vm-a", "instance_id": "i-3",
                "observation_id": "obs-1"},
    "state": {"goal": "open audio settings"},
    "candidates": [
        {"id": "as", "role": "Button", "name": "Áudio", "scope": "Cfg"},
        {"id": "ad", "role": "Button", "name": "Vídeo", "scope": "Cfg"},
    ],
    "deadline_ms": 5000,
}


def env(request=REQ, rid=None):
    return {"version": 1,
            "request_id": rid or request["request_id"],
            "request": request}


def run_worker(engine, envelopes, config=None):
    """Feed envelopes as JSON-lines through serve(); parse replies."""
    reader = io.StringIO("".join(json.dumps(e) + "\n" for e in envelopes))
    writer = io.StringIO()
    cfg = config if config is not None else {"mode": "shadow"}
    laya_worker.serve(reader, writer, engine, cfg)
    out = []
    for line in writer.getvalue().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


class FakeEngine:
    load_count = 0

    def __init__(self, answer=None):
        type(self).load_count += 1
        self.predict_count = 0
        self.identity = "fake-snapshot"
        self.device = "cpu"
        self._answer = answer or {
            "answers": {"target": {"choice": "as", "confidence": 0.9,
                                   "distribution": {"as": 0.9,
                                                    "ad": 0.1}}},
            "routing": {"model": "english", "reason": "latin"}}

    def predict(self, state, questions):
        self.predict_count += 1
        return self._answer


# --- serve loop --------------------------------------------------------------

def test_worker_reuses_engine():
    FakeEngine.load_count = 0
    e = FakeEngine()
    reqs = [dict(REQ, request_id=f"d-{i}") for i in range(2)]
    replies = run_worker(e, [env(r) for r in reqs])
    assert FakeEngine.load_count == 1
    assert e.predict_count == 2
    assert len(replies) == 2
    assert all(r["outcome"] == "suggestion" and
               r["candidate_id"] == "as" for r in replies)


def test_request_id_echoed():
    replies = run_worker(FakeEngine(), [env(REQ, rid="d-42")])
    assert replies[0]["request_id"] == "d-42"
    assert replies[0]["context"] == REQ["context"]


def test_malformed_json_line_abstains():
    writer = io.StringIO()
    laya_worker.serve(io.StringIO("{not json\n"), writer,
                      FakeEngine(), {"mode": "shadow"})
    [r] = [json.loads(l) for l in writer.getvalue().splitlines()]
    assert r["outcome"] == "abstain" and r["adoptable"] is False


def test_invalid_request_abstains():
    bad = dict(REQ, candidates=REQ["candidates"] +
               [dict(REQ["candidates"][0])])
    replies = run_worker(FakeEngine(), [env(bad)])
    assert replies[0]["outcome"] == "abstain"
    assert "invalid_request" in replies[0]["reason"]


def test_engine_stdout_noise_stays_off_protocol(capsys):
    class Noisy(FakeEngine):
        def predict(self, state, questions):
            print("WARNING: engine noise")   # would corrupt stdio proto
            return super().predict(state, questions)
    replies = run_worker(Noisy(), [env(REQ)])
    assert replies[0]["candidate_id"] == "as"
    assert "engine noise" in capsys.readouterr().err


def test_deadline_exceeded_abstains():
    class Slow(FakeEngine):
        def predict(self, s, q):
            time.sleep(0.05)
            return super().predict(s, q)
    req = dict(REQ, deadline_ms=1)
    replies = run_worker(Slow(), [env(req)])
    assert replies[0]["outcome"] == "abstain"
    assert replies[0]["reason"] == "deadline_exceeded"


def test_unknown_label_abstains():
    e = FakeEngine({"answers": {"target": {"choice": "invented",
                                           "confidence": 0.99}}})
    replies = run_worker(e, [env(REQ)])
    assert replies[0]["outcome"] == "abstain"
    assert replies[0]["reason"] == "unknown_label"


def test_none_choice_is_abstain():
    e = FakeEngine({"answers": {"target": {"choice": "__none__",
                                           "confidence": 0.8}}})
    replies = run_worker(e, [env(REQ)])
    assert replies[0]["outcome"] == "abstain"


def test_nan_confidence_abstains():
    e = FakeEngine({"answers": {"target": {"choice": "as",
                                           "confidence": float("nan")}}})
    replies = run_worker(e, [env(REQ)])
    assert replies[0]["outcome"] == "abstain"


def test_engine_exception_abstains():
    class Boom(FakeEngine):
        def predict(self, s, q):
            raise MemoryError("oom")
    replies = run_worker(Boom(), [env(REQ)])
    assert replies[0]["outcome"] == "abstain"
    assert replies[0]["reason"].startswith("engine_error")


def test_feature_off_never_predicts():
    e = FakeEngine()
    replies = run_worker(e, [env(REQ)], config={"mode": "off"})
    assert replies[0]["outcome"] == "abstain"
    assert replies[0]["reason"] == "feature_off"
    assert e.predict_count == 0


def test_disable_mid_session():
    cfg = {"mode": "shadow"}

    class Flip(FakeEngine):
        def predict(self, s, q):
            cfg["mode"] = "off"
            return super().predict(s, q)
    replies = run_worker(Flip(), [env(REQ), env(dict(REQ, request_id="d-2"))],
                         config=cfg)
    assert replies[0]["outcome"] == "suggestion"
    assert replies[1]["reason"] == "feature_off"


def test_eof_exits_cleanly():
    writer = io.StringIO()
    laya_worker.serve(io.StringIO(""), writer, FakeEngine(),
                      {"mode": "shadow"})
    assert writer.getvalue() == ""


def test_response_is_valid_recommendation():
    replies = run_worker(FakeEngine(), [env(REQ)])
    assert dc.validate_recommendation(replies[0], REQ) == []


# --- load_engine ---------------------------------------------------------------

def test_load_engine_missing_model_path(tmp_path):
    with pytest.raises(RuntimeError, match="model_path_missing"):
        laya_worker.load_engine(
            {"typed-decisions": {"path": str(tmp_path / "nope")}},
            "cpu")


def test_load_engine_sets_offline_env(tmp_path, monkeypatch):
    for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setitem(sys.modules, "laya", None)  # force ImportError
    with pytest.raises(RuntimeError, match="laya_import_failed"):
        laya_worker.load_engine({}, "cpu")
    import os
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"


def test_load_engine_digest_mismatch(tmp_path):
    f = tmp_path / "ckpt.bin"
    f.write_bytes(b"weights")
    with pytest.raises(RuntimeError, match="model_digest_mismatch"):
        laya_worker.load_engine(
            {"m": {"path": str(f), "sha256": "0" * 64}}, "cpu")


# --- DecisionClient -------------------------------------------------------------

ECHO_WORKER = r'''
import json, sys
for line in sys.stdin:
    env = json.loads(line)
    req = env["request"]
    print(json.dumps({"ok": True, "version": 1,
        "request_id": env["request_id"], "outcome": "suggestion",
        "candidate_id": req["candidates"][0]["id"],
        "context": req.get("context") or {},
        "raw_confidence": 0.5, "raw_top_probability": 0.5,
        "calibrated_probability": None, "calibration_id": None,
        "mode": "shadow", "adoptable": False, "reason": "uncalibrated",
        "model_identity": "echo", "profile_version": req["profile"]}),
        flush=True)
'''


def _client(tmp_path, body=ECHO_WORKER, timeout=10.0):
    script = tmp_path / "fake_worker.py"
    script.write_text(body, encoding="utf-8")
    return DecisionClient([sys.executable, "-u", str(script)],
                          timeout_s=timeout)


def test_client_roundtrip(tmp_path):
    c = _client(tmp_path)
    try:
        r = c.recommend(REQ)
        assert r["outcome"] == "suggestion"
        assert r["candidate_id"] == "as"
        assert r["request_id"] == "d-1"
    finally:
        c.close()


def test_client_timeout_abstains(tmp_path):
    c = _client(tmp_path, body="import time; time.sleep(30)",
                timeout=0.5)
    try:
        r = c.recommend(REQ)
        assert r["outcome"] == "abstain"
        assert r["reason"] == "worker_timeout"
    finally:
        c.close()


def test_client_rejects_foreign_reply(tmp_path):
    body = ECHO_WORKER.replace('env["request_id"]', '"d-FORGED"')
    c = _client(tmp_path, body=body)
    try:
        r = c.recommend(REQ)
        assert r["outcome"] == "abstain"
        assert r["reason"] == "worker_protocol_error"
    finally:
        c.close()


def test_client_close_terminates_own_child(tmp_path):
    c = _client(tmp_path)
    c.recommend(REQ)
    proc = c._proc
    c.close()
    assert proc.poll() is not None
