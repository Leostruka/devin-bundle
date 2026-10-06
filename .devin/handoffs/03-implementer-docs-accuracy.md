# Delegation contract

## Contract

- **Contract ID**: 03-implementer-docs-accuracy
- **Objective**: Fix the accuracy findings DOC-001, DOC-002, DOC-006,
  DOC-008, DOC-010, DOC-011, DOC-012, DOC-013, DOC-017, DOC-018 from
  `.devin/research/agent-docs-audit.md`. Doc files are rewritten in ENGLISH
  per ADR-005.
- **Profile**: implementer
- **Lane**: direct on main worktree (files below are exclusive to this
  contract)
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\agent-docs-audit.md`
    (findings DOC-xxx; evidence lines are verified, trust them but re-check
    before editing each file)
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\TOOLS-MAP.md`
  - `D:\Programing\ai_workspace\devin-bundle\hooks.v1.json`
  - `D:\Programing\ai_workspace\devin-bundle\scripts\pre-exec-guard.py`
    (head only: see which gates it chains)
  - `D:\Programing\ai_workspace\devin-bundle\scripts\pre-write-guard.py`
    (head only)
  - `D:\Programing\ai_workspace\devin-bundle\scripts\validate-tool-args.py`
  - `D:\Programing\ai_workspace\devin-bundle\agents\qa-ci.md`
- **Readable refs**: `.devin/vision.md`, `.devin/adr/005-agent-docs-language.md`,
  `data/bundle-models.json`, `.devin/agents/repo-reviewer.md`
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/research/agent-docs-audit.md` sha256:62e69163dd053bfd41508554434c4a0f7159c0876017f491b0bed37465cde74f
  - `.devin/vision.md` sha256:ee8e681d15264ae4c6b8b2fac73a4bdc79eb8cc3fa54386ac48258baea332479
- **Output**: edits to the files below + handoff doc at
  `.devin/handoffs/03-implementer-docs-accuracy-out.md`
- **Files you may modify (exclusive)**:
  - `.devin/docs/TOOLS-MAP.md` - DOC-001: hooks/validators sections must
    describe reality (PreToolUse wires `^exec$`->pre-exec-guard and
    `^(write|edit|notebook_edit)$`->pre-write-guard; the guards internally
    chain destructive-gate/architecture-gate/check-ai-signature/etc;
    `validate-tool-args.py` exists but is NOT wired - say so honestly, list
    its checks as "available, not wired"). DOC-008: subagent table must list
    all 8 profiles (add qa-ci; fix "7 perfis" and the VALID_PROFILES
    caption). DOC-010: one measured AGENTS.md token figure (measure bytes/4,
    delete divergent claims). DOC-018: `afk-loop` is a mode of `execution`,
    not a skill; AGENTS.md entry count is 28 not 20. Rewrite the file in
    ENGLISH.
  - `scripts/validate-tool-args.py` - DOC-002: add `"qa-ci"` and
    `"repo-reviewer"` to VALID_PROFILES. Nothing else.
  - `.devin/CONTEXT.md` - DOC-006: `docs/plans/` row -> `.devin/plans/`;
    any other dead `docs/` pointer -> `.devin/docs/`.
  - `.devin/ARCHITECTURE_MANIFEST.md` - DOC-006: `docs/` layout row ->
    `.devin/docs/`.
  - `skills/scan/SKILL.md` - DOC-012: remove the `(or subagent_explore)`
    offer; point at `researcher` per free-tier policy.
  - `skills/mcp-governance/SKILL.md` - DOC-011: replace the personal-name
    citation with a neutral one ("Context-window management for coding
    agents" talk, no person).
  - `CHANGELOG.md` - DOC-013: mask `C:\Users\Fingertech`, `C:\Users\leand`,
    `C:/Users/leand` -> `<user-path>` and person names -> `<contributor>`.
    Keep technical meaning.
  - `AGENTS.md` - DOC-017: add a one-line note at the rule index that
    numbering gaps are retained for reference stability (do NOT renumber;
    "Rule 20" is cited elsewhere).
- **Tools allowed**: profile default
- **Peer consults**: none
- **Boundaries (do NOT)**:
  - touch `manifest.json`, `.devin/docs/SKILL-TIERS.md`,
    `.devin/docs/MODEL-GUIDE.md`, `.devin/docs/3D-STACK-INSTALL.md`,
    `skills/rag/` (other contracts own them)
  - wire `validate-tool-args.py` into any hooks file (decision was
    doc-realign only)
  - renumber AGENTS.md rules; translate files outside your file list;
    reformat untouched sections
  - add comments narrating the change; no AI signatures anywhere
- **Termination**: max 60 turns / 45 minutes; stop conditions: all listed
  findings fixed + VFs pass locally, or a finding's evidence proves wrong
  (report it in the handoff, do not improvise)
- **Verification (VFs)**:
  - VF1: `python -c "import re;s=open('scripts/validate-tool-args.py').read();
    print('qa-ci' in s and 'repo-reviewer' in s)"` -> True
  - VF2: TOOLS-MAP contains no `19/28` claim and no false per-tool matcher
    table; contains `qa-ci` in the subagent table; file is English
  - VF3: `grep -n "docs/plans" .devin/CONTEXT.md .devin/ARCHITECTURE_MANIFEST.md`
    -> only `.devin/plans` references remain
  - VF4: `grep -n "subagent_explore" skills/scan/SKILL.md` -> absent or
    negative-only mention
  - VF5: `grep -nE "C:\\\\Users|leand|Fingertech|Pocock" CHANGELOG.md` ->
    no matches
  - VF6: `python audit.py` -> 0 errors; `pytest -q` -> green

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
