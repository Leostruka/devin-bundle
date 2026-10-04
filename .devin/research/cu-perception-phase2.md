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

## P2 — UIA client event handlers (comtypes COMObject, MTA thread)

Probe: `p2_uia_events.py` (+ decisive scope experiment inline). Handlers as
comtypes `COMObject` subclasses; whole UIA lifecycle inside one MTA thread
(`CoInitializeEx(COINIT_MULTITHREADED)`); `CacheRequest` prefetch verified.

| Channel | Result | Verdict |
|---|---|---|
| `AddStructureChangedEventHandler` on **root, TreeScope_Children** | fires on window spawn; wake **264ms p50** end-to-end (n=5, min 231) — dominated by process+window creation, UIA share is a fraction | WORKS |
| `AddStructureChangedEventHandler` on **element, TreeScope_Descendants** (XAML Notepad) + `AddPropertyChangedEventHandler` + `AddAutomationEventHandler` | registered without error; **ZERO events** across real verified mutations (Invoke added tab: 1→2 TabItems, 45→47 descendants — re-enumerated to confirm) | NO DELIVERY on this provider |
| `AddPropertyChangedEventHandler` on plain win32 window (SetWindowText) | 0 events | NO COVERAGE |
| `AddFocusChangedEventHandler` | ambient focus event arrived | WORKS |

Decisive finding: **UIA client events are reliable only at coarse scopes**
(desktop children). Element/subtree-scoped listeners — the ones that would
power per-window semantic wake — depend entirely on provider cooperation
and delivered nothing on XAML Notepad or plain windows. Matches MS warning
("not all property changes cause events … by the standard proxy
providers") — now measured, not just cited.

Gotchas found: `IUIAutomationFocusChangedEventHandler` is a distinct
interface (registration rejects generic `IUIAutomationEventHandler`);
`TreeScope_Subtree=0x7` (not 0x8 = Parent); thread-mode already set on
import (`comtypes.client` auto-STA) — handlers must live on a thread that
did `CoInitializeEx(MTA)` before importing client bindings.

**P2 verdict: PASS-CONSTRAINED** — usable wake = root-children structure
events + focus; element-level semantic events unreliable → P1 (WinEvents
out-of-context, 8-21ms, element-granular) is the primary wake channel;
P2 complements only at desktop scope. Feeds P11 daemon design.

## P3 — DPI v2 + coordinate-space precision

Probe: `p3_dpi.py` (extension venv + `cu_hints.enum_clickables`).

| Check | Result |
|---|---|
| Awareness upgrade | fresh python starts `DPI_AWARENESS_UNAWARE` (0); `SetProcessDpiAwarenessContext(-4)` -> `PER_MONITOR` (2). **Every future daemon entry point must set awareness before any coordinate read** — unaware on a scaled display = virtualized wrong coords |
| Display context | system DPI 96 (100%); `dpi_values=[96]` across 29 windows — no scaling stress-test possible on this host; logical==physical here |
| `GetWindowRect` vs `DWMWA_EXTENDED_FRAME_BOUNDS` | **13/29 windows differ by ±5px** — invisible resize borders counted by GWR even at 96 DPI. Window geometry for capture/UIA space must use DWM extended bounds |
| `GetCursorPos` vs `GetPhysicalCursorPos` | identical (96 DPI — trivially) |
| `ElementFromPoint(center)` round-trip on 22 clickable elements (focused window) | **22/22 hit** (100%), offsets ~0; 1 outlier resolved to a wider containing element (ancestor hit — expected for overlapped centers) |

Bug found+fixed in probe: `CurrentBoundingRectangle` returns RECT
(left/top/right/bottom), not w/h — earlier run's "miss" was probe-side
AttributeError, re-run corrected.

**P3 verdict: PASS** — v2 adopted (context flag; awareness reads 2),
round-trip hit-rate 100% >= baseline; two production-relevant findings:
DWM-vs-GWR border offset and per-entry-point awareness requirement.
Precision baseline recorded for regression on scaled setups (hardware
limitation noted — host is 100%).

## Pending

P4 OCR text->coords; P5 DXGI DDA backend; P6 WGC;
P7 numpy FFT-NCC; P11 integration verdict.
