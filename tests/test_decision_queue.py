import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "decision-queue.py"


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


def test_hook_records_decision_stop(tmp_path):
    run([], {"last_assistant_message": "Blocked: I need your approval?"},
        proj=tmp_path)
    q = tmp_path / ".devin" / "decisions.jsonl"
    assert q.exists()
    rec = json.loads(q.read_text(encoding="utf-8").strip())
    assert rec["resolved"] is False and rec["source"] == "stop"


def test_pending_and_resolve_roundtrip(tmp_path):
    q = tmp_path / ".devin" / "decisions.jsonl"
    q.parent.mkdir(parents=True)
    q.write_text(
        json.dumps({"id": "d1", "ts": 1, "excerpt": "x", "resolved": False})
        + "\n", encoding="utf-8")
    r = run(["--pending"], proj=tmp_path)
    assert json.loads(r.stdout)["pending"] == 1
    r = run(["--resolve", "d1"], proj=tmp_path)
    assert json.loads(r.stdout)["ok"] is True
    r = run(["--pending"], proj=tmp_path)
    assert json.loads(r.stdout)["pending"] == 0


def test_clean_message_records_nothing(tmp_path):
    run([], {"last_assistant_message": "All done, tests green."},
        proj=tmp_path)
    assert not (tmp_path / ".devin" / "decisions.jsonl").exists()
