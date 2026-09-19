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
