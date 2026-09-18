#!/usr/bin/env python3
"""Mouse control: move, click, scroll, drag, position. Prints JSON to stdout.

Action profiles (see profile.py / cu_motion.py): fast (teleport, default),
smooth (cinematic arc), human (bezier + jitter + Fitts timing). Resolve order:
--profile > $COMPUTER_USE_PROFILE > session file > fast.

Requires pynput (installed via requirements.txt into the extension's .venv).
"""
import argparse
import atexit
import json
import os
import random
import sys
import time

import cu_actions
import cu_browser
import cu_motion as cm
import cu_hints


def set_dpi_awareness():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def _ms(v):
    return round(v, 1) if v is not None else None


def _move(mouse, x, y, profile, target_w=30.0, motion=None, seed=None,
          dry_run=False):
    """Move cursor to (x, y) per profile. Returns (points, duration_s)."""
    if profile == "fast":
        if not dry_run:
            mouse.position = (x, y)
        return 1, 0.0
    cx, cy = mouse.position
    pts, dur = cm.gen_path(profile, cx, cy, x, y, target_w,
                           motion=motion, seed=seed)
    if not dry_run:
        cm.play_path(mouse, pts, dur)
    return len(pts), dur


def _resolve_xy(args):
    """click/move may take --hint instead of x y positionals.
    Returns (x, y, entry|None). Stale/invalid hints are rejected BEFORE any
    controller call — never click coordinates from an outdated observation."""
    if getattr(args, "hint", None):
        # resolved once at parse time (see main) — reuse that entry so the
        # coordinates are frozen at the moment of validation, not re-read
        # from a possibly newer observation
        entry = getattr(args, "_hint_entry", None)
        if entry is None:
            entry, reason = cu_hints.resolve_hint(
                args.hint, session=cu_hints.session_id(),
                generation=getattr(args, "gen", None))
            if not entry:
                fail(f"hint {args.hint!r} rejected: {reason} — "
                     "rerun screenshot.py --hints")
        return entry["x"], entry["y"], entry
    if args.x is None or args.y is None:
        fail("x and y are required unless --hint is given", 2)
    return args.x, args.y, None


def main():
    if os.environ.get("CU_SESSION") == "1":
        import cu_session_dispatch
        cu_session_dispatch.run_via_daemon("mouse", sys.argv[1:])
        return
    p = cm.JsonParser(description="Mouse control via pynput")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("move", "click", "scroll", "drag"):
        sp = sub.add_parser(name)
        sp.add_argument("--profile", choices=cm.PROFILES, default=None,
                        help="action profile override for this call")
        sp.add_argument("--motion", choices=cm.MOTIONS, default=None,
                        help="path generator: bezier (default) or minjerk "
                             "(minimum-jerk, no jitter/overshoot)")
        sp.add_argument("--seed", type=int, default=None,
                        help="seed the RNG for a reproducible path")
        sp.add_argument("--dry-run", action="store_true",
                        help="compute path/timing but dispatch no input")
        if name in ("move", "click"):
            sp.add_argument("x", type=int, nargs="?")
            sp.add_argument("y", type=int, nargs="?")
            sp.add_argument("--hint", default=None,
                            help="hint id from screenshot.py --hints "
                                 "(resolves to element center)")
            sp.add_argument("--gen", type=int, default=None,
                            help="generation from the same --hints output; "
                                 "pins the observation so a newer snapshot "
                                 "rejects the hint as stale_generation")
        else:
            sp.add_argument("x", type=int)
            sp.add_argument("y", type=int)
        if name == "click":
            sp.add_argument("--button", default="left",
                            choices=["left", "right", "middle"])
            sp.add_argument("--clicks", type=int, default=1,
                            help="1=single, 2=double (default: 1)")
            sp.add_argument("--hold", type=int, default=None,
                            help="ms between press and release (default: "
                                 "profile-driven; human jitters ~70ms)")
            sp.add_argument("--target-w", type=float, default=30.0,
                            help="target width px for Fitts timing (human)")
            sp.add_argument("--via", default="auto",
                            choices=["auto", "physical", "uia", "browser"],
                            help="with --hint: auto re-locates the element and "
                                 "uses its UIA Invoke pattern when available, "
                                 "falling back to a physical click; 'uia' "
                                 "rejects instead of falling back; 'browser' "
                                 "requires the element's window to be an "
                                 "explicitly bound browser (DOM click)")
            sp.add_argument("--verify", action="store_true",
                            help="with --hint: re-locate the element after "
                                 "dispatch and report postcondition.target_present")
        if name == "scroll":
            sp.add_argument("--dx", type=int, default=0, help="horizontal steps")
            sp.add_argument("--dy", type=int, default=0, help="vertical steps (+ down)")
        if name == "drag":
            sp.add_argument("--from-x", type=int, required=True)
            sp.add_argument("--from-y", type=int, required=True)
            sp.add_argument("--duration", type=float, default=None)
    spos = sub.add_parser("position", help="Print current cursor position")

    args = p.parse_args()
    if getattr(args, "via", None) == "browser" and \
            not getattr(args, "hint", None):
        fail("--via browser requires --hint (needs element hwnd)", 2)
    if getattr(args, "hint", None):
        e, r = cu_hints.resolve_hint(
            args.hint, session=cu_hints.session_id(),
            generation=getattr(args, "gen", None))
        if not e:
            fail(f"hint {args.hint!r} rejected: {r} — "
                 "rerun screenshot.py --hints")
        args._hint_entry = e  # freeze: single resolution per invocation
    set_dpi_awareness()

    try:
        from pynput.mouse import Button, Controller
    except ImportError:
        fail("pynput not installed — run: <venv-python> -m pip install -r requirements.txt", 2)
    atexit.register(cu_actions.emergency_release)

    profile = cm.get_profile(getattr(args, "profile", None))
    mouse = Controller()
    try:
        if args.cmd == "position":
            x, y = mouse.position
            print(json.dumps({"ok": True, "x": x, "y": y}))
            return
        if args.cmd == "move":
            x, y, entry = _resolve_xy(args)
            t0 = cu_actions.now_ms()
            n, dur = _move(mouse, x, y, profile, motion=args.motion,
                           seed=args.seed, dry_run=args.dry_run)
            fx, fy = mouse.position
            out = cu_actions.result("dispatched", "physical", cmd="move",
                                    x=fx, y=fy, profile=profile, points=n,
                                    secs=round(dur, 3),
                                    timings_ms={"move": None, "dispatch": None,
                                                "total": _ms(cu_actions.now_ms() - t0)})
            if entry is not None:
                out["hint"] = args.hint
            if args.dry_run:
                out["dry_run"] = True
                out["x"], out["y"] = x, y
            print(json.dumps(out))
            return
        if args.cmd == "click":
            x, y, entry = _resolve_xy(args)
            t0 = cu_actions.now_ms()
            out = cu_actions.result("dispatched", "physical", cmd="click",
                                    profile=profile)
            invoked = False
            if entry is not None and args.via == "browser":
                if args.dry_run:
                    out["dry_run"] = True
                else:
                    res, reason = cu_browser.dom_action(
                        entry.get("hwnd"), x, y, "click",
                        enabled=entry.get("enabled", True),
                        bounds_px=entry.get("bounds"))
                    if res:
                        invoked = True
                        out["dispatch"]["backend"] = "dom"
                        out["dispatch"]["dialect"] = res.get("dialect")
                        out["dispatch"]["css"] = res.get("css")
                    else:
                        fail(f"browser click rejected: {reason}")
            elif entry is not None and args.via in ("auto",) \
                    and not args.dry_run:
                # auto prefers DOM when the element's window is a bound browser
                ok, _ = cu_browser.check(entry.get("hwnd"))
                if ok:
                    res, reason = cu_browser.dom_action(
                        entry.get("hwnd"), x, y, "click",
                        enabled=entry.get("enabled", True),
                        bounds_px=entry.get("bounds"))
                    if res:
                        invoked = True
                        out["dispatch"]["backend"] = "dom"
                        out["dispatch"]["dialect"] = res.get("dialect")
                    elif reason and reason.startswith("browser_actionable_"):
                        out["dispatch"]["dom_fallback"] = reason
            if entry is not None and args.via in ("auto", "uia") \
                    and not invoked and not args.dry_run:
                res, reason = cu_hints.uia_perform(entry, "invoke")
                if res is not None and reason is None:
                    invoked = True
                    x, y = res["x"], res["y"]
                    out["dispatch"]["backend"] = "uia"
                    out["dispatch"]["pattern"] = res.get("pattern")
                elif args.via == "uia":
                    fail(f"uia invoke rejected: {reason}")
                else:
                    out["dispatch"]["uia_fallback"] = reason
            t_move = t_disp = None
            if not invoked:
                tm = cu_actions.now_ms()
                n, dur = _move(mouse, x, y, profile, target_w=args.target_w,
                               motion=args.motion, seed=args.seed,
                               dry_run=args.dry_run)
                t_move = cu_actions.now_ms() - tm
                out["points"] = n
                out["secs"] = round(dur, 3)  # planned path duration
                td = cu_actions.now_ms()
                if not args.dry_run:
                    hold = cm.click_hold(profile, args.hold, seed=args.seed)
                    with cu_actions.OwnedInputs() as owned:
                        time.sleep(cm.pre_click_delay(
                            profile, n_choices=cu_hints.hint_count(),
                            seed=args.seed))
                        btn = cu_actions.resolve_button(
                            Button, args.button)
                        for i in range(args.clicks):
                            owned.press(mouse, btn)
                            time.sleep(hold)
                            owned.release(mouse, btn)
                            if i < args.clicks - 1:
                                time.sleep(
                                    0.08 if profile == "fast"
                                    else max(0.03, cm.gauss(
                                        args.seed, 0.11, 0.03)))
                    t_disp = cu_actions.now_ms() - td
            fx, fy = (x, y) if invoked or args.dry_run else mouse.position
            out["x"], out["y"] = fx, fy
            if entry is not None:
                out["hint"] = args.hint
                out["hint_name"] = entry.get("name", "")
            if args.verify and entry is not None and not args.dry_run:
                res, _ = cu_hints.uia_perform(entry, "locate")
                out["postcondition"] = {"target_present": res is not None}
            if args.dry_run:
                out["dry_run"] = True
            out["timings_ms"] = {"move": _ms(t_move),
                                 "dispatch": _ms(t_disp),
                                 "total": _ms(cu_actions.now_ms() - t0)}
            print(json.dumps(out))
            return
        if args.cmd == "scroll":
            t0 = cu_actions.now_ms()
            if profile == "fast":
                if not args.dry_run:
                    mouse.position = (args.x, args.y)
                    time.sleep(0.05)
                    mouse.scroll(args.dx, args.dy)
            else:
                _move(mouse, args.x, args.y, profile, motion=args.motion,
                      seed=args.seed, dry_run=args.dry_run)
                if not args.dry_run:
                    seq = ([(1 if args.dx > 0 else -1, 0)] * abs(args.dx)
                           + [(0, 1 if args.dy > 0 else -1)] * abs(args.dy))
                    for (sx, sy), gap in zip(seq, cm.scroll_gaps(profile, len(seq), seed=args.seed)):
                        mouse.scroll(sx, sy)
                        time.sleep(gap)
            fx, fy = mouse.position
            out = cu_actions.result("dispatched", "physical", cmd="scroll",
                                    x=fx, y=fy, profile=profile,
                                    timings_ms={"move": None, "dispatch": None,
                                                "total": _ms(cu_actions.now_ms() - t0)})
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
        if args.cmd == "drag":
            t0 = cu_actions.now_ms()
            dur = args.duration
            if dur is None:
                dur = 0.3 if profile == "fast" else (0.6 if profile == "smooth" else 0.8)
            if not args.dry_run:
                drag_btn = cu_actions.resolve_button(Button, "left")
                with cu_actions.OwnedInputs() as owned:
                    if profile == "fast":
                        mouse.position = (args.from_x, args.from_y)
                        time.sleep(0.05)
                        owned.press(mouse, drag_btn)
                        steps = max(int(dur / 0.02), 1)
                        for i in range(1, steps + 1):
                            t = i / steps
                            mouse.position = (
                                round(args.from_x + (args.x - args.from_x) * t),
                                round(args.from_y + (args.y - args.from_y) * t))
                            time.sleep(dur / steps)
                        owned.release(mouse, drag_btn)
                    else:
                        mouse.position = (args.from_x, args.from_y)
                        time.sleep(cm.pre_click_delay(profile, seed=args.seed))
                        owned.press(mouse, drag_btn)
                        pts, _ = cm.gen_path(profile, args.from_x, args.from_y,
                                             args.x, args.y,
                                             motion=args.motion,
                                             seed=args.seed)
                        cm.play_path(mouse, pts, dur)
                        owned.release(mouse, drag_btn)
            fx, fy = mouse.position
            out = cu_actions.result("dispatched", "physical", cmd="drag",
                                    x=fx, y=fy, profile=profile,
                                    timings_ms={"move": None, "dispatch": None,
                                                "total": _ms(cu_actions.now_ms() - t0)})
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    cu_actions.run_cli(main)
