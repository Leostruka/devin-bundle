"""Gate for C03: QMP framing, id correlation, typed allowlist.

Reader/writer are injected streams — no QEMU process needed. Transcript
fixtures live in tests/fixtures/cu_qmp_transcripts.json.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_qmp = load("cu_qmp")

FIXTURES = json.loads((Path(__file__).parent / "fixtures"
                       / "cu_qmp_transcripts.json").read_text())


class ScriptReader:
    """Yields scripted chunks; returns "" (EOF) when exhausted."""

    def __init__(self, chunks):
        self._chunks = list(chunks)

    def read(self, n=4096):
        return self._chunks.pop(0) if self._chunks else ""


class LineReader:
    """Pipe-like: only readline(), no read(). A read(4096) on a real pipe
    blocks until the buffer fills — this double proves we don't do that."""

    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self):
        return self._lines.pop(0) if self._lines else ""


class ListWriter:
    def __init__(self):
        self.data = []

    def write(self, s):
        self.data.append(s)

    def flush(self):
        pass


def _client(lines, deadline=5.0):
    r = ScriptReader(lines)
    w = ListWriter()
    return cu_qmp.QmpClient(r, w, deadline_s=deadline), w


def _msg(obj):
    return json.dumps(obj) + "\r\n"


def test_negotiate_sends_capabilities_after_greeting():
    c, w = _client([_msg(FIXTURES["greeting"]),
                    _msg(FIXTURES["caps_ack"])])
    c.negotiate()
    sent = [json.loads(d) for d in w.data]
    assert sent[0]["execute"] == "qmp_capabilities"


def test_negotiate_requires_greeting():
    c, _ = _client([_msg({"return": {}})])
    with pytest.raises(cu_qmp.QmpError, match="greeting"):
        c.negotiate()


def test_call_correlates_id_skipping_events_and_strays():
    lines = [
        _msg(FIXTURES["greeting"]), _msg(FIXTURES["caps_ack"]),
        _msg(FIXTURES["async_event"]),                 # event: not an answer
        _msg({"id": "other", "return": {}}),            # stray id
        _msg({"id": "qmp-1",
              "return": {"status": "running", "running": True}}),
    ]
    c, w = _client(lines)
    c.negotiate()
    out = c.call("query-status")
    assert out["status"] == "running"
    sent = [json.loads(d) for d in w.data]
    assert sent[1]["execute"] == "query-status"


def test_fragmented_message_reassembles():
    full = _msg(FIXTURES["greeting"]) + _msg(FIXTURES["caps_ack"])
    chunks = [full[:7], full[7:20], full[20:]]  # split mid-object
    c, w = _client(chunks)
    c.negotiate()
    assert json.loads(w.data[0])["execute"] == "qmp_capabilities"


def test_eof_is_typed_not_silent():
    c, _ = _client([_msg(FIXTURES["greeting"]), _msg(FIXTURES["caps_ack"])])
    c.negotiate()
    with pytest.raises(cu_qmp.QmpEOF):
        c.call("query-status")


def test_invalid_json_is_protocol_error():
    c, _ = _client(["{not json\n"])
    with pytest.raises(cu_qmp.QmpError, match="protocol"):
        c.negotiate()


def test_deadline_expires_on_incomplete_read():
    r = ScriptReader(['{"QMP": {"version": {}'])  # never completes
    c = cu_qmp.QmpClient(r, ListWriter(), deadline_s=0)
    with pytest.raises(cu_qmp.QmpTimeout):
        c.negotiate()


def test_error_response_is_refused_not_success():
    lines = [_msg(FIXTURES["greeting"]), _msg(FIXTURES["caps_ack"]),
             _msg({"id": "qmp-1",
                   "error": {"class": "CommandNotFound", "desc": "nope"}})]
    c, _ = _client(lines)
    c.negotiate()
    with pytest.raises(cu_qmp.QmpRefused, match="CommandNotFound"):
        c.call("query-status")


def test_empty_ack_is_transport_success_only():
    """{"return": {}} proves the command reached QEMU — it is NOT
    evidence of a UI effect."""
    lines = [_msg(FIXTURES["greeting"]), _msg(FIXTURES["caps_ack"]),
             _msg({"id": "qmp-1", "return": {}})]
    c, _ = _client(lines)
    c.negotiate()
    assert c.call("query-status") == {}  # transport ok, no effect claimed


def test_disallowed_command_never_written():
    c, w = _client([_msg(FIXTURES["greeting"]), _msg(FIXTURES["caps_ack"])])
    c.negotiate()
    for bad in ("human-monitor-command", "migrate", "chardev-add",
                "blockdev-add", "getfd"):
        with pytest.raises(cu_qmp.QmpError, match="not_allowed"):
            c.call(bad)
    # only the handshake was ever written
    assert len(w.data) == 1


def test_monitor_escape_is_not_a_public_operation():
    assert cu_qmp.public_operation_allowed("human-monitor-command") is False


def test_readline_reader_no_read_method():
    """Regression: a pipe exposes readline, and read(4096) on a pipe
    blocks until the buffer fills. The client must prefer readline."""
    r = LineReader([_msg(FIXTURES["greeting"]), _msg(FIXTURES["caps_ack"]),
                    _msg({"id": "qmp-1", "return": {"running": True}})])
    c = cu_qmp.QmpClient(r, ListWriter(), deadline_s=5)
    c.negotiate()
    assert c.call("query-status") == {"running": True}
    assert cu_qmp.public_operation_allowed("migrate") is False
    assert cu_qmp.public_operation_allowed("query-status") is False
    assert cu_qmp.public_operation_allowed("env.capture") is True
