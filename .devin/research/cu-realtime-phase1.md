# CU real-time Phase 1: loop map, baseline, hypotheses, threshold

Spec: `.devin/scratch/optimized_ready.md`. Branch `feat/cu-realtime`.
All claims verified with tools on 2026-10-04; file citations inline.

## 1. devin-cli agent loop (verified map)

Runtime is closed (`devin.exe`); map built from transcripts, hook wiring, and
installed docs, not deduced.

```
user prompt
  -> UserPromptSubmit hooks (stdin: {hook_event_name, prompt, session_id};
     may inject hookSpecificOutput.additionalContext)
       evidence: scripts/behavioral-nudge.py docstring; hooks.v1.json
  -> model turn (source:"agent" step; emits message + tool_calls[])
       evidence: transcripts ATIF-v1.7 (cli/transcripts/*.json),
       step keys {step_id, timestamp, source, message, tool_calls,
       observation, extra{generation_model, telemetry.operation=inference}}
  -> per tool call: PreToolUse hooks -> tool executes -> PostToolUse hooks
       evidence: hooks.v1.json (8 events); docs/DEVIN-CLI-COMPATIBILITY.md
       "Lifecycle hooks" (payload fields per event; PreToolUse decision:block
       + exit 2 blocks the call, siblings continue)
  -> observation.results[] appended into the SAME agent step -> next turn
       evidence: transcript step 7: tool_calls + observation co-located
  -> async injections land BETWEEN turns only:
       <subagent_completion_notification> (run_subagent is_background=true),
       user interrupt (parks subagents, 3000.11.1),
       Stop hook {"decision":"block","reason":...} re-prompts the agent once
       evidence: scripts/refine-review-prompt.py lines 7-17 (Stop does NOT
       support additionalContext but supports decision:block -> re-prompt);
       scripts/_hookrun.py merge logic (first block wins, contexts concat)
  -> turn ends -> Stop hooks -> SessionEnd
       evidence: hooks.v1.json; scripts/stop-guard.py consolidation
```

**Structural fact:** there is NO mid-turn injection surface. Every external
signal (tool result, subagent notification, stop re-prompt, user) arrives at a
turn boundary. "Real-time" therefore = minimizing turns-per-cycle and
turn latency, not interrupting the model.

## 2. Current CU cycle (perceive -> decide -> act -> reperceive)

`extensions/computer-use/` per `USAGE.md` + `skills/computer-use/SKILL.md`:

- Perceive: `exec` spawns venv python -> `screenshot.py` (mss grab ->
  PNG encode -> temp file) -> agent `read` of PNG (image tokens) or parses
  `--hints` JSON (UIA enum -> `{id,x,y,name,type,bounds}` + sidecar).
- Decide: model turn.
- Act: `exec` `mouse.py` / `type_text.py` (spawn again; `timings_ms` in JSON;
  `status: dispatched` = sent, effect not verified).
- Reperceive: another `screenshot.py` (+`read`), or `--if-changed`/`--diff`
  skip; `--verify` re-observes after dispatch.

### Measured baselines (this machine, today)

Tool-boundary bench: `extensions/computer-use/cu_bench.py --runs 10
--warmup 2` (fresh; frozen ref `.devin/research/cu-benchmark-baseline.json`,
20 runs, in parens):

| Boundary | p50 ms (today) | p50 ms (frozen) |
|---|---|---|
| startup_subprocess | 154.5 | 141.7 |
| capture_full | 28.1 | 20.5 |
| capture_region | 6.9 | 6.9 |
| png_encode | 175.2 | 101.8 |
| hints_enum | 17.6 | 30.9 |
| input_dispatch | ~0.002 | ~0.002 |

CLI wall-clock (measured via subprocess): `screenshot.py` 321ms,
`screenshot.py --hints` 591ms, `mouse.py position` 169ms,
`screenshot.py --if-changed` 315ms.
=> tool-side perceive->act->reperceive floor ~= **0.8-1.1s**.

Agent-loop level: transcript `cli/transcripts/ahead-candytuft.json` (a real
CU session, "desligue o computador", 126 agent steps, browser.py + mouse.py +
screenshot.py + type_text.py):

- per-agent-turn latency: **p50 9.55s, p90 17.4s, max 119s**
- ~75 turns invoke CU tools; agent already batches (`click && sleep N &&
  screenshot`), sleeps of 0.6-6s dominate in-command time
- session tokens: 11.05M prompt / 27.2K completion / 9.64M cached
  (final_metrics); per-step token counts NOT recorded

PTY domain (terminal.py, measured today): spawn 200ms warm (692ms cold),
send-to 141ms, `recv --wait REGEX` hit 196ms and verified blocking
(3205ms on absent pattern vs --timeout 3).

**Bottleneck decomposition:** of a ~9.5s median CU turn, tools are
~0.3-1.2s, self-imposed `sleep` settling waits ~0.6-6s, model inference +
loop overhead the rest. The turn boundary IS the latency problem: a cycle
costs >=2 turns (perceive-turn + act-turn) at ~5-17s each.

## 3. Hypotheses (evidence + verdict)

| # | Hypothesis | Mechanism (file evidence) | Verdict |
|---|---|---|---|
| H1 | Persistent CU worker removes 154ms/call spawn | `cu_session.py --daemon` (loopback socket, pidfile, idle TTL 600s, gen+session rotation); `cu_session_dispatch.py` routes via `$CU_SESSION=1`; adopted in `cu-stage-report.md` stage 5 | VIABLE: bounded ~150ms/call win; plumbing exists, opt-in |
| H2 | Text perception replaces PNG cycle | `--hints` JSON (17.6ms enum vs ~203ms capture+encode, zero image tokens); `terminal.py read/exec`; `browser.py eval/find`; real session already mixes them | VIABLE: biggest per-cycle token+latency cut; limited to UIA/DOM/TTY surfaces |
| H3 | Blocking-wait reperception collapses poll loop | `terminal.py recv --wait REGEX --timeout` (measured 196ms hit); `browser.py wait --selector/--text/--url/--fn`; `browser_events.py` daemon (buffers CDP/BiDi events, drain); `system-control events open/drain` (cursor-resumable, USAGE.md L141) | VIABLE: turns N poll-turns into 1 blocking call |
| H4 | Action batching in one exec/turn | transcript already shows `click && sleep && click && screenshot` chains; `cu_actions` result contract carries per-step timings | VIABLE: directly reduces turns/cycle; sleeps still waste fixed time |
| H5 | Delta/region perception | `--if-changed`/`--diff` skip unchanged (measured 315ms); `--region` 6.9ms vs 28.1ms full | VIABLE: parameterization of H2; modest alone |
| H6 | Background subagent as motor loop | `run_subagent is_background` + `<subagent_completion_notification>` wakeup (tool schema) | VIABLE for parallelism but does NOT cut per-cycle latency; notification is turn-boundary |
| H7 | Hooks inject events mid-turn | none found | INVIABLE: 8 lifecycle events all fire at turn/tool boundaries (DEVIN-CLI-COMPATIBILITY.md L79-96); no mid-turn channel exists in the runtime |
| H8 | Event->agent wakeup at boundary | watcher = background subagent OR daemon; agent polls inbox cheaply / gets notified at next boundary; Stop `decision:block` re-prompt proven (`refine-review-prompt.py`) | VIABLE: boundary-granular event-driven wake |
| H9 | record.py contact sheet reperceives N frames in 1 artifact | `record.py` reservoir-sampled sheet readable via `read` | VIABLE for verification batching; adds time, doesn't cut turns |
| H10 | Local model short-circuits target choice | `cu_decision.py`: laya worker, `suggestion|abstain`, <=8 candidates, shadow-only by design (`adoptable()` gate for assist) | VIABLE-CONSTRAINED: shadow/advisory only; assist needs approved calibration |
| H11 | Daemon-side reflex loop (no model in loop) | `terminal.py link` pump precedent (output->input pipe w/ per-line command gate) | VIABLE-SCOPED: scripted reflex, not reasoning; must keep command gate |

## 4. Metric + threshold (pre-registered, before Phase 2 tests)

Standardized task **S1 (terminal domain, no GUI risk)**: spawned cmd PTY
emits marker after randomized delay (1-4s); cycle = act(send command) ->
reperceive(marker verified). Variants: agent-poll loop vs blocking
`recv --wait` vs link-driven. GUI variant **S2** is deferred to Phase 2;
it needs user's desktop; will use bound-browser page or scoped Notepad
channels (`--channel scope|uia`, never global queue).

Metrics per hypothesis run (N>=5):
- `cycle_s`: wall-clock per perceive->decide->act->reperceive cycle
- `turns`: agent steps consumed per cycle (transcript step count)
- `tokens`: session `final_metrics` delta per run
- `success`: action landed AND verified (`status:verified` or observed
  postcondition), per contract; `dispatched` is not success

**Satisfactory threshold:** median `cycle_s` <= 0.5 x same-task baseline AND
`turns` strictly reduced AND `success` >= 4/5 AND zero safety violations
(no blind dispatch, no global-input tricks, command gate intact).

Baseline anchors: agent-turn p50 9.55s (transcript); tool floor 0.8-1.1s;
poll-detection of a ~2s event ~= 1-2 turns ~= 10-19s. A blocking-wait cycle
is predicted ~= event_time + ~0.2s tool + 1 turn ~= ~7s -> expected to pass.

## 5. Checkpoint

- Gates ledger: `.devin/ledgers/cu-realtime.md` (gitignored working file).
- This doc = Phase-1 checkpoint evidence; commit on `feat/cu-realtime`.
- STOP per spec: Phase 2 (per-hypothesis testing) awaits approval.
