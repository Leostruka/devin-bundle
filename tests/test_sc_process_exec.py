"""sc_process.spawn/wait/cancel — bounded one-shot argv execution."""
import json
import os
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_backend  # noqa: E402
import sc_contract as contract  # noqa: E402
import sc_process  # noqa: E402

PY = sys.executable


def py(code):
    return [PY, "-c", code]


def _handle(proc):
    return {"process": proc, "pid": proc.pid, "start_time": 1,
            "owner_request_id": "t",
            "tree": {"kind": "job" if os.name == "nt" else "pg",
                     "job": None, "closed": False},
            "readers": []}


class RecordingSubprocess:
    """Subprocess seam: captures Popen kwargs, delegates to real."""

    PIPE = subprocess.PIPE
    DEVNULL = subprocess.DEVNULL

    def __init__(self):
        self.kwargs = None
        self.proc = None

    def Popen(self, **kwargs):
        self.kwargs = kwargs
        self.proc = subprocess.Popen(**kwargs)
        return self.proc


def test_spawn_rejects_bad_argv():
    for bad in ("ls -l", ("ls", "-l"), [], ["ls", ""], ["a\x00b"],
                [""], [123]):
        with pytest.raises(contract.InvalidRequest):
            sc_process.spawn(bad)


def test_spawn_rejects_bad_numbers():
    for kw in ({"timeout_s": 0}, {"timeout_s": -1}, {"timeout_s": 301},
               {"timeout_s": True}, {"timeout_s": float("nan")},
               {"timeout_s": float("inf")}, {"timeout_s": "5"},
               {"output_limit": 0}, {"output_limit": -1},
               {"output_limit": 1048577}, {"output_limit": True},
               {"output_limit": 1.5}):
        with pytest.raises(contract.InvalidRequest):
            sc_process.spawn(py("pass"), **kw)


def test_spawn_rejects_bad_cwd(tmp_path):
    with pytest.raises(contract.InvalidRequest):
        sc_process.spawn(py("pass"), cwd=str(tmp_path / "missing"))
    f = tmp_path / "f.txt"
    f.write_text("x")
    with pytest.raises(contract.InvalidRequest):
        sc_process.spawn(py("pass"), cwd=str(f))


def test_spawn_rejects_bad_spill_dir(tmp_path):
    with pytest.raises(contract.InvalidRequest):
        sc_process.spawn(py("pass"),
                         spill_dir=str(tmp_path / "missing"))


def test_spawn_never_creates_spill_dir(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(contract.InvalidRequest):
        sc_process.spawn(py("pass"), spill_dir=str(missing))
    assert not missing.exists()


def test_env_secret_keys_rejected():
    for key in ("MY_SECRET", "APP_TOKEN", "PASSWORD", "CREDENTIAL_X",
                "PRIVATE_KEY", "MY_API_KEY", "AUTH", "COOKIE",
                "x_secret_y"):
        with pytest.raises(contract.InvalidRequest,
                           match="environment key"):
            sc_process.spawn(py("pass"), env_allow={key: "x"})


def test_env_bad_shapes_rejected():
    for env in (["x"], {"": "v"}, {"A\x00B": "v"}, {"K": "v\x00x"},
                {"K": 5}, {"K": None}):
        with pytest.raises(contract.InvalidRequest):
            sc_process.spawn(py("pass"), env_allow=env)


def test_env_only_baseline_plus_allow(tmp_path):
    rec = RecordingSubprocess()
    sc_process.spawn(py("pass"), env_allow={"FOO_SAFE": "1"},
                     backend=rec)
    env = rec.kwargs["env"]
    assert env["FOO_SAFE"] == "1"
    assert set(env) <= set(sc_process._ENV_BASELINE) | {"FOO_SAFE"}


def test_spawn_popen_kwargs(tmp_path):
    rec = RecordingSubprocess()
    sc_process.spawn(py("pass"), cwd=str(tmp_path), backend=rec)
    kw = rec.kwargs
    assert kw["shell"] is False
    assert kw["stdin"] is subprocess.DEVNULL
    assert kw["stdout"] is subprocess.PIPE
    assert kw["stderr"] is subprocess.PIPE
    assert kw["args"][0] == PY
    assert Path(kw["cwd"]) == tmp_path.resolve()
    if os.name == "nt":
        assert kw["creationflags"] == (
            subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000004)
    else:
        assert kw["start_new_session"] is True


def test_argv_semicolon_stays_one_argument():
    r = sc_process.spawn(
        [PY, "-c",
         "import json,sys;print(json.dumps(sys.argv[1:]))",
         "a;b", "c&d", "$(whoami)"])
    v = r["value"]
    assert r["ok"] and r["status"] == "dispatched"
    assert json.loads(v["stdout"]["value"]) == ["a;b", "c&d",
                                               "$(whoami)"]


def test_spawn_result_shape():
    r = sc_process.spawn(py(
        "import sys;sys.stdout.write('hi');sys.stderr.write('err')"))
    assert r["ok"] and r["status"] == "dispatched"
    assert r["backend"] == "subprocess"
    assert r["precondition"] == {"argv_only": True,
                               "cwd_verified": True,
                               "environment_sanitized": True}
    assert r["postcondition"] == {"exit_observed": True,
                                "tree_cleanup": True}
    v = r["value"]
    assert v["exit_code"] == 0
    assert v["stdout"] == {"untrusted": True, "value": "hi"}
    assert v["stderr"]["value"] == "err"
    assert v["stdout_bytes"] == 2 and v["stderr_bytes"] == 3
    assert v["stdout_truncated"] is False
    assert v["stderr_truncated"] is False
    assert v["target"]["pid"] > 0
    assert isinstance(v["target"]["start_time"], int)
    assert v["owner_request_id"]
    assert r["evidence"]["spill"] is None
    assert r["evidence"]["dropped"] == 0
    json.dumps(r)  # result must serialize: no runtime objects


def test_spawn_nonzero_exit_maps_unknown():
    r = sc_process.spawn(py("import sys;sys.exit(3)"))
    assert r["ok"] is False and r["status"] == "unknown"
    assert r["error"] == "process exited with code 3"
    assert r["postcondition"]["tree_cleanup"] is True


def test_spawn_timeout_cleans_tree():
    code = ("import subprocess,sys,time;"
            "p=subprocess.Popen([sys.executable,'-c',"
            "'import time;time.sleep(60)']);"
            "print(p.pid,flush=True);time.sleep(60)")
    t0 = time.time()
    r = sc_process.spawn(py(code), timeout_s=1)
    elapsed = time.time() - t0
    assert r["ok"] is False and r["status"] == "timeout"
    assert r["error"] == "process timed out"
    if r["postcondition"]["tree_cleanup"] is not True and os.name != "nt":
        probe = subprocess.run(
            ["ps", "-axo", "pid=,pgid=,stat=,comm="],
            capture_output=True, timeout=10)
        diag = probe.stdout.decode("utf-8", "replace")
        root_pid = r["value"]["target"]["pid"]
        diag = "\n".join(ln for ln in diag.splitlines()
                         if ln.split() and ln.split()[1] == str(root_pid))
        pytest.fail(f"tree_cleanup False; pgid={root_pid} members:\n{diag}\n"
                    f"ps rc={probe.returncode} "
                    f"err={probe.stderr.decode('utf-8','replace')!r}")
    assert elapsed < 30
    gpid = int(r["value"]["stdout"]["value"].strip())
    root = r["value"]["target"]["pid"]
    backend = sc_backend.current()
    deadline = time.time() + 5
    gpid_l = root_l = None
    while time.time() < deadline:
        def _list(p):
            try:
                return backend.process_list(p)
            except LookupError:
                return []
        gpid_l, root_l = _list(gpid), _list(root)
        if not gpid_l and not root_l:
            break
        time.sleep(0.1)
    else:
        group = ""
        if os.name != "nt":
            try:
                group = subprocess.run(
                    ["ps", "-axo", "pid=,pgid=,stat=,comm="],
                    capture_output=True, timeout=10
                ).stdout.decode("utf-8", "replace")
                group = "\n".join(
                    ln for ln in group.splitlines()
                    if str(root) in ln.split()[:2] or str(gpid) in ln.split()[:2])
            except Exception as exc:
                group = f"<ps diag failed: {exc}>"
        pytest.fail(f"owned process tree still alive after timeout: "
                    f"gpid={gpid_l} root={root_l}\ngroup:\n{group}")


def test_spawn_output_flood_spills_combined(tmp_path):
    code = ("import sys;sys.stdout.write('A'*200000);sys.stdout.flush();"
            "sys.stderr.write('B'*200000);sys.stderr.flush()")
    r = sc_process.spawn(py(code), timeout_s=30, output_limit=1000,
                         spill_dir=str(tmp_path))
    v = r["value"]
    assert r["ok"]
    assert v["stdout_truncated"] and v["stderr_truncated"]
    assert v["stdout_bytes"] == 200000 and v["stderr_bytes"] == 200000
    assert v["stdout"]["value"] == "A" * 1000
    assert v["stderr"]["value"] == "B" * 1000
    spill = Path(r["evidence"]["spill"])
    data = spill.read_bytes()
    assert data == (b"=== stdout ===\n" + b"A" * 200000 +
                    b"\n=== stderr ===\n" + b"B" * 200000 + b"\n")
    assert r["evidence"]["dropped"] == 2 * (200000 - 1000)
    leftovers = [p for p in tmp_path.iterdir() if p != spill]
    assert leftovers == []
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(spill).st_mode) == 0o600


def test_spawn_single_stream_spill(tmp_path):
    code = "import sys;sys.stdout.write('A'*50000);sys.stdout.flush()"
    r = sc_process.spawn(py(code), output_limit=1000,
                         spill_dir=str(tmp_path))
    v = r["value"]
    assert v["stdout_truncated"] and not v["stderr_truncated"]
    spill = Path(r["evidence"]["spill"])
    assert spill.read_bytes() == b"A" * 50000


def test_concurrent_drain_no_deadlock():
    # Both pipes flooded far beyond OS pipe capacity: serial drains
    # would deadlock into a timeout.
    code = ("import sys,threading;"
            "t=threading.Thread(target=lambda:"
            " sys.stderr.write('B'*300000));"
            "t.start();sys.stdout.write('A'*300000);"
            "sys.stdout.flush();sys.stderr.flush();t.join()")
    r = sc_process.spawn(py(code), timeout_s=30)
    assert r["ok"]
    assert r["value"]["stdout_bytes"] == 300000
    assert r["value"]["stderr_bytes"] == 300000


def test_wait_timeout_calls_cancel():
    proc = subprocess.Popen(py("import time;time.sleep(30)"))
    h = _handle(proc)
    r = sc_process.wait(h, timeout_s=0.2)
    assert r["timed_out"] is True
    assert proc.returncode is not None
    assert h["tree"]["closed"] is True


def test_wait_normal_exit_cleans_tree():
    proc = subprocess.Popen(py("pass"))
    h = _handle(proc)
    r = sc_process.wait(h, timeout_s=10)
    assert r["timed_out"] is False
    assert r["exit_code"] == 0
    assert h["tree"]["closed"] is True


def test_cancel_reaps_and_is_idempotent():
    proc = subprocess.Popen(py("import time;time.sleep(30)"))
    h = _handle(proc)
    r = sc_process.cancel(h)
    assert r == {"tree_cleanup": True, "exit_observed": True}
    assert proc.returncode is not None
    r2 = sc_process.cancel(h)
    assert r2 == {"tree_cleanup": True, "exit_observed": True}


def test_cancel_grace_bounds():
    proc = subprocess.Popen(py("pass"), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        for bad in (-1, -0.5, 31, True, float("nan"), "x"):
            with pytest.raises(contract.InvalidRequest):
                sc_process.cancel(_handle(proc), grace_s=bad)
        proc.wait()
        for good in (0, 30):
            r = sc_process.cancel(_handle(proc), grace_s=good)
            assert r["tree_cleanup"] is True
    finally:
        proc.wait()


def test_spawn_wait_failure_reaps_child():
    class WaitBoom:
        def __init__(self, real):
            self._r = real

        def __getattr__(self, name):
            return getattr(self._r, name)

        def wait(self, timeout=None):
            raise RuntimeError("wait boom")

    rec = RecordingSubprocess()
    real_popen = rec.Popen

    def wrap(**kw):
        p = real_popen(**kw)
        rec.proc = WaitBoom(p)
        return rec.proc

    rec.Popen = wrap
    with pytest.raises(RuntimeError, match="wait boom"):
        sc_process.spawn(py("import time;time.sleep(30)"),
                         backend=rec)
    assert rec.proc._r.poll() is not None  # child killed and reaped


def test_spawn_reader_start_failure_reaps_child(monkeypatch):
    real_thread = threading.Thread
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("thread boom")
        return real_thread(*a, **k)

    monkeypatch.setattr(sc_process.threading, "Thread", flaky)
    rec = RecordingSubprocess()
    with pytest.raises(RuntimeError, match="thread boom"):
        sc_process.spawn(py("import time;time.sleep(30)"),
                         backend=rec)
    assert rec.proc.poll() is not None


def test_spawn_thread_start_failure_reaps_child(monkeypatch):
    real_start = threading.Thread.start
    calls = {"n": 0}

    def flaky(self):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("start boom")
        return real_start(self)

    monkeypatch.setattr(sc_process.threading.Thread, "start", flaky)
    rec = RecordingSubprocess()
    with pytest.raises(RuntimeError, match="start boom"):
        sc_process.spawn(py("import time;time.sleep(30)"),
                         backend=rec)
    assert rec.proc.poll() is not None


def test_reader_spill_close_error_marks_incomplete(tmp_path,
                                                 monkeypatch):
    real_open = sc_process._open_spill

    class BadClose:
        def __init__(self, fh):
            self._fh = fh

        def write(self, data):
            return self._fh.write(data)

        def close(self):
            self._fh.close()
            raise OSError("close boom")

    def bad_open(state):
        real_open(state)
        state["spill_fh"] = BadClose(state["spill_fh"])

    monkeypatch.setattr(sc_process, "_open_spill", bad_open)
    r = sc_process.spawn(
        py("import sys;sys.stdout.write('A'*5000);sys.stdout.flush()"),
        output_limit=100, spill_dir=str(tmp_path))
    assert r["ok"] is False and r["status"] == "unknown"
    assert r["error"] == "output capture incomplete"
    assert r["postcondition"]["tree_cleanup"] is True


def test_finalize_combine_failure_cleans_all(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise OSError("combine boom")

    monkeypatch.setattr(sc_process.shutil, "copyfileobj", boom)
    rec = RecordingSubprocess()
    code = ("import sys;sys.stdout.write('A'*5000);sys.stdout.flush();"
            "sys.stderr.write('B'*5000);sys.stderr.flush()")
    with pytest.raises(OSError, match="combine boom"):
        sc_process.spawn(py(code), output_limit=100,
                         spill_dir=str(tmp_path), backend=rec)
    assert list(tmp_path.iterdir()) == []
    assert rec.proc.poll() is not None


def test_reader_failure_still_cleans_tree(monkeypatch):
    def boom(stream, state):
        state["error"] = RuntimeError("reader died")

    monkeypatch.setattr(sc_process, "_reader_run", boom)
    rec = RecordingSubprocess()
    r = sc_process.spawn(py("import time;time.sleep(60)"),
                         timeout_s=1, backend=rec)
    assert r["ok"] is False and r["status"] == "timeout"
    assert r["postcondition"]["tree_cleanup"] is True
    assert rec.proc.poll() is not None


class _FakeK32:
    def __init__(self, terminate=1, close=1):
        self.terminate = terminate
        self.close = close
        self.calls = []

    def TerminateJobObject(self, job, code):
        self.calls.append("terminate")
        return self.terminate

    def CloseHandle(self, job):
        self.calls.append("close")
        return self.close


@pytest.mark.skipif(os.name != "nt", reason="Win32 seam")
def test_tree_cleanup_close_failure_false(monkeypatch):
    proc = subprocess.Popen(py("pass"), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    h = _handle(proc)
    h["tree"]["job"] = 4321
    fake = _FakeK32(terminate=0, close=0)
    monkeypatch.setattr(sc_process, "_kernel32", lambda: fake)
    r = sc_process.cancel(h)
    assert r["tree_cleanup"] is False
    assert proc.returncode is not None  # root still reaped
    assert "closed" not in h["tree"] or not h["tree"]["closed"]
    # idempotent: cached result, no re-attempt
    r2 = sc_process.cancel(h)
    assert r2["tree_cleanup"] is False
    assert fake.calls == ["terminate", "close"]


@pytest.mark.skipif(os.name != "nt", reason="Win32 seam")
def test_tree_cleanup_failed_terminate_recovered_by_close(
        monkeypatch):
    proc = subprocess.Popen(py("pass"), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    h = _handle(proc)
    h["tree"]["job"] = 4321
    fake = _FakeK32(terminate=0, close=1)
    monkeypatch.setattr(sc_process, "_kernel32", lambda: fake)
    r = sc_process.cancel(h)
    assert r["tree_cleanup"] is True
    assert h["tree"]["closed"] is True


def test_tree_cleanup_root_reap_failure_false():
    class Zombie:
        pid = 999999
        returncode = None

        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired(["x"], timeout or 0)

        def kill(self):
            pass

    h = {"process": Zombie(), "pid": 999999, "start_time": 1,
         "owner_request_id": "t",
         "tree": {"kind": "pg" if os.name != "nt" else "job",
                  "job": None, "closed": False},
         "readers": []}
    r = sc_process.cancel(h, grace_s=0)
    assert r["tree_cleanup"] is False
    assert r["exit_observed"] is False


def test_env_values_never_in_result(tmp_path):
    rec = RecordingSubprocess()
    r = sc_process.spawn(py("print('done')"),
                         env_allow={"VISIBLE": "s3cr3t-value"},
                         backend=rec)
    assert r["ok"]
    assert "s3cr3t-value" not in json.dumps(r)
