#!/usr/bin/env python3
"""P6 probe: Windows.Graphics.Capture per-window via raw winrt bindings.

Reuses dxcam's Device/StageSurface for D3D11 plumbing, but the session is
built with create_for_window(hwnd) — the per-window path dxcam does not
expose. Measures the hypothesis P5 killed: does FrameArrived fire for
SINGLE window updates (event-driven capture), plus per-window isolation,
occluded-surface capture, border-free content, and surface->numpy cost.
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import statistics
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_deps"))

TRIALS = int(sys.argv[sys.argv.index("--trials") + 1]) \
    if "--trials" in sys.argv else 10

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def find_window(substr, timeout=15):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def en(h, l):
        if user32.IsWindowVisible(h):
            n = user32.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(h, b, n + 1)
                out.append((h, b.value))
        return True

    dl = time.time() + timeout
    while time.time() < dl:
        out.clear()
        user32.EnumWindows(en, 0)
        for h, t in out:
            if substr in t:
                return h
        time.sleep(0.1)
    return None


def summ(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p50": round(statistics.median(v), 3),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 3),
            "min": round(min(v), 3), "max": round(max(v), 3)}


def main():
    import comtypes
    import dxcam
    import numpy as np
    from dxcam._libs.dxgi import IDXGIDevice, IDXGISurface
    from dxcam._libs.d3d11 import ID3D11Texture2D
    from dxcam.core.stagesurf import StageSurface
    from winrt.windows.graphics.capture import Direct3D11CaptureFramePool
    from winrt.windows.graphics.capture.interop import create_for_window
    from winrt.windows.graphics.directx import DirectXPixelFormat
    from winrt.windows.graphics.directx.direct3d11.interop import (
        create_direct3d11_device_from_dxgi_device,
        get_dxgi_surface_from_object,
    )

    rep = {"ok": True}

    marker = f"cu_p6_{int(time.time())}"
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         marker, "120", "--drawtext", "--topmost"])
    hwnd = find_window(marker)
    rep["target_hwnd"] = hwnd
    if not hwnd:
        print(json.dumps({"ok": False, "err": "no target"}))
        return

    # D3D11 device via dxcam's plumbing (adapter 0)
    cam = dxcam.create(backend="dxgi", processor_backend="numpy",
                       output_color="RGB")
    device = cam._device
    dxgi_dev = device.device.QueryInterface(IDXGIDevice)
    dxgi_ptr = ctypes.cast(dxgi_dev, ctypes.c_void_p).value
    winrt_dev = create_direct3d11_device_from_dxgi_device(dxgi_ptr)

    item = create_for_window(hwnd)
    rep["item_size"] = (int(item.size.width), int(item.size.height))
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    rep["window_rect_wh"] = (r.right - r.left, r.bottom - r.top)

    pool = Direct3D11CaptureFramePool.create_free_threaded(
        winrt_dev,
        DirectXPixelFormat.B8_G8_R8_A8_UINT_NORMALIZED,
        2,
        item.size,
    )
    session = pool.create_capture_session(item)
    for attr, val in (("is_border_required", False),
                      ("is_cursor_capture_enabled", False)):
        try:
            setattr(session, attr, val)
            rep[f"set_{attr}"] = True
        except Exception:
            rep[f"set_{attr}"] = False

    ev = threading.Event()
    ev_count = {"n": 0}

    def on_frame(sender, args):
        ev_count["n"] += 1
        ev.set()

    tok = pool.add_frame_arrived(on_frame)
    session.start_capture()
    time.sleep(0.4)  # initial frame(s) arrive

    def drain():
        n = 0
        while True:
            f = pool.try_get_next_frame()
            if f is None:
                return n
            try:
                f.close()
            except Exception:
                pass
            n += 1

    rep["initial_frames_drained"] = drain()
    freq = ctypes.c_int64()
    kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
    freq = freq.value

    # wake_ms: single window RESIZE (content change) -> FrameArrived.
    # Pure position moves do NOT fire — the item's content surface is
    # unchanged; that is correct per-window semantics, measured separately.
    wake, move_only = [], []
    for i in range(TRIALS):
        drain()
        ev.clear()
        trig = {}
        use_move = i < 3  # first 3: pure move (expected: no frame)

        def mv():
            time.sleep(0.3 + (i % 5) * 0.12)
            rr = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rr))
            c = ctypes.c_int64()
            kernel32.QueryPerformanceCounter(ctypes.byref(c))
            trig["qpc"] = c.value
            if use_move:
                user32.SetWindowPos(hwnd, None, rr.left + 25, rr.top,
                                    0, 0, 0x0001 | 0x0004 | 0x0400)
            else:
                user32.MoveWindow(hwnd, rr.left + 25, rr.top,
                                  320 + (i % 3) * 10, 200, True)

        th = threading.Thread(target=mv, daemon=True)
        th.start()
        got = ev.wait(4.0)
        t_ret = time.perf_counter()
        th.join()
        if "qpc" in trig:
            if use_move:
                move_only.append(got)
            elif got:
                wake.append((t_ret - trig["qpc"] / freq) * 1000)
        time.sleep(0.15)
    rep["frame_arrived_wake_ms"] = summ(wake)
    rep["pure_move_events_3"] = move_only  # expect [False,False,False]

    # spurious wakes: idle 2s
    ev.clear()
    drain()
    n0 = ev_count["n"]
    ev.wait(2.0)
    rep["idle_events_2s"] = ev_count["n"] - n0
    rep["idle_frames_drained"] = drain()

    # frame content: size vs window + surface -> numpy cost + non-empty
    drain()
    ev.clear()
    r2 = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r2))
    user32.MoveWindow(hwnd, r2.left + 25, r2.top, 330, 200, True)
    ev.wait(3.0)
    frame = pool.try_get_next_frame()
    if frame is not None:
        rep["content_size"] = (int(frame.content_size.width),
                               int(frame.content_size.height))
        try:
            rep["system_relative_time_ticks"] = int(
                frame.system_relative_time.total_seconds() * 1e7)
        except Exception:
            pass
        from dxcam._libs.d3d11 import D3D11_TEXTURE2D_DESC
        surf_ptr = get_dxgi_surface_from_object(frame.surface)
        surf = ctypes.cast(surf_ptr, ctypes.POINTER(IDXGISurface))
        tex = surf.QueryInterface(ID3D11Texture2D)
        td = D3D11_TEXTURE2D_DESC()
        tex.GetDesc(ctypes.byref(td))
        rep["tex_desc"] = (td.Width, td.Height)
        stage = StageSurface(output=cam._output, device=device)
        stage.release()  # post_init allocates at monitor size; rebuild
        stage.rebuild(cam._output, device, dim=(td.Width, td.Height))
        device.im_context.CopyResource(stage.texture, tex)
        t0 = time.perf_counter()
        rect = stage.map()
        arr = np.ctypeslib.as_array(
            (ctypes.c_uint8 * (rect.Pitch * stage.height)).from_address(
                ctypes.addressof(rect.pBits.contents))
        ).reshape(stage.height, rect.Pitch)[:, : stage.width * 4] \
            .reshape(stage.height, stage.width, 4)
        img = np.array(arr[:, :, :3])
        copy_ms = (time.perf_counter() - t0) * 1000
        stage.unmap()
        rep["surface_to_numpy_ms"] = round(copy_ms, 3)
        rep["pixels_shape"] = list(img.shape)
        rep["pixels_nonblack_pct"] = round(
            float(np.count_nonzero(img) / img.size * 100), 1)
        try:
            frame.close()
        except Exception:
            pass
    else:
        rep["content_size"] = None

    # occluded window: spawn a NON-topmost target, keep it behind, move it
    occ_marker = f"cu_p6o_{int(time.time())}"
    proc2 = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         occ_marker, "60", "--drawtext"])
    occ_hwnd = find_window(occ_marker)
    occ = {"spawned": bool(occ_hwnd)}
    if occ_hwnd:
        item2 = create_for_window(occ_hwnd)
        pool2 = Direct3D11CaptureFramePool.create_free_threaded(
            winrt_dev, DirectXPixelFormat.B8_G8_R8_A8_UINT_NORMALIZED,
            2, item2.size)
        session2 = pool2.create_capture_session(item2)
        try:
            session2.is_border_required = False
        except Exception:
            pass
        ev2 = threading.Event()
        tok2 = pool2.add_frame_arrived(lambda s, a: ev2.set())
        session2.start_capture()
        time.sleep(0.4)
        # occlude: move the topmost target OVER the occ window
        ro = wt.RECT()
        user32.GetWindowRect(occ_hwnd, ctypes.byref(ro))
        user32.SetWindowPos(hwnd, None, ro.left, ro.top, 0, 0,
                            0x0001 | 0x0004)
        time.sleep(0.3)
        while pool2.try_get_next_frame() is not None:
            pass
        ev2.clear()
        trig = {}

        def mv2():
            time.sleep(0.3)
            rr = wt.RECT()
            user32.GetWindowRect(occ_hwnd, ctypes.byref(rr))
            c = ctypes.c_int64()
            kernel32.QueryPerformanceCounter(ctypes.byref(c))
            trig["qpc"] = c.value
            # resize the OCCLUDED window (move only might be clipped)
            user32.MoveWindow(occ_hwnd, rr.left, rr.top,
                              330, 205, True)

        th = threading.Thread(target=mv2, daemon=True)
        th.start()
        got = ev2.wait(4.0)
        t_ret = time.perf_counter()
        th.join()
        occ["frame_arrived_while_occluded"] = got
        if got and "qpc" in trig:
            occ["wake_ms"] = round(
                (t_ret - trig["qpc"] / freq) * 1000, 2)
        f2 = pool2.try_get_next_frame()
        occ["frame_after_occluded_move"] = f2 is not None
        if f2 is not None:
            try:
                f2.close()
            except Exception:
                pass
        session2.close()
        pool2.close()
        proc2.kill()
    rep["occluded"] = occ

    # dirty region support probe (newer API surface)
    try:
        import winrt.windows.graphics.capture as cap
        rep["dirty_region_enum"] = hasattr(cap,
                                           "GraphicsCaptureDirtyRegionMode")
        rep["session_has_dirty_region_mode"] = hasattr(
            session, "dirty_region_mode")
    except Exception:
        rep["dirty_region_enum"] = False

    print(json.dumps(rep, indent=1))
    try:
        pool.remove_frame_arrived(tok)
        session.close()
        pool.close()
        cam.release()
    except Exception:
        pass
    proc.kill()


if __name__ == "__main__":
    main()
