"""OS adapters for system-control. Shared helpers only; no state."""

import subprocess
import threading

RUN_TIMEOUT_S = 10
OUTPUT_CAP = 1000000
_CHUNK = 65536


def _drain(stream, sink, cap):
    """Read the pipe to EOF, retaining at most cap bytes.

    Always drains fully so the child never blocks on a full pipe.
    """
    kept = 0
    while True:
        chunk = stream.read(_CHUNK)
        if not chunk:
            break
        if kept < cap:
            take = chunk[:cap - kept]
            sink.append(take)
            kept += len(take)
    stream.close()


def run_bounded(argv, timeout=RUN_TIMEOUT_S, cap=OUTPUT_CAP):
    """Argv-array subprocess: shell=False, timeout, bounded output.

    stdout/stderr are drained concurrently so a chatty child cannot
    deadlock; only `cap` bytes per stream are retained. On timeout the
    child is killed and reaped, then TimeoutExpired is raised.
    Returns (returncode, stdout_bytes, stderr_bytes).
    """
    proc = subprocess.Popen(argv, shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out_parts, err_parts = [], []
    threads = [
        threading.Thread(target=_drain,
                         args=(proc.stdout, out_parts, cap),
                         daemon=True),
        threading.Thread(target=_drain,
                         args=(proc.stderr, err_parts, cap),
                         daemon=True),
    ]
    for t in threads:
        t.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        for t in threads:
            t.join()
        raise subprocess.TimeoutExpired(
            argv, timeout,
            output=b"".join(out_parts), stderr=b"".join(err_parts))
    for t in threads:
        t.join()
    return proc.returncode, b"".join(out_parts), b"".join(err_parts)


def make_process_provider(process_list, source):
    """Snapshot-diff provider: process.start / process.exit events.

    `process_list` is a zero-arg callable returning
    [{"pid","start_time","name"}]. The first poll is a baseline and
    emits nothing; a snapshot failure yields one provider.error event —
    the callable never raises.
    """
    state = {"prev": None}
    lock = threading.Lock()

    def poll():
        with lock:
            return _poll()

    def _poll():
        import sc_telemetry
        try:
            procs = process_list()
        except Exception as exc:
            return [sc_telemetry.normalize(
                {}, source=source, kind="provider.error",
                severity="error",
                attrs={"message": str(exc)})]
        snap = {}
        for p in procs:
            try:
                snap[(int(p["pid"]), int(p["start_time"]))] = \
                    p.get("name")
            except (KeyError, TypeError, ValueError):
                continue
        prev = state["prev"]
        state["prev"] = snap
        if prev is None:
            return []
        out = []
        for key, pname in snap.items():
            if key not in prev:
                out.append(sc_telemetry.normalize(
                    {"pid": key[0], "start_time": key[1]},
                    source=source, kind="process.start",
                    attrs={"name": pname}))
        for key, pname in prev.items():
            if key not in snap:
                out.append(sc_telemetry.normalize(
                    {"pid": key[0], "start_time": key[1]},
                    source=source, kind="process.exit",
                    attrs={"name": pname}))
        return out

    return poll
