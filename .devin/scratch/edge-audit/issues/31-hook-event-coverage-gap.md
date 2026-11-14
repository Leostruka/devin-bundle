# 31 -- Hook event coverage gap: PreCompact/PostCompact unwired, dual PostCompaction contract

- **Status**: resolved
- **Category**: devin-cli-limitations
- **Severity**: P3
- **File**: hooks.v1.json:1-113

## Evidence

`hooks.v1.json` wires 8 of the 10 documented events: PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop, SessionEnd, PostCompaction, PermissionRequest (empty array). `DEVIN-CLI-COMPATIBILITY.md:156-157` documents `PreCompact`/`PostCompact` (since 3000.11.92) as distinct events with manual/auto matchers, but no matcher uses them. `constraint-pinning.py` hangs off `PostCompaction`, the legacy event; the CLI now keeps both `PostCompaction` and `PostCompact` supported, so the bundle depends on an event name with two live spellings and no stated deprecation horizon.

## Recommendation

Add explicit matchers for `PreCompact`/`PostCompact` (even if only logging or delegating to `constraint-pinning.py`), and document which of PostCompaction vs PostCompact is canonical for the pinning workaround.

## Tradeoffs

- Merits of current wiring: PostCompaction is still supported, pinning works, zero extra hook spawns.
- Demerits: if the CLI ever stops firing PostCompaction in favor of PostCompact, constraint re-injection silently dies (pinning is a repair mechanism for exactly this failure mode). Adding both events risks double-firing pinning logic unless made idempotent.
- Better contorno: wire `PostCompact` as the primary event (newer contract) and keep `PostCompaction` as a no-op alias guarded by a "already ran this compaction" marker keyed on `session_id`.

## Verification

`grep -n 'PreCompact\|PostCompact' hooks.v1.json` returns nothing; `grep -n 'PostCompaction' hooks.v1.json` shows the only compaction hook.

## Answer

Documented the dual compaction contract in TOOLS-MAP.md hook notes: `PostCompaction` is the canonical pinning event; `PostCompact`/`PreCompact` are deliberately unwired (double-fire risk on constraint-pinning; migration path = rewire PostCompact with a session_id idempotency marker). Wiring change deferred to CLI deprecation since hooks.v1.json is owned elsewhere.
