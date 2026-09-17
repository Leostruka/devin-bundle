"""Gate for ticket 07: persistent worker isolation. Real subprocesses over
pipes (loopback-only by construction — no sockets anywhere)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cs = cu_load.load("cu_session")

ECHO = (
    "import sys, json\n"
    "for line in sys.stdin:\n"
    "    env = json.loads(line)\n"
    "    print(json.dumps({'ok': True, 'echo': env['cmd'],"
    "                      'session': env['session'], 'gen': env['gen']}),"
    "          flush=True)\n"
)

HANG = (
    "import sys, json, time\n"
    "for line in sys.stdin:\n"
    "    env = json.loads(line)\n"
    "    if env['cmd'].get('sleep'):\n"
    "        time.sleep(env['cmd']['sleep'])\n"
    "    print(json.dumps({'ok': True}), flush=True)\n"
)


def _worker(script=ECHO, timeout=5.0):
    return cs.Worker([sys.executable, "-u", "-c", script], timeout=timeout)


@pytest.fixture
def worker():
    w = _worker()
    yield w
    w.close()


def test_request_roundtrip(worker):
    r = worker.request({"op": "ping"})
    assert r["ok"] is True and r["echo"] == {"op": "ping"}
    assert r["session"] == worker.session and r["gen"] == worker.generation


def test_session_a_envelope_rejected_by_b(worker):
    """An envelope stamped by worker A is stale for worker B."""
    a_env = worker._envelope({"op": "x"})
    b = _worker()
    try:
        assert not b.verify_envelope(a_env)
        assert a_env["session"] != b.session
    finally:
        b.close()


def test_restart_invalidates_ids(worker):
    old = (worker.pid, worker.session, worker.generation)
    worker.restart()
    assert worker.pid != old[0]
    assert worker.session != old[1]
    assert worker.generation == old[2] + 1
    stale_env = {"session": old[1], "gen": old[2]}
    assert not worker.verify_envelope(stale_env)


def test_hung_worker_terminated_and_recreated():
    w = _worker(HANG, timeout=0.3)
    try:
        r = w.request({"sleep": 30}, timeout=0.3)
        assert r["status"] == "timeout"
        assert w.alive  # respawned
        r2 = w.request({"ok": True})
        assert r2["ok"] is True
    finally:
        w.close()


def test_dead_worker_respawns(worker):
    worker._proc.kill()
    worker._proc.wait(timeout=5)
    r = worker.request({"op": "after-death"})
    assert r["ok"] is True and r["echo"]["op"] == "after-death"


def test_cancel_drains_pending(worker):
    worker.submit({"op": 1})
    worker.submit({"op": 2})
    assert worker.cancel() == 2
    assert worker.run_pending() == []


def test_pending_queue_runs_in_order(worker):
    worker.submit({"op": "first"})
    worker.submit({"op": "second"})
    out = worker.run_pending()
    assert [r["echo"]["op"] for r in out] == ["first", "second"]


def test_transport_is_pipes_only(worker):
    """No socket object anywhere on the worker — loopback guarantee by
    construction (child stdio pipes)."""
    assert not any(isinstance(v, __import__("socket").socket)
                   for v in vars(worker).values())
    assert worker._proc.stdin and worker._proc.stdout


def test_non_json_line_is_unknown():
    BAD = "import sys\nsys.stdout.write('garbage\\n'); sys.stdout.flush()\n"
    w = cs.Worker([sys.executable, "-u", "-c", BAD], timeout=2.0)
    try:
        r = w.request({"op": "x"})
        assert r["ok"] is False and r["status"] == "unknown"
    finally:
        w.close()
