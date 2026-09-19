# Task 2 brief — One-shot request-bound confirmations

## Context

Task 1 is complete at commit `b02cdec`. Add the policy layer above the v1 contract. This slice classifies capabilities and creates/consumes one-shot confirmation tokens. No mutation is implemented here.

## Binding constraints

- Python 3.9+ stdlib only.
- Deny wins. Unknown capability fails closed.
- Tokens are random 256-bit values, TTL 1..120 seconds, request-bound, single-use.
- Store only token metadata: digest, created_at, expires_at. Never raw request/args.
- Token is deleted before validation returns, including mismatch/expiry.
- Compare digests with `hmac.compare_digest`.
- Owner-only state directory/files where supported; atomic write/replace.
- `dry_run` never authorizes mutation.
- stdout remains exactly one JSON object; diagnostics stderr.
- Do not read/edit `tests/held-out/`, plan, research, README, installers, or computer-use.
- Tests first; no commit or staging; lead owns commits.

## Files

Create:
- `extensions/system-control/sc_policy.py`
- `tests/test_sc_policy.py`

Modify:
- `extensions/system-control/sc_contract.py`
- `extensions/system-control/sc_cli.py`
- `extensions/system-control/schemas/v1.json`
- visible Task 1 tests only when contract behavior requires coverage.

## Exact interfaces

- `request_digest(request: dict) -> str`
- `classify(request: dict) -> dict`
- `issue_confirmation(request: dict, ttl_s: int = 120) -> dict`
- `consume_confirmation(request: dict, confirmation_id: str) -> dict`

Decision shape:
- allow: `{"decision":"allow","reason":"capability_allowed"}`
- confirm: `{"decision":"confirm","reason":"confirmation_required"}`
- deny explicit: `{"decision":"deny","reason":"capability_denied"}`
- deny unknown: `{"decision":"deny","reason":"unknown_capability"}`

Consume shape always includes `ok: bool`, `reason: str`; success reason `confirmed`; failures: `unknown_confirmation`, `expired`, `request_mismatch`.

Optional request policy:
```json
{"dry_run": false, "confirmation_id": null}
```
`validate_request` accepts no other policy keys. `dry_run` must be bool. `confirmation_id` must be string or null.

## Decision table

```python
DENY = {"file.delete", "disk.format", "security.disable", "credential.read"}
CONFIRM = {
    "process.exec", "process.cancel", "session.spawn", "session.send",
    "session.cancel", "daemon.stop", "service.restart", "file.copy",
    "file.copy_overwrite", "broker.dispatch",
}
ALLOW = {
    "capabilities", "process.observe", "process.wait", "service.observe",
    "file.inspect", "events.open", "events.drain", "events.close",
    "session.status", "session.recv", "session.resize", "session.close",
    "daemon.start", "daemon.status", "broker.status",
}
```

Classification checks `DENY`, then `CONFIRM`, then `ALLOW`, then unknown deny. Tests must monkeypatch overlapping sets and prove deny wins.

## Canonical digest

1. Validate and copy request.
2. Copy `policy`; remove only `confirmation_id`.
3. Serialize with `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
4. SHA-256 hex digest.

Changing target, args, deadline, capability, request_id, or `dry_run` changes the digest. Adding the issued confirmation ID does not.

## Token storage

- Default `STATE_DIR = Path(tempfile.gettempdir()) / "devin-system-control-confirmations"`.
- Create directory mode `0o700`; enforce best-effort chmod on Windows.
- Token: `secrets.token_hex(32)`.
- File name: `<token>.json`; token regex exactly 64 lowercase hex chars before path use.
- Write metadata to a random sibling temp file opened mode `0o600`, flush+fsync, then `os.replace` to final path.
- `consume_confirmation` validates token format, reads one file, deletes it immediately, then checks expiry and `compare_digest`.
- Reject TTL bool/non-int, ≤0, or >120 using `InvalidRequest`.

## CLI preflight

Add command:
`sc_cli.py preflight REQUEST_JSON`

- Exactly one positional JSON string.
- Parse errors and invalid requests: canonical `status:"rejected"`, exit 2.
- Valid classification: canonical `status:"verified"`, exit 0, `value` equal to the decision shape.
- Preflight never issues a token or dispatches an action.

Future mutation commands must call `classify`; no mutation command exists in Task 2.

## Required tests

Use the exact request helper and tests from plan Task 2. Also test:
- policy schema valid/invalid/extra keys;
- digest excludes confirmation ID but binds all other fields;
- overlapping DENY/CONFIRM proves deny wins;
- unknown capability deny;
- TTL bounds including bool;
- token format path traversal rejection;
- metadata contains no `args`, `target`, capability or raw request;
- file mode owner-only where `stat.S_IMODE` is meaningful;
- mismatch and expiry consume/delete token;
- malformed metadata fails closed and consumes token;
- CLI preflight allow/confirm/deny/invalid JSON and exactly-one-positional behavior.

## Verification

RED:
`python -m pytest tests/test_sc_policy.py -q`
Expected: fail because `sc_policy` does not exist.

GREEN:
`python -m pytest tests/test_sc_policy.py tests/test_sc_contract.py tests/test_sc_cli.py -q`
Expected: all pass.

Audit:
`python audit.py`
Expected: exit 0, zero errors.

Full suite:
`python -m pytest -q`
Expected: zero failures.

Commit message reserved for lead:
`feat(system-control): bind confirmations to requests`
