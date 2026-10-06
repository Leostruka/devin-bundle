# Delegation contract

## Contract

- **Contract ID**: 02-researcher-agent-docs-audit
- **Objective**: Produce `.devin/research/agent-docs-audit.md`: a complete
  inventory of agent-facing documentation surfaces in this repo plus ranked
  findings (severity x reach) with file:line evidence. This audit drives the
  docs-fix slices.
- **Profile**: researcher
- **Lane**: read-only
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\vision.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\docs\SKILL-TIERS.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\GLOBAL_BUNDLE_AUDIT.md`
  - `D:\Programing\ai_workspace\devin-bundle\manifest.json`
  - `D:\Programing\ai_workspace\devin-bundle\AGENTS.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\CONTEXT.md`
- **Readable refs**: `.devin/ARCHITECTURE_MANIFEST.md`, `.devin/docs/` (all),
  `.devin/global_rules.md`, `data/bundle-models.json`,
  `skills/writing-skills/SKILL.md`,
  `skills/writing-skills/reference/writing-for-agents.md`
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/vision.md` sha256:ee8e681d15264ae4c6b8b2fac73a4bdc79eb8cc3fa54386ac48258baea332479
  - `.devin/docs/SKILL-TIERS.md` sha256:ac210661a54f9ed03f08dec3a3907c3315cdc4979feffdccd29db16974352d81
  - `manifest.json` sha256:52fc1ca5e57ffc9f9cde9cace5e223fb288e8dd80a41dd3763719b3caab43e88
  - `AGENTS.md` sha256:c557bf572207abc9c3dabaeecf2c5d6308f3d9b15e793778dab8c50b3f0e2370
  - `.devin/CONTEXT.md` sha256:1d3d0e59782d22ea96f25fa80026eb4e99b3e251cb905453770f7f768a7fafc3
- **Output**: report at `.devin/research/agent-docs-audit.md` + handoff doc
  at `.devin/handoffs/02-researcher-agent-docs-audit-out.md` (template:
  `skills/project-orchestrator/templates/handoff-doc.md`)
- **Tools allowed**: profile default (read, grep, glob)
- **Peer consults**: none
- **Boundaries (do NOT)**:
  - write outside `.devin/research/agent-docs-audit.md` and the handoff path
  - modify any audited file
  - propose fixes beyond a one-line fix class per finding (implementation
    is a later contract)
  - re-report GLOBAL_BUNDLE_AUDIT findings without checking current state:
    mark each as still-open / fixed / stale
- **Termination**: max 80 turns / 60 minutes; stop when all surfaces are
  inventoried
- **Verification (VFs)**:
  - VF1: `.devin/research/agent-docs-audit.md` exists; states surface count
    and % covered
  - VF2: findings table has unique IDs (DOC-001...), severity, reach,
    `file:line` evidence for every row
  - VF3: ranked output (Critical first) with a recommended fix order
  - VF4: SKILL-TIERS cross-check: every skill named there verified against
    `skills/` on disk; mismatches listed as findings
  - VF5: manifest.json cross-check: skill dirs on disk vs manifest entries,
    drift listed
- **Surfaces to inventory** (all, no sampling): root `AGENTS.md`,
  `README.md` (agent-facing parts only), every `skills/*/SKILL.md`
  frontmatter (`name`, `description` trigger quality, size, stale model
  pins or dead pointers), `docs/` top-level if present, `.devin/docs/*`,
  `.devin/CONTEXT.md`, `.devin/global_rules.md`, `agents/*.md` and
  `.devin/agents/*.md` (model pins vs `data/bundle-models.json`),
  `manifest.json` sync, hooks/configs that point at docs (`hooks.v1.json`,
  `config.json` doc references).

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
