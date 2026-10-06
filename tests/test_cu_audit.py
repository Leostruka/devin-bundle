"""cu_audit: append-only JSONL trail for dispatched actions."""
import json, os, sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

ca = cu_load.load("cu_actions")
au = cu_load.load("cu_audit")


def test_result_writes_audit(monkeypatch, tmp_path):
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setattr(sys, "argv", ["mouse.py", "click", "500", "300"])
    r = ca.result("dispatched", "physical", timings_ms={"total": 3})
    lines = p.read_text().strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["status"] == "dispatched" and rec["tool"] == "mouse.py"
    assert rec["backend"] == "physical" and "500" not in lines[0]


def test_audit_disabled(monkeypatch, tmp_path):
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setenv("CU_AUDIT", "off")
    ca.result("dispatched", "physical")
    assert not p.exists()


def test_rotation_keeps_tail(monkeypatch, tmp_path):
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setenv("CU_AUDIT_MAX_BYTES", "1024")
    monkeypatch.setattr(sys, "argv", ["type_text.py", "x"])
    for i in range(60):
        ca.result("dispatched", "physical", n=i)
    lines = p.read_text().strip().splitlines()
    assert len(lines) <= 1000
    assert json.loads(lines[-1])["extra"]["n"] == 59


def test_audit_failure_never_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(au, "audit_path",
                        lambda: str(tmp_path / "x\x00bad.jsonl"))
    r = ca.result("dispatched", "physical")  # must not raise
    assert r["status"] == "dispatched"
