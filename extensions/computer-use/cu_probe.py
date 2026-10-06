#!/usr/bin/env python3
"""cu_probe.py — what is at screen point (x,y)?

    cu_probe.py --at 640,480                  # UIA element + visual edge box
    cu_probe.py --at 640,480 --no-uia         # edges only (UIA-blind surface)
    cu_probe.py --at 640,480 --tolerance 50   # looser edge match

Two independent channels, each degrading to a typed error:

  uia    IUIAutomation::ElementFromPoint -> deepest element's name/type/
         bounds/hwnd. Semantic truth where a provider exists.
  edges  PowerToys Screen Ruler algorithm (EdgeDetection.cpp port): scan
         outward from the seed pixel in 4 directions; an edge is the first
         pixel whose per-channel diff vs the SEED pixel exceeds
         --tolerance. Returns the bounding box of the visually coherent
         region containing the point — works on canvas/game/image
         surfaces where UIA has no tree. hit_image_edge flags regions
         that likely extend past the capture (retry with --tolerance up).

Coordinates are physical pixels (PerMonitorV2), same space as mouse.py.
"""
import argparse
import json
import os
import queue
import sys
import threading

import cu_dpi


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


# --- UIA channel -------------------------------------------------------------

def _probe_uia_impl(x, y):
    import ctypes.wintypes as wt
    import cu_hints
    core = cu_hints._uia_core()
    try:
        pt = wt.POINT(int(x), int(y))
    except Exception:
        return None, "bad_point"
    el = None
    try:
        try:
            el = core.ElementFromPoint(pt)
        except Exception:
            el = core.ElementFromPoint(pt.x, pt.y)
        if el is None:
            return None, "no_element"
        r = el.CurrentBoundingRectangle
        return {"name": (el.CurrentName or "")[:120],
                "control_type_id": int(el.CurrentControlType),
                "type": cu_hints.CLICKABLE.get(
                    int(el.CurrentControlType), "?"),
                "bounds": [r.left, r.top, r.right - r.left,
                           r.bottom - r.top],
                "hwnd": int(el.CurrentNativeWindowHandle or 0) or None,
                "enabled": bool(el.CurrentIsEnabled)}, None
    except Exception as exc:
        return None, f"error:{type(exc).__name__}"
    finally:
        # release the element inside its own apartment (cu_hints contract)
        del el


def probe_uia(x, y, timeout=4.0):
    """-> (result_dict, reason). None result means UIA blind or failed."""
    if os.environ.get("CU_NO_UIA") or sys.platform != "win32":
        return None, "no_uia"
    q = queue.Queue(maxsize=1)

    def run():
        try:
            import cu_hints
            q.put(cu_hints._com_thread(lambda: _probe_uia_impl(x, y)))
        except Exception as exc:
            q.put((None, f"error:{type(exc).__name__}"))

    threading.Thread(target=run, daemon=True).start()
    try:
        res = q.get(timeout=timeout)
    except queue.Empty:
        return None, "timeout"
    return res if res else (None, "error")


# --- pixel edge channel ------------------------------------------------------

def _monitor_for(x, y, mons):
    """Smallest mss monitor containing (x,y); monitors[0] (virtual union)
    as fallback for points outside every real monitor."""
    best = None
    for m in mons[1:]:
        if (m["left"] <= x < m["left"] + m["width"]
                and m["top"] <= y < m["top"] + m["height"]):
            area = m["width"] * m["height"]
            if best is None or area < best[0]:
                best = (area, m)
    return best[1] if best else mons[0]


def _edge_box(img, ix, iy, tolerance):
    """4-direction scan from (ix, iy) in IMAGE coords. Returns
    (l, t, r, b, hit_image_edge) — image coords, bound = last pixel still
    close to the seed (Screen Ruler semantics)."""
    w, h = img.width, img.height
    rgb = img.rgb

    def px(px_, py_):
        i = (py_ * w + px_) * 3
        return rgb[i], rgb[i + 1], rgb[i + 2]

    sr, sg, sb = px(ix, iy)

    def close(p):
        return (abs(p[0] - sr) <= tolerance
                and abs(p[1] - sg) <= tolerance
                and abs(p[2] - sb) <= tolerance)

    hit = False
    l = 0
    for px_ in range(ix - 1, -1, -1):
        if not close(px(px_, iy)):
            l = px_ + 1
            break
    else:
        hit = True
    r = w - 1
    for px_ in range(ix + 1, w):
        if not close(px(px_, iy)):
            r = px_ - 1
            break
    else:
        hit = True
    t = 0
    for py_ in range(iy - 1, -1, -1):
        if not close(px(ix, py_)):
            t = py_ + 1
            break
    else:
        hit = True
    b = h - 1
    for py_ in range(iy + 1, h):
        if not close(px(ix, py_)):
            b = py_ - 1
            break
    else:
        hit = True
    return l, t, r, b, hit


def probe_edges(x, y, tolerance=30):
    """-> (result_dict, reason). Screen-coord bounds of the coherent
    region around (x,y)."""
    try:
        import cu_capture
        mons = cu_capture.monitors()
        m = _monitor_for(x, y, mons)
        img, _meta = cu_capture.grab(
            {"left": m["left"], "top": m["top"],
             "width": m["width"], "height": m["height"]})
    except Exception as exc:
        return None, f"capture:{type(exc).__name__}"
    ix, iy = int(x) - m["left"], int(y) - m["top"]
    if not (0 <= ix < img.width and 0 <= iy < img.height):
        return None, "point_outside_capture"
    l, t, r, b, hit = _edge_box(img, ix, iy, tolerance)
    return {"bounds": [l + m["left"], t + m["top"],
                       r - l + 1, b - t + 1],
            "tolerance": tolerance,
            "hit_image_edge": hit,
            "monitor_origin": [m["left"], m["top"]]}, None


def main():
    p = argparse.ArgumentParser(prog="cu_probe.py")
    p.add_argument("--at", required=True, metavar="X,Y")
    p.add_argument("--tolerance", type=int, default=30,
                   help="per-channel edge tolerance 0-255 (default 30)")
    p.add_argument("--no-uia", action="store_true")
    p.add_argument("--no-edges", action="store_true")
    p.add_argument("--timeout", type=float, default=4.0)
    args = p.parse_args()
    try:
        x, y = [int(v) for v in args.at.split(",")]
    except ValueError:
        fail("--at must be 'x,y' integers", 2)
    if args.no_uia and args.no_edges:
        fail("nothing to probe — both channels disabled", 2)

    cu_dpi.set_dpi_awareness()
    out = {"ok": True, "point": [x, y]}
    if not args.no_uia:
        res, err = probe_uia(x, y, timeout=args.timeout)
        out["uia"] = res if err is None else {"error": err}
    if not args.no_edges:
        res, err = probe_edges(x, y, tolerance=args.tolerance)
        out["edges"] = res if err is None else {"error": err}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
