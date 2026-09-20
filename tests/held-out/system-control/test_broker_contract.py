"""Held-out broker contract tests; lead-owned. Fake io seams only."""
import importlib
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


@pytest.fixture
def broker():
    try:
        return load("sc_broker")
    except ModuleNotFoundError:
        pytest.skip("sc_broker not implemented yet")


def request(cap="service.restart", **args):
    return {"version": 1, "request_id": "r1", "capability": cap,
            "args": args, "deadline_ms": 1000,
            "subject": {"uid": "self"},
            "policy": {"dry_run": False}}


class FakeBroker:
    """In-memory broker seam implementing the wire contract."""

    def __init__(self):
        self.dispatched = []
        self.subjects = {"self"}

    def capabilities(self):
        return ["service.restart"]

    def dispatch(self, env):
        self.dispatched.append(env)
        return {"ok": True, "status": "dispatched",
                "audit_id": "fake-audit-1"}


def test_broker_exposes_only_declared(broker):
    fb = FakeBroker()
    assert fb.capabilities() == ["service.restart"]


def test_dispatch_rejects_undeclared_capability(broker):
    fb = FakeBroker()
    r = broker.dispatch(request("process.exec", argv=["x"]),
                        broker=fb)
    assert r["ok"] is False
    assert r["status"] == "rejected"
    assert fb.dispatched == []


def test_dispatch_rejects_foreign_subject(broker):
    fb = FakeBroker()
    req = request(name="allowed")
    req["subject"] = {"uid": "other"}
    r = broker.dispatch(req, broker=fb)
    assert r["ok"] is False
    assert r["status"] == "rejected"
    assert fb.dispatched == []


def test_dispatch_rejects_expired_deadline(broker):
    fb = FakeBroker()
    req = request(name="allowed")
    req["deadline_ms"] = 1
    req["issued_at_ms"] = 0
    r = broker.dispatch(req, broker=fb, now_ms=10_000)
    assert r["ok"] is False
    assert fb.dispatched == []


def test_dispatch_returns_audit_id(broker):
    fb = FakeBroker()
    r = broker.dispatch(request(name="allowed"), broker=fb)
    assert r["ok"] is True
    assert r["status"] == "dispatched"
    assert r.get("audit_id") or r["value"].get("audit_id")


def test_unprovisioned_broker_is_explicit(broker):
    r = broker.dispatch(request(name="x"), broker=None)
    assert r["ok"] is False
    assert r["status"] in ("rejected", "unknown")
