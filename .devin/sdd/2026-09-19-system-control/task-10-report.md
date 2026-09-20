# Task 10 report — opt-in privileged brokers

## Scope

`sc_broker.py` (~170 lines), `brokers/` declarative templates,
`sc_cli.py` `broker preflight|status` (+21).

## Delivered

- `dispatch(request, *, broker, now_ms=None)` — gates in order:
  provisioned → readable declared caps → capability in declared AND
  hardcoded `BROKER_CAPABILITIES = {"service.restart"}` →
  `subject.uid` bound → deadline not expired → broker invoked.
  Fail-closed at every gate; broker never called on rejection.
- `preflight`/`status` — fail-closed probe; reports raw declared list
  split into `capabilities` (supported) and `unsupported`
  (over-declared, masks nothing).
- `audit_id` sanitized to `[A-Za-z0-9_.:-]{1,128}` (also read from
  `result["value"]["audit_id"]`); broker `error` strings get the same
  bounded charset — args can never echo through responses.
- `issued_at_ms` optional; deadline gate skipped only when absent
  (documented deliberate: deadline_ms contract-bounded, subject +
  one-shot confirmation bound replay).
- CLI `broker preflight|status` → contract envelope, exit 1
  unprovisioned. `broker.dispatch` already CONFIRM in sc_policy —
  one-shot token consumed by existing path.
- Templates: `windows-jea.pssc` (one `Restart-AllowedService`
  function, `ValidateSet` allowlist, `VisibleCmdlets=@()`),
  `linux-polkit.policy` (single action, `auth_admin` all defaults),
  README install/status/disable/uninstall with per-step verify
  commands + SDDL access-grant note. Installer only copies.

## Review

Independent review: Spec PASS / Standards PASS → minors fixed:

1. README: verify commands added to disable/uninstall steps;
   RoleDefinitions/access-grant documented.
2. Broker `error` sanitized (was verbatim — args could echo).
3. preflight/status now surface over-declared caps as `unsupported`.
4. `audit_id` fallback under `value`.
5. Deliberate `issued_at_ms` skip commented.

## Verification

- Held-out `test_broker_contract.py`: 6/6 pass.
- Focused: `test_sc_broker.py` 19 + policy 25 + cli 34 + held-out 6
  → 84 passed.
- Full suite: **931 passed, 8 skipped**; audit 0 errors;
  `git diff --check` clean.

## Residuals

- No real pipe/socket transport (design seam; plan scope).
- `broker` CLI reports unprovisioned until an operator installs a
  template — intended.
