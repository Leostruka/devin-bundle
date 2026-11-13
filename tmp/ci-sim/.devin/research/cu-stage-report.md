# Computer-Use staged upgrades — comparative report (protocol 4.4)

Frozen evidence: `.devin/research/cu-benchmark-baseline.json`
(20 runs, Windows, Python 3.14.4, 1920x1080x1 monitor — this machine).
Tickets: `.devin/scratch/computer-use-staged-upgrades/`.

## Measured boundaries (p50 / p95, ms)

| Boundary | p50 | p95 | Share of a typical observe+act step |
|---|---|---|---|
| startup_subprocess | 141.7 | 146.0 | dominant per-call cost |
| png_encode | 101.8 | 106.1 | dominant in observe path |
| hints_enum | 30.9 | 36.9 | moderate |
| capture_full | 20.5 | 24.2 | minor |
| capture_region | 6.9 | 11.1 | minor |
| input_dispatch | 0.002 | 0.04 | negligible |

## Stage decisions

| Stage | Decision | Evidence |
|---|---|---|
| 4 — browser DOM/AX/CDP | **Contract landed** (`cu_browser.py`): explicit loopback binding, pid check, session+TTL, CDP driver seam returns None until a driver is approved. No DOM actions ship without a real bound browser + approved dep. | `tests/test_cu_browser_contract.py` 12/12 |
| 5 — persistent session | **Adopted** (`cu_session.py`): stdin/stdout pipes, recyclable worker, generation+session rotation on restart, queue cancel, timeout→kill+respawn. Opt-in module; frontends unchanged by default. | startup 141.7ms p50 justifies amortization; `test_cu_session_isolation.py` 9/9 |
| 6 — GPU capture (DXcam/WGC) | **Not adopted.** Grab is ~20ms of a ~120ms observe path; PNG encode (102ms) dominates 5×. DXcam would shave grab, not encode — no measured win to buy. Seam (`cu_capture.grab`) stays so a backend can register later if workloads change. | baseline JSON; `test_cu_capture_frames.py` 9/9 |
| 8 — adversarial/held-out | **Landed** as seeded workflows + stateful sequence tests: stale/foreign-session/focus-change → zero dispatch; 20 seeds invariant-clean; replays byte-identical. | `test_cu_workflows.py` + `test_cu_stateful.py` 31/31 |

## Honest limits

- Numbers are this machine, this moment — not a spec. Re-run
  `cu_bench.py --runs 20` when hardware/monitor count changes.
- PNG encode is the next real target if observe-path latency matters:
  options are JPEG/WebP encode, region-scoped captures, or delta frames —
  none implemented yet; the encode cost was measured, not optimized.
- `cu_session` is plumbing, not wired into `mouse.py`/`type_text.py` yet —
  frontends keep the one-JSON-per-call contract; session adoption is an
  explicit opt-in step, not silent.
- Browser DOM/CDP actions remain unavailable by design (`_cdp_client()`
  → None) until a driver dependency is explicitly approved.

## Raw artifacts

- `cu-benchmark-baseline.json` — frozen samples (never regenerated in-place;
  new runs get new files).
