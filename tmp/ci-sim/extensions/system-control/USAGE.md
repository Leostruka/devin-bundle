# system-control — authorized OS control

Interpreter: `sc_cli.py` — run with any Python 3.9+; stdlib only, no
venv, no third-party deps:

```bash
python extensions/system-control/sc_cli.py <command> [flags]
# installed: %APPDATA%\devin\extensions\system-control\sc_cli.py
#         or ~/.config/devin/extensions/system-control/sc_cli.py
```

stdout carries exactly one JSON object per invocation; diagnostics go
to stderr. Exit codes: `0` verified/dispatched, `1` runtime failure
(including timeouts), `2` rejected request (bad args, denied
capability, stale/expired confirmation).

## JSON status semantics

Every reply is a contract envelope:

```json
{"ok": true, "status": "verified", "request_id": "...",
 "backend": "windows", "value": {...}, "error": null}
```

| status | meaning |
|---|---|
| `verified` | result confirmed by the backend |
| `dispatched` | action sent, effect not proven |
| `rejected` | refused before execution (exit 2) |
| `timeout` | deadline exceeded |
| `unknown` | could not determine outcome (exit 1) |
| `cancelled` | cancelled via confirmed request |

## Policy — deny wins, one-shot confirmations

Capabilities classify DENY → CONFIRM → ALLOW → unknown-deny:

- **DENY (always):** `file.delete`, `disk.format`,
  `security.disable`, `credential.read`, and anything unknown.
- **CONFIRM:** `process.exec`, `process.cancel`, `session.spawn`,
  `session.send`, `session.cancel`, `daemon.stop`, `service.restart`,
  `file.copy`, `file.copy_overwrite`, `broker.dispatch`.
- **ALLOW:** read-only and session-lifecycle reads (`capabilities`,
  `process.observe`, `process.wait`, `service.observe`,
  `file.inspect`, `events.*`, `session.status|recv|resize|close`,
  `daemon.*`, `broker.status`).

A CONFIRM call needs a **one-shot confirmation**: the user issues a
token (TTL ≤120 s) bound to the exact request digest; consumption
deletes it before validation — replay, mutation and expiry all fail.
Tokens are minted outside this CLI (policy API); pass the id via
`--confirmation-id` plus `--request-id`. Tokens whose TTL elapsed are
**dropped** at consumption time; get a fresh one.

### Canonical request shapes (what the token binds)

A confirmation token is bound to the digest of the exact request
envelope the CLI builds. Mint it over this shape — any deviation
(missing key, different value, different `deadline_ms`) fails with
`request_mismatch`:

```json
{"version": 1, "request_id": "<--request-id>",
 "capability": "<capability>", "args": {<see table>},
 "deadline_ms": <see table>,
 "policy": {"dry_run": false,
            "confirmation_id": "<--confirmation-id>"}}
```

| Command | capability | args | deadline_ms |
|---|---|---|---|
| `exec` | `process.exec` | `{"argv": [...], "cwd": <str\|null>, "timeout_s": <num>}` | `timeout_s*1000` |
| `session spawn` | `session.spawn` | `{"argv": [...], "cwd": <str\|null>, "capacity": <int>, "idle_ttl_s": <int>}` | 30000 |
| `session send` | `session.send` | `{"session_id": <str>, "data": <str>}` | 30000 |
| `session cancel` | `session.cancel` | `{"session_id": <str>}` | 30000 |
| `sessions stop` | `daemon.stop` | `{}` | 30000 |
| `service restart` | `service.restart` | `{"name": <str>, "allowed": [<str>...]}` | 30000 |
| `file copy` | `file.copy` / `file.copy_overwrite` | `{"root","src","dst": <str>, "expected_hash": <hex64>, "dry_run": <bool>, "overwrite": <bool>}` | 30000 |

`overwrite: true` switches the capability to `file.copy_overwrite`.
The CLI validates every argument BEFORE consuming the token, so bad
input never burns one — but a token minted over the wrong shape is
always rejected.

Check a request's classification without side effects:

```bash
python sc_cli.py preflight '{"version":1,"request_id":"r1","capability":"capabilities","args":{},"deadline_ms":30000,"policy":{"dry_run":true}}'
```

## Commands

| Command | Capability | Confirm? |
|---|---|---|
| `capabilities` | capabilities | no |
| `process-list [--pid N] [--limit N]` | process.observe | no |
| `process-get --pid N --start-time S` | process.observe | no |
| `process wait --pid N --start-time S [--timeout S]` | process.wait | no |
| `service-status NAME` | service.observe | no |
| `exec --argv-json '[...]' --request-id R --confirmation-id T [--cwd D] [--timeout S]` | process.exec | yes |
| `file inspect --root R --path P` | file.inspect | no |
| `file copy --root R --src S --dst D --expected-hash H --confirmation-id T --request-id R [--dry-run] [--overwrite]` | file.copy[/_overwrite] | yes |
| `sessions start|status|list|stop` | daemon.* | stop: yes |
| `session spawn|send|recv|resize|close|cancel` | session.* | spawn/send/cancel: yes |
| `events open|drain|close|list` | events.* | no |
| `broker preflight|status` | broker.status | no |
| `service restart --name N --allowed L --confirmation-id T --request-id R` | service.restart | yes |

## Capability × platform matrix

| Capability | Windows | Linux | macOS |
|---|---|---|---|
| process.observe | CIM via powershell | `/proc/<pid>/stat` | `ps` projection |
| process.wait | native SCM/Job | pidfd or procfs-poll | kqueue or poll |
| service.observe | `sc.exe` query | systemctl | launchctl |
| process.exec / sessions | argv spawn, Job Object | argv spawn, process group | argv spawn, process group |
| file.* | realpath+reparse walk | realpath + dirfd O_NOFOLLOW | realpath + dirfd O_NOFOLLOW |
| service.restart | SCM direct under caller rights (confirm + `--allowed`), or broker (JEA) | broker only (polkit) | broker only |

`capabilities` reports the live matrix — trust it over this table.

## Sessions

`sessions start` launches a loopback daemon (127.0.0.1, token-auth,
atomic pidfile, idle-TTL exit) that holds spawned children across CLI
invocations. `session spawn -- ARGV` returns a session dict — persist
it with `--out-file`, then `send`/`recv`/`resize`/`close` by
`--session-file`. Children are bound to a Job Object / process group:
daemon death kills every owned child; nothing orphans.

## Files

`file` ops are root-bound: the path must resolve under `--root`, no
absolute/`..`/symlink/reparse components. `file copy` is hash-pinned
end to end (`--expected-hash`, 64 hex) with re-hash after commit;
`--dry-run` validates without writing.

## Telemetry

`events open` registers a bounded, cursor-resumable stream inside the
session daemon; `events drain --stream-id ID [--cursor N]` returns
events after the cursor and flags `resync_required` when the cursor
fell behind the retained window. Secret-like attributes are redacted.

## Broker (opt-in privilege)

There is **no privileged daemon by default**. `broker` is a fail-closed
seam: unprovisioned → `broker_not_provisioned` (exit 1). An
administrator may provision exactly one capability — `service.restart`
of an allowlisted service — via the templates in `brokers/`
(JEA `.pssc` on Windows, polkit `.policy` on Linux). No generic
execution, no wildcards, no credential forwarding; every dispatch is a
CONFIRM capability audited by `audit_id`.

## Failure modes

- bad/unknown flags, missing args → `rejected`, exit 2
- denied or unknown capability → `rejected`, exit 2
- expired/mismatched/replayed confirmation → `rejected`, exit 2
- backend unavailable (missing powershell/`/proc`/`ps`) →
  `capabilities` reports `supported:false` with `reason`; calls fail
  `unknown`, exit 1
- subprocess timeout → status `timeout`, exit 1; child tree cleaned
- daemon gone → session ops report `unknown`; restart with
  `sessions start`
- broker unprovisioned → `broker_not_provisioned`, exit 1 (fail closed)

## Install

The bundle installer copies `extensions/system-control/` verbatim —
no venv, no build step. Run `install.ps1`/`install.sh` with `-DryRun`/
`--dry-run` to verify enumeration. Broker templates are copied only;
provisioning is a separate, manual, admin-level step (see `brokers/`).

Extensions are install-side only by design: `export.sh`/`export.ps1`
handle skills and configuration, not local-tool extensions (which
carry their own interpreters and environments). Sync extensions back
to a bundle via git, not export.

## Safe examples (read-only / owned-process only)

```bash
python sc_cli.py capabilities
python sc_cli.py process-list --limit 20
python sc_cli.py service-status wuauserv        # Windows example
python sc_cli.py sessions status
python sc_cli.py file inspect --root "$PWD" --path README.md
```
