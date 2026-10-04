# CU real-time Phase 2: hypothesis test results

Spec `.devin/scratch/optimized_ready.md`. Harness `.devin/scratch/cu-realtime/s1_probe.py`.
Threshold (phase 1 §4): median `cycle_s` <= 0.5 x same-task baseline AND
turns strictly reduced AND success >= 4/5 AND zero safety violations.
Turn-latency anchors: 9.55s p50 (CU transcript ahead-candytuft),
18.9s p50 (this session bead-thought, heavier context).

## S1 harness (terminal domain, spawned cmd PTY)

Task: PTY emits `CU_READY_MARK42` after a fixed delay (1-4s, `ping -n`).
Marker is assembled at runtime (`set` + `%M%`/`call echo %M%`) so the
literal never sits in the command text - kills input-echo false positives.

Two protocol bugs found and fixed while building it (evidence for the
loop map, not hypothesis results):

- `send-to` needs `\r` to submit on ConPTY; `\n` echoes the line and
  never executes (cu_terminal.py:965 writes verbatim; the link pump
  appends `\r` itself at cu_terminal.py:1133). USAGE.md example
  `send-to "echo hi\n"` does not submit on cmd.
- cmd expands `%VAR%` at parse time per line: `set` and `%M%` consumers
  must be separate lines (or `call echo %M%` for one-line exec).

Results (5 runs each, delays 1,2,3,2,4s):

| variant | calls/cycle | total_s per run | found |
|---|---|---|---|
| poll (`recv --tail` + 0.5s sleep) | 5-9 | 1.57, 2.25, 3.66, 2.30, 4.35 | 5/5 |
| wait (`recv --wait MARKER`) | 3 | 1.20, 2.19, 3.20, 2.20, 4.19 | 5/5 |
| batch (`terminal.py exec`, 1 call) | 1 | 1.62, 2.36, 3.61, 2.61, 4.62 | 5/5 |

`exec` = spawn+send+recv-wait+close in one call (terminal.py:233-240).

## Per-hypothesis results

### H3 blocking-wait reperception - PASS threshold

Tool: total ~= delay + 0.2s vs poll ~= delay + 0.3-0.4s AND N recv calls.
Agent projection (the metric that matters): poll cycle = send-turn +
N poll-turns (each recv is a model turn; N grows with delay/interval):
delay 2s -> ~4-6 turns ~= 38-57s @9.55s anchor. wait = 2 turns
(send + blocking recv; combinable into 1 exec) ~= 19-38s.
=> cycle_s <= 0.5x baseline (typically ~0.35x), turns 5-9 -> 2, 5/5
success. PASS. Extends to `browser.py wait --selector/--text/--url/--fn`
and `browser_events.py`/`sc events` for push sources.

### H4 action batching - PASS threshold

`terminal.py exec` collapses act+reperceive into 1 CLI call = 1 agent
turn ~= 9.5-19s + delay, vs poll's 5-9 turns ~= 50-170s. cycle_s <=
0.2x baseline, 5/5. Also the general pattern: `click && sleep &&
screenshot` chains in one exec (already used in the wild,
ahead-candytuft). PASS. Constraint: batching is only safe when each
step's precondition is deterministic or checked inside the batch
(`--verify`, `--wait`); blind chains violate the action contract.

### H2 text perception over PNG - PASS threshold

| channel | wall ms | payload | inference |
|---|---|---|---|
| `recv --tail 8` | 194 | 518B JSON | none (string match) |
| `screenshot --hints` (fast profile) | 248 | 1.4KB JSON (8 els) | none |
| `screenshot --hints --image` | 408 | +154KB PNG | vision |
| `screenshot --region` | 229 | +15KB JPG | vision |
| `screenshot` full | 321 | ~1-2MB PNG | vision |

Verified mechanism (screenshot.py:353): under profile `fast`,
`--hints` engages visual bypass (`capture:"skipped"`) - pure UIA text,
no PNG, unless `--image` forces capture. Text reperception cuts tool
time ~30-60%, removes image tokens + a vision parse entirely, and the
match is deterministic (`name`/`type`/regex vs OCR-by-eyeball). PASS.
Bounded: only surfaces with UIA/DOM/TTY text; canvas/games/pixels need
the image path by design.

### H5 delta/region perception - MARGINAL (parameter of H2)

`--region` capture 6.9ms vs full 28.1ms; region CLI 229ms vs 321ms.
`--if-changed` called 4x on a live desktop: never skipped - ambient
pixel drift (clock, cursor blink) defeats the default threshold, so
the call still captures+encodes. Value = skipping the agent's
read+inference on truly static frames, which real desktops rarely are.
Keep as parameterization, not a standalone win.

### H1 persistent CU daemon - MARGINAL

`CU_SESSION=1` measured: `screenshot --region` 236 -> 160ms p50
(-76ms), `mouse position` 147 -> 152ms (0). The dispatch front-end
(`cu_session_dispatch.py`) still pays a ~140ms subprocess spawn per
call - the daemon only amortizes module imports (mss/PIL/comtypes),
not interpreter startup. Net: ~30-75ms on import-heavy scripts,
~0 on light ones. VIABLE but bounded far below the 150ms implied by
the frozen boundary table; irrelevant vs 9.5s turns.

### H11 daemon-side reflex loop - PASS (scoped)

`terminal.py link src dst` measured: src `echo ver` -> output `ver`
forwarded -> dst executed `ver` in **0.327s**, zero model turns
(link stats: 1 forward, 0 dropped). The pump is per-line with the
send/exec command gate (deny/confirm lists enforced, cu_terminal.py
link pump + gate). Model-free latency floor, but it is scripted
reflex, not reasoning - scope it to deterministic triggers with a
bounded `--limit` (the brake, USAGE.md:351). PASS within scope.

### H8/H6 event wakeup + background motor loop - measured

`debugger` subagent (agent c2b1d5c9) ran the S1 wait-cycle in
background. Reported: send->wait-return 3.27s (delay ~3s + ~0.27s
overhead), marker found. The `<subagent_completion_notification>`
reached the parent at the next turn boundary - confirmed live.

- H8 (wakeup): VIABLE. A watcher subagent blocks on an event;
  the completion notification IS the boundary-granular wake channel.
  Latency ~= event + subagent-wrap + parent boundary.
- H6 (motor loop): VIABLE for parallelism only - the subagent pays
  the same per-turn inference internally (its wait took 3.27s, same
  as in-process). Delegation offloads turns; it does not shorten a
  cycle.

### H9 record.py contact sheet - N/A for S1 domain

Spawned PTYs have no window; record.py captures the real screen.
Domain-limited to visible-GUI tasks (verify N frames in 1 artifact =
1 read vs N screenshots+reads). Mechanism verified in USAGE.md and
test suite (`test_cu_record`); no live S1 run meaningful. Deferred to
S2 if a GUI task is approved.

### H10 laya shadow suggestions - BLOCKED, cannot test

`laya` 0.3.5 installed in `extensions/laya-tools/.venv`, but no
approved local checkpoint exists: `profile.example.json` has a
placeholder path, and `load_engine` requires path+sha256 under
offline env flags (`model_path_missing`, laya_worker.py:76). Policy
forbids downloading to satisfy a run. Verdict: VIABLE-CONSTRAINED,
gated on an approved checkpoint + calibration. Not reward-hacked:
untested is reported, not skipped.

## Standing results summary

| H | verdict | measured key |
|---|---|---|
| H1 | marginal | -76ms/call import-heavy, 0 on light |
| H2 | PASS | text 194-248ms/no-tokens vs image 229-408ms+PNG+vision |
| H3 | PASS | 5-9 -> 2 turns; ~=0.35x cycle |
| H4 | PASS | -> 1 turn; ~=0.2x cycle |
| H5 | marginal | region -21ms; if-changed never skips live |
| H6 | viable-parallel | 3.27s delegated cycle; offloads, not faster |
| H7 | INVIABLE (P1) | no mid-turn injection surface |
| H8 | PASS | completion-notification = boundary wake, verified live |
| H9 | domain-limited | mechanism verified, no S1 window |
| H10 | blocked | no approved checkpoint |
| H11 | PASS (scoped) | 0.327s model-free reflex |
