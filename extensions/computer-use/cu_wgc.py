"""cu_wgc.py — optional Windows.Graphics.Capture frames (P6).

    cu_wgc.py shot --hwnd 123456 --out frame.png   # latest/next frame
    cu_wgc.py shot --hwnd 123456 --wait 5          # event-driven: next
                                                   # content change
    cu_wgc.py wait [--monitor N] [--timeout S]     # block until ANY
                    [--out path.png]               # monitor repaints
    cu_wgc.py caps                                 # capability probe

Unique capability (probe-validated): captures pixels of an OCCLUDED
window — mss sees whatever is on top, WGC sees the window's surface.
FrameArrived fires on content change only (38-44ms p50 wake); pure
position moves do NOT fire — correct per-window semantics.

Optional backend: requires dxcam + the winrt-Windows.Graphics.Capture*
package family. `caps` reports availability; every other path degrades
to a structured error instead of an ImportError crash, so the base
extension installs stay lean.
"""
import argparse
import json
import os
import sys
import tempfile
import threading
import time

import cu_dpi

_PIXFMT = None  # resolved lazily


def capability():
    """-> (available, reason). Import check only — no device init."""
    if sys.platform != "win32":
        return False, "windows only"
    try:
        import dxcam  # noqa: F401
        import numpy  # noqa: F401
        from winrt.windows.graphics.capture import (  # noqa: F401
            Direct3D11CaptureFramePool)
        from winrt.windows.graphics.capture.interop import (  # noqa: F401
            create_for_window, create_for_monitor)
        from winrt.windows.graphics.directx.direct3d11.interop import \
            create_direct3d11_device_from_dxgi_device  # noqa: F401
        return True, "ok"
    except Exception as e:
        return False, f"wgc deps missing: {e}"


class _WgcSession:
    """WGC session over any GraphicsCaptureItem: device + pool + frame
    drain + resize. Subclasses supply the item (window or monitor)."""

    def __init__(self, item):
        ok, why = capability()
        if not ok:
            raise RuntimeError(why)
        import comtypes  # noqa: F401 — MTA state for interop calls
        import dxcam
        from dxcam._libs.dxgi import IDXGIDevice
        from winrt.windows.graphics.capture import (
            Direct3D11CaptureFramePool)
        from winrt.windows.graphics.directx import DirectXPixelFormat

        self._dxcam = dxcam
        self._D3DPool = Direct3D11CaptureFramePool
        self._pixfmt = DirectXPixelFormat.B8_G8_R8_A8_UINT_NORMALIZED
        self._interops = __import__(
            "winrt.windows.graphics.directx.direct3d11.interop",
            fromlist=["interop"])
        self.item = item
        self.cam = dxcam.create(backend="dxgi", processor_backend="numpy",
                                output_color="RGB")
        self.device = self.cam._device
        dxgi = self.device.device.QueryInterface(IDXGIDevice)
        import ctypes
        dxgi_ptr = ctypes.cast(dxgi, ctypes.c_void_p).value
        self.winrt_dev = self._interops.\
            create_direct3d11_device_from_dxgi_device(dxgi_ptr)
        self._psize = (int(self.item.size.width),
                       int(self.item.size.height))
        self.pool = self._new_pool(self.item.size)
        self.session = self.pool.create_capture_session(self.item)
        for attr in ("is_border_required", "is_cursor_capture_enabled"):
            try:
                setattr(self.session, attr, False)
            except Exception:
                pass
        self._frame_ev = threading.Event()
        self._tok = self.pool.add_frame_arrived(
            lambda s, a: self._frame_ev.set())
        self.session.start_capture()
        time.sleep(0.35)  # initial frame(s) queue — kept for shot()

    def _new_pool(self, size):
        return self._D3DPool.create_free_threaded(
            self.winrt_dev, self._pixfmt, 2, size)

    def drain(self):
        n = 0
        while True:
            f = self.pool.try_get_next_frame()
            if f is None:
                return n
            try:
                f.close()
            except Exception:
                pass
            n += 1

    def next_frame(self, timeout=4.0, fresh=False):
        """-> newest frame or None. fresh=True drains queued frames and
        waits for the NEXT content change; fresh=False takes the latest
        already-queued frame (initial frame = current content even when
        the window is static)."""
        if fresh:
            self.drain()
            self._frame_ev.clear()
            if not self._frame_ev.wait(timeout):
                return None
        else:
            self._frame_ev.wait(timeout)  # initial frame may lag
        frame = None
        while True:
            f = self.pool.try_get_next_frame()
            if f is None:
                break
            if frame is not None:
                try:
                    frame.close()
                except Exception:
                    pass
            frame = f
        return frame

    def _check_size(self, frame):
        """Frame pool is pinned to creation size; on window resize we
        must recreate it with the new content_size or frames stall."""
        size = frame.content_size
        wh = (int(size.width), int(size.height))
        if wh != self._psize:
            self.pool.recreate(self.winrt_dev, self._pixfmt, 2, size)
            self._psize = wh

    def frame_to_array(self, frame):
        """D3D11 surface -> numpy RGB via dxcam StageSurface staging."""
        import ctypes
        import numpy as np
        from dxcam._libs.dxgi import IDXGISurface
        from dxcam._libs.d3d11 import (
            ID3D11Texture2D, D3D11_TEXTURE2D_DESC)
        from dxcam.core.stagesurf import StageSurface

        self._check_size(frame)
        surf_ptr = self._interops.get_dxgi_surface_from_object(
            frame.surface)
        surf = ctypes.cast(surf_ptr, ctypes.POINTER(IDXGISurface))
        tex = surf.QueryInterface(ID3D11Texture2D)
        td = D3D11_TEXTURE2D_DESC()
        tex.GetDesc(ctypes.byref(td))
        if not hasattr(self, "_stage") or \
                self._stage_size != (td.Width, td.Height):
            if hasattr(self, "_stage"):
                self._stage.release()
            self._stage = StageSurface(output=self.cam._output,
                                       device=self.device)
            self._stage.release()
            self._stage.rebuild(self.cam._output, self.device,
                                dim=(td.Width, td.Height))
            self._stage_size = (td.Width, td.Height)
        self.device.im_context.CopyResource(self._stage.texture, tex)
        rect = self._stage.map()
        arr = np.ctypeslib.as_array(
            (ctypes.c_uint8 * (rect.Pitch * self._stage.height))
            .from_address(ctypes.addressof(rect.pBits.contents))
        ).reshape(self._stage.height, rect.Pitch)[:, : td.Width * 4] \
            .reshape(self._stage.height, td.Width, 4)
        img = np.array(arr[:, :, :3])
        self._stage.unmap()
        return img

    def close(self):
        for fn in (lambda: self.pool.remove_frame_arrived(self._tok),
                   self.session.close, self.pool.close,
                   self.cam.release):
            try:
                fn()
            except Exception:
                pass


class WgcWindow(_WgcSession):
    """Per-window WGC session."""

    def __init__(self, hwnd):
        from winrt.windows.graphics.capture.interop import (
            create_for_window)
        self.hwnd = int(hwnd)
        super().__init__(create_for_window(self.hwnd))


class WgcMonitor(_WgcSession):
    """Per-monitor WGC session (CreateForMonitor — Screen Ruler path)."""

    def __init__(self, hmon):
        from winrt.windows.graphics.capture.interop import (
            create_for_monitor)
        self.hmon = int(hmon)
        super().__init__(create_for_monitor(self.hmon))


def enum_monitors():
    """-> [{"hmon": int, "rect": [l,t,r,b]}], 1-based CLI index order."""
    import ctypes
    from ctypes import wintypes
    out = []
    proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

    def cb(h, _d, r, _l):
        rc = r.contents
        out.append({"hmon": int(h),
                    "rect": [rc.left, rc.top, rc.right, rc.bottom]})
        return True
    ctypes.windll.user32.EnumDisplayMonitors(None, None, proc(cb), 0)
    return out


def wait_change(timeout=10.0, monitor=None):
    """Block until the next frame on any (or the Nth, 1-based) monitor.
    -> (result_dict, error). changed=True carries the newest frame."""
    mons = enum_monitors()
    if not mons:
        return None, "no_monitors"
    if monitor is not None:
        if not (1 <= monitor <= len(mons)):
            return None, f"monitor_out_of_range:1..{len(mons)}"
        targets = [(monitor, mons[monitor - 1])]
    else:
        targets = list(enumerate(mons, start=1))
    sessions = []
    t0 = time.monotonic()
    try:
        first_err = None
        for idx, m in targets:
            try:
                sessions.append((idx, WgcMonitor(m["hmon"])))
            except Exception as exc:
                if first_err is None:
                    first_err = f"{type(exc).__name__}:{exc}"
        if not sessions:
            return None, f"no_capture_sessions:{first_err}"
        # arm: drop the initial frame each session queued at start
        for _idx, s in sessions:
            s.drain()
            s._frame_ev.clear()
        deadline = t0 + timeout
        while time.monotonic() < deadline:
            for idx, s in sessions:
                if s._frame_ev.wait(0.05):
                    frame = s.next_frame(timeout=0.5)
                    arr = None
                    if frame is not None:
                        try:
                            arr = s.frame_to_array(frame)
                        finally:
                            try:
                                frame.close()
                            except Exception:
                                pass
                    return {"changed": True, "monitor": idx,
                            "elapsed_s": round(time.monotonic() - t0, 3),
                            "frame_array": arr}, None
        return {"changed": False, "monitor": None,
                "elapsed_s": round(time.monotonic() - t0, 3),
                "frame_array": None}, None
    finally:
        for _idx, s in sessions:
            s.close()


def shot(hwnd, timeout=4.0, wait=False):
    """Capture one frame of hwnd. wait=False -> latest queued frame
    (initial = current content, works on static windows); wait=True ->
    next content change (event-driven)."""
    w = None
    try:
        w = WgcWindow(hwnd)
        frame = w.next_frame(timeout, fresh=wait)
        if frame is None:
            return None, "no frame (content unchanged / timeout)"
        try:
            return w.frame_to_array(frame), None
        finally:
            try:
                frame.close()
            except Exception:
                pass
    except RuntimeError as e:
        return None, str(e)
    except Exception as e:
        return None, f"capture failed: {e}"
    finally:
        if w is not None:
            w.close()


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(prog="cu_wgc.py")
    p.add_argument("cmd", choices=["shot", "caps", "wait"])
    p.add_argument("--hwnd", type=int, default=None)
    p.add_argument("--monitor", type=int, default=None,
                   help="with wait: 1-based monitor index (default: all)")
    p.add_argument("--out", default=None)
    p.add_argument("--wait", action="store_true",
                   help="with shot: wait for the NEXT content change "
                        "instead of returning the current frame")
    p.add_argument("--timeout", type=float, default=4.0)
    args = p.parse_args()

    if args.cmd == "caps":
        ok, why = capability()
        print(json.dumps({"ok": True, "available": ok, "reason": why}))
        return
    if args.cmd == "wait":
        ok, why = capability()
        if not ok:
            fail(f"wgc unavailable: {why}")
        res, err = wait_change(timeout=args.timeout, monitor=args.monitor)
        if res is None:
            fail(err)
        arr = res.pop("frame_array")
        if arr is not None:
            res["frame_w"], res["frame_h"] = int(arr.shape[1]), int(arr.shape[0])
        if args.out and arr is not None:
            from PIL import Image
            Image.fromarray(arr).save(args.out, format="PNG")
            res["path"] = args.out
        res["ok"] = True
        print(json.dumps(res))
        return
    if args.hwnd is None:
        fail("--hwnd required")
    cu_dpi.set_dpi_awareness()
    img, err = shot(args.hwnd, timeout=args.timeout, wait=args.wait)
    if img is None:
        fail(err)
    from PIL import Image
    out = args.out or os.path.join(
        tempfile.gettempdir(), f"cu-wgc-{args.hwnd}.png")
    Image.fromarray(img).save(out, format="PNG")
    print(json.dumps({"ok": True, "hwnd": args.hwnd,
                      "w": int(img.shape[1]), "h": int(img.shape[0]),
                      "path": out}))


if __name__ == "__main__":
    main()
