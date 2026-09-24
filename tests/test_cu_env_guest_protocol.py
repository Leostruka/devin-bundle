"""Gate for C10: guest worker channel negotiation.

virtio-serial pipe owned by the supervisor; handshake yields a
CAPABILITY SET consistent with session reality — claimed caps
incompatible with session state are stripped, never trusted.
"""
import io
import json
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_guest = load("cu_guest")
cu_env = load("cu_env")


# --- handshake validation ----------------------------------------------------------

def test_guest_session_zero_has_no_interactive_capability():
    caps = cu_guest.validate_handshake(
        {"version": 1, "interactive": False, "session_id": 0,
         "capabilities": {"text_insert": True, "uia": True}})
    assert caps["text_insert"] is False
    assert caps["uia"] is False


def test_interactive_session_keeps_claimed_caps():
    caps = cu_guest.validate_handshake(
        {"version": 1, "interactive": True, "session_id": 2,
         "capabilities": {"text_insert": True, "uia": False}})
    assert caps["text_insert"] is True
    assert caps["uia"] is False


def test_claimed_cap_not_in_catalog_is_dropped():
    caps = cu_guest.validate_handshake(
        {"version": 1, "interactive": True, "session_id": 1,
         "capabilities": {"text_insert": True,
                          "kernel_memory_read": True}})
    assert "kernel_memory_read" not in caps


def test_malformed_handshake_rejected():
    with pytest.raises(cu_guest.GuestProtocolError):
        cu_guest.validate_handshake({"version": 99})
    with pytest.raises(cu_guest.GuestProtocolError):
        cu_guest.validate_handshake("not a dict")


# --- channel framing -----------------------------------------------------------------

def _channel_pair():
    """GuestChannel bound to an in-memory duplex (no virtio needed)."""
    a_in, a_out = io.BytesIO(), io.BytesIO()

    class Duplex:
        """read returns what the peer wrote."""
        def __init__(self):
            self.r, self.w = io.BytesIO(), io.BytesIO()

    return a_in, a_out


def test_request_reply_roundtrip():
    srv_in, srv_out = io.BytesIO(), io.BytesIO()
    ch = cu_guest.GuestChannel(io.BytesIO(b'{"ok": true, "pong": 1}\n'),
                             srv_in)
    assert ch.call("ping") == {"ok": True, "pong": 1}
    req = json.loads(srv_in.getvalue().decode().strip())
    assert req["method"] == "ping"
    assert "id" in req


def test_oversized_response_rejected():
    big = json.dumps({"ok": True, "blob": "x" * (70000)}).encode()
    ch = cu_guest.GuestChannel(io.BytesIO(big + b"\n"), io.BytesIO(),
                             max_reply=65536)
    with pytest.raises(cu_guest.GuestProtocolError, match="size"):
        ch.call("ping")


def test_unenumerated_method_rejected():
    ch = cu_guest.GuestChannel(io.BytesIO(), io.BytesIO(),
                             methods=frozenset({"ping"}))
    with pytest.raises(cu_guest.GuestProtocolError, match="method"):
        ch.call("exec_shell")


def test_response_timeout_is_typed():
    class HungReader:
        def readline(self):
            time.sleep(2)
            return b""

    ch = cu_guest.GuestChannel(HungReader(), io.BytesIO(),
                             timeout_s=0.05)
    with pytest.raises(cu_guest.GuestTimeout):
        ch.call("ping")


def test_boot_change_invalidates_channel():
    """A reply stamped with a different boot_id means the worker is
    answering for a DIFFERENT guest boot — drop it."""
    ch = cu_guest.GuestChannel(
        io.BytesIO(b'{"ok": true, "boot_id": "other-boot"}\n'),
        io.BytesIO(), boot_id="expected-boot")
    with pytest.raises(cu_guest.GuestProtocolError, match="boot"):
        ch.call("ping")


# --- argv wiring ----------------------------------------------------------------------

def _argv_spec(**kw):
    s = {"env_id": "e", "provider": "qemu", "accel": "whpx",
         "qemu_path": "qemu", "image_ref": "img.iso",
         "resources": {"vcpus": 1, "memory_mib": 512}}
    s.update(kw)
    return s


def test_argv_adds_virtio_serial_port(tmp_path):
    spec = _argv_spec(guest_worker=True)
    overlay = tmp_path / "o.qcow2"
    argv = cu_env.build_qemu_argv(spec, overlay)
    s = " ".join(argv)
    assert "virtio-serial" in s
    assert "devin.cu" in s


def test_argv_without_worker_stays_qmp_only(tmp_path):
    """Profiles without the guest driver keep working via QMP with
    explicitly reduced capabilities — no virtio port appears."""
    spec = _argv_spec()
    overlay = tmp_path / "o.qcow2"
    argv = cu_env.build_qemu_argv(spec, overlay)
    assert "devin.cu" not in " ".join(argv)


# --- guest worker pure side -----------------------------------------------------------

def test_worker_handshake_payload():
    worker = load("cu_guest_worker")
    hello = worker.build_handshake(
        {"interactive": True, "session_id": 3,
         "capabilities": {"text_insert": True}})
    assert hello["version"] == cu_guest.PROTOCOL_VERSION
    assert hello["interactive"] is True
    assert "boot_id" in hello


def test_worker_rejects_unknown_method():
    worker = load("cu_guest_worker")
    r = worker.handle_request({"id": "1", "method": "rm_rf",
                               "params": {}}, caps={"text_insert": True})
    assert r["ok"] is False
    assert "method" in r["error"]
