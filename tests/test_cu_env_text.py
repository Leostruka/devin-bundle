"""Gate for C11: Unicode text + clipboard inside the guest only.

- check_operation is the pure gate; clipboard requires an explicit
  opt-in capability, never implicit host sync
- full string validated BEFORE any effect; partial inserts report
  'unknown' with a known count — never a blind retry
- guest replies are untrusted: content never lands in journals/logs
"""
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_guest = load("cu_guest")
cu_qmp_backend = load("cu_qmp_backend")
cu_backend = load("cu_backend")


# --- check_operation (pure gate) ------------------------------------------------------

def test_clipboard_disabled_is_rejected():
    r = cu_guest.check_operation("clipboard.set", {"clipboard": False})
    assert r == {"allowed": False, "reason": "capability_unavailable"}


def test_clipboard_optin_allows():
    r = cu_guest.check_operation("clipboard.set", {"clipboard": True})
    assert r == {"allowed": True}


def test_text_insert_requires_cap():
    r = cu_guest.check_operation("text.insert", {"text_insert": False})
    assert r["allowed"] is False
    r = cu_guest.check_operation("text.insert", {"text_insert": True})
    assert r["allowed"] is True


def test_unknown_operation_rejected():
    r = cu_guest.check_operation("shell.exec", {"exec": True})
    assert r["allowed"] is False
    assert r["reason"] == "unknown_operation"


# --- text.insert path on backend ------------------------------------------------------

@pytest.fixture
def env_dir(tmp_path):
    d = tmp_path / "devin-linux"
    d.mkdir()
    (d / "ready.json").write_text(json.dumps({
        "socket": "tcp://127.0.0.1:1", "token": "t0k",
        "qemu_pid": 1, "daemon_pid": 2,
        "guest_caps": {"text_insert": True, "clipboard": False}}))
    return d


def test_guest_call_routes_over_ipc(env_dir):
    sent = []

    def ipc(sock, msg, timeout_s, token=None):
        sent.append(msg)
        return {"ok": True, "return": {"ok": True, "inserted": 5}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    r = be.guest_call("text.insert", {"text": "ação"})
    assert sent[0]["command"] == "guest-call"
    assert sent[0]["arguments"]["method"] == "text.insert"
    assert r["inserted"] == 5


def test_text_insert_validates_before_sending(env_dir):
    """Oversized text rejects before a byte leaves — no partial effect
    attempted on the wire."""
    def must_not_run(*a, **k):
        raise AssertionError("sent oversized text")

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=must_not_run)
    with pytest.raises(cu_qmp_backend.BackendError, match="size"):
        be.guest_call("text.insert", {"text": "x" * 200000})


def test_partial_insert_reports_unknown(env_dir):
    """inserted < len(text): the effect is real but incomplete — status
    'unknown' with the known count, never silent success."""
    def ipc(sock, msg, timeout_s, token=None):
        return {"ok": True, "return": {"ok": True, "inserted": 3}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    r = be.text_insert("ação!")  # 5 chars, 3 landed
    assert r["status"] == "unknown"
    assert r["inserted"] == 3


def test_full_insert_is_dispatched(env_dir):
    def ipc(sock, msg, timeout_s, token=None):
        return {"ok": True, "return": {"ok": True, "inserted": 5}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    r = be.text_insert("ação!")
    assert r["status"] == "dispatched"
    assert r["inserted"] == 5


def test_unicode_text_not_transliterated(env_dir):
    """Emoji/combining accents pass through as-is; a platform that
    can't represent them fails honestly — never silent munging."""
    seen = []

    def ipc(sock, msg, timeout_s, token=None):
        seen.append(msg["arguments"]["params"]["text"])
        t = msg["arguments"]["params"]["text"]
        return {"ok": True, "return": {"ok": True,
                                       "inserted": len(t)}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    be.text_insert("ação ç 🚀\ne\u0301")
    assert seen == ["ação ç 🚀\ne\u0301"]


def test_text_insert_without_cap_rejected(env_dir, tmp_path):
    """Spec says clipboard off + no text_insert cap -> typed rejection,
    no IPC."""
    d = tmp_path / "nocap"
    d.mkdir()
    (d / "ready.json").write_text(json.dumps({
        "socket": "tcp://127.0.0.1:1", "token": "t",
        "guest_caps": {"text_insert": False}}))
    be = cu_qmp_backend.QmpBackend(
        "devin-linux", env_dir=d,
        ipc=lambda *a, **k: pytest.fail("IPC without capability"))
    with pytest.raises(cu_qmp_backend.BackendError,
                       match="capability_unavailable"):
        be.text_insert("hello")


# --- worker-side insert accounting ---------------------------------------------------

def test_worker_insert_reports_count():
    worker = load("cu_guest_worker")
    r = worker.handle_request(
        {"id": "1", "method": "text.insert",
         "params": {"text": "hi"}},
        caps={"text_insert": True})
    # not_implemented in C11 host tests is fine — but the shape must be
    # a reply, never a crash
    assert r["id"] == "1"
    assert "ok" in r


def test_worker_clipboard_requires_cap():
    worker = load("cu_guest_worker")
    r = worker.handle_request(
        {"id": "1", "method": "clipboard.set",
         "params": {"text": "secret"}},
        caps={"clipboard": False})
    assert r["ok"] is False
    assert "capability" in r["error"]


# --- clipboard spec gating ------------------------------------------------------------

def test_spec_clipboard_guest_is_allowed_value():
    cu_env = load("cu_env")
    spec = {"schema_version": 1, "env_id": "e", "provider": "qemu",
            "image_ref": "i", "image_sha256": "0" * 64,
            "guest_os": "linux", "keyboard_layout": "en-us",
            "accel": "whpx", "qemu_path": "q",
            "resources": {"vcpus": 1, "memory_mib": 512},
            "network": "off", "clipboard": "guest",
            "mounts": [], "physical_devices": []}
    assert cu_env.validate_spec(spec) == []


def test_spec_clipboard_on_is_still_rejected():
    """'on' would imply host<->guest sync — only 'guest' (in-guest
    clipboard, opt-in ops) is a legal non-off value."""
    cu_env = load("cu_env")
    spec = {"schema_version": 1, "env_id": "e", "provider": "qemu",
            "image_ref": "i", "image_sha256": "0" * 64,
            "guest_os": "linux", "keyboard_layout": "en-us",
            "accel": "whpx", "qemu_path": "q",
            "resources": {"vcpus": 1, "memory_mib": 512},
            "network": "off", "clipboard": "on",
            "mounts": [], "physical_devices": []}
    errors = cu_env.validate_spec(spec)
    assert any("clipboard" in e for e in errors)
