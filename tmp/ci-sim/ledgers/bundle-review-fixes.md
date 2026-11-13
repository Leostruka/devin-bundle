# GATES: bundle-review-fixes

Scope: 9 flags from the 2026-10-03 full bundle review. Branch
`chore/bundle-review-fixes`, one logical commit per flag group.

- [x] G1 F9 pytest_full.log tracked
  CHECK: git ls-files | grep pytest_full.log; git check-ignore -v pytest_full.log
  EXPECT: untracked + ignored
  EVIDENCE: not in ls-files; `.gitignore:46:*.log` matches
  ABANDON: false positive — file is untracked local residue, already ignored. No repo change.

- [x] G2 F4 dead ref "Replaces operate-spline"
  CHECK: grep operate-spline skills/operate-blender/SKILL.md manifest.json
  EXPECT: 0 matches
  EVIDENCE: phrase removed from description + manifest purpose

- [x] G3 F5 youtube name collision
  CHECK: youtube-fetcher description contains social-midia pointer
  EXPECT: disambiguation clause present
  EVIDENCE: appended "Not for publishing or posting to YouTube; use social-midia/youtube"

- [x] G4 F8 testing quartet boundary
  CHECK: 4 descriptions each carry explicit not-for clause
  EXPECT: testing/e2e-testing/observability-quality/gates updated
  EVIDENCE: boundary sentence appended to all 4 + manifest purposes synced

- [x] G5 F2 refinements.log.jsonl absent
  CHECK: .gitignore contains .devin/refinements.log.jsonl
  EXPECT: intentionally gitignored runtime artifact
  EVIDENCE: `.gitignore:29`; Rule 15 amended to document runtime/gitignored nature

- [x] G6 F3 docs/templates path
  CHECK: install.ps1 maps .devin/templates -> docs/templates
  EXPECT: path already correct; clarify wording only
  EVIDENCE: `install.ps1:595-597`; Rule 29 amended with installed-path note

- [x] G7 F1 mcp_count semantics
  CHECK: audit section [10b] enforces mcp_count == len(bundle-integrations.mcp)
  EXPECT: check passes
  EVIDENCE: `OK  mcp_count = 1 (bundle-integrations.json)`; semantics = available integrations, atlassian

- [x] G8 F6 manifest export_hash schema
  CHECK: all skill entries have export_hash, no stray fields
  EXPECT: 0 missing, 0 extras
  EVIDENCE: 36 filled, 4 `hash` renamed (stale values replaced), schema uniform

- [x] G9 F7 audit hardcoded counts
  CHECK: python audit.py; pytest -k "audit or manifest or consistency"
  EXPECT: 0 errors; tests pass
  EVIDENCE: `Errors: 0`; 22 passed incl. test_audit_passes x3; warnings 2 pre-existing + 7 drift (live stale post-edit, resolves on install)

- [x] G10 final: full audit + git state + test suite
  CHECK: python audit.py; pytest tests -q; git log --oneline -4
  EXPECT: 0 errors; suite green; 4 scoped commits
  EVIDENCE: audit Errors: 0; 1543 passed, 4 skipped (174s); da687de..51715fc
