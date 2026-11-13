# CU real-time: phase 4 - remaining ceilings

Date: 2026-10-12. Follow-up to `cu-realtime-verdict.md`: tests the three
avenues left untested - (a) deterministic reflexes beyond PTY (UIA/DOM
consumers), (b) laya suggestion latency in shadow mode, (c) a full GUI
perceive->act->verify cycle. Harness: `.devin/scratch/cu-realtime/`
(`p4_probe.py`, `p4_laya.py`, `reflex_page.html`). All reflex loops are
resident processes using the extension modules in-process; the action
surface is a fixed allowlist, one action per run, poll caps, deadlines.

## Results

| Probe | Metric | Value | Verdict |
|---|---|---|---|
| DOM reflex | event -> reaction (page-side `performance.now`) | **16.2 ms** | PASS - fastest reflex measured |
| DOM reflex | resident `Runtime.evaluate` round-trip | 0.81 ms p50 (~20 Hz poll) | - |
| UIA reflex | detect -> `uia_invoke` delivered | **54.4 ms** | PASS |
| UIA reflex | spawn -> hwnd -> element -> action, end to end | 840.7 ms | decomposition below |
| GUI cycle | enum -> invoke File -> enum verify, in-process | **249.3 ms** total | PASS |
| GUI cycle | perceive / act / verify split | 31.3 / 50.2 / 167.8 ms | verify includes menu render |
| Laya shadow | `recommend()` steady-state, CPU | **432 ms p50** (max 443) | fits inside a turn |
| Laya shadow | engine build / first predict (cold) | 4.2 s / 57.1 s | resident worker mandatory |

## Reflex consumer for UIA/DOM events (P4a)

Prototype proved sub-second model-free reflexes outside the PTY domain:

- DOM (bound browser): resident websocket `Runtime.evaluate` poll at
  ~20 Hz; a timed element was clicked **16.2 ms** after it appeared
  (page-side stamps). Fastest reflex in the suite - an order of
  magnitude below the PTY `link` (0.33 s), because a ws eval is ~0.8 ms
  while the link pump runs per output line.
- UIA (scoped window): `cu_scope.find_windows` + per-hwnd
  `_enum_impl` poll detected a new Notepad window's element, then
  `cu_scope.uia_invoke(hwnd, name=...)` delivered the Invoke pattern
  **54 ms** after detection. The 840 ms end-to-end number is mostly
  environment: 471 ms OS window creation + 315 ms app UI build; the
  reflex share is poll granularity + ~54 ms action.

Architectural finding: the reflex consumer must be **resident**. A
subprocess-per-poll loop pays ~150-300 ms per call (the H1 result in
miniature) and could never reach 16 ms. The extension's daemons
(`cu_session`, `browser_events`, the `link` pump) already embody this;
a UIA/DOM reflex daemon is the missing sibling - the pieces exist
(`enum_clickables`, `uia_invoke`, `_WSClient`, `browser_events` drain).

Two real constraints found:

- Provider elements (Notepad/XAML) carry `hwnd: null` in the enum;
  `cu_hints.uia_perform` re-resolves by entry hwnd and therefore
  returns `no_hwnd` for them - `mouse.py --via uia` silently falls back
  to a physical click on these. `cu_scope.uia_invoke(hwnd, name=...)`
  is the correct provider-side path (addresses by window + element
  name).
- Win11 Notepad owns two `Notepad`-class hwnds (tab-strip frame vs
  content); element goals must match the right one ("Add New Tab" is
  frame, "File" menu is content). Window spawn also runs a stub pid, so
  tracking by pid fails - track new hwnds of the class instead.

## Laya shadow latency (P4b)

`extensions/laya-tools/.venv` exists and the HF cache already holds
`convaiinnovations/laya` weights, so `load_engine({})` resolves locally
(offline flags set inside; zero downloads, `mode:"shadow"` in every
request - nothing adoptable). Measured:

- Router build: 4.2 s once per process.
- First predict: 57.1 s (lazy weight load + compile) - a per-request
  spawn is hopeless; the `serve-stdio` resident worker is the only
  viable shape, exactly as `decision_client.py` assumes.
- Steady-state `recommend()` over 8 candidates: **~432 ms p50**, well
  inside the 1000 ms `deadline_ms` the contract sends.

Latency verdict: PASS for the shadow path - a laya suggestion adds
~0.4 s to a decision turn, far under the ~9.5 s model-turn floor. It
would genuinely help: exact-match short-circuit already covers the
easy cases for free, and the closed-set call costs less than a second
of inference.

Quality verdict: UNPROVEN. All six probe requests abstained
(`no_match`) on synthetic candidates - correct contract behavior, but
says nothing about suggestion accuracy. `mode:"assist"` still requires
the calibration record (`checkpoint_sha256`, `evaluation_id`,
threshold, cardinality) bound to an approved eval - that gate stands
and is a user decision, not a measurement problem.

## Full GUI cycle (P4c)

On a scoped Notepad window, in-process: enum 31 ms -> `uia_invoke`
"File" 50 ms -> re-enum until menu items appear 168 ms. Total 249 ms
for perceive -> act -> verify with zero pixel reads. The same cycle
through CLIs costs ~0.6-1 s in subprocess overhead plus one agent
turn; the in-process floor shows the turn boundary remains the only
real cost, as established in phase 1.

## Updated position

| Lever | Status |
|---|---|
| Sub-second reflexes | now proven in all three domains: DOM 16 ms, UIA ~54 ms + poll, PTY link 0.33 s |
| Structural gap | no shipped UIA/DOM reflex consumer - prototypes only, in scratch |
| Laya | latency fits shadow use today; assist quality still gated on approved eval |
| GUI cycle | 249 ms in-process floor measured; agent-side cost is still one turn |

Recommended next step (not done): a `reflex` op inside the extension -
resident daemon taking {source: uia-enum|ws-eval|pty, match, action:
allowlisted, limit} so these consumers ship as plumbing rather than
living in `.devin/scratch`.
