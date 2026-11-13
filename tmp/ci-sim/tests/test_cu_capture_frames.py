"""Gate for tickets 02+03: capture seam interface and move/dirty-rect
reconstruction. Synthetic frames only — no real screen capture."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cap = cu_load.load("cu_capture")


def _frame(w, h, bpp=3):
    """Deterministic frame: byte value = (x + y*W) % 251 per pixel."""
    buf = bytearray(w * h * bpp)
    for y in range(h):
        for x in range(w):
            v = (x + y * w) % 251
            for c in range(bpp):
                buf[(y * w + x) * bpp + c] = v
    return bytes(buf)


def _region(frame, w, x, y, rw, rh, bpp=3):
    out = bytearray()
    for row in range(rh):
        o = ((y + row) * w + x) * bpp
        out += frame[o:o + rw * bpp]
    return bytes(out)


def test_grab_contract_meta():
    """grab() meta contract is backend-tagged with origin/size/monotonic."""
    class Shot:
        rgb = b"\x00" * 12
        width, height, size = 2, 2, (2, 2)

    cap._BACKENDS["fake"] = lambda bbox: Shot()
    try:
        img, meta = cap.grab({"left": -100, "top": 50,
                              "width": 2, "height": 2}, backend="fake")
        assert img.rgb == Shot.rgb
        assert meta["backend"] == "fake"
        assert meta["origin_px"] == [-100, 50]
        assert meta["size_px"] == [2, 2]
        assert isinstance(meta["monotonic_ns"], int)
    finally:
        del cap._BACKENDS["fake"]


def test_grab_unknown_backend_rejected():
    with pytest.raises(ValueError, match="unknown capture backend"):
        cap.grab({"left": 0, "top": 0, "width": 1, "height": 1},
                 backend="nope")


def test_apply_delta_dirty_only():
    w = h = 4
    base = _frame(w, h)
    patch = _region(_frame(w, h), w, 0, 0, 4, 4)
    patch = b"\xff" * (2 * 2 * 3)  # 2x2 white block at (1,1)
    new = cap.apply_delta(base, w, h, 3, [], [(1, 1, 2, 2, patch)])
    exp = bytearray(base)
    for row in range(2):
        o = ((1 + row) * w + 1) * 3
        exp[o:o + 6] = b"\xff" * 6
    assert bytes(new) == bytes(exp)


def test_apply_delta_move_then_dirty_order():
    """Move rects read source from the PREVIOUS frame; dirties overwrite
    after all moves. A dirty that overlaps a move destination must win."""
    w = h = 4
    base = _frame(w, h)
    # move 2x2 block from (0,0) to (2,2)
    moves = [(0, 0, 2, 2, 2, 2)]
    # dirty a 1x1 white pixel at (2,2) — inside the move destination
    dirties = [(2, 2, 1, 1, b"\xff" * 3)]
    new = cap.apply_delta(base, w, h, 3, moves, dirties)
    exp = bytearray(base)
    for row in range(2):
        so = row * w * 3
        do = ((2 + row) * w + 2) * 3
        exp[do:do + 6] = base[so:so + 6]
    o = (2 * w + 2) * 3
    exp[o:o + 3] = b"\xff" * 3
    assert bytes(new) == bytes(exp)


def test_apply_delta_move_source_is_previous_frame():
    """Chained-move fixture: src of move2 overlaps dst of move1 — move2 must
    still read the ORIGINAL pixels, not move1's output."""
    w = h = 4
    base = _frame(w, h)
    moves = [(0, 0, 1, 0, 2, 1),   # row0 (0..1) -> (1..2)
             (1, 0, 3, 0, 1, 1)]   # (1,0) reads original base, -> (3,0)
    new = cap.apply_delta(base, w, h, 3, moves, [])
    # pixel (3,0) in result must equal original (1,0), not moved (0,0)
    orig_10 = base[(0 * w + 1) * 3:(0 * w + 1) * 3 + 3]
    assert bytes(new[(0 * w + 3) * 3:(0 * w + 3) * 3 + 3]) == orig_10


def test_apply_delta_lost_base_resyncs():
    assert cap.apply_delta(None, 4, 4, 3, [], []) is None


def test_apply_delta_rejects_mismatched_base():
    with pytest.raises(ValueError, match="geometry"):
        cap.apply_delta(b"\x00" * 10, 4, 4, 3, [], [])


def test_apply_delta_rejects_short_dirty_payload():
    w = h = 4
    with pytest.raises(ValueError, match="payload"):
        cap.apply_delta(_frame(w, h), w, h, 3, [], [(0, 0, 2, 2, b"\x00")])


def test_end_to_end_byte_exact_reconstruction():
    """Synthetic scenario: move a block, dirty two pixels, verify the result
    equals a hand-computed expected frame byte-for-byte."""
    w, h = 8, 6
    base = _frame(w, h)
    moves = [(2, 1, 4, 3, 3, 2)]
    dirty_src = _frame(w, h)  # pretend new pixels from a fresh frame region
    d1 = _region(dirty_src, w, 0, 5, 2, 1)
    dirties = [(0, 5, 2, 1, d1), (6, 0, 1, 1, b"\xab" * 3)]
    new = cap.apply_delta(base, w, h, 3, moves, dirties)

    exp = bytearray(base)
    tmp = bytearray(base)
    for row in range(2):
        so = ((1 + row) * w + 2) * 3
        do = ((3 + row) * w + 4) * 3
        exp[do:do + 9] = tmp[so:so + 9]
    for row in range(1):
        o = ((5 + row) * w + 0) * 3
        exp[o:o + 6] = d1[row * 6:(row + 1) * 6]
    o = (0 * w + 6) * 3
    exp[o:o + 3] = b"\xab" * 3
    assert bytes(new) == bytes(exp)
