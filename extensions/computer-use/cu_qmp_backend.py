#!/usr/bin/env python3
"""QMP capture backend — observe the guest framebuffer via screendump.

The daemon (cu_env_daemon) owns the QEMU process and its private QMP
stdio pipes; this module is the client side over a per-user AF_UNIX
socket inside the env's private dir. Frame pixels transit via a
screendump file inside that dir — the socket carries only small JSON.

- axis_to_qmp maps a guest pixel coordinate to QMP's absolute axis
  range 0..32767 (C06 pointer uses the same mapping).
- screendump negotiates PNG vs PPM: PNG is requested first, and only if
  the build refuses (no CONFIG_PIXMAN) does it fall back to PPM.
- Frame paths are confined to the env dir — a daemon that writes
  elsewhere is a protocol violation, not a feature.
"""
import hashlib
import json
import os
import socket
import struct
import time
import zlib
from pathlib import Path

import cu_target

QMP_AXIS_MAX = 32767
_MAX_DIM = 16384


class BackendError(Exception):
    """Transport, protocol or confinement failure on the env channel."""


def axis_to_qmp(v, size):
    """Guest pixel -> absolute QMP axis value (0..32767), clamped."""
    if size <= 1:
        return 0
    v = max(0, min(int(v), size - 1))
    return round(v * QMP_AXIS_MAX / (size - 1))


def qmp_to_axis(v, size):
    """Inverse mapping — for tests/diagnostics."""
    return round(v * (size - 1) / QMP_AXIS_MAX) if size > 1 else 0


# -- frame parsing -------------------------------------------------------------

class Frame:
    """mss.ScreenShot-compatible stand-in: .rgb/.width/.height/.size."""
    __slots__ = ("rgb", "width", "height", "size")

    def __init__(self, rgb, width, height):
        self.rgb = rgb
        self.width = width
        self.height = height
        self.size = (width, height)


def _ppm_decode(data):
    """P6 PPM -> Frame. Comments allowed; maxval must be 255."""
    if not data.startswith(b"P6"):
        raise BackendError("ppm: bad magic")
    # header: P6 <w> <h> <maxval> <single whitespace> <raster>
    toks, i = [], 2
    while len(toks) < 3:
        while i < len(data) and data[i:i + 1].isspace():
            i += 1
        if i < len(data) and data[i:i + 1] == b"#":
            while i < len(data) and data[i] != 0x0A:
                i += 1
            continue
        j = i
        while j < len(data) and not data[j:j + 1].isspace():
            j += 1
        toks.append(data[i:j])
        i = j
    try:
        w, h, maxval = int(toks[0]), int(toks[1]), int(toks[2])
    except (ValueError, IndexError):
        raise BackendError("ppm: bad header")
    if maxval != 255:
        raise BackendError(f"ppm: maxval {maxval} unsupported")
    if not (1 <= w <= _MAX_DIM and 1 <= h <= _MAX_DIM):
        raise BackendError(f"ppm: bad geometry {w}x{h}")
    raster = data[i + 1:]  # exactly one whitespace byte separates raster
    if len(raster) != w * h * 3:
        raise BackendError(
            f"ppm: raster {len(raster)}B != {w}x{h}x3")
    return Frame(raster, w, h)


def _png_decode(data):
    """Minimal 8-bit PNG decoder (stdlib zlib + unfilter). QEMU
    screendump emits truecolor; we accept RGB/RGBA, reject the rest."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise BackendError("png: bad magic")
    pos = 8
    idat = bytearray()
    w = h = bitdepth = colortype = None
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            w, h, bitdepth, colortype = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    if w is None or not (1 <= w <= _MAX_DIM and 1 <= h <= _MAX_DIM):
        raise BackendError(f"png: bad geometry {w}x{h}")
    if bitdepth != 8 or colortype not in (2, 6):
        raise BackendError(
            f"png: unsupported depth={bitdepth} type={colortype}")
    bpp = 3 if colortype == 2 else 4
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise BackendError(f"png: {exc}")
    stride = w * bpp
    if len(raw) != (stride + 1) * h:
        raise BackendError("png: truncated raster")
    out = bytearray()
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        row = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:      # Sub
            for x in range(bpp, stride):
                row[x] = (row[x] + row[x - bpp]) & 0xFF
        elif f == 2:    # Up
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 0xFF
        elif f == 3:    # Average
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif f == 4:    # Paeth
            for x in range(stride):
                a = row[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else \
                    (b if pb <= pc else c)
                row[x] = (row[x] + pred) & 0xFF
        elif f != 0:
            raise BackendError(f"png: unknown filter {f}")
        if bpp == 3:
            out += row
        else:           # RGBA -> RGB (drop alpha)
            for x in range(0, stride, 4):
                out += row[x:x + 3]
        prev = row
    return Frame(bytes(out), w, h)


def parse_frame(path):
    """Dispatch on magic bytes — never trust the requested format."""
    data = Path(path).read_bytes()
    if data.startswith(b"P6"):
        return _ppm_decode(data)
    if data.startswith(b"\x89PNG"):
        return _png_decode(data)
    raise BackendError("frame: unknown format (not P6/PNG)")


# -- IPC ------------------------------------------------------------------------

def ipc_call(sock_path, message, timeout_s=10, sock=None, token=None):
    """One request -> one JSON-line response. `sock` injectable.
    sock_path may be a filesystem path (AF_UNIX) or tcp://host:port —
    TCP endpoints require the ready.json token (private dir)."""
    s = sock
    if s is None:
        if str(sock_path).startswith("tcp://"):
            host, port = str(sock_path)[6:].rsplit(":", 1)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout_s)
            s.connect((host, int(port)))
        else:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(timeout_s)
            s.connect(str(sock_path))
    else:
        s.settimeout(timeout_s)
    if token is not None:
        message = {"token": token, **message}
    try:
        s.sendall(json.dumps(message).encode("utf-8") + b"\n")
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                raise BackendError("ipc: daemon closed connection")
            buf += chunk
        return json.loads(buf.split(b"\n", 1)[0])
    finally:
        if sock is None:
            s.close()


class QmpBackend:
    """Client handle for one running env. `ipc` is injectable for tests:
    ipc(sock_path, message, timeout_s) -> response dict."""

    def __init__(self, env_id, env_dir=None, ipc=None):
        self.env_id = env_id
        if env_dir is None:
            env_dir = Path(cu_target.runtime_root()) / env_id / env_id
        self.env_dir = Path(env_dir)
        self._ipc = ipc or ipc_call

    def _ready(self):
        try:
            return json.loads(
                (self.env_dir / "ready.json").read_text("utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BackendError(f"env_not_ready:{self.env_id}:{exc}")

    def instance_id(self):
        try:
            st = json.loads(
                (self.env_dir / "state.json").read_text("utf-8"))
            return st.get("instance_id")
        except (OSError, json.JSONDecodeError):
            return None

    def _new_dump_path(self):
        p = self.env_dir / f"screendump-{time.monotonic_ns()}.frame"
        rp, rr = p.resolve(), self.env_dir.resolve()
        if os.path.commonpath([str(rr), str(rp)]) != str(rr):
            raise BackendError(f"escape:{p}")
        return p

    def observe(self, timeout_s=15):
        """screendump -> fresh file inside env_dir -> parsed Frame.

        Negotiates PNG first; a refusal (no pixman build) retries the
        QEMU default (PPM). Returns (img, meta) with the rgb digest —
        meta never claims more than transport + parse success.
        """
        ready = self._ready()
        sock, token = ready["socket"], ready.get("token")
        dump = self._new_dump_path()
        args = {"filename": str(dump), "format": "png"}
        resp = self._ipc(sock, {"command": "screendump",
                              "arguments": args}, timeout_s,
                         token=token)
        if not resp.get("ok"):
            resp = self._ipc(sock, {"command": "screendump",
                                    "arguments": {"filename": str(dump)}},
                             timeout_s, token=token)
        if not resp.get("ok"):
            raise BackendError(
                f"screendump:{resp.get('error_class', '?')}:"
                f"{resp.get('error', '?')}")
        img = parse_frame(dump)
        meta = {"backend": "qmp",
                "origin_px": [0, 0],
                "size_px": [img.width, img.height],
                "frame_sha256": hashlib.sha256(img.rgb).hexdigest(),
                "instance_id": self.instance_id(),
                "env_id": self.env_id,
                "monotonic_ns": time.monotonic_ns()}
        return img, meta

    def status(self):
        ready = self._ready()
        resp = self._ipc(ready["socket"],
                         {"command": "query-status"}, 10,
                         token=ready.get("token"))
        if not resp.get("ok"):
            raise BackendError(resp.get("error", "?"))
        return resp["return"]
