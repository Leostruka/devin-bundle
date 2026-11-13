#!/usr/bin/env python3
"""Capture backend seam.

grab(bbox, backend=None) -> (img, meta)
  img: object with .rgb (bytes, RGB), .width, .height, .size — the mss
       ScreenShot contract. Alternative backends must expose the same.
  meta: {"backend": str, "origin_px": [x, y], "size_px": [w, h],
         "monotonic_ns": int}

Backend selection: $CU_CAPTURE (default "mss"). Unknown/unavailable backends
raise ValueError — callers decide whether to fail or fall back; nothing here
silently downgrades.
"""
import os
import time


def _grab_mss(bbox):
    import mss
    sct = mss.MSS()
    try:
        img = sct.grab(bbox)
        # Detach from the context manager: copy so the caller owns the buffer.
        img = _MssShot(bytes(img.rgb), img.width, img.height, img.size)
        return img
    finally:
        sct.close()


class _MssShot:
    """Buffer-owning stand-in for mss.ScreenShot (grab results die with the
    context manager otherwise)."""

    __slots__ = ("rgb", "width", "height", "size")

    def __init__(self, rgb, width, height, size):
        self.rgb = rgb
        self.width = width
        self.height = height
        self.size = size


_BACKENDS = {"mss": _grab_mss}


def monitors(backend=None):
    """Virtual-screen monitor list, index 0 = all combined (mss contract)."""
    name = (backend or os.environ.get("CU_CAPTURE") or "mss").lower()
    if name != "mss":
        raise ValueError(f"monitors() unsupported for backend '{name}'")
    import mss
    with mss.MSS() as sct:
        return [dict(m) for m in sct.monitors]


def grab(bbox, backend=None):
    name = (backend or os.environ.get("CU_CAPTURE") or "mss").lower()
    fn = _BACKENDS.get(name)
    if fn is None:
        raise ValueError(f"unknown capture backend '{name}' "
                         f"(available: {sorted(_BACKENDS)})")
    t0 = time.monotonic_ns()
    img = fn(bbox)
    meta = {"backend": name,
            "origin_px": [bbox["left"], bbox["top"]],
            "size_px": [img.width, img.height],
            "monotonic_ns": t0}
    return img, meta


def apply_delta(base, width, height, bpp, moves, dirties):
    """Reconstruct a frame from move + dirty rectangles.

    base:     previous frame as bytes/bytearray, or None to force resync.
    moves:    [(src_x, src_y, dst_x, dst_y, w, h)] — source coords read from
              the PREVIOUS frame (DXGI semantics), applied before dirties.
    dirties:  [(x, y, w, h, pixels)] — raw scanlines of the new frame region.

    Returns new frame bytearray, or None if base is None (resync required —
    never apply deltas onto an arbitrary/foreign base).
    """
    if base is None:
        return None
    stride = width * bpp
    if len(base) != stride * height:
        raise ValueError("base size does not match frame geometry")

    new = bytearray(base)
    tmp = bytearray(base)

    def _copy(buf_src, buf_dst, sx, sy, dx, dy, w, h):
        for row in range(h):
            so = (sy + row) * stride + sx * bpp
            do = (dy + row) * stride + dx * bpp
            buf_dst[do:do + w * bpp] = buf_src[so:so + w * bpp]

    for sx, sy, dx, dy, w, h in moves:
        _copy(tmp, new, sx, sy, dx, dy, w, h)
    for x, y, w, h, px in dirties:
        if len(px) != w * h * bpp:
            raise ValueError("dirty rect pixel payload size mismatch")
        for row in range(h):
            o = (y + row) * stride + x * bpp
            new[o:o + w * bpp] = px[row * w * bpp:(row + 1) * w * bpp]
    return new
