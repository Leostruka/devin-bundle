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
import json
import os
import sys
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
    buttons = (mouse.Button.left, mouse.Button.right, mouse.Button.middle)
    # A stray button-UP fires WM_CONTEXTMENU even with no prior DOWN —
    # release only buttons the OS reports held. Unqueryable state falls
    # back to unconditional release (dead-worker cleanup must still work).
    vks = (0x01, 0x02, 0x04)
    if buttons_swapped():
        vks = (0x02, 0x01, 0x04)
    held = [_async_key_down(vk) for vk in vks]
    if None not in held:
        buttons = tuple(b for b, h in zip(buttons, held) if h)
    for b in buttons:
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


_SM_SWAPBUTTON = 23
_swap_state = None


def _get_system_metrics(index):
    """user32.GetSystemMetrics(index); 0 off-Windows or on any failure."""
    if os.name != "nt":
        return 0
    try:
        import ctypes
        return ctypes.windll.user32.GetSystemMetrics(index)
    except Exception:
        return 0


def buttons_swapped():
    """True when the OS reports swapped primary/secondary buttons
    (SM_SWAPBUTTON=23). Cached: the setting requires re-login to change."""
    global _swap_state
    if _swap_state is None:
        _swap_state = bool(_get_system_metrics(_SM_SWAPBUTTON))
    return _swap_state


def resolve_button(Button, name):
    """Logical button name -> physical pynput Button constant.

    pynput's Button.left emits MOUSEEVENTF_LEFTDOWN, which Windows routes
    through SM_SWAPBUTTON — on a left-handed host that event IS the
    secondary click. Swap left<->right at dispatch so the caller's
    semantic 'left' stays the primary action; middle never swaps."""
    if buttons_swapped() and name in ("left", "right"):
        name = "right" if name == "left" else "left"
    return getattr(Button, name)


def _async_key_down(vk):
    """GetAsyncKeyState high bit for vk; None off-Windows or on failure.
    VK_LBUTTON/VK_RBUTTON are logical (post-swap), so physical button
    state surfaces under the swapped VK on swapped hosts."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return None


def run_cli(main):
    """Entry-point guard for the stdout JSON contract: an unhandled crash
    still emits exactly one {"ok": false} object so a downstream
    json.loads(sys.stdin) never sees a traceback. SystemExit (fail/usage
    paths) re-raises untouched — those paths already printed their JSON."""
    try:
        main()
    except SystemExit:
        raise
    except BaseException as e:
        print(json.dumps({"ok": False,
                          "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
