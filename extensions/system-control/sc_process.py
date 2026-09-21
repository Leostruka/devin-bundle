"""Process inventory plus bounded one-shot argv execution.

spawn() owns the child: argv only, shell=False, DEVNULL stdin,
baseline-only environment, validated cwd, concurrent bounded output
drain with owner-only spill, timeout that cleans the whole process
tree (Windows Job Object / POSIX process group). Nothing persists
between calls; persistent sessions are a later task.
"""

import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

import sc_backend
import sc_contract as contract

if os.name == "posix":
    import signal

_CHUNK = 65536
_JOIN_TIMEOUT_S = 10
_TIMEOUT_S_MAX = 300
_GRACE_S_MAX = 30
_OUTPUT_LIMIT_MAX = 1048576

_ENV_BASELINE = (
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "LANG", "LC_ALL", "TMPDIR",
)
_ENV_SECRET = re.compile(
    r"(^|_)(SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE_KEY"
    r"|API_KEY|AUTH|COOKIE)($|_)",
    re.IGNORECASE)


def snapshot(*, pid=None, limit=100, backend=None) -> dict:
    """Bounded process list wrapped in the result envelope."""
    b = backend if backend is not None else sc_backend.current()
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        raise contract.InvalidRequest("limit must be an integer")
    if lim < 0:
        raise contract.InvalidRequest("limit must be non-negative")
    items = list(b.process_list(pid))[:lim]
    return contract.result(
        ok=True, status="verified",
        request_id=uuid.uuid4().hex[:12],
        backend=sc_backend.backend_name(b), value=items)


def _valid_argv(argv):
    if not isinstance(argv, list) or not argv:
        raise contract.InvalidRequest(
            "argv must be a non-empty list")
    for item in argv:
        if (not isinstance(item, str) or not item
                or "\x00" in item):
            raise contract.InvalidRequest(
                "argv items must be non-empty strings without NUL")
    return list(argv)


def _valid_num(value, name, lo, hi, integer=False,
               inclusive_lo=False):
    if isinstance(value, bool):
        raise contract.InvalidRequest(f"{name} must be a number")
    if integer:
        ok = isinstance(value, int)
    else:
        ok = (isinstance(value, (int, float))
              and math.isfinite(value))
    if not ok or (inclusive_lo and value < lo) \
            or (not inclusive_lo and value <= lo) or value > hi:
        raise contract.InvalidRequest(
            f"{name} must be in "
            f"{'[' if inclusive_lo else '('}{lo}, {hi}]")
    return value


def _valid_dir(value, name):
    try:
        p = Path(value).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as exc:
        raise contract.InvalidRequest(f"{name} does not resolve: {exc}")
    if not p.is_dir():
        raise contract.InvalidRequest(f"{name} is not a directory")
    return p


def _safe_env(env_allow):
    if env_allow is None:
        env_allow = {}
    if not isinstance(env_allow, dict):
        raise contract.InvalidRequest("environment key is not allowed")
    env = {k: os.environ[k] for k in _ENV_BASELINE if k in os.environ}
    for key, val in env_allow.items():
        if (not isinstance(key, str) or not key or "\x00" in key
                or _ENV_SECRET.search(key)
                or not isinstance(val, str) or "\x00" in val):
            raise contract.InvalidRequest(
                "environment key is not allowed")
        env[key] = val
    return env


# --- Windows Job Object ownership -----------------------------------

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _KILL_ON_CLOSE = 0x00002000
    _EXT_LIMIT_INFO = 9  # JobObjectExtendedLimitInformation

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in (
            "ReadOperationCount", "WriteOperationCount",
            "OtherOperationCount", "ReadTransferCount",
            "WriteTransferCount", "OtherTransferCount")]

    class _BASIC_LIMIT(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD)]

    class _EXT_LIMIT(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BASIC_LIMIT),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t)]

    _k32 = None

    def _kernel32():
        global _k32
        if _k32 is None:
            k32 = ctypes.windll.kernel32
            k32.CreateJobObjectW.restype = wintypes.HANDLE
            k32.CreateJobObjectW.argtypes = [
                wintypes.LPVOID, wintypes.LPCWSTR]
            k32.SetInformationJobObject.restype = wintypes.BOOL
            k32.SetInformationJobObject.argtypes = [
                wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                wintypes.DWORD]
            k32.AssignProcessToJobObject.restype = wintypes.BOOL
            k32.AssignProcessToJobObject.argtypes = [
                wintypes.HANDLE, wintypes.HANDLE]
            k32.TerminateJobObject.restype = wintypes.BOOL
            k32.TerminateJobObject.argtypes = [
                wintypes.HANDLE, wintypes.UINT]
            k32.CloseHandle.restype = wintypes.BOOL
            k32.CloseHandle.argtypes = [wintypes.HANDLE]
            _k32 = k32
        return _k32

    def _create_job():
        """New KILL_ON_JOB_CLOSE job object handle; raise on failure."""
        k32 = _kernel32()
        job = k32.CreateJobObjectW(None, None)
        if not job:
            raise RuntimeError("CreateJobObjectW failed")
        try:
            info = _EXT_LIMIT()
            info.BasicLimitInformation.LimitFlags = _KILL_ON_CLOSE
            if not k32.SetInformationJobObject(
                    job, _EXT_LIMIT_INFO, ctypes.byref(info),
                    ctypes.sizeof(info)):
                raise RuntimeError("SetInformationJobObject failed")
        except BaseException:
            k32.CloseHandle(job)
            raise
        return job

    def _job_assign(proc):
        """Assign proc to a KILL_ON_JOB_CLOSE job; raise on failure."""
        job = _create_job()
        try:
            handle = getattr(proc, "_handle", None)
            if handle is None:
                raise RuntimeError("process handle unavailable")
            if not _kernel32().AssignProcessToJobObject(
                    job, wintypes.HANDLE(int(handle))):
                raise RuntimeError("AssignProcessToJobObject failed")
        except BaseException:
            _kernel32().CloseHandle(job)
            raise
        return job


def _assign_tree(proc):
    """Bind the child to a tree owner: Job Object or process group."""
    if os.name == "nt":
        return {"kind": "job", "job": _job_assign(proc),
                "closed": False}
    return {"kind": "pg", "job": None, "closed": False}


def _reap_root(proc, grace_s) -> bool:
    """Wait for the root, escalating to kill; true iff reaped."""
    try:
        proc.wait(timeout=max(grace_s, 5))
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
    return proc.returncode is not None


def _posix_group_has_live_member(pgid):
    """True while the group has a non-zombie member. killpg(pgid, 0)
    keeps succeeding while only zombies remain (macOS reaps reparented
    zombies on launchd's schedule), so membership is checked by state."""
    try:
        out = subprocess.run(["ps", "-axo", "pgid=,stat="],
                             capture_output=True, timeout=10)
    except Exception:
        return True  # unknown: fail closed
    if out.returncode != 0:
        return True
    for line in out.stdout.decode("utf-8", "replace").splitlines():
        f = line.split()
        if (len(f) >= 2 and f[0].isdigit() and int(f[0]) == pgid
                and not f[1].startswith("Z")):
            return True
    return False


def _reap_posix_group(proc, grace_s) -> bool:
    """TERM → grace → KILL the process group; verify absence."""
    ok = True
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError:
        ok = False
    try:
        proc.wait(timeout=grace_s)
    except Exception:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        ok = False
    if not _reap_root(proc, grace_s):
        ok = False
    if ok:
        deadline = time.time() + 5
        while True:
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                break  # group fully gone
            except OSError:
                ok = False
                break
            if not _posix_group_has_live_member(proc.pid):
                break  # only zombie members left
            if time.time() >= deadline:
                ok = False
                break
            time.sleep(0.05)
    return ok


def _reap_tree(handle, grace_s) -> bool:
    """Terminate the owned tree and reap the root.

    Returns the truthful outcome; the first result is cached on the
    tree dict so repeat calls are idempotent.
    """
    tree = handle["tree"]
    if "cleanup" in tree:
        return tree["cleanup"]
    proc = handle["process"]
    ok = True
    if os.name == "nt":
        job = tree.get("job")
        if job is not None:
            try:
                _kernel32().TerminateJobObject(job, 1)
            except Exception:
                pass  # KILL_ON_JOB_CLOSE still applies at close
        ok = _reap_root(proc, grace_s)
        if job is not None:
            try:
                closed = bool(_kernel32().CloseHandle(job))
            except Exception:
                closed = False
            if closed:
                tree["closed"] = True
            else:
                ok = False
        else:
            tree["closed"] = ok
    else:
        ok = _reap_posix_group(proc, grace_s)
        tree["closed"] = ok
    tree["cleanup"] = ok
    return ok


# --- bounded output readers -----------------------------------------

def _unlink_retry(path, attempts=5):
    """Best-effort bounded unlink; true when the path is gone."""
    for attempt in range(attempts):
        try:
            os.unlink(path)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            if attempt + 1 == attempts:
                return False
            time.sleep(0.01)
    return False


def _open_spill(state):
    fd, path = tempfile.mkstemp(dir=str(state["spill_dir"]),
                                prefix=state["spill_name"])
    try:
        state["spill_fh"] = os.fdopen(fd, "wb")
    except Exception:
        os.close(fd)
        raise
    state["spill_path"] = path


def _reader_run(stream, state):
    try:
        while True:
            chunk = stream.read(_CHUNK)
            if not chunk:
                break
            state["total"] += len(chunk)
            state["tail"] += chunk
            if state["total"] > state["limit"]:
                fh = state["spill_fh"]
                if fh is None:
                    _open_spill(state)
                    fh = state["spill_fh"]
                    fh.write(state["tail"])  # all bytes seen so far
                else:
                    fh.write(chunk)
                over = len(state["tail"]) - state["limit"]
                if over > 0:
                    del state["tail"][:over]
    except Exception as exc:
        state["error"] = exc
    finally:
        try:
            stream.close()
        except Exception:
            pass
        if state["spill_fh"] is not None:
            try:
                state["spill_fh"].close()
            except Exception as exc:
                if state["error"] is None:
                    state["error"] = exc


def _start_readers(proc, limit, spill_dir, out):
    """Start one drain thread per stream into `out` (the handle's
    reader list). States are appended before start so a later failure
    leaves partial readers visible to cleanup."""
    for stream, name in ((proc.stdout, "sc-stdout-"),
                         (proc.stderr, "sc-stderr-")):
        state = {"total": 0, "tail": bytearray(), "limit": limit,
                 "spill_dir": spill_dir, "spill_name": name,
                 "spill_fh": None, "spill_path": None, "error": None,
                 "thread": None, "stream": stream, "started": False}
        out.append(state)
        try:
            t = threading.Thread(target=_reader_run,
                                 args=(stream, state), daemon=True)
            state["thread"] = t
            t.start()
            state["started"] = True
        except BaseException:
            try:
                stream.close()
            except Exception:
                pass
            raise


def _join_reader(r) -> bool:
    """Bounded join; on timeout close the stream and re-join once.
    True iff the thread finished. A thread whose start failed is
    never joined."""
    t = r.get("thread")
    if t is None or not r.get("started"):
        return True
    t.join(timeout=_JOIN_TIMEOUT_S)
    if t.is_alive():
        try:
            r["stream"].close()
        except Exception:
            pass
        t.join(timeout=_JOIN_TIMEOUT_S)
    return not t.is_alive()


def _finalize_spill(readers, spill_dir):
    """Combine spilled streams into one owner-only file.

    On any failure the partial combined file and both intermediate
    stream files are deleted before re-raising; an intermediate that
    cannot be removed fails finalization rather than leaving residue.
    """
    spilled = [r["spill_path"] for r in readers if r["spill_path"]]
    if not spilled:
        return None
    if len(spilled) == 1:
        return spilled[0]
    fd, combined = tempfile.mkstemp(dir=str(spill_dir),
                                    prefix="sc-exec-")
    try:
        try:
            out = os.fdopen(fd, "wb")
        except Exception:
            os.close(fd)
            raise
        with out:
            for header, r in zip(
                    (b"=== stdout ===\n", b"=== stderr ===\n"),
                    readers):
                out.write(header)
                with open(r["spill_path"], "rb") as fh:
                    shutil.copyfileobj(fh, out)
                out.write(b"\n")
        for path in spilled:
            if not _unlink_retry(path):
                raise OSError(
                    f"failed to remove intermediate spill: {path}")
        return combined
    except BaseException:
        _unlink_retry(combined)
        for path in spilled:
            _unlink_retry(path)
        raise


# --- public seams ----------------------------------------------------

def validate_spawn(argv, *, cwd=None, env_allow=None, timeout_s=30,
                   output_limit=16000, spill_dir=None) -> dict:
    """Pure validation/normalization for spawn arguments.

    No Popen, no mutation. Returns normalized values (env mapping is
    for spawn internals only — never serialize it to callers).
    """
    return {
        "argv": _valid_argv(argv),
        "cwd": (_valid_dir(cwd, "cwd") if cwd is not None else None),
        "env": _safe_env(env_allow),
        "timeout_s": _valid_num(timeout_s, "timeout_s", 0,
                                _TIMEOUT_S_MAX),
        "output_limit": _valid_num(output_limit, "output_limit", 0,
                                   _OUTPUT_LIMIT_MAX, integer=True),
        "spill_dir": _valid_dir(
            spill_dir if spill_dir is not None
            else tempfile.gettempdir(), "spill_dir"),
    }


def spawn(argv: list, *, cwd=None, env_allow=None, timeout_s=30,
          output_limit=16000, spill_dir=None, backend=None) -> dict:
    """Bounded one-shot argv execution; owns the process tree."""
    be = backend if backend is not None else subprocess
    v = validate_spawn(argv, cwd=cwd, env_allow=env_allow,
                       timeout_s=timeout_s, output_limit=output_limit,
                       spill_dir=spill_dir)
    argv = v["argv"]
    timeout_s = v["timeout_s"]
    output_limit = v["output_limit"]
    cwd_p = v["cwd"]
    spill = v["spill_dir"]
    env = v["env"]
    owner_request_id = uuid.uuid4().hex[:12]
    started_at = time.time()
    start_ns = time.time_ns()
    kwargs = {"args": argv,
              "cwd": str(cwd_p) if cwd_p is not None else None,
              "env": env, "stdin": be.DEVNULL,
              "stdout": be.PIPE, "stderr": be.PIPE,
              "shell": False, "bufsize": 0}
    if os.name == "nt":
        # CREATE_SUSPENDED (0x4, not exported by the subprocess module)
        # closes the spawn->job-assign race: the child cannot run (or
        # spawn grandchildren) before the job owns it.
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                   | 0x00000004)
    else:
        kwargs["start_new_session"] = True
    proc = be.Popen(**kwargs)
    try:
        tree = _assign_tree(proc)
    except BaseException:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        raise
    if os.name == "nt":
        try:
            import sc_windows
            sc_windows.resume_main_thread(proc.pid)
        except BaseException:
            # Suspended proc is still killable; drop the job too so
            # nothing owns a dead tree. Original exception preserved.
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            job = tree.get("job")
            if job is not None:
                try:
                    _kernel32().TerminateJobObject(job, 1)
                except Exception:
                    pass
                try:
                    _kernel32().CloseHandle(job)
                except Exception:
                    pass
                tree["closed"] = True
            raise
    handle = {"process": proc, "pid": proc.pid, "start_time": start_ns,
              "owner_request_id": owner_request_id, "tree": tree,
              "readers": []}
    spill_path = None
    try:
        _start_readers(proc, output_limit, spill, handle["readers"])
        outcome = wait(handle, timeout_s=timeout_s, backend=be)
        out_r, err_r = handle["readers"]
        spill_path = _finalize_spill(handle["readers"], spill)
        dropped = ((out_r["total"] - len(out_r["tail"]))
                   + (err_r["total"] - len(err_r["tail"])))
        rc = outcome["exit_code"]
        return _spawn_result(
            ok_status=_outcome_status(outcome, out_r, err_r, rc),
            request_id=owner_request_id, proc=proc, start_ns=start_ns,
            started_at=started_at, outcome=outcome, out_r=out_r,
            err_r=err_r, output_limit=output_limit,
            spill_path=spill_path, dropped=dropped)
    except BaseException:
        try:
            _reap_tree(handle, 2)
        except Exception:
            pass
        for stream in (proc.stdout, proc.stderr):
            try:
                stream.close()
            except Exception:
                pass
        for r in handle["readers"]:
            _join_reader(r)
        for r in handle["readers"]:
            if r.get("spill_path"):
                _unlink_retry(r["spill_path"])
        if spill_path:
            _unlink_retry(spill_path)
        raise


def _outcome_status(outcome, out_r, err_r, rc):
    if outcome["timed_out"]:
        return False, "timeout", "process timed out"
    if (not outcome["eof_observed"] or out_r["error"]
            or err_r["error"]):
        return False, "unknown", "output capture incomplete"
    if rc == 0:
        return True, "dispatched", None
    return False, "unknown", f"process exited with code {rc}"


def _spawn_result(*, ok_status, request_id, proc, start_ns, started_at,
                  outcome, out_r, err_r, output_limit, spill_path,
                  dropped):
    ok, status, error = ok_status
    value = {
        "target": {"pid": proc.pid, "start_time": start_ns},
        "owner_request_id": request_id,
        "exit_code": outcome["exit_code"],
        "started_at": started_at,
        "ended_at": outcome["ended_at"],
        "stdout": contract.untrusted(
            bytes(out_r["tail"]).decode("utf-8", "replace")),
        "stderr": contract.untrusted(
            bytes(err_r["tail"]).decode("utf-8", "replace")),
        "stdout_bytes": out_r["total"],
        "stderr_bytes": err_r["total"],
        "stdout_truncated": out_r["total"] > output_limit,
        "stderr_truncated": err_r["total"] > output_limit,
    }
    postcondition = {"exit_observed": outcome["exit_observed"],
                     "tree_cleanup": outcome["tree_cleanup"]}
    precondition = {"argv_only": True, "cwd_verified": True,
                    "environment_sanitized": True}
    return contract.result(
        ok=ok, status=status, request_id=request_id,
        backend="subprocess", precondition=precondition, value=value,
        postcondition=postcondition, spill=spill_path,
        dropped=dropped, error=error)


def wait(handle: dict, *, timeout_s=30, backend=None) -> dict:
    """Wait for the root; on timeout cancel the tree, then drain."""
    _valid_num(timeout_s, "timeout_s", 0, _TIMEOUT_S_MAX)
    proc = handle["process"]
    try:
        proc.wait(timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
    if timed_out:
        outcome = cancel(handle, backend=backend)
    else:
        cleaned = _reap_tree(handle, 0)
        outcome = {"tree_cleanup": cleaned,
                   "exit_observed": proc.returncode is not None}
    eof = True
    for r in handle["readers"]:
        if not _join_reader(r):
            eof = False
    return {"timed_out": timed_out, "exit_code": proc.returncode,
            "ended_at": time.time(), "eof_observed": eof,
            "tree_cleanup": outcome["tree_cleanup"],
            "exit_observed": outcome["exit_observed"]}


def cancel(handle: dict, *, grace_s=2, backend=None) -> dict:
    """Terminate the owned tree via its handle, never by PID lookup."""
    _valid_num(grace_s, "grace_s", 0, _GRACE_S_MAX, inclusive_lo=True)
    cleaned = _reap_tree(handle, grace_s)
    return {"tree_cleanup": cleaned,
            "exit_observed":
                handle["process"].returncode is not None}
