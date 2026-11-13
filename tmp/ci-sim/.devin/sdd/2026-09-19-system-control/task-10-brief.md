# Task 10 brief — opt-in privileged brokers

## Plan reference

`.devin/plans/2026-09-19-system-control.md` Task 10 (~300-450 lines).

## Files

- Create `extensions/system-control/sc_broker.py`
- Create `extensions/system-control/brokers/README.md`
- Create `extensions/system-control/brokers/windows-jea.pssc`
- Create `extensions/system-control/brokers/linux-polkit.policy`
- Create `tests/test_sc_broker.py`
- Wire `broker preflight` + `broker status` into `sc_cli.py` if the
  contract already routes capabilities there (check `sc_cli.py`
  dispatch table first — keep diff minimal).

## Contract (held-out pins — do NOT read held-out dir)

`sc_broker.dispatch(request, *, broker, now_ms=None)`:

- `request` is a v1 envelope (`version`, `request_id`, `capability`,
  `args`, `deadline_ms`, `policy`).
- Broker seam object must expose `capabilities()` returning a declared
  list; requests for capabilities NOT in that list →
  `{"ok": False, "status": "rejected"}` without calling the broker.
- `request["subject"]["uid"]` must equal the broker's bound subject
  (`broker.subjects` in the fake; real impl compares OS peer identity).
  Foreign/missing subject → rejected, broker never called.
- Expired deadline (issued_at_ms + deadline_ms < now) → rejected,
  broker never called. `now_ms` injectable clock.
- Success → `{"ok": True, "status": "dispatched", "audit_id": ...}`
  (surface broker's audit_id top-level or under `value`).
- `broker=None` → `{"ok": False, "status": "rejected"|"unknown"}`
  explicit unprovisioned response.

## Requirements

- Only `service.restart` is ever a declared broker capability — no
  generic command execution, no wildcard.
- Confirmation: dispatch is a CONFIRM capability — reuse `sc_policy`
  confirmation flow in the CLI path (check how sc_process consumes).
- No credential forwarding, no shell strings, no auto-install.
- `preflight()`/`status()` helpers: report provisioned/not and the
  declared capability list; fail-closed on unreadable broker metadata.

## Templates (declarative, NOT auto-installed)

- `windows-jea.pssc`: JEA session configuration exposing ONE
  constrained function (Restart-AllowedService) with a validated
  service allowlist; standard PSSessionConfigurationFile fields.
- `linux-polkit.policy`: single action id naming one broker method;
  auth_admin required; no implicit yes.
- `brokers/README.md`: install/status/disable/uninstall steps, every
  step admin-required with a dry-run/check command; states bundle
  installer only copies templates.

## TDD

1. `tests/test_sc_broker.py` FIRST (RED): fake broker seam covering
   declared-cap gating, subject binding, deadline, audit_id,
   unprovisioned, confirmation-required via sc_policy.
2. Implement `sc_broker.py` (stdlib only).
3. GREEN + `python -m pytest tests/test_sc_policy.py -q` regression.
4. `python -m py_compile` on new files.

## Security gates

- No hardcoded credentials; no unauthenticated endpoint; no broad
  wildcard capability; logs/audit_id sanitized (no args echo).

## Out of scope

- Real pipe/socket transport to an OS broker (design seam only).
- Auto-provisioning.
