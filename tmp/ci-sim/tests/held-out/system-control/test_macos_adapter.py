"""Held-out macOS adapter contracts; lead-owned. Seam-based."""
import importlib
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


@pytest.fixture
def mac():
    return load("backends.macos")


def test_endpoint_security_explicitly_unsupported(mac):
    caps = mac.capabilities()
    es = next((c for c in caps if c["name"] == "endpoint_security"),
              None)
    assert es is not None
    assert es["supported"] is False
    assert es["reason"] == "entitlement_required"


def test_empty_label_rejected_before_subprocess(mac, monkeypatch):
    calls = []
    monkeypatch.setattr(mac, "run_bounded",
                        lambda *a, **kw: calls.append(a) or (0, b"", b""),
                        raising=False)
    with pytest.raises(Exception):
        mac.service_status("")
    assert calls == []


def test_stale_identity_rejected(mac, monkeypatch):
    monkeypatch.setattr(
        mac, "process_list", lambda pid=None: [
            {"pid": 7, "start_time": 100, "name": "p"}])
    with pytest.raises(LookupError):
        mac.process_get(7, start_time=999)


def test_wait_returns_when_process_gone(mac, monkeypatch):
    calls = {"n": 0}

    def gone(pid, start_time=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"pid": pid, "start_time": start_time or 100,
                    "name": "p"}
        raise LookupError("process not found")

    monkeypatch.setattr(mac, "process_get", gone)
    r = mac.wait_process({"pid": 7, "start_time": 100}, timeout_s=5)
    assert r["ok"] is True


def test_wait_rejects_stale_before_waiting(mac, monkeypatch):
    def stale(pid, start_time=None):
        raise LookupError("stale pid identity")

    monkeypatch.setattr(mac, "process_get", stale)
    r = mac.wait_process({"pid": 7, "start_time": 999}, timeout_s=5)
    assert r["ok"] is False
    assert r["status"] == "rejected"
