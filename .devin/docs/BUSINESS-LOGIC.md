# Business logic

Domain rules of the bundle, stated explicitly with code anchors. When a
rule changes, update this doc and the enforcing check together.

## Install semantics

- **R1. Live config is user-owned.** Default install merges and skips
  existing keys; only `-Force`/`--force` overwrites. Anchors:
  `install.ps1` merge block (~lines 158-162), `install.sh` (~lines
  218-224).
- **R2. Backups precede overwrite.** `-Backup`/`--backup` copies targets
  aside before writing; backup failure must abort the write (per
  DRIFT-LEDGER contract).
- **R3. Credentials are opt-in.** `credentials.toml` is never installed
  unless an explicit credentials flag is passed; masked placeholders are
  never written as real values.
- **R4. Hooks are rendered, not copied.** `hooks.v1.json` renders into
  live `config.json.hooks` via `scripts/render-user-hooks.py`; editing
  live hooks is ephemeral (ADR 005).
- **R5. Masked entries are sticky.** A `MASKED` value in the live config
  is a user secret placeholder; force-install must not silently replace
  a real secret with `MASKED` or vice versa (force-drift class, tracked
  issue 12).

## Export masking contract

- **R6. Masking is the default.** `-NoMask`/`--no-mask` is required to
  export real secrets; unmasked exports are never pushed to a public
  remote.
- **R7. Masked key set.** `credentials.toml`: all values. `config.json`:
  `org_id`. `mcp_config.json`: env values whose key matches
  token|secret|key|password|passwd|auth|bearer|credential|private|pat
  (case-insensitive). URLs of the form `https://user:pass@host` mask the
  credentials. Anchors: `export.ps1` lines 158-166 and the `export.sh`
  equivalents; parity tracked in INSTALL-PARITY.md.
- **R8. Hooks leave the export.** `config.json.hooks` is stripped on
  export; `hooks.v1.json` is the only versioned hook source.

## Hook event map

- **R9. Wired events.** `hooks.v1.json` binds PreToolUse (2 matchers),
  PostToolUse (2 matchers), UserPromptSubmit, SessionStart,
  PostCompaction, Stop, SessionEnd; `PermissionRequest` is present with
  an empty array to document the intent of not intercepting it.
- **R10. Intentionally unbound.** `PreCompact`/`PostCompact`
  (3000.11.92): `PostCompaction` is the canonical pinning event; wiring
  both would double-fire `constraint-pinning.py`. Rationale and
  migration path in `.devin/docs/TOOLS-MAP.md` (hook table notes).
- **R11. Fail policy.** `fail_closed: true` on both PreToolUse entries
  only; every other event is fail-open. Inner-script crashes are
  fail-open inside aggregators (`_hookrun.py`).

## Model routing policy

- **R12. Registry is the source.** `data/bundle-models.json` declares
  model UIDs, effort levels, `context_window`, and `cost_tier`. Per-agent
  `model:` frontmatter pins must resolve to a registry UID (TOOLS-MAP
  registry contract).
- **R13. Free follows free.** When the parent model has
  `cost_tier: free`, subagents must use free registry models or stop;
  paid aliases are forbidden (AGENTS.md rule 20, TOOLS-MAP conditional
  policy). When the parent is paid, paid subagents are allowed.
- **R14. No unverified aliases.** Short names (`opus`, `sonnet`,
  `codex`, `gemini`, `adaptive`) may resolve to paid entries; check the
  registry before use. `subagent_explore` routes through the CLI default
  router and is avoided; use `researcher` (`swe-2-max`).
- **R15. Env overrides.** `BUNDLE_DEFAULT_MODEL`, `BUNDLE_MAX_MODEL`,
  `BUNDLE_MEDIUM_MODEL` override per installation; values must still be
  registry UIDs (enforcement planned, issue 32).

## Manifest and versioning

- **R16. Bundle-level version.** `manifest.json` `version` is the only
  release version; it must equal the release tag (release.yml).
- **R17. Per-skill version signal.** `export_hash` per skill is the only
  ordering signal today: hash equality means identical, inequality means
  diverged with no older/newer semantics. An optional frontmatter
  version key (e.g. `x-bundle-version`) populated at export, plus
  audit reporting older/newer/equal instead of bare mismatch, is the
  accepted improvement (issue 33) pending implementation.
- **R18. Counts are contractual.** Skill count, script count, hook
  event count, and tool coverage numbers in README.md, SKILL-TIERS.md,
  and TOOLS-MAP.md are enforced by `audit.py` check 24; docs and disk
  must move together.

## Issue tracking

- **R19. Work items are in-repo.** `.devin/scratch/<effort>/issues/` is
  the tracker agents read and write (ADR 007); `.devin/issues/` holds
  milestone/design issues; GitHub PR numbers in CHANGELOG are for
  humans.
