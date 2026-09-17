# 02 — Capture seam `cu_capture` (MSS backend)

**Intent:** isolate capture behind an adapter so GPU backends can slot in
without touching screenshot.py.

**What to build:** `extensions/computer-use/cu_capture.py` with
`grab(bbox, backend=None) -> (img, meta)`; meta = {backend, origin_px,
size_px, monotonic_ns}. Backend from $CU_CAPTURE (default mss). MSS backend
returns the mss shot unchanged. `screenshot.py` routes grabs through it;
stdout contract unchanged.

**Proposed modules:** new `cu_capture.py`; `screenshot.py` grab call.

**Estimated size (lines):** ~120

**Input / Output:** bbox dict → (img with .rgb/.width/.height/.size, meta dict)

**Blocked by:** None — can start immediately.

**Gate:** `python -m pytest tests/test_cu_capture_frames.py -q` (interface part) + `screenshot.py` real run in venv

**Expect:** exit 0; screenshot stdout identical schema (ok/path/width/height/origin_px/captured_at)

**Evidence:** pytest output + screenshot JSON

**Status:** resolved

- [ ] screenshot.py identical output contract
- [ ] backend selectable via $CU_CAPTURE, mss default
- [ ] meta carries origin/size/monotonic_ns

## Answer

`cu_capture.py` landed (`grab`/`monitors`, $CU_CAPTURE); `screenshot.py`
routes through it — real-venv run produced identical schema; unknown backend
rejects cleanly. Evidence: 9/9 capture tests + live screenshot JSON.
