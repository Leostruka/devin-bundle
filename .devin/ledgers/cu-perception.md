# GATES: cu-perception (Windows perception/localization stack)

Spec: `.devin/scratch/cu-perception-ready.md`. Branch `feat/cu-perception`.
Phase structure: F1 map+inventory+hypotheses+thresholds (STOP) -> F2 per-hypothesis tests -> F3 verdict matrix.

## Phase 1

- [x] G1.1: inventory verified by tools (not deduced)
  CHECK: grep evidence per layer in `.devin/research/cu-perception-phase1.md` section 2
  EXPECT: every "present/absent" claim cites file:line or empty-grep result
  EVIDENCE: greps run 2026-10-04; cu_capture.py _BACKENDS={"mss"} L43, apply_delta L71; UIA FindAllBuildCache cu_hints.py L126-130; zero matches SetWinEventHook/AddAutomationEventHandler/GraphicsCapture/cv2/numpy; OCR only cu_terminal.py L425; DPI=SetProcessDpiAwareness(2) screenshot.py L29 (per-monitor v1, not v2)

- [x] G1.2: theoretical map complete, low->high
  CHECK: `.devin/research/cu-perception-phase1.md` section 1 covers compositor/GPU, win32k/user32 events, UIA/MSAA, semantic channels, pixels, decision
  EXPECT: each layer = mechanism + theoretical cost + impl state + >=1 primary source URL
  EVIDENCE: doc section 1 — L0 GPU (12 URLs), L1 WinEvents (4), L2 UIA/MSAA (7), L4 pixels (7), x-cut DPI/ETW (5); L3/L5 verified from extension files

- [x] G1.3: hypothesis table per layer with verdicts
  CHECK: section 3 lists all 10 pre-mapped candidates + any new; each has evidence, feasible/infeasible, predicted metric
  EXPECT: infeasible layers documented with reason, none silently skipped
  EVIDENCE: P1-P11 — VIABLE x6, VIABLE-CONSTRAINED x1, VIABLE-SCOPED x1, INVIABLE(ETW)+REJECTED(MSAA)+MAPPED-ONLY(DWM) with reasons; in-context hooks/RapidOCR/Magnification recorded as not-pursued

- [x] G1.4: metrics + thresholds pre-registered
  CHECK: section 4 defines metrics, harness, thresholds BEFORE any phase-2 test
  EXPECT: thresholds numeric, tied to frozen baselines (cu-realtime-phase1.md table)
  EVIDENCE: 8 metrics with baselines + pass thresholds; spec thresholds bound; N>=5/p50

- [x] G1.5: bundle audit green
  CHECK: python audit.py
  EXPECT: 0 errors
  EVIDENCE: "Errors: 0, Warnings: 9" — warnings = pre-existing live!=bundle drift + __pycache__, unrelated

- [x] G1.6: phase-1 checkpoint committed on feat/cu-perception
  CHECK: git log -1 --oneline && git status --porcelain
  EXPECT: doc committed, tree clean
  EVIDENCE: fcf7586, status clean

## Phase 2 (approved 2026-10-04)

- [x] G2.P1: WinEvents daemon
  CHECK: python .devin/scratch/cu-perception/p1_winevents.py --trials 10
  EXPECT: wake_ms <100 p50
  EVIDENCE: location_foreign 21.2ms p50, name_foreign 7.6ms p50 (n=10 each); own 0.54ms; noise ~1/3s; SKIPOWNPROCESS drops self-triggered events (documented finding)

- [x] G2.P2: UIA event handlers (MTA + CacheRequest)
  CHECK: p2_uia_events.py --trials 5 + decisive scope experiment (inline)
  EXPECT: wake_ms <100 on cooperating providers OR documented coverage limit
  EVIDENCE: root-children structure wake 264ms p50 (spawn-dominated); element-scoped/property handlers ZERO delivery on XAML Notepad + plain windows (verified mutations produced no events); Focus works — verdict PASS-CONSTRAINED, coarse scope only
- [x] G2.P3: PER_MONITOR_AWARE_V2 + ElementFromPoint round-trip precision
  CHECK: p3_dpi.py --notepad (extension venv)
  EXPECT: hit-rate >= baseline, no regression
  EVIDENCE: 22/22 round-trip hits (100%); fresh proc starts DPI-unaware (awareness must be set per entry point); GetWindowRect includes ~5px invisible borders vs DWMWA bounds on 13/29 windows; host=96DPI (no scaling stress)
- [x] G2.P4: OCR text->coords general channel
  CHECK: p4_ocr.py --trials 10 (extension venv)
  EXPECT: locate_ms <200 p50 on non-UIA surface
  EVIDENCE: 7.76ms p50 steady (first ~48ms); hit-rate 92.9%; coord fidelity 11/12 re-crop; MaxImageDimension=10000; ~48px image-height floor + winrt-Foundation.Collections dep discovered
- [x] G2.P5: DXGI Desktop Duplication backend
  CHECK: p5_dxgi.py + raw-COM matrix (blocking vs poll, move vs resize+spam, DuplicateOutput vs Output1)
  EXPECT: frame-event wake OR measurable capture advantage
  EVIDENCE: blocking AcquireNextFrame never wakes for desktop updates (10/10 timeout while move occurs inside wait); single updates never reach queue via poll(0) either (0 frames/3s vs mss-diff 10/10 @15-24ms); frames only flow under sustained spam (76 via dxcam thread); E_NOINTERFACE on resource-less frames unhandled by dxcam — verdict FAIL-CONSTRAINED, scratch-only, apply_delta stays orphaned
- [x] G2.P6: WGC per-window capture
  CHECK: p6_wgc.py --trials 10 (raw winrt create_for_window + free-threaded pool + FrameArrived event)
  EXPECT: event-driven per-window frame delivery OR documented failure
  EVIDENCE: FrameArrived 38-44ms p50 on content change (6/6); pure moves correctly fire 0/3; occluded window still delivers (29-40ms, unique vs DD/mss); is_border_required=False -> content-only rect; surface->numpy 1.8-3.2ms; 96.6% nonblack verified; stale-pooled-frame caveat on resize — verdict PASS, optional-plugin seam
- [x] G2.P7: numpy FFT-NCC template match
  CHECK: p7_template.py --trials 10 (FFT + integral-image norm, pure numpy)
  EXPECT: measured latency + precision vs direct NCC
  EVIDENCE: scoped region 31ms p50 10/10 pixel-exact score 1.0; full-screen 373ms (not competitive vs UIA); direct impl 13s (400x slower); noise ok; +-10% scale misses — verdict PASS-SCOPED (complement for pixel-only content)
- [x] G2.P11: event-driven perception daemon integration verdict
  CHECK: p11_daemon.py --trials 8 (WinEvent->filter->per-hwnd cu_hints enum->hints refreshed)
  EXPECT: measured event->hints latency + filter efficiency vs 591ms cold baseline
  EVIDENCE: refresh 55ms (UIA-native Notepad, 22 hints) .. 600ms (MSAA-proxied plain window, 4 hints) — 10x provider spread; filter drops 92% of ambient events pre-UIA; _uia_core cached 1.3-1.7ms — verdict SEAM JUSTIFIED design-constrained (resident async refresher + per-hwnd debounce; >=2x met via residency not per-refresh speed)

## Phase 3

- [x] G3.1: verdict matrix layer->decision; integration declared seams only
  CHECK: matrix in cu-perception-phase2.md (P1-P11 disposition per technique)
  EXPECT: integrate / scratch-only / infeasible decision each, no silent drops
  EVIDENCE: INTEGRATE=P3,P4,P1+P11(cu_events seam); optional-plugin=P6; scratch=P5,P7; excluded=P8,P9,P10; order P3>P4>P1+P11>P6
- [x] G3.2: final gates green (audit, pytest scoped if prod code changed, validate-skill-format if SKILL.md touched)
  CHECK: python audit.py + git diff main -- extensions/ + AI-signature scan
  EXPECT: 0 errors; no prod diffs (probes are scratch-only)
  EVIDENCE: audit Errors=0 Warnings=9 (pre-existing pycache+drift); extensions/ diff vs main = 0 files; sig scan clean — no prod code changed so no pytest needed

## Phase 4 — production integration (approved "com p6")

| Gate | Check | Expect | Evidence |
|---|---|---|---|
| G4.1 | P3 shipped | cu_dpi pmv2 + DWM bounds | `8fe7662`; live `set_dpi_awareness()` -> "pmv2" |
| G4.2 | P4 shipped | cu_ocr word rects screen space | `02d844a`; live `all --region` -> 23 words real coords |
| G4.3 | P1+P11 shipped | daemon + sidecar + debounce | `5ce8ee9`; live notepad: hook=1, watched gen 1, filtered ambient |
| G4.4 | P6 shipped optional | caps degrades w/o deps | `37e1af4`; live `caps` -> available:false structured reason |
| G4.5 | unit tests | new files green | 34/34: dpi 7, ocr 9, events 11, wgc 7 |
| G4.6 | full suite | no regression | 1577 passed, 4 skipped (pre-existing) |
| G4.7 | audit + AI-scan | 0 errors, clean | audit 0 err / 9 pre-existing warns; scan clean |
| G4.8 | diff scope | only intended files | git status: 9 modified + 8 new, all listed above |
