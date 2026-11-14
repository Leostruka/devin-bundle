# 55 -- No ADR for vendored/external skill adoption policy

- **Status**: resolved
- **Category**: adr
- **Severity**: P3
- **File**: manifest.json

## Evidence
CHANGELOG #295 describes a recurring pattern: vendoring external skills
("cursor/plugins MIT vendors, adapted to Devin run_subagent", Ponytail
lean-code port, Cloudflare security-audit renamed to avoid collision).
manifest.json tracks `source` per skill (e.g. `created:v2.8.0
skill-coverage`, upstream names) but no doc states the policy: which
licenses are acceptable, when to rename to avoid collision, whether to
keep upstream sync metadata, attribution format (NOTICE.md exists), and
who audits vendored code for secrets/telemetry. Rule 7-style decisions
like this are exactly what `.devin/adr/` exists for; only 4 ADRs exist
for a repo making dozens of such calls.

## Recommendation
Add `.devin/adr/NNN-vendored-skills.md`: license whitelist (MIT observed),
rename-on-collision rule, `source` field convention, NOTICE.md
attribution, and a required skills-audit step before vendoring.

## Tradeoffs
A formal policy adds friction to one-off adoptions; accept that or scope
the ADR to skills only (not extensions).

## Verification
ADR exists; `skill-coverage`/`skill-discovery` SKILL.md references it for
the "install/avalia externas" flow.

## Answer

Wrote `.devin/adr/008-vendored-skill-policy.md` (Accepted): license whitelist (MIT baseline), attribution via manifest source + NOTICE/header, rename-on-collision, adaptation notes, pre-vendoring secrets/telemetry audit; scoped to skills.
