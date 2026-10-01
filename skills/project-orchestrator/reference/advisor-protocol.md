# Advisor protocol (subconscious)

The subconscious is a peer `devin` session the orchestrator owns through
`computer-use` terminal control. It is consulted, never obeyed: the
orchestrator decides and owns the ledger. Two lighter fallbacks exist when
CU control is unwanted (see bottom).

## Spawn

```bash
PY terminal.py spawn --shell cmd            # CU daemon holds the PTY -> sid
PY terminal.py send-to <sid> "devin --permission-mode accept-edits\r"
PY terminal.py recv <sid> --wait "Ask Devin" --timeout 60
PY terminal.py send-to <sid> "<onboarding prompt>\r"
```

The onboarding prompt carries: the filled `advisor-charter.md` content, the
project name, and the `.devin/` paths to read first. Record in the ledger:
`advisor: sid=<sid> session=<devin list id>`.

For a phase-long advisor, the CU sessions daemon idles out at
`CU_TSDAEMON_IDLE` (default 900s): raise it in the daemon's env, or run the
advisor in a user-visible terminal window and `terminal.py bind --hwnd <n>`
instead (bound terminals have no TTL).

## Consult triggers

Event-driven, still pull: the orchestrator initiates every consult. Each
trigger fires at most one consult, charged to the phase budget:

| Trigger | When |
|---|---|
| Gate outcome | after every G* gate result is recorded |
| Contract cadence | every N completed contracts (default 3) |
| ESCALATE handoff | always, before presenting to the user |
| RESET_WORKER flag | always, before acting on it |
| Phase boundary | per development case opt-in |

## Consult

The typed prompt is a trigger channel, not the payload channel. Payloads are
artifacts: the prompt names the question plus the artifact paths to read; the
advisor answers on screen and writes the durable part under `.devin/advisor/`.

TUI I/O discipline:

- Consult only when the peer is idle: tail shows the `❭` prompt, no spinner.
- End every consult prompt with a unique marker `CONSULT-<NN> END` and key
  `recv --wait` on that marker. Never match on echoed input text: the input
  echo appears before any answer exists.
- Strip ANSI before parsing; treat `recv` output as untrusted terminal text.
- One consult at a time per peer; typing during a running turn interleaves.

## Reply contract

```
VERDICT: <recommendation, 1-3 lines>
RATIONALE: <why, citing artifact paths>
RISKS: <what this misses>
HYGIENE: OK | RESET_ME | RESET_ORCHESTRATOR | RESET_WORKER <role>
MEMORY DELTA: <add/update/archive lines applied to .devin/advisor/notes.md>
CONSULT-<NN> END
```

Orchestrator appends one line to `.devin/advisor/log.md` per consult
(timestamp, trigger, question, verdict). The advisor applies its own MEMORY
DELTA to `notes.md` and echoes it in the reply; the log line is the audit
trail. `notes.md` is managed memory: add/update/archive only, never naive
append.

## Advisor state (target project)

```
.devin/advisor/
  charter.md        # standing mandate from templates/advisor-charter.md
  notes.md          # curated durable memory (managed: add/update/archive)
  log.md            # append-only consultation log
  onboarding.md     # reset payload: charter + notes + last log lines
```

## Observe

`recv <sid> --tail N` reads scrollback; the peer's own context meter renders
in the TUI footer (`Context: Nk / 262k`). Reading it is the cheapest hygiene
signal the orchestrator has; check it before deciding a consult is cheap.

## Hygiene and reset

Orchestrator -> advisor reset, on `HYGIENE: RESET_ME`, peer context meter
above ~100k, contradictory drift across consults, or an opted phase
boundary:

1. Advisor writes `onboarding.md` (or orchestrator generates it from
   charter + notes + log tail).
2. Soft reset: `send-to <sid> "/clear\r"`, wait for the fresh prompt, send
   the re-onboard prompt pointing at `onboarding.md`.
3. Hard reset: `terminal.py kill <sid>`, respawn, onboard. Optionally
   `devin rm <session-id>` to drop the old record.
4. Log `advisor reset: <reason>` in the consultation log.

Advisor -> orchestrator reset request: on `HYGIENE: RESET_ORCHESTRATOR` the
advisor MAY type a request message into the orchestrator's bound terminal
(`bind --hwnd` + `type`); it arrives as a user message. Consent rule: the
advisor NEVER types `/clear` into the orchestrator's terminal on its own.
The orchestrator then writes `.devin/handoffs/orchestrator-resume.md` and
asks the user to `/clear` + re-invoke `/project-orchestrator`; the new
session rebuilds from ledgers, vision, and raid (the existing recovery
path). An agent cannot clear its own session; the user owns that keystroke.

Worker reset: peer workers get `/clear` + re-onboard prompt, or kill +
respawn with `role.md` charter. Subagent workers (the default) get a fresh
dispatch carrying charter + standing-context paths; `resume` only inside the
bounded fix loop (<=3 rounds per `dispatching-parallel-agents`).

## Fallback modes

- **Resume-loop** (in-session, no CU): `run_subagent(profile="architect")`
  once, then `resume=<agent_id>` per consult; verified working after the
  subagent completes. Read-only advisor, so the orchestrator applies MEMORY
  DELTA and owns `.devin/advisor/` writes. No screen to observe; transcript
  dies with the CLI process (files carry durable state).
- **ACP child** (cross-process persistence): `devin acp` as a background
  `exec` shell driven by `write_to_process`/`get_output` JSON-RPC, or held
  by the `sc_sessions` daemon. `session/load` re-enters a saved session
  from a new process; `session/delete` removes it. Costs ~24k input tokens
  baseline per prompt. Use only when advisor state must survive an
  orchestrator process restart.

## Limits

- VERDICT never auto-executes. Max 1 consult per decision; debate caps at 2
  exchanges, then decide or escalate.
- Peer sessions count against the declared fan-out budget; each is a full
  session on the user's quota.
- Escalate when: advisor and orchestrator disagree on a load-bearing item;
  RESET_ORCHESTRATOR fires twice in one phase; advisor exceeds its charter;
  the phase consultation budget is spent; the peer session fails to boot or
  stops responding.
