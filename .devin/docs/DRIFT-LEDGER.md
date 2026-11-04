# Install drift ledger (design)

Status: design recorded, implementation planned
(`.devin/issues/MILESTONE_2_06_install_drift_ledger.md`). This doc freezes
the contract so `audit.py`, the installers, and the future
`scripts/install-ledger.py` agree before code lands.

## Problem

`audit.py` detects live-vs-bundle drift by hashing a fixed list of file
pairs. Anything outside the pair list is invisible: skills/agents
renamed or deleted bundle-side leave foreign files in the live config;
a hash mismatch cannot be classified as user-edit vs stale-install vs
partial-install; shadow dirs (both `%APPDATA%/devin` and
`~/.config/devin` existing) are warn-only.

## Ledger schema (target)

`.devin/install-ledger/installs.json` (live-side, per install):

```json
{
  "records": [
    {
      "slug": "skills/thermos",
      "tool": "install",
      "scope": "user",
      "dest": "<devin-home>/skills/thermos",
      "source_hash": "sha256:...",
      "rendered_hash": "sha256:<bytes actually written>",
      "installed_at": "2026-..T..Z",
      "corpus_version": "<manifest.json version>"
    }
  ]
}
```

Rules:

- `rendered_hash` is the hash of the bytes written, not the repo bytes
  (rendered output may differ, e.g. hooks paths).
- Renderers must be deterministic: no timestamps or randomness in
  rendered bytes; the timestamp lives in the record, not the content.
- `backup_if_differs`: before any overwrite, copy prior bytes to
  `<devin-home>/.backups/<name>.<fs-safe-ts>`; if the backup fails the
  write aborts; byte-identical targets are skipped.

## Reconcile states

`install-ledger.py reconcile` maps every managed file to exactly one:

| State | Meaning |
|---|---|
| Current | live bytes == ledger `rendered_hash` |
| Outdated | ledger hash differs from bundle source; safe to re-install |
| Modified | live bytes differ from ledger `rendered_hash`; user edit, do not overwrite silently |
| Removed | ledger record exists, live file gone |
| Foreign | live file under a managed dir with no ledger record |

`audit.py` reports Modified/Foreign as warnings, Removed/Outdated as
informational; only ledger inconsistency is an error.

## Interim (pre-ledger)

Until `install-ledger.py` exists, the cheap reconcile is a name-set
diff: enumerate `skills/`, `agents/`, `scripts/` under the live dir and
diff the name sets against `manifest.json`, reporting foreign/missing
counts. This gives most of the reconcile value with no install-time
writes.

## Non-goals (M2_06 scope)

- No multi-CLI rendering yet.
- No content hashing outside managed files.
- `manifest.json` stays metadata; the ledger is runtime state and is
  never committed.
