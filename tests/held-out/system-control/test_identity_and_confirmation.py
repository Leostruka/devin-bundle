"""Held-out identity and confirmation contracts; lead-owned."""
import importlib
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


def test_process_request_rejects_pid_without_start_time():
    contract = load("sc_contract")
    with pytest.raises(ValueError, match="start_time"):
        contract.validate_request({
            "version": 1,
            "request_id": "held-out-identity",
            "capability": "process.observe",
            "target": {"pid": 42},
            "args": {},
            "deadline_ms": 1000,
        })


def test_unknown_schema_version_fails_closed():
    contract = load("sc_contract")
    with pytest.raises(ValueError, match="version"):
        contract.validate_request({
            "version": 2,
            "request_id": "held-out-version",
            "capability": "capabilities",
            "args": {},
            "deadline_ms": 1000,
        })


def process_cancel(pid=42, start_time=99):
    return {
        "version": 1,
        "request_id": "held-out-confirmation",
        "capability": "process.cancel",
        "target": {"pid": pid, "start_time": start_time},
        "args": {},
        "deadline_ms": 1000,
        "policy": {"dry_run": False, "confirmation_id": None},
    }


def test_confirmation_rejects_target_mutation(tmp_path, monkeypatch):
    policy = load("sc_policy")
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    original = process_cancel()
    token = policy.issue_confirmation(original)["confirmation_id"]
    assert policy.consume_confirmation(
        process_cancel(pid=43), token)["ok"] is False


def test_confirmation_is_single_use(tmp_path, monkeypatch):
    policy = load("sc_policy")
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    request = process_cancel()
    token = policy.issue_confirmation(request)["confirmation_id"]
    assert policy.consume_confirmation(request, token)["ok"] is True
    assert policy.consume_confirmation(request, token)["ok"] is False
