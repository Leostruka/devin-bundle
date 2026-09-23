#!/usr/bin/env python3
"""Container guest entrypoint — Xvfb + window manager + worker.

Runs INSIDE the locked-down container: starts a private Xvfb display
(no host X11/Wayland socket exists here), a minimal WM, then execs
guest/worker.py which serves the virtio/stdio channel the supervisor
connected. Exits if any component dies — the supervisor observes EOF
and reports the env down rather than a half-running desktop.
"""
import os
import signal
import subprocess
import sys
import time

DISPLAY = os.environ.get("CU_DISPLAY", ":77")
XVFB = os.environ.get("CU_XVFB", "Xvfb")
WM = os.environ.get("CU_WM", "openbox")
WORKER = os.environ.get("CU_WORKER",
                        "/opt/cu/guest/worker.py")


def _spawn(argv):
    return subprocess.Popen(argv)


def main():
    procs = []

    def _die(*_):
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        sys.exit(1)

    signal.signal(signal.SIGTERM, _die)
    signal.signal(signal.SIGINT, _die)

    xvfb = _spawn([XVFB, DISPLAY, "-screen", "0", "1280x800x24",
                   "-nolisten", "tcp"])
    procs.append(xvfb)
    time.sleep(0.5)
    if xvfb.poll() is not None:
        print("xvfb_failed", file=sys.stderr)
        sys.exit(1)

    env = dict(os.environ, DISPLAY=DISPLAY)
    wm = subprocess.Popen([WM], env=env)
    procs.append(wm)

    worker = subprocess.Popen([sys.executable, WORKER], env=env)
    procs.append(worker)

    # any component death = env down (honest EOF to the supervisor)
    while True:
        for p in procs:
            if p.poll() is not None:
                _die()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
