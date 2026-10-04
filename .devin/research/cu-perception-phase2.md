# CU perception Phase 2: per-hypothesis results

Pre-registered metrics/thresholds: `cu-perception-phase1.md` sec.4.
Harness: `.devin/scratch/cu-perception/`. N>=5, p50 primary.
Machine: this host, 2026-10-04. Python 3.14 stdlib ctypes (no deps).

## P1 — WinEvents daemon (out-of-context SetWinEventHook)

Probe: `p1_winevents.py` + `p1_target.py` (foreign window) + `p1_rename.py`
(third-process trigger w/ QPC stamp). Mechanism verified working from pure
Python ctypes: callback in client process, hmod=NULL, message-pump thread.

| Metric | Result | Threshold | Verdict |
|---|---|---|---|
| wake_ms LOCATIONCHANGE (foreign trigger via SetWindowPos) | **21.2ms p50** (n=10, min 12.9) | <100 | PASS |
| wake_ms NAMECHANGE (true foreign trigger, third process) | **7.6ms p50** (n=10, min 4.6) | <100 | PASS |
| wake_ms LOCATIONCHANGE (own-process, lower bound) | 0.54ms p50 | — | in-context floor ~sub-ms |
| idle noise | ~1 event/3s ambient | — | negligible |
| delivery | ordered, all hooked classes arrived (create/show/reorder/foreground/focus/hide/destroy/location/name) | — | — |

Poll comparison: a synchronous GetWindowRect poll sees a completed change in
0.01ms but must run continuously to catch an async change — a 50Hz poll costs
~50 calls/s forever and detects with ~interval/2 lag. The event bus delivers
in ~8-21ms with **zero work between events**: new capability confirmed
(OS-event wake < poll, per spec threshold).

Findings beyond latency:
- `WINEVENT_SKIPOWNPROCESS` also drops events the hook process itself
  *triggers* (our own SetWindowTextW -> NAMECHANGE never arrived; only a
  third-process trigger delivered). For a daemon: keep skip flag (agent
  actions verify separately; self-echo is noise). Measured.
- Out-of-context delivery ~8-21ms is the marshaling floor; same-process is
  sub-ms. In-context is DLL-only — out of scope by spec.
- Foreign-window reliability note: conhost windows spawned under Windows
  Terminal appear as WT tabs (frame not ownable/movable) — target windows
  for probes must be plain win32 (p1_target.py).

**P1 verdict: PASS** — feeds P11 (event-driven perception daemon design).

## Pending

P2 UIA event handlers; P3 DPI v2 + round-trip precision; P4 OCR text->coords;
P5 DXGI DDA backend; P6 WGC; P7 numpy FFT-NCC; P11 integration verdict.
