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

## P4 — Windows.Media.Ocr as general text->coords channel

Probe: `p4_ocr.py` (+ `p1_target --drawtext` known-text window). Same
winrt call pattern as `cu_terminal._ocr_image` but consuming
`res.lines -> words -> bounding_rect` (image space) + region origin.

| Metric | Result | Threshold | Verdict |
|---|---|---|---|
| locate_ms (full-window recognize, 306x193) | **7.76ms p50** steady (n=10; first call ~48ms decoder/stream warmup) | <200 | PASS |
| expected word hit rate | 92.9% (13/14; "OK"->"0k" OCR noise) | reported | — |
| coordinate fidelity (line-band re-crop, 3x) | **11/12** re-found at expected x | reported | sane rects confirmed |
| engine cold start | ~17ms once per process | — | — |
| `MaxImageDimension` | **10000** (runtime-measured; docs don't publish it) | — | — |

Hard constraints measured:
- **~48px image-height floor** — below it `recognize_async` returns EMPTY,
  silently. Single-word crops and small text need ~3-4x upscale
  (nearest-neighbor works). No error is raised — callers must check empty.
- **`winrt-Windows.Foundation.Collections` package required** for
  lines/words projection (`res.text` works without it; word rects don't).
  Installed in venv for probe; if integrated -> add to requirements.txt.
- OCR noise exists at word level (OK->0k) — coordinate use should prefer
  multi-char words; verification pattern (re-crop re-OCR) works.

**P4 verdict: PASS** — new capability confirmed: text->screen-coords on
any raster surface at ~8ms/region, zero added model deps. Integration
shape for P11: `region + query_text -> [word, x, y, w, h]` with upscale
guard and empty-result check.

## P5 — DXGI Desktop Duplication (dxcam 0.3.0, isolated scratch target)

Probe: `p5_dxgi.py` + inline matrix experiments
(`dxcam==0.3.0` in `scratch/_deps`, `processor_backend="numpy"`).
Target: `p1_target --topmost --drawtext` (always-on-top guarantees the
moved window is NOT occluded — required after first run showed 0 frames
for an occluded move, which is expected behavior).

### The negative result that matters

| Experiment | Result |
|---|---|
| `AcquireNextFrame(timeout=1500..5000)` while a topmost window moves DURING the wait | **timeout 10/10 — the blocking wait never fires for desktop updates on this host** |
| `AcquireNextFrame(timeout)` when frames already queued | returns immediately (acc=34 seen) — queue has data, the waitable object just isn't signaled |
| `acquire(0)` poll @0.5ms for 3s after a single window move | **0 frames — single updates never reach the duplicator queue at all** |
| dxcam `start(target_fps=0)` thread during continuous move+resize spam | 76 frames collected — frames flow only under sustained compositor activity |
| same single moves via mss grab+diff | 10/10 detected, 14.6–24.0ms |
| cursor spam | frames delivered with `LastMouseUpdateTime` (pointer path works) |
| `DuplicateOutput` vs `IDXGIOutput5::DuplicateOutput1` | identical behavior — not an API-variant issue |

Interpretation: on this host (Win11-class DWM, single monitor, likely
MPO/overlay-plane composition), a single window move is composed without
a full desktop present reaching the duplicator; only sustained
compositor activity produces DD frames, and even then the blocking wait
is not signaled. The frame-event premise of P5 fails empirically —
NOT a dxcam bug (verified at the raw COM layer, both API variants).

Secondary defect found: `AcquireNextFrame` raises `E_NOINTERFACE`
(0x80004002) for frames with no desktop resource (mouse-only/metadata);
dxcam's `update_frame` does not handle it -> `cam.grab()` crashes.
Integration would require handling this ourselves anyway.

**P5 verdict: FAIL-CONSTRAINED on this host** — DD cannot serve as a
frame-event channel (blocking wait dead) nor as a reliable pixel source
for single updates (queue never receives them). Scratch-only; raw-capture
speed was never measured as a benefit and is now moot. `apply_delta()`
in cu_capture remains orphaned — justified. If ever revisited: DD is
only viable during sustained animation (video-ish regions), which is
not the perception use case. `E_NOINTERFACE` + drain semantics must be
handled in any future impl.

## P6 — Windows.Graphics.Capture per-window (raw winrt bindings)

Probe: `p6_wgc.py` — create_for_window(hwnd) + free-threaded frame pool +
`add_frame_arrived` -> threading.Event (the event semantics dxcam's
monitor-only winrt backend does not expose). D3D11 plumbing reused from
dxcam internals. winrt stack: `winrt-Windows.Graphics{,.Capture{,.Interop},
.DirectX{,.Direct3D11{,.Interop}},.Foundation{,.Collections}}` 3.2.1.

| Metric | Result | Note |
|---|---|---|
| FrameArrived wake, single window content change (resize) | **p50 38.6–41.2ms, p95 43.6, n=6/6** | event-driven works — DD's exact failure mode absent |
| FrameArrived on pure position move | **0/3 events** | correct content-scoped semantics: item surface unchanged → no frame. Content changes are what fire |
| Idle noise | 0 events, 0 frames / 2s | no spurious wakes |
| **Occluded window** (fully covered by topmost) | **FrameArrived 29–40ms + frame content delivered** | WGC captures the window's own surface — works while covered; impossible for DD/mss/BitBlt |
| Per-window isolation | item 306x193 vs window 320x200 | `is_border_required=False` strips frame/titlebar |
| surface->numpy copy | **1.8–3.2ms** for ~316x193 | trivial vs PNG encode |
| frame pixels | 96.6% non-black, mean ~234 (white bg) | real content verified |
| frame.system_relative_time | present (ticks) | frame timestamps available |
| `session.dirty_region_mode` | attribute exists | delivery of dirty rects not measured |

Caveats found:
- Stale pooled frames: after resize, `try_get_next_frame` returned a
  frame whose texture (306x193) predates content_size (316x193) —
  consumers must read dims from the texture desc, not content_size.
- winrt pip namespace packages are fragile under `--target` (shared
  `winrt/` dir wiped by partial --upgrade) — single-shot install works.
- Wake ~40ms is slower than P1 WinEvents (~14ms) but content-scoped and
  carries the frame itself; complementary granularity.

**P6 verdict: PASS** — per-window event-driven capture is real:
FrameArrived on content change + occluded-surface capture + ~2ms
surface->numpy. Unique capabilities vs all other layers measured.
Integration shape for P11: daemon-side per-window frame pool feeding a
"window changed" wake + fresh content rect; heavier dep footprint
(5+ winrt wheels + D3D11 boilerplate) argues for optional-plugin seam.

## P7 — numpy FFT-NCC template matching (no cv2)

Probe: `p7_template.py` — FFT cross-correlation + integral-image local
normalization, pure numpy. Template: 120x60 text patch from
`p1_target --drawtext`, ground-truth offset known.

| Metric | Result |
|---|---|
| FFT-NCC full screen (1920x1080) | **373ms p50** — hit 10/10 pixel-exact, score 1.0 |
| FFT-NCC scoped region (640x480) | **31ms p50, p95 32** — hit 10/10 |
| Direct sliding-window NCC (same region) | ~13,000ms — 400x slower; FFT wins decisively |
| Noise robustness (sigma=12 gaussian) | hit, score 0.993 |
| Scale robustness (template ±10%) | **miss both ways, score ~0.32** — NCC is scale-brittle; scale-invariance needs a pyramid pass (not built) |

**P7 verdict: PASS-SCOPED** — viable only scoped to a known window/region
(~31ms vs UIA hint 18-31ms, so it is a complement for pixel-only
content: canvas, images, icons). Full-screen search (373ms) is not
competitive as a primary locator. Requires numpy (new extension dep).
Scale/DPI fragility documented: templates must be captured at the same
scale they are matched at.

## P11 — event-driven hint refresh (daemon seam end-to-end)

Probe: `p11_daemon.py` — WinEvent hook -> hwnd/event filter ->
`cu_hints` enum on the affected hwnd -> refreshed hint set. Measured
event->hints-ready + filter efficiency, plus enum cost breakdown by
provider type.

| Metric | Result |
|---|---|
| Event->refreshed hints, per-hwnd enum (plain win32 window, MSAA-proxied provider) | **~600ms** steady (ElementFromHandle ~82ms + FindAll subtree ~526ms, 4 hints) |
| Same on Notepad (native UIA provider) | **~55ms** (FromHandle 9ms + enum 46ms, 22 hints) |
| Per-call `_uia_core()` | 48ms first / 1.3-1.7ms cached — NOT the bottleneck; resident core is cheap |
| Filter efficiency | 199 ambient events -> 16 triggered refreshes (92% filtered before any UIA call) |
| Noise floor | 0 events in idle 3s |

Provider cost distribution is the design-shaping finding:
**enum cost spans ~10x (55ms UIA-native .. 610ms MSAA-proxy)**. Consequences:

- The daemon seam is justified ONLY as a resident async refresher —
  the agent reads a pre-computed sidecar at ~0 cost vs the 591ms cold
  `screenshot --hints` path (>10x effective for repeated reads). The
  ">=2x perception" criterion is met by the residency model, not by
  per-refresh speed on hostile providers.
- Refresh must be debounced/coalesced per hwnd (a move burst = one
  re-enum after settle, not N), and heavy MSAA windows may warrant
  lazy/on-demand enum instead of eager.
- `_uia_core()` per call is fine cached, but a resident core removes
  even that.

**P11 verdict: SEAM JUSTIFIED, design-constrained.** Recommended
production seam: `cu_events.py` (hook pump thread -> per-hwnd debounced
refresh -> existing sidecar format + generation bump). Order of
integration by cost/benefit: P3 (one-liners, mandatory) > P1 (wake
channel, ~14ms, cheap) > P4 (new OCR command, independent value) >
P11 daemon (needs the design + tests) > P6 (optional plugin, heavy
winrt+D3D11 deps, unique occluded-window capability) > P7
(scratch-complement until a consumer exists) > P5/P8/P9/P10 (dead/
observability-only/redundant/mapped-only — stay out).

## Pending

None — Phase 2 hypothesis sweep complete. Phase 3: verdict matrix +
final gates + integration decision per technique.
