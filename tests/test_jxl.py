"""media-tools/jxl.py - cjxl/djxl wrapper contract.

Round-trip test skips when libjxl binaries are absent (run
extensions/media-tools/jxl_bootstrap.py to fetch them).
"""
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

MT = Path(__file__).resolve().parents[1] / "extensions" / "media-tools"
sys.path.insert(0, str(MT))

import jxl  # noqa: E402


def _png_rgb(path, w=32, h=24, seed_fn=None):
    """Write a small RGB PNG (stdlib only)."""
    def px(x, y):
        return ((x * 8) % 256, (y * 10) % 256, (x * y) % 256)
    f = seed_fn or px
    raw = b"".join(
        b"\x00" + b"".join(bytes(f(x, y)) for x in range(w))
        for y in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + \
            struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _png_pixels(path):
    """Decode PNG -> {(x, y): (r, g, b)} for color-type-2, filter 0/1..4."""
    data = path.read_bytes()
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + ln]
        if tag == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and ctype == 2
        elif tag == b"IDAT":
            idat += body
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    out, prev = {}, bytearray(stride)
    for y in range(h):
        row = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        filt = raw[y * (stride + 1)]
        for i in range(stride):
            a = row[i - 3] if i >= 3 else 0
            b, c = prev[i], (prev[i - 3] if i >= 3 else 0)
            if filt == 1:
                row[i] = (row[i] + a) & 255
            elif filt == 2:
                row[i] = (row[i] + b) & 255
            elif filt == 3:
                row[i] = (row[i] + (a + b) // 2) & 255
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else \
                    (b if pb <= pc else c)
                row[i] = (row[i] + pred) & 255
        for x in range(w):
            out[(x, y)] = tuple(row[x * 3:x * 3 + 3])
        prev = row
    return out, w, h


def test_missing_binary_envelope(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(jxl, "PATHS_FILE", tmp_path / "none.json")
    monkeypatch.setattr(jxl, "CACHE", tmp_path / "no_cache")
    monkeypatch.setattr(jxl.shutil, "which", lambda n: None)
    res = jxl.encode("in.png", "out.jxl")
    assert res["ok"] is False
    assert res["status"] == "missing" and "hint" in res
    res = jxl.decode("in.jxl", "out.png")
    assert res["ok"] is False and res["status"] == "missing"
    res = jxl.identify("in.jxl")
    assert res["ok"] is False and res["status"] == "missing"


def test_input_missing_typed(tmp_path, monkeypatch):
    monkeypatch.setattr(jxl, "find_tool", lambda n: "/bin/true")
    res = jxl.encode(str(tmp_path / "no.png"), str(tmp_path / "o.jxl"))
    assert res["ok"] is False and res["error"].startswith("input_missing")


def test_bad_params_typed(tmp_path, monkeypatch):
    monkeypatch.setattr(jxl, "find_tool", lambda n: "/bin/true")
    src = tmp_path / "a.png"
    _png_rgb(src)
    assert "bad_quality" in jxl.encode(src, "o.jxl", 200)["error"]
    assert "bad_effort" in jxl.encode(src, "o.jxl", 90, 0)["error"]


@pytest.mark.skipif(not (jxl.find_tool("cjxl") and jxl.find_tool("djxl")),
                    reason="cjxl/djxl not bootstrapped")
def test_roundtrip(tmp_path):
    src = tmp_path / "src.png"
    _png_rgb(src)
    jxlf = tmp_path / "img.jxl"
    out = tmp_path / "out.png"
    enc = jxl.encode(src, jxlf, quality=100)
    assert enc["ok"], enc
    dec = jxl.decode(jxlf, out)
    assert dec["ok"], dec
    info = jxl.identify(jxlf)
    assert info["ok"], info
    assert (info["width"], info["height"]) == (32, 24)
    assert info["frames"] == 1
    src_px, _, _ = _png_pixels(src)
    out_px, w, h = _png_pixels(out)
    assert (w, h) == (32, 24)
    diffs = [max(abs(a - b) for a, b in zip(src_px[k], out_px[k]))
             for k in src_px]
    assert max(diffs) <= 8  # lossy codec tolerance
