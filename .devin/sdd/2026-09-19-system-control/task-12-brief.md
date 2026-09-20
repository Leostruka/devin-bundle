# Task 12 brief — integration, skill, docs

## Plan reference

`.devin/plans/2026-09-19-system-control.md` Task 12 (~250-350 lines).

## Files

- Create `extensions/system-control/USAGE.md`
- Create `skills/system-control/SKILL.md` (thin router ≤80 lines)
- Create `tests/validation/test_system_control_workflow.py`
- Modify `manifest.json`, `.devin/docs/SKILL-TIERS.md`,
  `.devin/docs/TOOLS-MAP.md`, `README.md`
- Installers ONLY if dry-run shows a real gap.

## TDD

1. `tests/validation/test_system_control_workflow.py` FIRST (RED):
   - SKILL.md references `extensions/system-control/USAGE.md`,
     ≤80 lines, frontmatter `triggers: [user, model]`.
   - USAGE.md contains "no privileged daemon by default",
     "one-shot confirmation", "dropped".
   - manifest has a `system-control` skill entry.
   - `install.sh --dry-run` / `export.sh --dry-run` mention
     `system-control` (or extension enumeration includes it).
2. Implement skill + USAGE + metadata via the repo's sync procedure
   (check how `skills/scan` was registered — manifest + SKILL-TIERS +
   TOOLS-MAP counts from actual disk; don't hand-edit generated
   hashes if a sync script owns them).

## SKILL.md requirements

- Thin router only — direct agent to USAGE.md for command reference.
- State when to prefer system APIs over GUI computer-use.
- Preserve confirmation + untrusted-output rules.

## USAGE.md requirements

- Interpreter, JSON status semantics, capabilities matrix
  (win/linux/macos), policy/confirmations, sessions, files,
  telemetry, failure modes, install, broker opt-in.
- Examples only for safe read-only/owned-process actions.
- Required phrases (test-pinned): "no privileged daemon by default",
  "one-shot confirmation", "dropped".

## Gates

1. `python -m pytest tests/validation/test_system_control_workflow.py -q`
2. `python audit.py` — 0 errors (skill count sync checks!)
3. `python -m pytest -q` — full suite
4. `bash -n install.sh`; `install.sh`/`export.sh` dry-runs exit 0
   listing system-control; PowerShell ParseFile tokenize gate on
   install.ps1; `install.ps1 -DryRun`/`export.ps1 -DryRun`.
5. Independent security review (lead will run after implementation).

## Notes

- Audit checks: skill count badges (51→52), TOOLS-MAP counts,
  SKILL-TIERS table, README diagram count, manifest purpose↔
  SKILL.md description sync. Update ALL of them.
- `data/` sync scripts may own generated values — use them.
