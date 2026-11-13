# CU real-time: final verdict and recommended parameters

Spec `.devin/scratch/optimized_ready.md`. Evidence:
`.devin/research/cu-realtime-phase1.md` (map, baselines, threshold),
`.devin/research/cu-realtime-phase2.md` (per-hypothesis results),
harness `.devin/scratch/cu-realtime/s1_probe.py`.

## Verdict

Five hypotheses passed the pre-registered threshold. The closest
approach to real-time the runtime allows is a **composition**, not a
single mechanism:

> **Perceive text, not pixels. Wait on events, don't poll. Batch the
> whole cycle into one turn. Use scripted reflexes only where the
> trigger is deterministic.**

At agent-loop granularity the floor is **one model turn per cycle**
(measured p50 9.55s in a real CU session; tool share <1s of that).
"Real-time" in devin-cli therefore means: cycle = 1 turn whose
perceive+act+verify run inside a single tool call, with the event
itself arriving via a blocking wait, and anything faster than a turn
handled by scripted reflex, not the model.

## Domain ladder (apply in this order)

1. **TTY**: `terminal.py spawn`/`exec`/`recv --wait` - text output,
   blocking match, deterministic. Cycle ~= event + ~0.2s + 1 turn.
   `exec` does act+verify in ONE call (1 turn total).
2. **DOM**: bound `browser.py` - `eval`/`find`/`wait --selector|--text|
   --url|--fn`; `browser_events.py` daemon for push streams (console/
   errors/network/nav/dialogs, drain API).
3. **UIA**: `screenshot.py --hints` under profile `fast` - visual
   bypass returns pure element JSON (verified: `capture:"skipped"`,
   248ms, 1.4KB). `click --hint`/`--via uia` acts semantically.
4. **Pixels**: last resort - `screenshot.py` (321ms + PNG + vision
   tokens + inference), `--region` when only an area matters.

## Measured results

| Mechanism | Evidence | Effect |
|---|---|---|
| blocking `recv --wait` | S1: 5/5, delay+0.2s | poll 5-9 turns -> 2 turns; ~0.35x cycle |
| `terminal.py exec` batch | S1: 5/5, 1 call | 1 turn/cycle; ~0.2x cycle |
| text perception | 194-248ms, 0.5-1.4KB | no image tokens, deterministic match |
| subagent + notification | 3.27s delegated wait | boundary wake verified; parallelism only |
| `link` reflex pump | 0.327s src->dst exec | model-free reflex, `--limit` brake, gate enforced |
| `CU_SESSION=1` daemon | -76ms screenshot, 0 mouse | marginal; dispatcher pays own spawn |
| `--region`/`--if-changed` | -21ms region; never skips live | parameterization only |
| laya shadow | no approved checkpoint | untestable; assist gated by design |
| mid-turn injection | none in runtime | impossible; boundary-only signals |

## Recommended parameters

- `send-to` payloads end with `\r` (ConPTY submit); `\n` only echoes.
- Marker/wait strings must not appear in the sent command text
  (input-echo false positive) - assemble at runtime (`%M%`, `call`).
- `recv --wait REGEX --timeout <event deadline>`; never `recv --tail`
  in a decide-loop.
- `terminal.py exec '<cmd>' --wait <postcondition>` as the default
  one-cycle primitive on TTY surfaces.
- `browser.py wait --fn <expr>` for DOM postconditions; events daemon
  when the trigger is a console/network/dialog event, not page text.
- Batch `act && verify` in one exec only when each step's
  precondition is deterministic or self-checked (`--verify`,
  `--wait`); blind chains violate the action contract.
- `link` reflexes only for deterministic text triggers, always with
  `--limit`; the command gate stays enforced per forwarded line.
- `CU_SESSION=1` only for screenshot-heavy loops (~30-75ms/call).
- Keep profile `fast` for hint-bypass text perception; `--image`
  when pixels are actually needed.

## What did NOT move the needle

- Interpreter/daemon plumbing (H1): saves tens of ms per call;
  irrelevant vs 9.5s turns.
- Pixel diffing (H5): live desktops drift; rarely skips.
- Subagent motor loop (H6): offloads turns, never shortens one.

## Non-goals confirmed

H7 (mid-turn injection) has no runtime surface - all async input
arrives at turn boundaries. H10 needs an approved local laya
checkpoint + calibration before even shadow testing; none exists on
this machine. H9 needs a visible window - applies to S2/GUI tasks.

## Return-to-hypotheses? No.

The threshold was met by 5 hypotheses; the verdict stands on measured
evidence. Residual latency is model inference per turn - out of scope
(closed runtime / model policy). If a GUI task needs S2 validation,
the same ladder applies with `--channel scope|uia` on bound windows.
