#!/usr/bin/env python3
"""Supervisor — owns the QEMU process and its private QMP stdio channel.

One Supervisor per running env instance. The QMP pipe is stdin/stdout of
the spawned process: no socket, no monitor mixed on stdout, no other
reader/writer. `powerdown` is graceful first (QMP system_powerdown); a
deadline that expires never silently escalates to kill — force requires
the caller (EnvironmentManager) to have collected a new consent.
"""
import time

import cu_qmp


class Supervisor:
    """Wrap a spawned QEMU proc: negotiate QMP, expose typed ops."""

    def __init__(self, proc, deadline_s=10):
        self.proc = proc
        self.qmp = cu_qmp.QmpClient(proc.stdout, proc.stdin,
                                    deadline_s=deadline_s)

    def negotiate(self):
        """Consume greeting + qmp_capabilities. Raises QmpError on EOF,
        timeout or protocol violation — caller treats as failed start."""
        self.qmp.negotiate()

    def call(self, command, arguments=None, deadline_s=None):
        return self.qmp.call(command, arguments, deadline_s)

    def powerdown(self, timeout_s=15, force=False):
        """Graceful ACPI shutdown via QMP; force=True kills only after the
        caller re-consented. Timeout without force raises TimeoutError —
        a stuck guest is `unknown`, never silently killed."""
        try:
            self.qmp.call("system_powerdown")
        except cu_qmp.QmpError:
            pass  # channel dead — wait/kill path still applies
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                return
            time.sleep(0.1)
        if force:
            self.proc.kill()
            self.proc.wait(timeout=5)
            return
        raise TimeoutError("powerdown_timeout")
