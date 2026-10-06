# Delegation contract

## Contract

- **Contract ID**: 06-implementer-rag-wiring
- **Objective**: Wire the new `rag` skill into the bundle's registries and
  close DOC-005 (manifest.docs resync). Convergence contract: makes
  `audit.py` green again after contracts 03/04/05.
- **Profile**: implementer
- **Lane**: direct on main worktree
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\agent-docs-audit.md`
    (DOC-005)
  - `D:\Programing\ai_workspace\devin-bundle\manifest.json` (skill entry
    format; `cu-realtime` entry shows hash-less entries are valid)
  - `D:\Programing\ai_workspace\devin-bundle\skills\rag\SKILL.md` (the
    `purpose` field must equal its `description` verbatim - audit.py ~788)
  - `D:\Programing\ai_workspace\devin-bundle\audit.py` (sections ~24 and
    the manifest/skills checks; doc_checks expect pt-BR strings that
    contract 03/04 removed - update the expected strings to the new EN
    text, or to whatever the rewritten docs actually contain)
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\TOOLS-MAP.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\SKILL-TIERS.md`
  - `D:\Programing\ai_workspace\devin-bundle\README.md`
- **Readable refs**: `.devin/vision.md`, `.devin/adr/004-rag-skill-tier-model.md`
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/research/agent-docs-audit.md` sha256:1185be4e9801d01e10d74f51a8af840710dabfa976749f0b82362d66cdfe7e3f
  - `skills/rag/SKILL.md` sha256:d6a765bb89cd70469a21f6c32680b07077df28af393c3c5daafca9884ffe161d
- **Output**: edits below + handoff at `.devin/handoffs/06-implementer-rag-wiring-out.md`
- **Files you may modify (exclusive)**:
  - `manifest.json` - add `rag` skill entry (name/source/purpose; purpose =
    SKILL.md description verbatim; follow the `cu-realtime` minimal-entry
    precedent - no export_hash/original_path/exported_at); `skill_count`
    67 -> 68; DOC-005: `docs` array -> path-qualified real files (installed
    `.devin/docs/` set + root `AGENTS.md`, `README.md`, `CHANGELOG.md`);
    keep valid JSON, no other fields touched.
  - `.devin/docs/SKILL-TIERS.md` - add `rag` row in the Documentation or
    Pesquisa/Data section (pick the honest fit: it teaches building
    retrieval - "Documentation" section or a new short row group; measure
    SKILL.md bytes/4 for the tok column).
  - `README.md` - skills count strings + badge `skills-67` -> `skills-68`
    wherever the diagram/count asserts the old number (audit checks
    `str(count) + ' skills'` in README).
  - `.devin/docs/TOOLS-MAP.md` - skills count string -> `68 skills` (audit
    §24 checks literal presence).
  - `audit.py` - §24 `doc_checks`: replace stale expected literals
    (`'8 eventos'`, `'9 excluídas'`, `'28 ferramentas'`, `'19/28'`,
    `'8 events'` for README as applicable) with the exact strings the
    EN-rewritten docs now contain. Do NOT weaken checks - update expected
    text, keep the assertion logic. Also check nothing else in audit.py
    hardcodes pt-BR doc strings.
- **Tools allowed**: profile default
- **Peer consults**: none
- **Boundaries (do NOT)**:
  - modify `skills/rag/` content (reviewer contract owns critique; fixes
    loop separately)
  - modify any other skill, hook wiring (`hooks.v1.json`, `config.json`),
    or `.devin/docs/` files beyond the two count/row updates
  - bump `version` in manifest.json or CHANGELOG (no release this track)
  - add `triggers`/frontmatter anywhere else; change rule_count/agent_count
- **Termination**: max 40 turns / 30 minutes; stop when VFs pass
- **Verification (VFs)**:
  - VF1: `python audit.py` -> 0 errors (warnings acceptable, list them)
  - VF2: `python -c "import json;m=json.load(open('manifest.json'));print(
    m['skill_count'], any(s['name']=='rag' for s in m['skills']))"` ->
    `68 True`
  - VF3: `grep -n "rag" .devin/docs/SKILL-TIERS.md` -> a `rag` table row
    exists
  - VF4: manifest purpose for `rag` == SKILL.md description (exact string
    compare via python)
  - VF5: `pytest -q` -> green

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
