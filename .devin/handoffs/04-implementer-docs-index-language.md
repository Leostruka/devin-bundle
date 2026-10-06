# Delegation contract

## Contract

- **Contract ID**: 04-implementer-docs-index-language
- **Objective**: Complete + normalize the agent-docs index and language:
  DOC-003 (SKILL-TIERS covers all top-level skills), DOC-004 (pt-BR -> EN on
  installed `.devin/docs/`), DOC-007 (genericize 3D-STACK-INSTALL),
  DOC-015 (missing `triggers:` frontmatter). All output in ENGLISH per
  ADR-005.
- **Profile**: implementer
- **Lane**: direct on main worktree (files below are exclusive to this
  contract)
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\agent-docs-audit.md`
    (DOC-003/004/007/015; the 14 missing skills are listed at DOC-003)
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\SKILL-TIERS.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\MODEL-GUIDE.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\3D-STACK-INSTALL.md`
  - `D:\Programing\ai_workspace\devin-bundle\data\bundle-models.json`
    (canonical model placeholders the docs must use)
- **Readable refs**: `.devin/vision.md`, `.devin/adr/005-agent-docs-language.md`,
  `skills/writing-skills/SKILL.md`, `skills/writing-skills/reference/writing-for-agents.md`
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/research/agent-docs-audit.md` sha256:62e69163dd053bfd41508554434c4a0f7159c0876017f491b0bed37465cde74f
  - `.devin/docs/TOOLS-MAP.md` sha256:cdca54ef7c2e8855c521747f2fd335d31aea1de6a96091ec16fc5161d45f3443
    (owned by contract 03 - do not touch)
- **Output**: edits to the files below + handoff doc at
  `.devin/handoffs/04-implementer-docs-index-language-out.md`
- **Files you may modify (exclusive)**:
  - `.devin/docs/SKILL-TIERS.md` - rewrite in ENGLISH; every top-level
    `skills/<dir>` on disk gets a row in the right domain (the 14 missing:
    ai3d-gen, architecture-diagrams, creative-engineering, fact-check,
    humanizer, implement-laya, media-tools, mesh-utils, operate-blender,
    operate-godot, prompt-compiler, project-orchestrator, scrape-tools,
    social-midia with nested children noted); fill `scan` tok value by
    measuring its SKILL.md bytes/4; keep the file ~1700 tok index purpose
    (rows stay terse; no new prose sections); keep `{{BUNDLE_*}}`
    placeholders and model table as-is semantically.
  - `.devin/docs/MODEL-GUIDE.md` - translate to ENGLISH; content unchanged
    otherwise.
  - `.devin/docs/3D-STACK-INSTALL.md` - translate to ENGLISH AND genericize:
    remove machine-specific paths (`C:\Program Files\Blender...`, `~/ComfyUI`
    concrete installs) into generic install instructions + a
    "this machine" note stripped of user paths.
  - `skills/self-improvement/modes/improvement-loop.md:165` - translate the
    stray pt line to EN.
  - `skills/{ai3d-gen,mesh-utils,operate-blender,operate-godot}/SKILL.md` -
    DOC-015: add `triggers: [user, model]` to frontmatter, matching the
    convention used by other skills.
- **Tools allowed**: profile default
- **Peer consults**: none
- **Boundaries (do NOT)**:
  - touch TOOLS-MAP.md, manifest.json, CHANGELOG.md, AGENTS.md,
    `skills/scan/`, `skills/mcp-governance/` (contract 03 owns)
  - add a `rag` skill row to SKILL-TIERS (skill does not exist yet;
    contract 07 wires it)
  - change SKILL-TIERS structure/headers; translate `.devin/` files not
    listed (plans/ledgers/notes stay in author's language)
  - invent tok numbers; measure each new row's bytes/4
- **Termination**: max 60 turns / 45 minutes; stop: all files done + VFs
  pass, or evidence contradicts a finding (report, don't improvise)
- **Verification (VFs)**:
  - VF1: every dir in `skills/` (top-level, excluding `_` paths) appears in
    SKILL-TIERS - `python` script comparing `os.listdir('skills')` vs file
    content -> zero missing
  - VF2: SKILL-TIERS, MODEL-GUIDE, 3D-STACK-INSTALL contain no pt-BR
    function words in headings/prose (spot grep for `quando|para|com |uso`
    patterns yields no prose hits)
  - VF3: 3D-STACK-INSTALL contains no `C:\Users`, `C:\Program Files`, or
    `~/ComfyUI` literal machine paths
  - VF4: the 4 named skills have `triggers:` in frontmatter
  - VF5: `python audit.py` -> 0 errors

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
