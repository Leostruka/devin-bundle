# Handoff doc

## Header

- **Handoff**: 02-researcher-agent-docs-audit
- **From role**: researcher
- **To role**: orchestrator
- **Date**: 2026-10-05
- **ESCALATE**: none (worker note: researcher profile is read-only; report
  was persisted verbatim by the orchestrator)
- **CONSULT**: none

## Inputs consumed

- `.devin/vision.md`, `.devin/docs/SKILL-TIERS.md`, `.devin/GLOBAL_BUNDLE_AUDIT.md`,
  `manifest.json`, `AGENTS.md`, `.devin/CONTEXT.md` - frozen inputs, all read.
- Readable refs: `.devin/ARCHITECTURE_MANIFEST.md`, all of `.devin/docs/`,
  `.devin/global_rules.md`, `data/bundle-models.json` (+5 other data files),
  `skills/writing-skills/SKILL.md`, `skills/writing-skills/reference/writing-for-agents.md`.

## Outputs produced

- `.devin/research/agent-docs-audit.md` - complete, VF1–VF5 satisfied
  (surface count + 100% coverage stated; DOC-001…DOC-018 unique IDs with
  severity/reach/file:line; ranked fix order; SKILL-TIERS + manifest
  cross-checks; GLOBAL_BUNDLE_AUDIT re-check).

## Decisions taken

- Severity scale: Critical = materially false/safety-relevant claims; High =
  drift with real impact; Medium = inconsistency/debt; Low = cosmetic.
- `.devin/hooks.v1.json` absence classified not-a-finding: `project-bootstrap`
  generates it per project (`skills/project-bootstrap/modes/setup.md:99`).
- social-midia nested skills classified as inventory blind spot, not manifest
  drift - audit.py counts top-level dirs only (audit.py:59-65).

## Verified claims

- 67 manifest skill names == 67 on-disk skill dirs -> manifest.json:13-472 +
  skills/ listing.
- All 75 SKILL.md have name+description frontmatter -> grep sweep; audit.py
  enforces `Use when` (audit.py:73).
- agents/*.md pins swe-2-max/medium consistent with bundle-models.json ->
  agents/*.md:3 + data/bundle-models.json:5-6.
- hooks.v1.json wires only exec + write/edit/notebook_edit matchers ->
  hooks.v1.json:2-45; CHECKS has 17 validators incl. dead run_subagent ->
  scripts/validate-tool-args.py:295-330.
- VALID_PROFILES missing qa-ci/repo-reviewer -> scripts/validate-tool-args.py:56-60.
- Root docs/ absent; installers source .devin/{docs,plans,templates} ->
  install.sh:583-610, install.ps1:592-613.

## Open items / gaps

- Exact SKILL.md byte sizes unmeasured; relied on SKILL-TIERS tok figures.
- Whether missing run_subagent matcher is intentional - needs owner decision
  (DOC-001).
- `.devin/` project-local artifacts audited by listing only.

## Requested next action

- Hand DOC-001…DOC-018 to docs-fix slice planning. Suggested slice order in
  report section 3.
