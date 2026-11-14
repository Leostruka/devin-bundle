# 03 — Move/dirty-rect reconstruction

**Intent:** DXGI incremental capture requires applying all move rects (source
= previous frame) before dirty rects; wrong order corrupts frames.

**What to build:** `cu_capture.apply_delta(base, w, h, bpp, moves, dirties)`
pure-python reference: moves copy base→new first, then dirties overwrite;
base=None -> None (resync required). Plus `tests/test_cu_capture_frames.py`
synthetic fixtures: overlapping moves, dirty-after-move order, lost frame,
resync, byte-exact reconstruction.

**Proposed modules:** `cu_capture.py` (+test file).

**Estimated size (lines):** ~80 + ~120 tests

**Input / Output:** (bytes, dims, rects) → new frame bytes or None

**Blocked by:** 02-capture-seam-mss

**Gate:** `python -m pytest tests/test_cu_capture_frames.py -q`

**Expect:** exit 0, all fixtures byte-exact

**Evidence:** pytest output

**Status:** resolved

- [ ] moves applied before dirties (order asserted by overlapping fixture)
- [ ] lost base -> resync signal, never delta on arbitrary base
- [ ] byte-exact reconstruction on all fixtures

## Answer

`apply_delta` landed: moves read previous frame, dirties applied after;
lost base -> None (resync); geometry/payload mismatches reject. Byte-exact
on all fixtures. Evidence: `test_cu_capture_frames.py` 9/9.
