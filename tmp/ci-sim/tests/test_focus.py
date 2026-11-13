"""focus.py contract tests (issue #419): start/stop/report over a
gitignored JSONL ledger, paired sessions, per-day/per-issue rollup."""
import importlib.util
import io
import json
import os
import sys
import time
from contextlib import redirect_stdout

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _load():
    spec = importlib.util.spec_from_file_location(
        "focus", os.path.join(SCRIPTS, "focus.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


f = _load()


@pytest.fixture
def proj(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVIN_PROJECT_DIR", str(tmp_path))
    return tmp_path


def _run(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = f.main(argv)
    return rc, out.getvalue()


def test_start_stop_report(proj):
    rc, out = _run(["start", "--issue", "ISSUE_02", "--effort", "dev-org"])
    assert rc == 0 and "focus start" in out
    rc, out = _run(["status"])
    assert "open since" in out and "ISSUE_02" in out
    rc, out = _run(["stop", "--note", "done chunk"])
    assert rc == 0 and "focus stop" in out
    rc, out = _run(["status"])
    assert "no open" in out
    rc, out = _run(["report"])
    assert "per day:" in out and "per issue:" in out
    assert "ISSUE_02" in out


def test_double_start_refused(proj):
    assert _run(["start"])[0] == 0
    rc, _ = _run(["start"])
    assert rc == 1
    assert _run(["stop"])[0] == 0


def test_stop_without_start_fails(proj):
    rc, _ = _run(["stop"])
    assert rc == 1


def test_report_json_and_day_filter(proj):
    _run(["start", "--issue", "A"])
    _run(["stop"])
    today = time.strftime("%Y-%m-%d")
    rc, out = _run(["report", "--json"])
    data = json.loads(out)
    assert data["open"] is None
    assert data["sessions"][0]["issue"] == "A"
    assert data["sessions"][0]["day"] == today
    rc, out = _run(["report", "--day", "1999-01-01"])
    assert "no focus sessions" in out


def test_unclosed_session_reported_open(proj):
    _run(["start", "--issue", "B"])
    rc, out = _run(["report", "--json"])
    data = json.loads(out)
    assert data["open"]["issue"] == "B"
    assert data["sessions"] == []


def test_empty_report(proj):
    rc, out = _run(["report"])
    assert rc == 0 and "no focus sessions" in out


def test_root_flag_overrides_env(tmp_path, monkeypatch):
    """--root DIR targets that project's ledger regardless of cwd/env."""
    monkeypatch.setenv("DEVIN_PROJECT_DIR", str(tmp_path / "envproj"))
    other = tmp_path / "other"
    f._ROOT = None
    rc, _ = _run(["--root", str(other), "start", "--issue", "X"])
    assert rc == 0
    led = other / ".devin" / "ledgers" / "focus.jsonl"
    assert led.exists()
    assert not (tmp_path / "envproj").exists()
    f._ROOT = None
