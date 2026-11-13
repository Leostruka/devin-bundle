# 72 -- Bundle business rules exist only as implicit code, no domain document

- **Status**: resolved
- **Category**: business-logic
- **Severity**: P2
- **File**: n/a (cross-cutting: install.sh/export.*, hooks.v1.json,
  data/bundle-models.json, manifest.json)

## Evidence

The bundle's core domain decisions are encoded in scripts and audit checks
but stated nowhere as rules:

- Install semantics: credentials gating, backup/merge of existing config,
  force-drift behavior of masked mcp entries (cf. issues 02, 12, 16-19)
  live only inside install.sh/install.ps1 branches.
- Export masking: which keys get MASKED, and the sh-vs-ps1 asymmetry
  (issue 06), is implicit in regexes.
- Hook event wiring: hooks.v1.json matchers + _hookrun aggregation are the
  contract; no doc states which events are intentionally unbound (audit.py:898
  notes "intentionally does" without saying which or why).
- Model routing policy: bundle-models.json + AGENTS.md Rule 20 + per-agent
  `model:` front matter agree today, but the free/paid routing rule
  ("parent free -> subagents free or stop") exists only in skill prose.
- Manifest contracts (counts, hashes, purposes) are enforced by audit.py but
  the schema is documented only by the checker itself.

A reader cannot answer "what is this bundle allowed to do" without diffing
audit.py against the scripts.

## Recommendation

Add `.devin/adr/` entries or a `docs/DOMAIN-RULES.md` capturing: install
merge/backup semantics, export masking contract, hook event map with
rationale for unbound events, and the routing policy table. Point audit.py at
it so checks cite the rule they enforce.

## Verification

`grep -rn "masking\|install semantics\|routing policy" .devin/adr .devin/docs`
returns no document stating these rules.

## Answer

Wrote `.devin/docs/BUSINESS-LOGIC.md`: 19 explicit rules (R1-R19) with code anchors covering install merge/backup/credentials semantics, the export masking contract, the hook event map with unbound-event rationale, the model routing/free-follows-free policy, manifest/versioning contracts, and the issue-tracker split.
