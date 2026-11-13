"""rl-resume-detect.py - Stop: rate-limit signature -> resume intent file."""
import importlib.util
import io
import json
import os
import sys
import time
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "rl_resume_detect", os.path.join(SCRIPTS, "rl-resume-detect.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _run(payload, root):
    out = io.StringIO()
    with patch.object(sys, "stdin",
                      io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, {"DEVIN_PROJECT_DIR": str(root)}), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out.getvalue()


def _intents(root):
    d = root / ".devin" / "rts" / "intents"
    return list(d.glob("i*.json")) if d.is_dir() else []


def test_normal_stop_silent(tmp_path):
    code, out = _run({"hook_event_name": "Stop",
                      "last_assistant_message": "done."}, tmp_path)
    assert code == 0 and out == "" and _intents(tmp_path) == []


def test_rate_limit_writes_intent(tmp_path):
    code, out = _run(
        {"hook_event_name": "Stop",
         "last_assistant_message": "API rate limit reached. Retry after 300 seconds."},
        tmp_path)
    assert code == 0
    assert "resume intent" in out
    files = _intents(tmp_path)
    assert len(files) == 1
    rec = json.loads(files[0].read_text(encoding="utf-8"))
    assert rec["kind"] == "resume_at"
    assert rec["auto"] is False
    assert rec["when"] >= int(time.time()) + 250


def test_429_and_quota_detected(tmp_path):
    code, _ = _run({"hook_event_name": "Stop",
                    "last_assistant_message": "HTTP 429 quota exceeded"},
                   tmp_path)
    assert code == 0 and len(_intents(tmp_path)) == 1


def test_retry_after_minutes_bounded(tmp_path):
    _run({"hook_event_name": "Stop",
          "last_assistant_message": "rate limit. retry after 60000 minutes"},
         tmp_path)
    rec = json.loads(_intents(tmp_path)[0].read_text(encoding="utf-8"))
    assert rec["when"] <= int(time.time()) + 86400
