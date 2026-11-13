# computer-use staged upgrades — spec

## Intent

Land the remaining stages of `.devin/research/swe2-action-capabilities.md` §6.2
that were deferred: measurement harness (4.4), GPU capture adapter, authorized
browser adapter, persistent session worker, adversarial/held-out validation.
Stages 1–3 and 7 already shipped (contracts, UIA semantics, minimum-jerk).

## Problem Statement

Current suite dispatches inputs but lacks: (a) measured per-boundary latency to
justify adapters, (b) a capture seam for DXGI/WGC, (c) any browser-semantic
channel, (d) session isolation for hang-prone UIA calls, (e) adversarial
coverage for stale/focus/Unicode races.

## Solution

Vertical tickets, each with its own gate. Measurement lands first and decides
whether the GPU-capture and persistent-session adapters are justified at all —
no speculative infrastructure.

## User Stories

1. As the agent, I want per-boundary latency numbers, so that adapter work is justified by evidence.
2. As the agent, I want a capture adapter seam, so that DXGI/DXcam can slot in without rewriting screenshot.py.
3. As the agent, I want move/dirty-rect reconstruction, so that incremental capture produces correct frames.
4. As the agent, I want an explicitly-bound browser channel, so that DOM/ARIA targeting is used only where authorized.
5. As the agent, I want a recyclable session worker, so that a stuck UIA provider cannot hang the executor.
6. As the user, I want adversarial fixtures, so that stale/focus/Unicode failures are caught before real dispatch.

## Estimated size (lines)

~700–900 across 8 tickets; each ticket ≤ ~250.

## Input / Output boundaries

- `cu_bench.py`: CLI args → JSON medians/raw samples to stdout/file.
- `cu_capture.py`: `grab(bbox) → (frame, meta)`; `apply_delta(base, w, h, bpp, moves, dirties) → frame|None`.
- `cu_browser.py`: binding file `<temp>/devin-cu-browser.json`; `check(hwnd) → (allowed, reason)`.
- `cu_session.py`: session-scoped worker; one input executor; IPC local-only.
- Tests: fake providers/controllers/clocks only — no real desktop control.

## Implementation Decisions

- Living: `cu_capture.py`, `cu_browser.py`, `cu_session.py`, `cu_bench.py`, new test files, `requirements.txt` optional pins.
- Disposable: bench JSON artifacts land in temp or `.devin/research/` as frozen evidence.
- No drivers, no auto remote-debugging enablement, no public listeners.

## Testing Decisions

- Same seam strategy as the landed work: `sys.modules` fakes for pynput/mss/UIA, fake clocks, `cu_load` helper.
- Good tests assert external behavior (zero dispatch on rejection, byte-exact delta reconstruction), never internals.

## Out of Scope

Driver/virtual-HID installs, third-party process hooking, anti-bot evasion,
UAC bypass, SWE-2 internals, distributed observability, permanent recording.
