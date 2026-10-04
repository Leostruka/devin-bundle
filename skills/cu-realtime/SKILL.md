---
name: cu-realtime
description: Use when computer-use or terminal automation needs the fastest reaction the runtime allows - event waits instead of screenshot polling, text perception instead of image reads, whole perceive-act-verify cycles batched into one exec, or deterministic reflex loops below model latency. Composes with the `computer-use` skill (same extension CLIs).
triggers: [user, model]
---

# CU Real-time

Latency patterns for `extensions/computer-use/`, measured on this bundle
(`.devin/research/cu-realtime-{phase1,phase2,verdict}.md`). The runtime
floor is one model turn per cycle (~9.5s p50 measured) - nothing injects
mid-turn, so "real-time" means one turn whose perceive+act+verify happen
inside one tool call.

## Domain ladder (try in order)

1. **TTY** - `terminal.py spawn`/`exec`/`recv --wait`. Text output,
   blocking regex match, deterministic. Fastest channel.
2. **DOM** - bound `browser.py`: `eval`/`find`/`wait --selector|--text|
   --url|--fn`; `browser_events.py` daemon for push streams.
3. **UIA** - `screenshot.py --hints` under profile `fast`: visual bypass
   returns pure element JSON (`capture:"skipped"`, ~250ms, ~1.4KB);
   `mouse.py click --hint <id>` / `--via uia`.
4. **Pixels** - last resort: `screenshot.py` (+PNG + vision tokens +
   inference). Use `--region` when only an area matters.

## Patterns (each measured)

- **Never poll `recv --tail` in a decide-loop.** Use
  `recv <sid> --wait <REGEX> --timeout <deadline>` - one call blocks
  until match (verified: hit at ~event+0.2s, true timeout otherwise).
- **One cycle = one call**: `terminal.py exec '<cmd>' --wait <regex>`
  does spawn+send+match+close in a single invocation (1 agent turn).
- **Batch inside one `exec`** when each step's precondition is
  deterministic or self-checked (`--verify`, `--wait`). Blind
  `click && sleep && click` chains violate the action contract.
- **Async events**: background subagent (`is_background=true`) that
  blocks on the event - its completion notification wakes the parent
  at the next turn boundary. Or a watcher daemon + cheap inbox poll.
- **Reflexes below model latency**: `terminal.py link <src> <dst>
  --limit N` pipes one spawned PTY's output lines into another's input
  (measured 0.33s src->dst execution, zero model turns). Deterministic
  triggers only; the send/exec command gate applies per forwarded
  line and `--limit` is the brake.
- **`CU_SESSION=1`**: persistent worker daemon amortizes imports
  (~30-75ms/call on screenshot-class ops, ~0 on light ones). Optional.

## Protocol gotchas (verified)

- `send-to` payloads submit on `\r`, not `\n` - `\n` echoes the line
  without executing (cmd/ConPTY). The link pump appends `\r` itself.
- A wait/match string must NOT appear literally in the command text
  (input echo = false positive). Assemble at runtime: `set "M=PRE_" &
  call echo %M%MARK` - `call` re-expands after `set` ran (cmd expands
  %VAR% at parse time per line).
- `--if-changed`/`--diff` rarely skips on a live desktop (clock/cursor
  drift) - do not count it as the reperceive saving.
- `dispatched` never means done - reperceive via `--wait`/`--verify`.

## Pointers

- Full CLI contract: `extensions/computer-use/USAGE.md`
- Evidence + thresholds: `.devin/research/cu-realtime-verdict.md`
- Harness: `.devin/scratch/cu-realtime/s1_probe.py`
