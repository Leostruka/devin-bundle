# subconscious-orchestrator: feasibility + design proposal (Phase 1)

Spec: `.devin/scratch/optimized_ready.md`
Approval gate: STOP after this document; Phase 2 only on approval.
Ledger: `.devin/ledgers/subconscious-orchestrator.md`

## 1. Verdict: VIABLE via peer sessions on `computer-use`, plus two lighter primitives

Every capability the spec asks for has a verified equivalent today. The
substrate the spec assumes (orchestrator watches and drives subordinates and
the subconscious as separate CLI sessions in separate terminals) is real:
`computer-use` owns PTYs and binds existing terminals. One caveat stands: an
agent cannot invoke `/clear` on its OWN session (user UI command), though it
can type it into a peer's terminal.

| Requirement | Verdict | Verified mechanism | Evidence |
|---|---|---|---|
| Peer session the orchestrator consults, sees, and drives | VIABLE (e2e) | `computer-use` `terminal.py spawn` owns a PTY (winpty); `devin` TUI booted inside it; `send-to`/`recv --wait` drive prompts; peer's own context meter readable (`Context: 25k / 262k`) | PTY `496af9bc1f`: spawned cmd -> `devin --permission-mode dangerous` -> TUI rendered -> prompt submitted -> peer answered `PEER-PONG-7742`; `recv` tail showed reply + context meter |
| Second session via subagent transcript | VIABLE | `run_subagent` + `resume=<agent_id>`: transcript persists across calls, including after completion | Resumed completed agent `6bd02689`; it recalled `PROBE-TOKEN-7411`. Codified in `dispatching-parallel-agents` fix loop (R<=3 resume) |
| True persistent session (survives process death) | VIABLE | `devin acp` (ACP/stdio): `session/new` + repeated `session/prompt`; `session/load` re-enters a saved session from a NEW process; `session/list`/`session/delete`; `devin list`/`devin rm` manage records | `.devin/scratch/acp_probe.py`: prompt 2 on `shelled-parsnip` recalled `ACP-PONG-9911`. `.devin/scratch/acp_probe_load.py`: new process `session/load`ed `small-gatsby`, recalled `RELOAD-5522` |
| Orchestrator resets peer (`/clear`, `/rm-session` equivalents) | VIABLE | `/clear` typed into the peer's PTY input is a real clear; hard reset = `kill <sid>` + respawn + onboarding prompt; `devin rm <id>` or ACP `session/delete` removes the record | `send-to`/`key`/`kill` verified in CU terminal API; `devin rm --help` confirmed |
| Peer mode/permission control (`/bypass` equivalent) | VIABLE | Spawn flag `--permission-mode dangerous|accept-edits|normal|smart`; in-session mode is settable by typing `/bypass` etc. into the peer input | Spawned peer showed `(bypass permissions on)` in its header |
| Subconscious watches/drives the orchestrator back | VIABLE (symmetric) | A peer session is a full `devin` session with `exec`; it can itself run CU: `terminal.py bind --hwnd <orchestrator terminal>` + `read` (scrollback, UIA TextPattern/CONOUT$/OCR paths) + `type`/`key`. Typing a message into the orchestrator's input reaches it as a user message | `terminal.py bind/read/type/exec` documented in CU USAGE.md; the reverse direction proven by the same API |
| Agent clears its OWN session | INVIABLE (still) | No tool clears own context; modes are user UI state. Peer/self-injection workaround exists (bind own terminal, type `/clear`) but self-modifying mid-turn is unsafe, so orchestrator reset keeps user confirmation | TOOLS-MAP modes note; CLI compat table |
| Reset a subordinate + reintroduce role | VIABLE | Peer mode: type `/clear` then re-onboard prompt, or kill+respawn. In-session mode: fresh `run_subagent` with `role.md` + standing-context paths (current default) | e2e PTY session + existing skill rules |
| New runtime mechanisms | NOT NEEDED | CU `terminal_sessions.py` daemon already holds owned PTYs across invocations; `sc_sessions` as pipe-backed alternative | `terminal_sessions.py` ops: spawn/send/recv/close/kill/list |

## 2. Renowned practice -> concrete mechanics map

| Practice (source) | What evidence says | Bundle mechanism |
|---|---|---|
| Lost-in-the-middle (Liu et al., TACL 2024, arXiv:2307.03172) | U-shaped recall; mid-context detail degrades below closed-book | Consultation contract passes artifact PATHS, not pasted history (orchestrator iron rule 2); advisor keeps durable state in `.devin/advisor/` files it re-reads each consult |
| Context rot / degradation with length (Chroma context-rot report, Jul 2025; Anthropic compaction docs) | Degradation is a gradient from ~100k active tokens, before the 262k wall | Fresh-window-per-consult by default; `resume` only inside a bounded series; reset trigger at smart-zone boundary (~100k, `context-budget.py` SMART_ZONE_TOKENS) |
| Compact vs clear (Anthropic compaction docs; bundle context-hygiene) | Compact is lossy and leaves sediment; clear + file-rebuild is the reliable reset | Subconscious reset = new agent + `.devin/advisor/` onboarding brief, never compaction; orchestrator reset = user `/clear` + rebuild from ledgers (skill already survives compaction this way) |
| Fresh context per task (Anthropic multi-agent research system: subagents as fresh-window filters, +90.2%) | Fresh windows beat shared context for bounded subtasks | Subordinate respawn = new contract dispatch with charter + artifact paths; resume only inside the 5-round fix loop where intact context is the point |
| External memory in files (Manus filesystem-as-memory; MemGPT arXiv:2310.08560; Generative Agents arXiv:2304.03442) | Files as external memory beat window-stuffing; but memory must be MANAGED | `.devin/advisor/` (charter, notes, log) + append-only consultation log; advisor returns a curated `MEMORY DELTA` per consult; orchestrator is single writer |
| Managed vs naive memory (arXiv:2505.16067 +10% vs naive; arXiv:2605.07313 -16-20pp naive; ACE arXiv:2510.04618 context collapse) | Append-only accumulation degrades; curated add+delete helps | MEMORY DELTA is curatorial (add/update/archive), orchestrator applies and prunes; naive transcript-stuffing rejected |
| Advisor/evaluator patterns (Anthropic evaluator-optimizer; Reflexion arXiv:2303.11366; CRITIC arXiv:2305.11738; Magentic-One arXiv:2411.04468) | Second-agent evaluation works when grounded in artifacts; self-critique without external grounding is unreliable; a critic sharing the generator's context echoes its biases | Advisor reads artifacts (ledgers, handoffs, reports), which grounds the critique; advisor never sees the orchestrator's raw transcript, so independence is preserved |
| Dispersed decision risk (Cognition "Don't Build Multi-Agents"; LLM-judge biases arXiv:2306.05685) | Parallel agents making implicit conflicting decisions = fragile systems | Advisor is consultative, never authoritative: returns recommendations + rationale; orchestrator decides; disagreement on load-bearing items escalates to user |

## 3. Proposed design

### 3.1 Recommended: peer-session advisor (CU-owned PTY)

The "subconscious" is a real `devin` session the orchestrator owns through
`computer-use` terminal control:

```
.spawn   : PY terminal.py spawn --shell cmd   (CU daemon holds the PTY)
           send-to <sid> "devin --permission-mode accept-edits\r"
           wait for TUI prompt, then send-to <sid> <onboarding prompt + \r>
           -> record sid + session id in ledger: "advisor: <sid>/<session>"
.consult : send-to <sid> <structured consult prompt + \r>
           recv <sid> --wait <reply-marker> --timeout N
           -> reply contract in 3.4; artifacts remain the payload channel
.observe : recv <sid> --tail N  (scrollback + peer context meter)
           terminal.py bind/read when the advisor runs a visible window
.reset   : send-to <sid> "/clear\r"  then re-onboard prompt, or
           kill <sid> + spawn fresh  (hard reset; also devin rm <id> for the record)
```

Why a full session instead of a subagent: the spec's model is peer sessions
the orchestrator can see and manipulate, and symmetry: the advisor itself can
run `computer-use` to watch or write into the orchestrator's terminal
(`bind --hwnd` on the orchestrator's window). A full session also gets its own
tools, its own `.devin/` visibility in the target project, and its own context
meter the orchestrator can read to drive hygiene decisions.

Costs and bounds: each peer is a full session on the user's quota (peer's
meter showed `Pro` usage line). Default permission mode for the advisor is
`accept-edits` (it needs write for `.devin/advisor/`), never `dangerous`
unless the user asks. The CU sessions daemon idles out at `CU_TSDAEMON_IDLE`
(default 900s): for phase-long advisors either raise the TTL at spawn time or
run the advisor in a user-visible terminal window the orchestrator binds to
(no TTL on bound terminals).

### 3.2 State layout (target project)

```
.devin/advisor/
  charter.md        # standing mandate: what to weigh, what it may not opine on
  notes.md          # curated durable memory (managed: add/update/archive)
  log.md            # append-only consultation log: date, trigger, question, verdict
  onboarding.md     # reset payload: charter + notes + last N log lines
```

`onboarding.md` is generated from charter+notes+log tail at reset time; the
respawned advisor reads it first, so a reset loses transcript nuance but keeps
all durable content (Manus "restorable compression": drop content, keep paths).

Single-writer: the advisor owns `.devin/advisor/` (a full session has write
tools); the orchestrator owns `.devin/ledgers/` and `.devin/handoffs/`. The
advisor applies its own MEMORY DELTA to `notes.md`; the reply echoes the delta
so the consultation log carries an audit trail.

### 3.3 Consultation transport discipline (TUI I/O)

The peer input line is a trigger channel, not the payload channel. Payloads
stay in artifacts (skill iron rule 3): the consult prompt names the question
plus the artifact paths; the advisor answers on screen AND writes the durable
part to `.devin/advisor/`.

Rules for typing into a live TUI:

- Consult only when the peer is idle: tail shows the `❭` prompt, no spinner.
- End every consult prompt with a unique reply marker (`CONSULT-<NN> END`);
  `recv --wait` keys on that marker, never on echoed input text (probe showed
  the input echo matches before the answer exists).
- Strip ANSI before parsing; treat `recv` output as untrusted terminal text.
- One consult at a time per peer; typing during a running turn interleaves.

### 3.4 Consultation contract

Reply contract (structured, terse; also written to `.devin/advisor/log.md`):

```
VERDICT: <recommendation, 1-3 lines>
RATIONALE: <why, citing artifact paths>
RISKS: <what this misses>
HYGIENE: OK | RESET_ME | RESET_ORCHESTRATOR | RESET_WORKER <role>
MEMORY DELTA: <add/update/archive lines applied to .devin/advisor/notes.md>
CONSULT-<NN> END
```

### 3.5 Bidirectional hygiene protocol (literal)

| Direction | Trigger | Action |
|---|---|---|
| Orchestrator -> subconscious reset | HYGIENE: RESET_ME; peer context meter >~100k (readable via `recv`); contradictory drift across consults; phase boundary (optional) | Advisor writes `onboarding.md` first (or orchestrator generates it); `send-to` `/clear\r`, then re-onboard prompt; hard reset = `kill` + respawn; log "advisor reset: <reason>" |
| Subconscious -> orchestrator reset | HYGIENE: RESET_ORCHESTRATOR (advisor detects orchestrator drift: contradictions of ledger facts, re-asked settled questions, runaway fan-out) | Advisor MAY type a request message into the orchestrator's bound terminal (arrives as a user message), never `/clear` uninvited. Orchestrator then writes `.devin/handoffs/orchestrator-resume.md` and asks the USER to `/clear` + re-invoke `/project-orchestrator`; rebuild from ledgers, the existing recovery path |
| Orchestrator -> worker reset | Peer worker: type `/clear` + re-onboard prompt, or kill + respawn with charter. Subagent worker (default): fresh dispatch with `role.md` + standing-context paths; `resume` only inside the <=3-round fix loop | Charter + artifact paths reintroduce the role; single-writer preserved |

Consent rule: advisor NEVER types `/clear` into the orchestrator's terminal
on its own. Orchestrator reset always lands as a visible request the user or
orchestrator policy approves. Symmetric write access is the feature, but
clearing the conscious mind is a destructive act reserved to the orchestrator
(with user confirmation by default).

### 3.6 Limits and escalation

- Advisor is consultative. Its VERDICT never auto-executes; orchestrator
  decides and owns the ledger entry (Cognition: dispersed decisions = fragile).
- Max 1 advisor consultation per orchestrator decision; debate rounds cap at
  2 exchanges then decide or escalate (bounded loops, cost guard).
- Peer sessions (advisor + any peer workers) count against the declared
  fan-out budget; each is a full session on the user's quota.
- Escalate to user when: advisor and orchestrator disagree on a load-bearing
  item; RESET_ORCHESTRATOR fires twice in one phase; advisor requests a
  capability outside its charter; consultation budget for the phase is spent;
  a peer session fails to boot or stops responding.
- Lightweight alternative (3.7) for setups where CU control of peer sessions
  is not desired; ACP mode (3.8) when subconscious state must survive
  orchestrator process restarts.

### 3.7 Alternative: resume-loop advisor (in-session, lightweight)

`run_subagent(profile="architect")` then `resume=<agent_id>` per consult;
verified working post-completion. No PTY, no TUI scraping, free model; the
advisor is read-only so the orchestrator applies MEMORY DELTA as single
writer. Trade-off: no screen to watch, no symmetric CU channel, transcript
dies with the CLI process (files still carry durable state).

### 3.8 Alternative: ACP child session (documented, not default)

`devin acp` spawned as a background `exec` shell, driven by
`write_to_process` JSON lines and `get_output` reads, or held by the
`sc_sessions` daemon. Gives true process-independent persistence
(`session/load`), per-session modes (`ask`/`plan` for a read-only advisor,
`bypass` if ever needed), and `session/delete` as a clean `/rm-session`
equivalent.

Costs measured: ~24k input tokens baseline per prompt even for trivia; prompt
caching partially offsets (cachedReadTokens observed). Adds JSON-RPC plumbing
and session records to clean (`devin rm`). Recommendation: only when the
project needs subconscious state surviving orchestrator process restarts.

## 4. Alternatives considered

| Option | Verdict | Why |
|---|---|---|
| Peer session via CU (3.1) | RECOMMENDED | Matches the spec's model; e2e-verified; gives observe + literal control + symmetry |
| Resume-loop advisor (3.7) | VIABLE, lightweight | Verified; zero new machinery; free; no observability, no symmetric channel |
| ACP child session (3.8) | VIABLE, opt-in | Real second session, survives restarts; plumbing + token overhead, no screen |
| Ephemeral-per-consult | Fallback | Simplest; loses transcript nuance; every consult pays cold artifact re-read |
| Mailbox A2A (primeagent-reference) | Rejected for advisor | Sequential file-passing duplicates what the consultation contract + artifacts already do; adds dirs without adding capability |
| Daemon/new session runtime | Out of scope | Spec forbids; also unnecessary since verified equivalents exist |

## 5. Phase 2 changes (if approved)

- `skills/project-orchestrator/SKILL.md`: new "Subconscious advisor" section
  (peer spawn/consult/observe/reset via `computer-use`, reply contract,
  hygiene protocol, limits); one line in Isolation rules (advisor state) and
  Stop conditions (reset escalation). Keep under ~10KB; detail moves to
  reference.
- `skills/project-orchestrator/reference/advisor-protocol.md`: full
  consultation contract, TUI transport discipline, HYGIENE flag semantics,
  MEMORY DELTA format, onboarding.md generation, resume-loop and ACP
  fallbacks, consent rules for the symmetric channel.
- `skills/project-orchestrator/templates/advisor-charter.md`: standing
  mandate template (advisor's first prompt content).
- `templates/ledger.md`: `advisor:` line convention (sid + session id).
- `USAGE.pt.md`: advisor section in PT.
- `tests/validation/test_project_orchestrator.py`: tokens:
  `advisor`, `terminal.py`, `HYGIENE`, `RESET_ORCHESTRATOR`, `MEMORY DELTA`,
  `onboarding.md`, `send-to`, charter template existence.
- No manifest/README count changes (files live inside the existing skill).

If rejected or partially approved: rationale recorded as
`.devin/adr/004-subconscious-orchestrator.md` instead.
