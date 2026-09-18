#!/usr/bin/env python3
"""Action/result contract and session-owned input cleanup for computer-use.

Result statuses (stdout JSON "status" field):
  verified   — expected postcondition confirmed by re-observation
  dispatched — input/pattern accepted; effect NOT verified (ok:true means
               dispatch, never task success)
  rejected   — pre-condition failed; zero input was dispatched
  timeout    — effect wait exceeded its deadline
  unknown    — outcome could not be determined; do not blind-retry
  cancelled  — aborted before/while dispatching

OwnedInputs tracks buttons/keys this session pressed and releases exactly
those in finally paths — a held physical key owned by the user is never
touched.
"""
import time

STATUSES = ("verified", "dispatched", "rejected", "timeout",
            "unknown", "cancelled")


def now_ms():
    return time.monotonic_ns() / 1e6


class OwnedInputs:
    """Context manager: records (controller, key) pairs this session
    pressed; releases only those on exit/exception. Usage:

        with OwnedInputs() as owned:
            owned.press(mouse, Button.left)
            ...
            owned.release(mouse, Button.left)
        # anything still held is released here
    """

    def __init__(self):
        self._held = []

    def press(self, controller, key):
        controller.press(key)
        self._held.append((controller, key))

    def release(self, controller, key):
        controller.release(key)
        for i in range(len(self._held) - 1, -1, -1):
            c, k = self._held[i]
            if c is controller and k == key:
                self._held.pop(i)
                break

    def release_all(self):
        while self._held:
            c, k = self._held.pop()
            try:
                c.release(k)
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release_all()
        return False


def emergency_release():
    """Release the standard modifier set + mouse buttons unconditionally.

    Input state is OS-global — ANY process can keyUp a key another process
    left held. Registered via atexit in the frontends (covers abnormal
    non-exception exits) and invoked by the session daemon after killing a
    worker mid-gesture (the dead worker cannot clean itself). Releasing a
    modifier the user is physically holding is a no-op semantically — the
    OS still reports it held while the user's finger is down; we only send
    release events, never presses.
    """
    try:
        from pynput import keyboard, mouse
    except ImportError:
        return
    kb = keyboard.Controller()
    for k in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
              keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
              keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
              getattr(keyboard.Key, "cmd", None),
              getattr(keyboard.Key, "cmd_l", None),
              getattr(keyboard.Key, "cmd_r", None)):
        if k is None:
            continue
        try:
            kb.release(k)
        except Exception:
            pass
    ms = mouse.Controller()
    for b in (mouse.Button.left, mouse.Button.right, mouse.Button.middle):
        try:
            ms.release(b)
        except Exception:
            pass


def result(status, backend, extra=None, **kw):
    """Result object per the action contract. `ok` keeps CLI compatibility;
    `status` carries the evidence level — never report "verified" without
    an independent observation."""
    # ok=false only when nothing was dispatched; timeout/unknown/cancelled
    # keep ok=true because input may have reached the app — status says which.
    out = {"ok": status != "rejected",
           "status": status,
           "dispatch": {"backend": backend}}
    if extra:
        out["dispatch"].update(extra)
    out.update(kw)
    return out
