"""sc_broker — opt-in privileged broker seam: declared-cap gating,
subject binding, deadline enforcement, audit_id surfacing."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_broker as broker_mod  # noqa: E402
import sc_policy as policy  # noqa: E402


class FakeBroker:
    """In-memory broker seam: declared capabilities, bound subjects,
    recorded calls, fixed audit_id."""

    def __init__(self, subjects=("uid-1",),
                 capabilities=("service.restart",),
                 audit_id="audit-0001", result=None):
        self.subjects = list(subjects)
        self._capabilities = list(capabilities)
        self._audit_id = audit_id
        self._result = result
        self.calls = []

    def capabilities(self):
        return list(self._capabilities)

    def dispatch(self, request):
        self.calls.append(request)
        if self._result is not None:
            return self._result
        return {"ok": True, "audit_id": self._audit_id}


class BrokenBroker:
    """capabilities() unreadable — preflight/status must fail closed."""

    subjects = ["uid-1"]

    def capabilities(self):
        raise OSError("broker metadata unreadable")

    def dispatch(self, request):  # pragma: no cover - never reached
        raise AssertionError("must not be called")


def request(capability, args, **extra):
    req = {
        "version": 1, "request_id": "r1", "capability": capability,
        "args": args, "deadline_ms": 1000, "policy": {"dry_run": False},
        "subject": {"uid": "uid-1"}, "issued_at_ms": 5000,
    }
    req.update(extra)
    return req


@pytest.fixture
def fake_broker():
    return FakeBroker()


def test_broker_exposes_only_declared_capabilities(fake_broker):
    assert fake_broker.capabilities() == ["service.restart"]


def test_dispatch_success_surfaces_audit_id(fake_broker):
    res = broker_mod.dispatch(
        request("service.restart", {"name": "allowed"}),
        broker=fake_broker, now_ms=5500)
    assert res["ok"] is True
    assert res["status"] == "dispatched"
    assert res["audit_id"] == "audit-0001"
    assert len(fake_broker.calls) == 1


def test_rejects_undeclared_capability_without_calling(fake_broker):
    res = broker_mod.dispatch(
        request("process.exec", {"argv": ["x"]}),
        broker=fake_broker, now_ms=5500)
    assert res["ok"] is False
    assert res["status"] == "rejected"
    assert fake_broker.calls == []


def test_rejects_capability_outside_broker_allowlist():
    # Even if a broker *declares* a capability, only service.restart
    # may ever be dispatched — no wildcard, no generic execution.
    wide = FakeBroker(capabilities=["service.restart", "shell.exec"])
    res = broker_mod.dispatch(
        request("shell.exec", {"cmd": "x"}), broker=wide, now_ms=5500)
    assert res["ok"] is False
    assert res["status"] == "rejected"
    assert wide.calls == []


def test_broker_rejects_unbound_identity(fake_broker):
    req = request("service.restart", {"name": "allowed"})
    req["subject"] = {"uid": "other"}
    res = broker_mod.dispatch(req, broker=fake_broker, now_ms=5500)
    assert res["status"] == "rejected"
    assert fake_broker.calls == []


def test_missing_subject_rejected(fake_broker):
    req = request("service.restart", {"name": "allowed"})
    del req["subject"]
    res = broker_mod.dispatch(req, broker=fake_broker, now_ms=5500)
    assert res["ok"] is False
    assert res["status"] == "rejected"
    assert fake_broker.calls == []


def test_expired_deadline_rejected_before_broker_call(fake_broker):
    res = broker_mod.dispatch(
        request("service.restart", {"name": "allowed"}),
        broker=fake_broker, now_ms=7000)
    assert res["ok"] is False
    assert res["status"] == "rejected"
    assert fake_broker.calls == []


def test_deadline_boundary_still_dispatches(fake_broker):
    # issued(5000) + deadline(1000) == now(6000): not yet expired.
    res = broker_mod.dispatch(
        request("service.restart", {"name": "allowed"}),
        broker=fake_broker, now_ms=6000)
    assert res["ok"] is True
    assert res["status"] == "dispatched"


def test_unprovisioned_broker_explicit_response():
    res = broker_mod.dispatch(
        request("service.restart", {"name": "allowed"}),
        broker=None, now_ms=5500)
    assert res["ok"] is False
    assert res["status"] in ("rejected", "unknown")


def test_broker_failure_is_unknown_not_dispatched():
    failing = FakeBroker(result={"ok": False, "error": "svc failed"})
    res = broker_mod.dispatch(
        request("service.restart", {"name": "allowed"}),
        broker=failing, now_ms=5500)
    assert res["ok"] is False
    assert res["status"] in ("rejected", "unknown")


def test_broker_exception_never_raises():
    class Exploding(FakeBroker):
        def dispatch(self, request):
            raise RuntimeError("transport down")
    res = broker_mod.dispatch(
        request("service.restart", {"name": "allowed"}),
        broker=Exploding(), now_ms=5500)
    assert res["ok"] is False
    assert res["status"] == "unknown"


def test_audit_id_sanitized_no_args_echo():
    leaky = FakeBroker(result={"ok": True, "audit_id": 12345})
    res = broker_mod.dispatch(
        request("service.restart", {"name": "secret-svc"}),
        broker=leaky, now_ms=5500)
    assert "secret-svc" not in str(res)


def test_broker_dispatch_requires_confirmation():
    req = {
        "version": 1, "request_id": "r1",
        "capability": "broker.dispatch",
        "args": {"capability": "service.restart"},
        "deadline_ms": 1000, "policy": {"dry_run": False},
    }
    assert policy.classify(req)["decision"] == "confirm"


def test_confirmation_roundtrip_for_broker_dispatch(
        tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = {
        "version": 1, "request_id": "r1",
        "capability": "broker.dispatch",
        "args": {"capability": "service.restart",
                 "name": "allowed"},
        "deadline_ms": 1000, "policy": {"dry_run": False},
    }
    token = policy.issue_confirmation(req)["confirmation_id"]
    assert policy.consume_confirmation(req, token)["ok"] is True


def test_preflight_reports_declared_capabilities(fake_broker):
    res = broker_mod.preflight(fake_broker)
    assert res["ok"] is True
    assert res["provisioned"] is True
    assert res["capabilities"] == ["service.restart"]


def test_preflight_unprovisioned():
    res = broker_mod.preflight(None)
    assert res["ok"] is False
    assert res["provisioned"] is False
    assert res["capabilities"] == []


def test_preflight_fails_closed_on_unreadable_metadata():
    res = broker_mod.preflight(BrokenBroker())
    assert res["ok"] is False
    assert res["provisioned"] is False


def test_status_reports_bound_subject_count(fake_broker):
    res = broker_mod.status(fake_broker)
    assert res["ok"] is True
    assert res["provisioned"] is True
    assert res["capabilities"] == ["service.restart"]
    assert res["subjects"] == 1


def test_status_unprovisioned():
    res = broker_mod.status(None)
    assert res["ok"] is False
    assert res["provisioned"] is False
