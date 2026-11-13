# Task 6 report — verified file inspection and copy

## Result
- `extensions/system-control/sc_files.py` (new, ~360): root-bound
  `inspect_path` + hash-verified `copy_verified` + `validate_copy_args`.
- `sc_cli.py`: `file inspect|copy` — inspect allow; copy/copy_overwrite
  CONFIRM, `--request-id` required, validation before token burn; full
  `contract.result` envelope; `--`-prefixed token after a value flag →
  exit 2.
- `tests/test_sc_files.py`: 45 tests (2 POSIX-fifo skipped on Windows).

## Design
- Resolution: reject non-str/empty/NUL/absolute/`..`/trailing-dot-or-
  space (nt); realpath escape rejected; every component under root
  checked for `FILE_ATTRIBUTE_REPARSE_POINT` (0x400) — junctions,
  mount points, OneDrive placeholders.
- POSIX hardening: `_open_under_root` dirfd walk
  (`O_NOFOLLOW|O_DIRECTORY` intermediates, `O_NOFOLLOW` leaf) for
  inspect-hash + copy source reads — closes the resolve→open swap.
- Copy pipeline: pre-hash src → mkstemp sibling → looped `os.write`
  (memoryview, 1 MiB chunks) → fsync → close → re-read temp hash →
  `os.link` no-clobber (FileExistsError → rejected) or `os.replace`
  (overwrite) → dst re-hash. `finally` unlinks temp on every path.
- `S_ISREG` gate — FIFO/device/socket reported `type:"other"`, never a
  blocking open.
- Operational `OSError` → `status:"unknown"` (exit 1); request-shape
  violations → `rejected` (exit 2).

## Review history
- Round 1: Spec FAIL / Standards FAIL — missing dirfd opens (plan
  Step 3), streamed-hash trusted instead of re-read, non-atomic
  overwrite check, envelope parity gap, unchecked `os.write`, FIFO
  block, missing-src token burn, OSError→rejected misclassification,
  flag swallow, Windows trailing dot/space.
- Rework: all 10 closed; held-out still 5/5.

## Evidence
- `pytest tests/test_sc_files.py tests/test_sc_cli.py
  tests/test_sc_policy.py`: 101 passed, 2 skipped (POSIX fifo).
- Held-out `test_file_integrity.py`: 5/5 (both rounds).
- Full suite: 829 passed, 3 skipped.
- `python audit.py`: 0 errors, 1 pre-existing `__pycache__` warning.

## Residual
- Windows resolve→open swap window remains (documented; T7 native
  adapter may close with handle-based ops).
- Destination-parent resolution is path-based on both platforms.
- `expected_hash` is sha256-only (brief-pinned signature).
