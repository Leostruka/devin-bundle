# CU perception Phase 1: stack map, verified inventory, hypotheses, thresholds

Spec: `.devin/scratch/cu-perception-ready.md`. Branch `feat/cu-perception`.
Prior art: `cu-realtime-{phase1,phase2,phase4,verdict}.md` (merged via PR #80/#81).
All inventory claims verified with tools on 2026-10-04; grep/file evidence inline.
Ledger: `.devin/ledgers/cu-perception.md` (gitignored working file).

## 1. Theoretical map — perception/localization stack, low -> high

Layer model: each layer can deliver "what is on screen" (perception) and/or
"where is target X" (localization) and/or "tell me when it changes" (wake).

### L0 — GPU / compositor (DWM, DXGI, WGC)

| Mechanism | What it gives | Theoretical cost | Impl state |
|---|---|---|---|
| GDI BitBlt screen-DC copy (`mss`) | full/region pixels, CPU buffer | 28.1ms full / 6.9ms region measured (cu_bench); synchronous poll; misses protected output | **PRESENT** — sole backend, `_BACKENDS={"mss"}` `cu_capture.py:43` |
| DXGI Desktop Duplication (`IDXGIOutputDuplication`) | per-OUTPUT desktop frames as D3D textures; `AcquireNextFrame(timeout)` **blocks until new frame**; `GetFrameDirtyRects`/`GetFrameMoveRects` = free delta rects | frame acquire ~sub-ms GPU-side; one duplication per output; Win8+; ACCESS_LOST on mode change; no secure desktop | ABSENT — but `apply_delta()` already implements move-then-dirty reconstruction `cu_capture.py:71-105` (DXGI semantics, written ahead of the backend) |
| Windows.Graphics.Capture (`FramePool.FrameArrived`) | per-WINDOW and per-monitor GPU frames; **push event** `FrameArrived`; `DirtyRegions` on Win11 24H2 | requires 1903+ interop (`IGraphicsCaptureItemInterop::CreateForWindow/Monitor`), DispatcherQueue (removable via `CreateFreeThreaded`, 1809+), D3D11 device; border can't be removed unpackaged | ABSENT — only `winrt-Windows.Graphics.Imaging` vendored (`requirements.txt:12`); Capture package not vendored |
| `DwmRegisterThumbnail` | live thumbnail relation src->dst HWND | DWM renders INTO your window; **no pixel handoff to app** | ABSENT — verified inviable for perception (no CPU/GPU surface access) |
| `PrintWindow(PW_RENDERFULLCONTENT)` | occluded-window stills incl. D3D content | synchronous, unpredictable latency; RFC flag undocumented in ref but MS-confirmed | ABSENT — candidate fallback, not real-time |
| Compositor timing | `IDXGIOutput::WaitForVBlank` (documented block-to-vblank); `DwmGetCompositionTimingInfo` (documented but discouraged, hwnd=NULL since Win8.1); D3DKMT/DwmDx internals **undocumented** — research boundary per spec | — | ABSENT — vsync probe only if needed |

Sources: [desktop-dup-api](https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/desktop-dup-api), [AcquireNextFrame](https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_2/nf-dxgi1_2-idxgioutputduplication-acquirenextframe), [DirtyRects](https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_2/nf-dxgi1_2-idxgioutputduplication-getframedirtyrects), [MoveRects](https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_2/nf-dxgi1_2-idxgioutputduplication-getframemoverects), [WGC screen-capture](https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture), [WGC interop](https://learn.microsoft.com/en-us/windows/win32/api/windows.graphics.capture.interop/nn-windows-graphics-capture-interop-igraphicscaptureiteminterop), [CreateFreeThreaded](https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture.direct3d11captureframepool.createfreethreaded), [DirtyRegionMode](https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture.graphicscapturedirtyregionmode), [DwmRegisterThumbnail](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/nf-dwmapi-dwmregisterthumbnail), [PrintWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-printwindow), [WaitForVBlank](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/nf-dxgi-idxgioutput-waitforvblank), [DwmGetCompositionTimingInfo](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/nf-dwmapi-dwmgetcompositiontiminginfo)

### L1 — Window-manager events (win32k/user32 WinEvents)

| Mechanism | What it gives | Theoretical cost | Impl state |
|---|---|---|---|
| `SetWinEventHook` out-of-context (`WINEVENT_OUTOFCONTEXT`, hmod=NULL) | async callback on `EVENT_SYSTEM_FOREGROUND`, `EVENT_OBJECT_CREATE/DESTROY/SHOW/HIDE/FOCUS/SELECTION/LOCATIONCHANGE/NAMECHANGE/VALUECHANGE` + hwnd/idObject/idChild; ordered delivery | marshaled cross-process → "noticeably slower than in-context", no doc'd ms; needs message-pump thread; same-thread Unhook; `SKIPOWNPROCESS` filter | **ABSENT** — zero matches for `SetWinEventHook|EVENT_OBJECT_` in extension |
| in-context hook | synchronous, fastest | requires real DLL injected into target — **impossible from pure Python** and injection-adjacent | out of scope (security boundary) |
| `AccessibleObjectFromEvent` | resolves WinEvent (hwnd,idObject,idChild) -> IAccessible | one COM call per event | ABSENT |

Sources: [SetWinEventHook](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook), [out-of-context hooks](https://learn.microsoft.com/en-us/windows/win32/winauto/out-of-context-hook-functions), [event constants](https://learn.microsoft.com/en-us/windows/win32/winauto/event-constants), [reentrancy](https://learn.microsoft.com/en-us/windows/win32/winauto/guarding-against-reentrancy-in-hook-functions)

### L2 — Accessibility tree (UIA / MSAA)

| Mechanism | What it gives | Theoretical cost | Impl state |
|---|---|---|---|
| `FindAllBuildCache` enum | clickable elements + bounds/name/type in one cross-process call | **17.6ms p50** focused window measured; per-property getters are per-call RPC (MS: "slow and inefficient") | **PRESENT** — `cu_hints.py:119-145` (CreateCacheRequest + FindAllBuildCache, daemon thread, 6s timeout) |
| UIA patterns (Invoke/Value/Scroll/Text) | semantic act/read | same RPC model; `uia_invoke` ~50ms act share measured (p4) | **PRESENT** — `cu_scope.py:377-393`, `uia_invoke` L444; TextPattern in `cu_terminal.py:206-225` |
| UIA client event handlers (`AddAutomationEventHandler`, `AddPropertyChangedEventHandler`, `AddStructureChangedEventHandler`, `AddFocusChangedEventHandler`) | push events carrying sender element **with cached props** (CacheRequest at register) | needs dedicated MTA thread (STA "can prevent clients from removing event handlers"); no client pump needed on MTA; coverage provider-dependent (MS: "not all property changes cause events") | **ABSENT** — zero matches for `AddAutomationEventHandler`/`AddPropertyChangedEventHandler` |
| MSAA / IAccessible | legacy coverage | UIA already **proxies MSAA servers** — legacy apps appear in UIA with less info; per-call COM, no caching | ABSENT and not needed as separate pipeline; only `AccessibleObjectFromEvent` as edge-case resolver |

Sources: [UIA events for clients](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-eventsforclients), [UIA threading](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-threading), [UIA caching](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-cachingforclients), [event IDs](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-event-ids), [providers/proxies](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-providersoverview), [MSAA vs UIA](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-msaa), [architecture & interop](https://learn.microsoft.com/en-us/windows/win32/winauto/architecture-and-interoperability)

### L3 — App-specific semantic channels

| Channel | Surface | Cost (measured) | Impl state |
|---|---|---|---|
| CDP/BiDi websocket | bound Chromium | `Runtime.evaluate` RTT 0.81ms p50; DOM reflex 16.2ms event->click | **PRESENT** — `browser.py`, `browser_events.py` daemon (CDP Network/Log/Runtime/Page + BiDi subscriptions) |
| ConPTY / TextPattern / `CONOUT$` / WinRT-OCR(mintty) | terminals | `recv --wait` hit ~196ms; PTY link reflex 0.33s src->dst | **PRESENT** — `cu_terminal.py` (WT TextPattern L174-225, conhost CONOUT$, mintty OCR L425-460), `terminal.py` spawn/link |
| QMP guest channel | QEMU envs | socket JSON | **PRESENT** — `cu_qmp.py`, `cu_qmp_backend.py`, `cu_guest*.py` |
| adb | Android envs | shell RTT | **PRESENT** — `cu_adb_backend.py` |

### L4 — Pixels (capture, OCR, vision)

| Mechanism | What it gives | Theoretical cost | Impl state |
|---|---|---|---|
| PNG encode + vision read | full-fidelity scene to the model | **175.2ms encode** + file + image tokens + inference | **PRESENT** — `screenshot.py` PIL path |
| `Windows.Media.Ocr` word BoundingRect | text -> pixel coords on ANY raster surface (canvas, images, mintty) | community ~30-100ms per 500-2000px region (unverified); `[RemoteAsync]` out-of-proc; word rects in image space + capture offset; `MaxImageDimension` runtime-queried; small images need upscale | **PARTIAL** — vendored (`requirements.txt:7-12`) but wired only to mintty `cu_terminal.py:425`; not a general text->coords channel |
| Template matching (numpy FFT-NCC, Lewis 1995) | visual target -> coords where no DOM/UIA/text exists | ~10-40ms est for 64x64 in 1080p (float32 rfft2); sub-px via parabolic peak/phase correlation; NOT scale-invariant (per-DPI templates) | **ABSENT** — no numpy/cv2/matchTemplate (grep 0); numpy would be a NEW dep |
| Delta perception (dirty/move rects) | reconstruct changed regions only | DXGI gives rects free with frame; `apply_delta` already implements move->dirty order | **DORMANT** — `cu_capture.py:71-105` written for DXGI, no producer |

Sources: [OcrEngine](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine), [OcrWord.BoundingRect](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrword.boundingrect), [MaxImageDimension](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine.maximagedimension), [screen-ocr winrt driver](https://github.com/wolfmanstout/screen-ocr/blob/master/screen_ocr/_winrt.py), [skimage match_template](https://github.com/scikit-image/scikit-image/blob/v0.25.2/skimage/feature/template.py), [phase_cross_correlation](https://scikit-image.org/docs/stable/api/skimage.registration.html), [RapidOCR](https://github.com/RapidAI/RapidOCR)

### L5 — Decision / reflexes

| Mechanism | State |
|---|---|
| hints sidecar (`devin-cu-hints.json` schema v2, session/generation/TTL) | **PRESENT** — `cu_hints.py:9-13`, `resolve_hint` L514 with typed stale/expired rejection |
| laya shadow suggestion (<=8 candidates, `suggestion|abstain`) | **PRESENT** — `cu_decision.py`; steady-state **432ms p50** measured (p4); assist gated on approved calibration (user decision) |
| reflex consumers | PTY `link` **shipped** (0.33s); UIA/DOM resident reflexes **prototype-only** in `.devin/scratch/cu-realtime/p4_probe.py` (54ms/16ms) — integration gap already identified in phase4 |

### Cross-cutting — coordinate space / DPI

Verified: scripts call `SetProcessDpiAwareness(2)` = **PROCESS_PER_MONITOR_DPI_AWARE (v1)** with `SetProcessDPIAware` fallback (`screenshot.py:25-34`, same in `mouse.py`, `type_text.py`, `record.py`). NOT per-monitor v2. USAGE.md's "per-monitor DPI awareness" claim is loose — v2 (`SetProcessDpiAwarenessContext`, Win10 1703+) adds child-window `WM_DPICHANGED`, non-client/menu/comctl32 scaling.
Doc facts: UIA `BoundingRectangle`/`ElementFromPoint` are **physical** pixels always ([UIA screen scaling](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-screenscaling)); `GetCursorPos` returns logical → `GetPhysicalCursorPos` exists ([doc](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getphysicalcursorpos)); mss returns raw pixels = physical **only if** process is DPI-aware; `GetWindowRect` virtualizes for unaware callers; `DWMWA_EXTENDED_FRAME_BOUNDS` = real visible frame (physical claim is community-grade — verify empirically).

### Cross-cutting — ETW

Mechanism documented (`StartTrace`/`EnableTraceEx2`/`ProcessTrace` real-time); relevant manifests exist (`Microsoft-Windows-UIAutomationCore` {820a42d8-...}, `Microsoft-Windows-Dwm-Core`, `Microsoft-Windows-Win32k`) but **event schemas undocumented**; real-time consumption needs admin/"Performance Log Users"; Python = `pywintrace` only (unmaintained ~2019). Sources: [consuming events](https://learn.microsoft.com/en-us/windows/win32/etw/consuming-events), [OpenTrace access](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/nf-evntrace-opentracea), [EnableTraceEx2](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/nf-evntrace-enabletraceex2)

## 2. Verified inventory (tool-verified, this machine)

| Claim in spec | Verification | Result |
|---|---|---|
| capture seam, mss only | `cu_capture.py:43` `_BACKENDS = {"mss"}`; `grab()` L56 | CONFIRMED |
| apply_delta for DXGI, no producer | `cu_capture.py:71-105` | CONFIRMED (code exists, zero callers — grep `apply_delta` = def only) |
| UIA enum ~17-31ms, patterns via comtypes | `cu_hints.py:119-145`; `cu_scope.py:328-424`; cu_bench hints_enum 17.6ms p50 | CONFIRMED |
| no WinEvents | grep `SetWinEventHook|EVENT_OBJECT_|WinEventProc` → 0 matches | CONFIRMED |
| no UIA event handlers | grep `AddAutomationEventHandler|AddPropertyChangedEventHandler|AddStructureChanged` → 0 | CONFIRMED |
| no DXGI/WGC/thumbnail | grep `DXGI|AcquireNextFrame|GraphicsCapture|DwmRegisterThumbnail` → 0 code matches (1 doc comment, 1 unrelated winrt pkg) | CONFIRMED |
| no ETW | grep `StartTrace|EventTrace|TDH|etw` → all false positives ("network", "between") | CONFIRMED |
| OCR mintty-only | `cu_terminal.py:425-460` `_ocr_image`; sole call site L555 | CONFIRMED |
| no template matching | grep `cv2|opencv|matchTemplate|numpy` → 0 | CONFIRMED |
| DPI per-monitor | `SetProcessDpiAwareness(2)` `screenshot.py:29` (v1, not v2); fallback `SetProcessDPIAware` L32 | CONFIRMED — correction to spec: v1 present, **v2 absent** |
| semantic channels | `browser.py`, `browser_events.py`, `cu_terminal.py`, `cu_qmp*.py`, `cu_adb_backend.py` all present | CONFIRMED |
| hints sidecar + laya | `cu_hints.py:9-13` schema v2; `cu_decision.py` laya shadow | CONFIRMED |
| reflex prototypes | `.devin/scratch/cu-realtime/{p4_probe.py,p4_laya.py,s1_probe.py}` exist | CONFIRMED |

Frozen baselines (cu_bench, `.devin/research/cu-benchmark-baseline.json` +
phase1 fresh): capture_full 28.1ms (frozen 20.5), capture_region 6.9ms,
png_encode 175.2ms (frozen 101.8), hints_enum 17.6ms (frozen 30.9),
screenshot.py CLI 321ms, --hints 591ms, agent turn p50 9.55s,
GUI in-process cycle 249ms (enum31/invoke50/verify168), reflexes DOM 16.2ms /
UIA ~54ms / PTY 0.33s, laya 432ms p50.

## 3. Hypothesis table (evidence -> verdict -> predicted metric)

Pre-registered BEFORE any test. Order = phase-2 execution order (impact/cost).

| # | Hypothesis | Layer | Evidence (sec.1) | Verdict | Predicted metric |
|---|---|---|---|---|---|
| P1 | **WinEvents daemon** (out-of-context, pump thread): OS push bus for foreground/create/destroy/focus/name/location/value -> wake + hwnd pre-filter before enum | L1 | works from Python (hmod=NULL); ordered async delivery; SKIPOWNPROCESS | **VIABLE** — cheapest real wake channel | `wake_ms` event->consumer < 100ms p50 (vs poll floor = enum 17.6ms x interval); ~0 cost idle |
| P2 | **UIA event handlers** (MTA thread, Structure/Property/Focus + CacheRequest): semantic wake carrying element+props | L2 | documented threading model; provider-dependent coverage — pair with P1 as fallback | **VIABLE-CONSTRAINED** | `wake_ms` < 100ms on cooperating providers; coverage % measurable per-app |
| P3 | **PER_MONITOR_AWARE_V2** at startup + physical-space audit (GetPhysicalCursorPos, DWMWA bounds) + `ElementFromPoint` round-trip precision gate | x-cut | UIA rects are physical always; v1 lacks v2 scaling fixes | **VIABLE** — cheap, enabler for precision metric | `coord_precision`: round-trip hit rate >= baseline (no regression), ideally > |
| P4 | **General OCR text->coords**: WinRT OcrEngine word BoundingRect on arbitrary region (dedicated worker thread for COM) | L4 | vendored already; word rects + capture offset = coords | **VIABLE** — new capability (non-UIA surfaces) | `locate_ms` ~30-100ms predicted (community figure, verify); new metric `ocr_hit%` |
| P5 | **DXGI Desktop Duplication backend** in `cu_capture` seam: blocking `AcquireNextFrame` = frame-event; dirty/move -> `apply_delta` | L0 | blocking wait documented; delta code already written; one dup per output | **VIABLE** — highest impl cost (COM/D3D11 from comtypes/ctypes; no mature Py binding) | `capture_ms` < mss 28.1 full (predicted 1-10ms); `wake_ms` new-frame < poll equivalent; `delta_coverage%` |
| P6 | **WGC backend** (free-threaded FrameArrived): per-WINDOW capture + push event; DirtyRegions on 24H2 | L0 | documented interop + event; needs `winrt-Windows.Graphics.Capture` pkg + D3D11 interop | **VIABLE** — only documented per-window GPU capture | per-window `capture_ms`; `wake_ms` frame->consumer; compare vs P5 |
| P7 | **numpy FFT-NCC template match**: visual targets (icons/canvas/rasterized text) | L4 | FFT-NCC standard; ~10-40ms est; no cv2 needed; NEW dep numpy | **VIABLE-SCOPED** — dep cost noted | `locate_ms` p50; `match_precision` sub-px; false-positive rate at threshold |
| P8 | **ETW telemetry** (UIAutomationCore/DwmCore/Win32k providers) | x-cut | schemas undocumented; admin/PLU required; pywintrace unmaintained | **INVIABLE** operational / observability-only | documented, not implemented — reason recorded |
| P9 | **MSAA pipeline** | L2 | UIA proxies MSAA servers automatically | **REJECTED** — redundant; `AccessibleObjectFromEvent` kept as P1 edge-case resolver only | n/a |
| P10 | **DWM internals** (composition surfaces, present timing) | L0 | public surface = WaitForVBlank + discouraged timing API; D3DKMT/DwmDx undocumented | **MAPPED-ONLY** — undocumented internals = research boundary per spec; WaitForVBlank available as vsync probe if P5 needs it | n/a |
| P11 | **Event-driven perception daemon** (integration shape): resident process combining P1+P2 wake -> `enum_clickables` on demand -> sidecar refresh; sibling of `browser_events.py`/`link` pump | L1+L2 | p4 proved resident reflexes 16-54ms; subprocess-per-poll kills them (150-300ms) | **VIABLE if P1/P2 pass** — declared seam: new `cu_events.py` daemon, inbox/drain contract like `browser_events` | end-to-end `event->hints-refresh` < 200ms p50 |

Not pursued: in-context WinEvent hooks (DLL injection — security boundary),
RapidOCR (loses to vendored WinRT on cold start/latency/weight — revisit only
if WinRT accuracy fails), Magnification API (deprecated-ish, unreliable).

## 4. Metrics + thresholds (pre-registered)

Harness: `.devin/scratch/cu-perception/` probes + `cu_bench.py` extensions.
N>=5 runs per measurement, **p50 primary**, p95 reported. Warmup >=2.
Machine = this host; baselines frozen above.

| Metric | Definition | Baseline | Pass threshold |
|---|---|---|---|
| `capture_ms` | grab -> CPU buffer | mss full 28.1 / region 6.9 | P5/P6: < 28.1 full AND < region-equivalent when deltas used; OR wake capability below |
| `wake_ms` | OS event (frame/UI change) -> consumer notified, page/OS-side stamps | none — polling only | NEW CAPABILITY: < 100ms p50 AND < equivalent poll interval cost |
| `locate_ms` | target -> usable coords | hints_enum 17.6 (UIA surfaces only) | P4/P7: < 200ms p50 on non-UIA surfaces (new coverage), no regression on UIA path |
| `coord_precision` | `ElementFromPoint(center(rect))` round-trip hit rate + center error px | implicit (clicks land today) | >= baseline; P3 must not regress |
| `tokens/cycle` | bytes of perception payload (JSON vs PNG) | hints JSON ~1.4KB vs PNG ~100KB+ | no regression |
| `delta_coverage` | % of frame area delivered via dirty/move rects vs full | 0 (no producer) | reported, no threshold |
| `ocr_hit`/`match_precision` | OCR words found w/ sane rects; NCC peak vs truth | none | reported; match FPR < 5% at chosen threshold |

Spec thresholds (bind to above): perception >=2x faster on same task OR new
measurable capability (OS-event wake < poll); localization precision >=
baseline; **zero security violations** (no injection, no cross-process hooks
in-context, no undocumented win32k internals, scoped/consented channels only).

Phase-2 execution order: P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7, then P11
integration verdict. One commit checkpoint per hypothesis.

## 5. Checkpoint

Phase 1 = this doc + ledger. STOP per spec: Phase 2 awaits approval.
