# Task 2 Report — One-shot request-bound confirmation policy

Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`
Branch: `feat/system-control` (Task 1 committed at `b02cdec`)

## Files changed

Created:
- `extensions/system-control/sc_policy.py` — DENY/CONFIRM/ALLOW sets,
  `request_digest`, `classify`, `issue_confirmation`,
  `consume_confirmation`, atomic token-file persistence.
- `tests/test_sc_policy.py` — 17 visible tests (classification order,
  deny-wins, unknown deny, digest binding/stability, token format,
  TTL validation incl. bool rejection, metadata minimality, single-use,
  expiry, mismatch, replay, malformed metadata, token-path validation).

Modified:
- `extensions/system-control/sc_contract.py` — optional `policy` object
  validation in `validate_request`: only `dry_run`/`confirmation_id`
  keys, `dry_run` bool-only, `confirmation_id` string-or-null, other
  keys rejected; present-but-non-object `policy` rejected.
- `extensions/system-control/sc_cli.py` — `preflight REQUEST_JSON`
  subcommand: exactly one positional, JSON parse errors → exit 2,
  invalid request → exit 2, valid → `status:"verified"` exit 0 with
  `value` = policy decision. No token issuance, no dispatch.
- `extensions/system-control/schemas/v1.json` — `policy` object added
  to request schema (`dry_run` boolean, `confirmation_id` string|null,
  `additionalProperties: false`).
- `tests/test_sc_cli.py` — 7 preflight tests (allow/confirm/deny/
  unknown-deny/invalid JSON/invalid request/positional count).

Not touched: `tests/held-out/` (never read or edited — note: worktree
shows `test_identity_and_confirmation.py` modified; that change is not
mine, the file is lead-owned; its 4 tests pass). No staging, no commits.

## RED gate

```
python -m pytest tests/test_sc_policy.py tests/test_sc_contract.py tests/test_sc_cli.py -q
```

```
collected 42 items / 1 error
ERROR collecting tests/test_sc_policy.py
E   ModuleNotFoundError: No module named 'sc_policy'
=========== 1 error in 0.20s ===========
```

Expected failure: `sc_policy` module absent; collection interrupted
before other tests ran. New preflight/policy-schema tests were
subsequently exercised in GREEN.

## GREEN gate

```
python -m pytest tests/test_sc_policy.py tests/test_sc_contract.py tests/test_sc_cli.py tests/test_sc_inventory.py -q
```

```
collected 75 items
tests\test_sc_policy.py .................        [ 22%]  (17)
tests\test_sc_contract.py ...............        [ 42%]  (15)
tests\test_sc_cli.py ........................... [ 78%]  (27)
tests\test_sc_inventory.py ................       [100%]  (16)
============= 75 passed in 1.33s =============
```

## Audit

```
python audit.py   →  exit 0
=== SUMMARY ===
Errors:   0
Warnings: 2
```

Warnings (pre-existing, unchanged): `__pycache__` directories;
`v3.1.1` tag missing.

## Full suite

```
python -m pytest -q
```

```
============= 659 passed, 1 skipped in 102.89s =============
```

Skip is the pre-existing `test_cu_screenshot` environment skip.
Held-out `system-control/test_identity_and_confirmation.py` (4 tests)
passes.

## Security self-review

- Deny-wins: `classify` checks DENY → CONFIRM → ALLOW → unknown deny,
  in that order; unknown capabilities always deny.
- `dry_run` never authorizes anything: this task adds no mutation path;
  `preflight` only classifies — it issues no token and dispatches no
  action. `dry_run`/`confirmation_id` are contract fields only.
- Digest binding: `request_digest` validates via `validate_request`
  (fail-closed canonicalization), strips only `confirmation_id`, then
  SHA-256 over `json.dumps(sort_keys, separators=(",", ":"),
  ensure_ascii=False)`. Tests prove target/args/deadline/capability/
  request_id/dry_run each change the digest; `confirmation_id` does not.
- Token entropy: `secrets.token_hex(32)` → 256 bits, 64 lowercase hex.
- Metadata minimality: token file contains only
  `{digest, created_at, expires_at}` — verified by test; no args,
  target, capability, or raw request persisted.
- Single-use: `consume_confirmation` reads the file then unlinks it
  before any expiry/digest/metadata check returns — verified for
  success, mismatch, expiry, malformed metadata, and replay.
- Constant-time comparison: `hmac.compare_digest` on digest strings.
- Path safety: token validated against `^[0-9a-f]{64}$` (fullmatch)
  before joining to `STATE_DIR`; no traversal possible.
- Atomic write: `tempfile.mkstemp` (O_CREAT|O_EXCL, 0600) in the state
  dir → write → flush → `os.fsync` → `os.replace`; temp cleaned on error.
- Permissions: state dir `os.makedirs(mode=0o700)` + best-effort
  `chmod 0o700` (Windows ACLs differ; best-effort per brief).
- TTL: integer-only, `bool` rejected explicitly (bool ⊂ int), range
  `1..120`, invalid → typed `InvalidRequest`.
- Malformed metadata: JSON/type errors → token already deleted →
  `{"ok": False, "reason": "unknown_confirmation"}` (fails closed).
- CLI: exactly one JSON object on stdout; errors → stderr diagnostics
  + canonical envelope; exit 2 for parse/validation, exit 0 verified.
- `consume_confirmation` validates the request first via
  `request_digest`; malformed request → `InvalidRequest` (typed error),
  token file untouched — no consume decision made on bad input.
- No secrets, no credentials, no daemon/server started; stdlib only.

## Deviations / decisions

- `policy: null` (key present, value null) is rejected as non-object —
  consistent with the JSON schema (`"type": "object"`); an absent
  `policy` key remains valid.
- `consume_confirmation` computes the digest before the token-format
  check, so a malformed request raises `InvalidRequest` rather than
  returning a consume-failure dict. Token untouched in that case.

## Rework round 1 (review findings)

Four defects fixed, tests first:

1. **Atomic single-use consume** — `consume_confirmation` now claims the
   token via `os.replace(path, .consume-<token>-<rand>)` before reading;
   loser gets `unknown_confirmation`. Claimed file is read, then
   unlinked before any validation returns; unlink failure →
   `unknown_confirmation` (never success). New tests:
   `test_consume_is_atomic_single_use` (two threads rendezvous inside a
   patched `Path.read_text` on the original token name — deterministic:
   old read-then-unlink code let both succeed; new code lets only the
   rename winner read, and its claimed filename never hits the barrier)
   and `test_consume_unlink_failure_never_succeeds` (patched
   `Path.unlink` → OSError → `unknown_confirmation`).
2. **Issue only for confirm capabilities** — `issue_confirmation`
   classifies first and raises `InvalidRequest("capability does not
   require confirmation")` unless decision is `confirm`.
   `test_issue_confirmation_rejects_non_confirm` covers explicit deny,
   unknown, and allow; also asserts no token files are left behind.
3. **Preflight is policy-only** — `preflight` handled first inside the
   try with `name = "policy"`; `sc_backend.current()` only runs for
   inventory commands; duplicate branch removed.
   `test_cli_preflight_does_not_need_backend` monkeypatches
   `sc_backend.current` to raise and still gets verified +
   `backend == "policy"`.
4. **Hardened metadata parsing** — exact key set
   `{digest, created_at, expires_at}`; digest must be `str`; times must
   be finite int/float (bool rejected); `expires_at >= created_at`;
   lifetime `0 < expires_at - created_at <= 120`; expiry check now
   `time.time() >= expires_at`. All malformed → `unknown_confirmation`
   after deletion. `test_consume_rejects_malformed_metadata_fields`
   covers missing/extra keys, non-str digest, bool/NaN/Infinity times,
   reversed timestamps, lifetime >120, non-numeric time, non-dict meta.
   `test_consume_expired_deletes_token` updated to keep well-formed
   metadata (created_at back-dated) so the expiry path is reached;
   malformed-JSON test also asserts no leaked claim files.

### Rework RED

```
python -m pytest tests/test_sc_policy.py tests/test_sc_cli.py -q
```

```
FAILED test_consume_is_atomic_single_use        (both threads ok=True)
FAILED test_consume_unlink_failure_never_succeeds (returned confirmed)
FAILED test_issue_confirmation_rejects_non_confirm (DID NOT RAISE)
FAILED test_consume_rejects_malformed_metadata_fields (extra key → confirmed)
FAILED test_cli_preflight_does_not_need_backend (exit 1, backend init)
5 failed, 44 passed in 0.42s
```

### Rework GREEN

```
python -m pytest tests/test_sc_policy.py tests/test_sc_contract.py tests/test_sc_cli.py tests/test_sc_inventory.py -q
```

```
collected 80 items
test_sc_policy.py   21 passed
test_sc_contract.py 15 passed
test_sc_cli.py      28 passed
test_sc_inventory.py 16 passed
============= 80 passed in 1.64s =============
```

### Rework audit

```
python audit.py   →  exit 0
Errors: 0   Warnings: 2 (same pre-existing: __pycache__ dirs, v3.1.1 tag)
```

### Rework full suite

```
python -m pytest -q
============= 664 passed, 1 skipped in 46.69s =============
```

(pre-existing `test_cu_screenshot` skip; held-out untouched.)

### Rework security notes

- Claim-by-rename is atomic per filesystem; only one consumer can own
  the claimed path. Original token path disappears at claim time, so a
  second consumer can never observe it.
- Success is unreachable unless the claimed file is fully deleted
  first — an unlink failure returns `unknown_confirmation` rather than
  risking a replayable token.
- Orphan `.consume-*` files can remain only if unlink fails after a
  successful claim; they contain the same minimal metadata and are
  unguessable-named; acceptable residue per the prescribed shape.
- `issue_confirmation` fail-closed: any non-`confirm` decision —
  including unknown and explicit deny — raises before a token exists.
- Preflight now carries `backend: "policy"` and cannot be blocked by
  backend discovery failures.

## Rework round 2 (independent review: suite flake)

Independent review observed `1 failed / 663 passed` full-suite flake and
`6/60` races where both consumers returned false. Root cause: the race
test barriered `Path.read_text` on `<token>.json`, but the claim-based
implementation reads `.consume-*` — so the barrier never fired and the
two claims were unsynchronized; on Windows a transient `OSError` while
reading the claimed file could also make the winner fail.

Fixes:

1. **Race test syncs the claim, not the read** — barrier now wraps
   `os.replace` when `Path(src).name == "<token>.json"`, forcing both
   threads to contend on the atomic rename. Asserts both threads
   terminate (`join(15)` + `is_alive` check) and
   `sorted(results) == [False, True]`.
2. **`_read_claimed` bounded retry** — transient `OSError` reading an
   already-claimed token retried up to 5 attempts with 10 ms sleep;
   final failure re-raises into the existing fail-closed path
   (unlink claimed → `unknown_confirmation`). The initial
   `os.replace` claim is never retried — one-shot semantics unchanged.
3. **New tests** — `test_consume_retries_transient_claimed_read`
   (`.consume-*` read raises `PermissionError` twice, then succeeds:
   consume returns `confirmed`, `calls == 3`, dir empty) and
   `test_consume_persistent_claimed_read_failure_fails_closed`
   (always raises: `unknown_confirmation`, no files remain).

### Rework-2 focused run

```
python -m pytest tests/test_sc_policy.py -q
============= 23 passed in 0.50s =============
```

### Stress verification

`pytest-repeat` not installed (`ModuleNotFoundError`). Fallback loop:

```
fails=0; for i in $(seq 1 50); do
  python -m pytest tests/test_sc_policy.py::test_consume_is_atomic_single_use -q \
    > /tmp/race_$i.log 2>&1 || fails=$((fails+1))
done
ITERATIONS=50 FAILURES=0
```

### Rework-2 gates

```
python -m pytest tests/test_sc_policy.py tests/test_sc_contract.py tests/test_sc_cli.py tests/test_sc_inventory.py -q
============= 82 passed in 1.63s =============
(policy 23, contract 15, cli 28, inventory 16)

python audit.py   →  exit 0
Errors: 0   Warnings: 2 (same pre-existing: __pycache__ dirs, v3.1.1 tag)

python -m pytest -q
============= 666 passed, 1 skipped in 45.59s =============
(pre-existing test_cu_screenshot skip; held-out untouched)
```

## Rework round 3 (final review cleanup)

1. **Non-UTF-8 / deeply nested metadata fail closed** —
   `_read_claimed` call site now catches `(OSError, UnicodeError)`
   (invalid UTF-8 bytes → `UnicodeDecodeError` previously propagated
   and leaked the `.consume-*` file); `json.loads` now catches
   `(ValueError, RecursionError)` (deeply nested JSON). New tests:
   `test_consume_invalid_utf8_metadata_fails_closed` (writes
   `b"\xff\xfe\x00bad"`) and
   `test_consume_deeply_nested_json_fails_closed` (100k `[`) — both
   return `unknown_confirmation` and leave the state dir empty.
2. **Preflight backend name set at branch entry** — `name = "policy"`
   assigned before positional/JSON validation, so every preflight
   response (verified or rejected) reports `backend: "policy"`.
   `test_cli_preflight_invalid_json_rejected` and
   `test_cli_preflight_exactly_one_positional` now assert it.

### Rework-3 RED

```
python -m pytest tests/test_sc_policy.py tests/test_sc_cli.py -q
```

```
FAILED test_consume_invalid_utf8_metadata_fails_closed   (UnicodeDecodeError propagated)
FAILED test_consume_deeply_nested_json_fails_closed      (RecursionError propagated)
FAILED test_cli_preflight_invalid_json_rejected          (backend 'none')
FAILED test_cli_preflight_exactly_one_positional         (backend 'none')
4 failed, 49 passed in 0.80s
```

### Rework-3 gates

```
python -m pytest tests/test_sc_policy.py tests/test_sc_contract.py tests/test_sc_cli.py tests/test_sc_inventory.py -q
============= 84 passed in 1.82s =============
(policy 25, contract 15, cli 28, inventory 16)

python audit.py   →  exit 0
Errors: 0   Warnings: 1 (pre-existing __pycache__ dirs; v3.1.1 tag
warning no longer present)

python -m pytest -q
============= 668 passed, 1 skipped in 48.23s =============
(pre-existing test_cu_screenshot skip; held-out untouched)
```

## Concerns

1. Windows file permissions are best-effort: `mkstemp` gives 0600 on
   POSIX; on Windows the token file inherits directory ACLs. The state
   dir chmod is best-effort per brief; ACL hardening is platform work
   for a later task.
2. `consume_confirmation` expiry check reads `time.time()` — clock
   jumps could extend/shrink validity; acceptable per brief (monotonic
   not specified).
3. `tests/held-out/system-control/test_identity_and_confirmation.py`
   shows as modified in the worktree — not by me; flagged for lead
   awareness in case staging splits are needed.
