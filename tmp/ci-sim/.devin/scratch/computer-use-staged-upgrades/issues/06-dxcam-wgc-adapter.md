# 06 — DXcam/WGC capture adapter

**Intent:** adopt GPU capture ONLY if 01 shows capture/encoding dominates the
step budget; otherwise record "not justified" and close as evidence.

**What to build:** dxcam backend in `cu_capture.py` behind import-guard +
`$CU_CAPTURE=dxcam`; pinned `dxcam` in requirements (only if evidence
justifies); parity check vs MSS output on identical frames; access-lost ->
backend recreate; move/dirty via 03's apply_delta.

**Proposed modules:** `cu_capture.py`, `requirements.txt`.

**Estimated size (lines):** ~150

**Input / Output:** same grab() contract; meta.backend="dxcam"

**Blocked by:** 01, 02, 03

**Gate:** `python -m pytest tests/test_cu_capture_frames.py -q` + paired bench (01 harness, same runs both backends)

**Expect:** byte-exact frames; median capture latency better than mss on the recorded workload — else do not adopt, record result

**Evidence:** bench JSON diff + pytest output

**Status:** resolved (not adopted — evidence)

- [ ] import-guarded, optional dep
- [ ] no adoption without measured win
- [ ] access-lost recovery path tested with fake device

## Answer

NOT ADOPTED. Baseline: grab p50 20.5ms vs png_encode 101.8ms — capture is
not the dominant boundary, so the gate says do not adopt. Seam stays;
`apply_delta` ready for a future backend. Recorded in cu-stage-report.md.
