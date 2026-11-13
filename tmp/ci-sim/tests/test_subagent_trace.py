import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "subagent-trace.py"


def run(args, payload=None, proj=None):
    env = dict(os.environ)
    if proj is not None:
        env["DEVIN_PROJECT_DIR"] = str(proj)
    r = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env)
    return r


def trace_file(proj):
    return proj / ".devin" / "subagent-trace.jsonl"


def test_record_appends_record(tmp_path):
    r = run(["record"], {"agent": "implementer", "title": "fix tests",
                         "profile": "swe-2-medium"}, proj=tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode == 0 and out["ok"] is True
    rec = json.loads(trace_file(tmp_path).read_text(
        encoding="utf-8").strip())
    assert rec["agent"] == "implementer" and rec["status"] == "running"
    assert rec["id"] == out["id"] and rec["ts"]


def test_record_updates_existing_id(tmp_path):
    run(["record"], {"id": "s1", "agent": "implementer"},
        proj=tmp_path)
    r = run(["record"], {"id": "s1", "status": "done",
                         "notes": "3 files changed"}, proj=tmp_path)
    assert json.loads(r.stdout)["ok"] is True
    lines = trace_file(tmp_path).read_text(encoding="utf-8").strip()
    recs = [json.loads(x) for x in lines.splitlines()]
    assert len(recs) == 1
    assert recs[0]["status"] == "done" and recs[0]["agent"] == "implementer"


def test_record_args_and_bad_status(tmp_path):
    r = run(["record", "--id", "s9", "--agent", "reviewer",
             "--status", "bogus"], proj=tmp_path)
    assert r.returncode == 2 and json.loads(r.stdout)["ok"] is False
    r = run(["record", "--id", "s9", "--agent", "reviewer",
             "--status", "running"], proj=tmp_path)
    assert r.returncode == 0
    rec = json.loads(trace_file(tmp_path).read_text(
        encoding="utf-8").strip())
    assert rec["agent"] == "reviewer"


def test_pending_lists_running_only(tmp_path):
    run(["record"], {"id": "a", "status": "running"}, proj=tmp_path)
    run(["record"], {"id": "b", "status": "done"}, proj=tmp_path)
    r = run(["--pending"], proj=tmp_path)
    out = json.loads(r.stdout)
    assert out["pending"] == 1 and out["records"][0]["id"] == "a"
    r = run(["--list"], proj=tmp_path)
    assert len(json.loads(r.stdout)["records"]) == 2


def test_abort_flag_roundtrip(tmp_path):
    run(["record"], {"id": "s1", "status": "running"}, proj=tmp_path)
    r = run(["check-abort", "s1"], proj=tmp_path)
    assert r.returncode == 1 and json.loads(r.stdout)["abort"] is False
    r = run(["--abort", "s1"], proj=tmp_path)
    assert json.loads(r.stdout)["ok"] is True
    assert (tmp_path / ".devin" / "subagent-abort" / "s1").exists()
    r = run(["check-abort", "s1"], proj=tmp_path)
    assert r.returncode == 0 and json.loads(r.stdout)["abort"] is True
    run(["--clear-abort", "s1"], proj=tmp_path)
    r = run(["check-abort", "s1"], proj=tmp_path)
    assert r.returncode == 1


def test_clear_abort_missing_is_ok(tmp_path):
    r = run(["--clear-abort", "nope"], proj=tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode == 0 and out["ok"] is True
    assert out["removed"] is False
