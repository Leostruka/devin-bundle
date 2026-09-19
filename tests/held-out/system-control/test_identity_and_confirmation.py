"""Held-out identity and confirmation contracts; lead-owned."""
import importlib
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    sys.modules.pop(name, None)
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
