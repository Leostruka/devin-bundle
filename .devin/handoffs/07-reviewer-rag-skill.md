# Delegation contract

## Contract

- **Contract ID**: 07-reviewer-rag-skill
- **Objective**: Two-axis review (Standards vs Spec) of the new `skills/rag/`
  deliverable. Standards = `writing-skills` + `writing-for-agents` criteria;
  Spec = the research claims it must encode (`.devin/research/rag-practices.md`)
  + contract 05 content requirements.
- **Profile**: reviewer
- **Lane**: read-only
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\skills\rag\SKILL.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\rag\reference\tier-recipes.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\rag\reference\eval-and-failures.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\rag-practices.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\writing-skills\SKILL.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\writing-skills\reference\writing-for-agents.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\handoffs\05-implementer-rag-skill.md`
    (content requirements are the spec)
- **Readable refs**: `.devin/vision.md`, `.devin/adr/004-rag-skill-tier-model.md`,
  neighbor skills for collision check: `skills/knowledge-modeling/SKILL.md`,
  `skills/memory-management/SKILL.md`, `skills/research/SKILL.md`,
  `skills/context7/SKILL.md`
- **Frozen inputs**:
  - `.devin/research/rag-practices.md` sha256:04960e75164406fc5b8aa0a3ac25989a332871c5e9bb443a6aa460ae1d60c09d
  - `skills/rag/SKILL.md` sha256:d6a765bb89cd70469a21f6c32680b07077df28af393c3c5daafca9884ffe161d
- **Output**: review report at `.devin/research/rag-skill-review.md` +
  handoff at `.devin/handoffs/07-reviewer-rag-skill-out.md`
- **Tools allowed**: profile default
- **Peer consults**: none
- **Review axes**:
  - Spec compliance: every contract-05 content requirement present; every
    factual claim in the skill traces to a C-number that exists and says
    the claimed thing (sample-check at least 10, flag mismatches)
  - Standards: frontmatter trigger quality (would an agent pick this for
    RAG work and NOT confuse it with knowledge-modeling/memory-management/
    research/context7?), ~10KB budget, progressive disclosure correctness
    (pointers resolve), telegraphic style, no vendor defaults, no em-dash,
    no AI signature
  - Trigger-collision analysis: write the exact boundary sentence -
    "invoke rag when X; invoke <neighbor> when Y"
- **Boundaries (do NOT)**: edit any file; propose out-of-scope redesigns;
  re-do the research (judge claims only against the research file)
- **Termination**: max 40 turns / 30 minutes
- **Verification (VFs)**:
  - VF1: review file exists with a VERDICT line (SHIP / FIX: <list>)
  - VF2: every FIX item cites file:line + the violated rule or C-number
  - VF3: trigger-collision boundary sentences present for >=3 neighbors

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
