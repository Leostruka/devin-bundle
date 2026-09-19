"""Native Windows adapter: ctypes Win32 process/service control.

stdlib + ctypes only. Every Win32 handle opened here is closed in a
finally. spawn_owned is fail-closed: any failure between CreateProcessW
and ResumeThread terminates the suspended child and closes all handles.
"""

import math
import os
import re
import subprocess
import time

import sc_contract as contract
from sc_backend import BackendUnavailable

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

_SERVICE_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")
_EPOCH_DELTA_100NS = 116444736000000000

_QUERY_LIMITED = 0x1000
_SYNCHRONIZE = 0x00100000
_CREATE_SUSPENDED = 0x00000004
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102
_WAIT_FAILED = 0xFFFFFFFF
_THREAD_SUSPEND_RESUME = 0x0002
_TH32CS_SNAPTHREAD = 0x00000004
_INVALID_HANDLE = -1

_SC_MANAGER_CONNECT = 0x0001
_SERVICE_QUERY_STATUS = 0x0004
_SERVICE_START = 0x0010
_SERVICE_STOP = 0x0020
_SERVICE_CONTROL_STOP = 1
_SC_STATUS_PROCESS_INFO = 0
_ERROR_SERVICE_NOT_ACTIVE = 1062
_ERROR_ACCESS_DENIED = 5
_ERROR_INVALID_PARAMETER = 87
_ERROR_SERVICE_DOES_NOT_EXIST = 1060

_SERVICE_STATES = {
    1: "stopped", 2: "start_pending", 3: "stop_pending",
    4: "running", 5: "continue_pending", 6: "pause_pending",
    7: "paused",
}

_SVC_WAIT_S = 30.0
_SVC_POLL_S = 0.25

if os.name == "nt":

    class THREADENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", ctypes.c_long),
            ("tpDeltaPri", ctypes.c_long),
            ("dwFlags", wintypes.DWORD)]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", wintypes.LPVOID),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD)]

    class SERVICE_STATUS_PROCESS(ctypes.Structure):
        _fields_ = [
            ("dwServiceType", wintypes.DWORD),
            ("dwCurrentState", wintypes.DWORD),
            ("dwControlsAccepted", wintypes.DWORD),
            ("dwWin32ExitCode", wintypes.DWORD),
            ("dwServiceSpecificExitCode", wintypes.DWORD),
            ("dwCheckPoint", wintypes.DWORD),
            ("dwWaitHint", wintypes.DWORD)]

    _k32 = None
    _adv = None

    def _kernel32():
        global _k32
        if _k32 is None:
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.OpenProcess.restype = wintypes.HANDLE
            k32.OpenProcess.argtypes = [
                wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            k32.GetProcessTimes.restype = wintypes.BOOL
            k32.GetProcessTimes.argtypes = [
                wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
            k32.QueryFullProcessImageNameW.restype = wintypes.BOOL
            k32.QueryFullProcessImageNameW.argtypes = [
                wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                ctypes.POINTER(wintypes.DWORD)]
            k32.WaitForSingleObject.restype = wintypes.DWORD
            k32.WaitForSingleObject.argtypes = [
                wintypes.HANDLE, wintypes.DWORD]
            k32.GetExitCodeProcess.restype = wintypes.BOOL
            k32.GetExitCodeProcess.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            k32.CloseHandle.restype = wintypes.BOOL
            k32.CloseHandle.argtypes = [wintypes.HANDLE]
            k32.TerminateProcess.restype = wintypes.BOOL
            k32.TerminateProcess.argtypes = [wintypes.HANDLE,
                                             wintypes.UINT]
            k32.CreateProcessW.restype = wintypes.BOOL
            k32.CreateProcessW.argtypes = [
                wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.LPVOID,
                wintypes.LPVOID, wintypes.BOOL, wintypes.DWORD,
                wintypes.LPVOID, wintypes.LPCWSTR,
                ctypes.POINTER(STARTUPINFOW),
                ctypes.POINTER(PROCESS_INFORMATION)]
            k32.ResumeThread.restype = wintypes.DWORD
            k32.ResumeThread.argtypes = [wintypes.HANDLE]
            k32.OpenThread.restype = wintypes.HANDLE
            k32.OpenThread.argtypes = [
                wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
            k32.CreateToolhelp32Snapshot.argtypes = [
                wintypes.DWORD, wintypes.DWORD]
            k32.Thread32First.restype = wintypes.BOOL
            k32.Thread32First.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
            k32.Thread32Next.restype = wintypes.BOOL
            k32.Thread32Next.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
            k32.AssignProcessToJobObject.restype = wintypes.BOOL
            k32.AssignProcessToJobObject.argtypes = [
                wintypes.HANDLE, wintypes.HANDLE]
            _k32 = k32
        return _k32

    def _advapi32():
        global _adv
        if _adv is None:
            adv = ctypes.WinDLL("advapi32", use_last_error=True)
            adv.OpenSCManagerW.restype = wintypes.HANDLE
            adv.OpenSCManagerW.argtypes = [
                wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
            adv.OpenServiceW.restype = wintypes.HANDLE
            adv.OpenServiceW.argtypes = [
                wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
            adv.CloseServiceHandle.restype = wintypes.BOOL
            adv.CloseServiceHandle.argtypes = [wintypes.HANDLE]
            adv.QueryServiceStatusEx.restype = wintypes.BOOL
            adv.QueryServiceStatusEx.argtypes = [
                wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
            adv.ControlService.restype = wintypes.BOOL
            adv.ControlService.argtypes = [
                wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID]
            adv.StartServiceW.restype = wintypes.BOOL
            adv.StartServiceW.argtypes = [
                wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID]
            _adv = adv
        return _adv


def _require_nt():
    if os.name != "nt":
        raise BackendUnavailable("sc_windows requires Windows")


def _filetime_epoch(ft):
    raw = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return (raw - _EPOCH_DELTA_100NS) // 10_000_000


def _pid(value):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise contract.InvalidRequest("pid must be an integer")
    if isinstance(value, bool) or v < 0:
        raise contract.InvalidRequest("pid must be a non-negative int")
    return v


def _open_process(pid, access):
    h = _kernel32().OpenProcess(access, False, pid)
    if not h:
        err = ctypes.get_last_error()
        if err == _ERROR_ACCESS_DENIED:
            raise PermissionError(f"access denied: pid {pid}")
        raise LookupError(f"process not found: {pid}")
    return h


def _creation_time(handle):
    times = (wintypes.FILETIME * 4)()
    if not _kernel32().GetProcessTimes(
            handle, *[ctypes.byref(t) for t in times]):
        raise LookupError("GetProcessTimes failed")
    return _filetime_epoch(times[0])


def _image_name(handle):
    k32 = _kernel32()
    size = wintypes.DWORD(32768)
    buf = ctypes.create_unicode_buffer(size.value)
    if k32.QueryFullProcessImageNameW(
            handle, 0, buf, ctypes.byref(size)):
        return buf.value
    return None


def process_get(pid, start_time=None):
    """{pid, start_time, name} for a live pid; LookupError otherwise.

    A non-None start_time that differs from the live creation time is
    a stale (reused) pid identity -> LookupError("stale pid identity").
    """
    _require_nt()
    pid = _pid(pid)
    if start_time is not None:
        try:
            start_time = int(start_time)
        except (TypeError, ValueError):
            raise contract.InvalidRequest(
                "start_time must be an integer")
        if start_time < 0:
            raise contract.InvalidRequest(
                "start_time must be non-negative")
    h = _open_process(pid, _QUERY_LIMITED)
    try:
        created = _creation_time(h)
        if start_time is not None and created != start_time:
            raise LookupError("stale pid identity")
        return {"pid": pid, "start_time": created,
                "name": _image_name(h)}
    finally:
        _kernel32().CloseHandle(h)


def wait_process(identity, timeout_s):
    """Handle-wait on a verified identity; never pid polling."""
    _require_nt()
    if not isinstance(identity, dict):
        raise contract.InvalidRequest("identity must be an object")
    pid = _pid(identity.get("pid"))
    start_time = identity.get("start_time")
    try:
        timeout_s = float(timeout_s)
    except (TypeError, ValueError):
        raise contract.InvalidRequest("timeout_s must be a number")
    if not math.isfinite(timeout_s) or timeout_s < 0:
        raise contract.InvalidRequest(
            "timeout_s must be a non-negative finite number")
    k32 = _kernel32()
    h = k32.OpenProcess(_QUERY_LIMITED | _SYNCHRONIZE, False, pid)
    if not h:
        err = ctypes.get_last_error()
        if err == _ERROR_ACCESS_DENIED:
            return {"ok": False, "status": "rejected",
                    "error": f"access denied: pid {pid}"}
        return {"ok": False, "status": "rejected",
                "error": f"process not found: {pid}"}
    try:
        # PID-reuse guard BEFORE waiting.
        if _creation_time(h) != start_time:
            return {"ok": False, "status": "rejected",
                    "error": "stale pid identity"}
        ms = min(int(timeout_s * 1000), 0xFFFFFFFE)
        rc = k32.WaitForSingleObject(h, ms)
        if rc == _WAIT_TIMEOUT:
            return {"ok": False, "status": "timeout"}
        if rc != _WAIT_OBJECT_0:
            return {"ok": False, "status": "unknown",
                    "error": f"WaitForSingleObject: {rc}"}
        code = wintypes.DWORD(0)
        if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
            return {"ok": False, "status": "unknown",
                    "error": "GetExitCodeProcess failed"}
        return {"ok": True, "exit_code": int(code.value)}
    finally:
        k32.CloseHandle(h)


def _create_process(argv, cwd=None):
    """CreateProcessW CREATE_SUSPENDED; caller owns both handles.

    Returns {"pid", "start_time", "process", "thread"}; on failure the
    process/thread handles are already closed — nothing leaks.
    """
    _require_nt()
    k32 = _kernel32()
    cmdline = subprocess.list2cmdline(list(argv))
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    buf = ctypes.create_unicode_buffer(cmdline)
    ok = k32.CreateProcessW(
        None, buf, None, None, False, _CREATE_SUSPENDED, None,
        str(cwd) if cwd is not None else None,
        ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        raise RuntimeError(
            f"CreateProcessW failed: "
            f"{ctypes.WinError(ctypes.get_last_error())}")
    try:
        return {"pid": int(pi.dwProcessId),
                "start_time": _creation_time(pi.hProcess),
                "process": int(pi.hProcess),
                "thread": int(pi.hThread)}
    except BaseException:
        k32.TerminateProcess(pi.hProcess, 1)
        k32.CloseHandle(pi.hThread)
        k32.CloseHandle(pi.hProcess)
        raise


def _terminate_process(proc):
    """Best-effort terminate + close for a _create_process result."""
    k32 = _kernel32()
    try:
        k32.TerminateProcess(wintypes.HANDLE(proc["process"]), 1)
    except Exception:
        pass
    try:
        k32.WaitForSingleObject(
            wintypes.HANDLE(proc["process"]), 5000)
    except Exception:
        pass
    for key in ("thread", "process"):
        h = proc.get(key)
        if h:
            try:
                k32.CloseHandle(wintypes.HANDLE(h))
            except Exception:
                pass
            # Clear so spawn_owned's finally cannot double-close a
            # handle value that may have been reused.
            proc[key] = None


def spawn_owned(argv, *, cwd=None):
    """Race-free owned spawn: suspended -> job assign -> resume.

    Returns {"ok", "pid", "start_time", "job", "process"}. The caller
    owns the job and process handles and must call close_owned.
    Fail-closed: any error before resume terminates the suspended
    child and closes every handle acquired so far.
    """
    import sc_process
    proc = _create_process(argv, cwd=cwd)
    job = None
    k32 = _kernel32()
    try:
        job = sc_process._create_job()
        if not k32.AssignProcessToJobObject(
                wintypes.HANDLE(job),
                wintypes.HANDLE(proc["process"])):
            raise RuntimeError("AssignProcessToJobObject failed")
        if k32.ResumeThread(wintypes.HANDLE(proc["thread"])) \
                == 0xFFFFFFFF:
            raise RuntimeError("ResumeThread failed")
        return {"ok": True, "pid": proc["pid"],
                "start_time": proc["start_time"],
                "job": job, "process": proc["process"]}
    except BaseException:
        if job is not None:
            try:
                sc_process._kernel32().CloseHandle(
                    wintypes.HANDLE(job))
            except Exception:
                pass
        _terminate_process(proc)
        raise
    finally:
        if proc.get("thread"):
            try:
                k32.CloseHandle(wintypes.HANDLE(proc["thread"]))
            except Exception:
                pass
            proc["thread"] = None


def close_owned(s):
    """TerminateJobObject + close handles; KILL_ON_JOB_CLOSE reaps
    the whole tree."""
    _require_nt()
    import sc_process
    k32 = sc_process._kernel32()
    job = s.get("job")
    if job:
        try:
            k32.TerminateJobObject(wintypes.HANDLE(job), 1)
        except Exception:
            pass
        try:
            k32.CloseHandle(wintypes.HANDLE(job))
        except Exception:
            pass
    proc_h = s.get("process")
    if proc_h:
        try:
            _kernel32().CloseHandle(wintypes.HANDLE(proc_h))
        except Exception:
            pass
    return {"ok": True}


def resume_main_thread(pid):
    """Resume every thread owned by pid (the suspended main thread).

    Toolhelp32 snapshot -> Thread32 walk -> OpenThread ->
    ResumeThread -> close. Raises on any step failure.
    """
    _require_nt()
    pid = _pid(pid)
    k32 = _kernel32()
    snap = k32.CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
    invalid = wintypes.HANDLE(_INVALID_HANDLE).value
    if not snap or snap == invalid:
        raise RuntimeError(
            f"CreateToolhelp32Snapshot failed: "
            f"{ctypes.WinError(ctypes.get_last_error())}")
    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(te)
        found = False
        ok = k32.Thread32First(snap, ctypes.byref(te))
        while ok:
            if te.th32OwnerProcessID == pid:
                found = True
                th = k32.OpenThread(
                    _THREAD_SUSPEND_RESUME, False,
                    te.th32ThreadID)
                if not th:
                    raise RuntimeError(
                        f"OpenThread failed: "
                        f"{ctypes.WinError(ctypes.get_last_error())}")
                try:
                    if k32.ResumeThread(th) == 0xFFFFFFFF:
                        raise RuntimeError(
                            "ResumeThread failed: "
                            f"{ctypes.WinError(ctypes.get_last_error())}")
                finally:
                    k32.CloseHandle(th)
                break  # first thread of a suspended proc is the main
            ok = k32.Thread32Next(snap, ctypes.byref(te))
        if not found:
            raise LookupError(f"no thread for pid: {pid}")
    finally:
        k32.CloseHandle(snap)


def _valid_service_name(name):
    if not isinstance(name, str) or not _SERVICE_NAME.match(name):
        raise contract.InvalidRequest("invalid service name")
    return name


def _open_scm():
    scm = _advapi32().OpenSCManagerW(None, None, _SC_MANAGER_CONNECT)
    if not scm:
        raise BackendUnavailable(
            f"OpenSCManagerW failed: "
            f"{ctypes.WinError(ctypes.get_last_error())}")
    return scm


def scm_available():
    """True when the SCM accepts a connect on this host."""
    if os.name != "nt":
        return False
    try:
        scm = _open_scm()
    except Exception:
        return False
    try:
        return True
    finally:
        _advapi32().CloseServiceHandle(scm)


def _service_state(svc):
    adv = _advapi32()
    # Generous buffer: some hosts demand more than sizeof().
    buf = (ctypes.c_byte * 256)()
    need = wintypes.DWORD(0)
    if not adv.QueryServiceStatusEx(
            svc, _SC_STATUS_PROCESS_INFO, buf,
            ctypes.sizeof(buf), ctypes.byref(need)):
        raise RuntimeError(
            f"QueryServiceStatusEx failed: "
            f"{ctypes.WinError(ctypes.get_last_error())}")
    st = SERVICE_STATUS_PROCESS.from_buffer_copy(
        bytes(buf[:ctypes.sizeof(SERVICE_STATUS_PROCESS)]))
    return _SERVICE_STATES.get(st.dwCurrentState, "unknown")


def service_status(name):
    """{name, state} via SCM; LookupError for unknown service."""
    _require_nt()
    _valid_service_name(name)
    adv = _advapi32()
    scm = _open_scm()
    try:
        svc = adv.OpenServiceW(scm, name, _SERVICE_QUERY_STATUS)
        if not svc:
            err = ctypes.get_last_error()
            if err == _ERROR_ACCESS_DENIED:
                raise PermissionError(f"access denied: {name}")
            raise LookupError(f"service not found: {name}")
        try:
            return {"name": name, "state": _service_state(svc)}
        finally:
            adv.CloseServiceHandle(svc)
    finally:
        adv.CloseServiceHandle(scm)


def _wait_state(svc, targets, deadline):
    while True:
        state = _service_state(svc)
        if state in targets:
            return state
        if time.time() >= deadline:
            return None
        time.sleep(_SVC_POLL_S)


def restart_service(name, *, allowed):
    """Bounded stop/start via SCM; allowlist checked BEFORE any SCM
    call. Never touches service config or identity."""
    _require_nt()
    _valid_service_name(name)
    if not allowed or name not in allowed:
        return {"ok": False, "status": "rejected"}
    adv = _advapi32()
    scm = _open_scm()
    try:
        svc = adv.OpenServiceW(
            scm, name,
            _SERVICE_STOP | _SERVICE_START | _SERVICE_QUERY_STATUS)
        if not svc:
            err = ctypes.get_last_error()
            if err == _ERROR_ACCESS_DENIED:
                raise PermissionError(f"access denied: {name}")
            raise LookupError(f"service not found: {name}")
        try:
            pre = _service_state(svc)
            if pre != "stopped":
                raw = SERVICE_STATUS_PROCESS()
                if not adv.ControlService(
                        svc, _SERVICE_CONTROL_STOP,
                        ctypes.byref(raw)):
                    err = ctypes.get_last_error()
                    if err != _ERROR_SERVICE_NOT_ACTIVE:
                        return {"ok": False, "status": "unknown",
                                "error": f"ControlService stop: {err}",
                                "precondition": {"state": pre}}
                state = _wait_state(svc, {"stopped"},
                                    time.time() + _SVC_WAIT_S)
                if state is None:
                    return {"ok": False, "status": "timeout",
                            "error": "service did not stop",
                            "precondition": {"state": pre}}
            if not adv.StartServiceW(svc, 0, None):
                return {"ok": False, "status": "unknown",
                        "error": "StartServiceW failed: "
                                 f"{ctypes.get_last_error()}",
                        "precondition": {"state": pre}}
            post = _wait_state(svc, {"running"},
                               time.time() + _SVC_WAIT_S)
            if post is None:
                return {"ok": False, "status": "timeout",
                        "error": "service did not start",
                        "precondition": {"state": pre}}
            return {"ok": True, "status": "verified",
                    "precondition": {"state": pre},
                    "postcondition": {"state": post}}
        finally:
            adv.CloseServiceHandle(svc)
    finally:
        adv.CloseServiceHandle(scm)
