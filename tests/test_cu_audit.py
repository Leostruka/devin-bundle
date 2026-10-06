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


def test_rotation_actually_truncates(monkeypatch, tmp_path):
    """Supplemental: actually exercise _rotate. `_MAX_BYTES` binds at
    import time, so monkeypatch the module constant directly; >1000
    records force a real truncation the cap-env test cannot reach."""
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setattr(au, "_MAX_BYTES", 4096)
    monkeypatch.setattr(sys, "argv", ["type_text.py", "x"])
    for i in range(1100):
        ca.result("dispatched", "physical", n=i)
    data = p.read_bytes()
    lines = data.decode().strip().splitlines()
    # rotate runs before append: at most 1000 kept + 1 new line
    assert len(lines) <= 1001
    assert len(lines) < 1100  # proves lines were dropped
    assert json.loads(lines[-1])["extra"]["n"] == 1099
    assert json.loads(lines[0])["extra"]["n"] > 0  # head was truncated
    line_len = len(lines[-1].encode()) + 2  # +\r\n
    assert len(data) < 1100 * line_len  # below unrotated size


def test_positional_text_never_audited(monkeypatch, tmp_path):
    """type_text.py takes its literal text positionally; argv[1] must
    never reach the audit trail (typed-value exclusion rule)."""
    p = tmp_path / "a.jsonl"
    monkeypatch.setenv("CU_AUDIT_PATH", str(p))
    monkeypatch.setattr(sys, "argv", ["type_text.py", "s3cret-passphrase"])
    ca.result("dispatched", "physical")
    line = p.read_text().strip()
    assert "s3cret" not in line
    rec = json.loads(line)
    assert rec.get("cmd") is None
    assert rec["tool"] == "type_text.py"


def test_audit_failure_never_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(au, "audit_path",
                        lambda: str(tmp_path / "x\x00bad.jsonl"))
    r = ca.result("dispatched", "physical")  # must not raise
    assert r["status"] == "dispatched"
