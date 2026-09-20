# Task 6 brief — verified file inspection and copy

Lead notes:
- Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`, branch `feat/system-control`.
- Follow `.devin/plans/2026-09-19-system-control.md` Task 6.
- Do not read or modify `tests/held-out/`; do not commit/PR/push.

Create `extensions/system-control/sc_files.py`: root-bound path
inspection + hash-verified copy. stdlib only; target ~350 lines.

## API (pinned by held-out — implement exactly)

- `inspect_path(root, rel) -> result envelope dict`
  - `rel` must be relative; absolute, `..` traversal, empty, NUL →
    `{"ok": False, "status": "rejected"}`.
  - Resolve under `root` with `os.path.realpath`; reject if the resolved
    path escapes root (symlink/reparse chains included — a `l1 -> l2 ->
    outside` chain rejects).
  - Windows: check `FILE_ATTRIBUTE_REPARSE_POINT` on every resolved
    component under root (junctions, symlinks) — reject any.
  - Returns `{"ok": True, "status": "verified", "value": {"path", "type"
    ("file"|"dir"|"missing"), "size", "mtime", "inode/file_id",
    "sha256" (streaming, files only), "is_link": false}}`. Never returns
    file contents. Missing path → `type: "missing"`, no hash.
- `copy_verified(root, rel_src, rel_dst, *, expected_hash, dry_run=False,
  overwrite=False) -> envelope`
  - Same root-bound resolution for BOTH paths; dst parent must exist
    under root.
  - Read source → streaming sha256; mismatch vs `expected_hash` →
    `{"ok": False, "status": "rejected"}`, dst untouched, no partial
    temp left (verify: no extra files in root).
  - `dry_run=True` → `status: "verified"`, `value` carries
    `{"src_sha256", "dst", "bytes"}`; writes nothing.
  - Real copy: sibling temp via `tempfile.mkstemp(dir=dst_parent)` →
    stream-copy → `os.fsync` → re-hash temp → `os.replace` → re-hash
    dst. `precondition.sha256` == `postcondition.sha256` ==
    expected_hash in the envelope.
  - Existing dst → `rejected` unless `overwrite=True` (CLI maps
    overwrite to `file.copy_overwrite` CONFIRM; plain copy is
    `file.copy` CONFIRM).
  - Any failure after temp creation → temp deleted in finally.
  - Source mutation between hash check and copy → hash mismatch on
    temp verify → rejected, dst absent.

## CLI (`sc_cli.py`)

- `file inspect --root DIR --path REL` → `file.inspect` (allow).
- `file copy --root DIR --src REL --dst REL --expected-hash HEX
  [--dry-run] [--overwrite]` → `file.copy` (CONFIRM;
  `file.copy_overwrite` when `--overwrite`). Confirmation consumed after
  full arg validation; `--request-id` required; exit 2 on reject.

## Visible tests (RED first)

`tests/test_sc_files.py`: parent escape, absolute path, symlink chain,
reparse-point file, missing file, dir inspect, streaming hash on a
multi-MB file (sparse ok), hash mismatch leaves no residue, dry-run
writes nothing, overwrite gating, dst-in-subdir, mutation invalidation,
CLI reject paths. tmp_path fixtures.

## Gates

- `python -m pytest tests/test_sc_files.py -q` → 0 fails.
- `python -m pytest tests/test_sc_cli.py tests/test_sc_policy.py -q` → no regression.
- `python -m py_compile` touched files.

Report: files+lines, signatures, test names/counts, residuals.
