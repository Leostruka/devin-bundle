"""Tests for subagent dispatch budgets in validate-tool-args.py (#515).

Policy file <state>/subagent-budget.json with optional knobs:
  max_dispatches, session_max_minutes, max_cost_usd + spent_usd.
Ledger <state>/subagent-ledger.jsonl records each run_subagent dispatch.
"""
import json
import os
import subprocess
import sys
import time

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
VALIDATE_SCRIPT = os.path.join(SCRIPTS_DIR, "validate-tool-args.py")


def run_validate(state_dir: str, session_id: str = "s1") -> tuple[int, str]:
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "run_subagent",
        "tool_input": {"task": "do thing", "profile": "researcher",
                       "title": "t"},
        "session_id": session_id,
    })
    env = dict(os.environ, DEVIN_STATE_DIR=state_dir)
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        input=payload, capture_output=True, text=True, timeout=15,
        encoding="utf-8", errors="replace", env=env,
    )
    return result.returncode, result.stdout.strip()


def write_policy(state_dir: str, policy: dict):
    with open(os.path.join(state_dir, "subagent-budget.json"), "w",
              encoding="utf-8") as f:
        json.dump(policy, f)


def ledger_lines(state_dir: str) -> list[dict]:
    path = os.path.join(state_dir, "subagent-ledger.jsonl")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except OSError:
        return []


def test_no_policy_allows_and_records_nothing(tmp_path):
    code, _ = run_validate(str(tmp_path))
    assert code == 0
    # no policy file = uncapped AND no ledger overhead (opt-in)
    assert ledger_lines(str(tmp_path)) == []


def test_policy_enables_ledger(tmp_path):
    write_policy(str(tmp_path), {"max_cost_usd": 100.0})
    code, _ = run_validate(str(tmp_path))
    assert code == 0
    recs = ledger_lines(str(tmp_path))
    assert len(recs) == 1 and recs[0]["profile"] == "researcher"


def test_max_dispatches_blocks_at_cap(tmp_path):
    write_policy(str(tmp_path), {"max_dispatches": 1})
    code, _ = run_validate(str(tmp_path))
    assert code == 0  # first allowed
    code, out = run_validate(str(tmp_path))
    assert code == 2, f"second dispatch should block, got {code}: {out}"
    assert "max_dispatches" in out
    assert len(ledger_lines(str(tmp_path))) == 1  # blocked call not recorded


def test_max_dispatches_scoped_to_session(tmp_path):
    write_policy(str(tmp_path), {"max_dispatches": 1})
    run_validate(str(tmp_path), session_id="other")
    code, _ = run_validate(str(tmp_path), session_id="mine")
    assert code == 0  # different session unaffected


def test_session_max_minutes_blocks(tmp_path):
    write_policy(str(tmp_path), {"session_max_minutes": 1})
    # seed an old ledger record for this session
    old = {"ts": int(time.time()) - 600, "session_id": "s1",
           "profile": "researcher", "title": "old"}
    with open(os.path.join(str(tmp_path), "subagent-ledger.jsonl"), "w",
              encoding="utf-8") as f:
        f.write(json.dumps(old) + "\n")
    code, out = run_validate(str(tmp_path))
    assert code == 2, f"elapsed session should block, got {code}: {out}"
    assert "session_max_minutes" in out


def test_max_cost_blocks_when_spent(tmp_path):
    write_policy(str(tmp_path), {"max_cost_usd": 5.0, "spent_usd": 5.25})
    code, out = run_validate(str(tmp_path))
    assert code == 2
    assert "max_cost_usd" in out


def test_cost_under_cap_allows(tmp_path):
    write_policy(str(tmp_path), {"max_cost_usd": 5.0, "spent_usd": 1.0})
    code, _ = run_validate(str(tmp_path))
    assert code == 0


def test_invalid_policy_fail_open(tmp_path):
    with open(os.path.join(str(tmp_path), "subagent-budget.json"), "w",
              encoding="utf-8") as f:
        f.write("{not json")
    code, _ = run_validate(str(tmp_path))
    assert code == 0
