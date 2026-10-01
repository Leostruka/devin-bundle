"""gh-pr-assignee.py — PostToolUse hook: assigns the PR author on `gh pr create`."""
import importlib.util
import io
import json
import os
import subprocess
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "gh_pr_assignee", os.path.join(SCRIPTS, "gh-pr-assignee.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

URL = "https://github.com/Acme/widgets/pull/42"


def _payload(cmd=None, output="", success=True, tool="exec", workdir=None):
    ti = {"command": cmd or "gh pr create --title t --body b"}
    if workdir:
        ti["workdir"] = workdir
    return {"hook_event_name": "PostToolUse", "tool_name": tool,
            "tool_input": ti,
            "tool_response": {"success": success, "output": output,
                              "error": None},
            "session_id": "t"}


def _run(payload, run_result=None):
    out_buf = io.StringIO()
    rr = run_result if run_result is not None else \
        subprocess.CompletedProcess([], 0, "ok", "")
    with patch.object(mod.subprocess, "run", return_value=rr) as m, \
         patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out_buf), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out_buf.getvalue(), m


def test_ignores_non_exec():
    code, out, m = _run(_payload(tool="read"))
    assert code == 0 and out == "" and not m.called


def test_ignores_non_create_command():
    code, out, m = _run(_payload(cmd="gh pr list", output=URL))
    assert code == 0 and out == "" and not m.called


def test_skips_when_assignee_flag_present():
    p = _payload(cmd="gh pr create --assignee Leostruka", output=URL)
    code, out, m = _run(p)
    assert code == 0 and out == "" and not m.called


def test_skips_failed_create():
    p = _payload(output="", success=False)
    code, out, m = _run(p)
    assert code == 0 and out == "" and not m.called


def test_skips_when_no_pr_url():
    code, out, m = _run(_payload(output="no url here"))
    assert code == 0 and out == "" and not m.called


def test_assigns_on_create():
    code, out, m = _run(_payload(output=f"created\n{URL}\n"))
    assert code == 0
    m.assert_called_once()
    argv = m.call_args[0][0]
    assert argv[:3] == ["gh", "pr", "edit"]
    assert URL in argv and "Leostruka" in argv
    assert "assigned Leostruka" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"]


def test_assign_failure_reports_context():
    rr = subprocess.CompletedProcess([], 1, "", "boom")
    code, out, m = _run(_payload(output=URL), run_result=rr)
    assert code == 0
    assert "failed" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"]


def test_env_override_assignee(monkeypatch):
    monkeypatch.setenv("GH_PR_ASSIGNEE", "someone-else")
    code, out, m = _run(_payload(output=URL))
    assert "someone-else" in m.call_args[0][0]
    monkeypatch.delenv("GH_PR_ASSIGNEE")
