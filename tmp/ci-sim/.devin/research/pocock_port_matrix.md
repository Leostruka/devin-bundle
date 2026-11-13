# Port matrix, mattpocock/skills -> devin-bundle (ISSUE_07)

Upstream: github.com/mattpocock/skills @ 49dd158d1076134a641b33efb035946536778336 (MIT)
Date: 2026-10-10 · Scope: skills/{engineering,productivity,misc}; in-progress/* skipped (unreleased)

## same (already ported/adapted, no action)

| upstream | ours | evidence |
|---|---|---|
| engineering/code-review | skills/code-review (+modes/giving.md) | two-axis Standards/Spec + parallel sub-agents already present |
| engineering/diagnosing-bugs | skills/debugging (+modes/ci,local) | 6-phase red->minimise->hypothesise->instrument->fix loop present |
| engineering/implement | skills/execution | implement-per-spec flow |
| engineering/implement-spec | skills/execution | spec->tickets->implement |
| engineering/prototype | skills/prototype | LOGIC/UI branches already adapted |
| engineering/research | skills/research | ours larger (PRISMA-lite + deep mode) |
| engineering/tdd | skills/testing | red-green-refactor + seams |
| engineering/to-spec | skills/planning | spec mode |
| engineering/to-tickets | skills/planning (modes/tickets.md) | tickets mode |
| engineering/triage | skills/intake | triage states + agent-ready briefs |
| engineering/wayfinder | skills/planning/modes/wayfinder.md | mode file exists |
| engineering/wizard | skills/wizard | same shape |
| engineering/codebase-design | skills/architecture | deep-modules vocabulary merged |
| engineering/improve-codebase-architecture | skills/architecture | deepening-opportunity flow merged |
| engineering/domain-modeling | skills/knowledge-modeling | glossary/bounded contexts |
| engineering/grill-with-docs | skills/grilling (With-docs mode row) | composition pointer upstream; ours names the mode |
| productivity/grill-me | skills/grilling | grill-me covered |
| productivity/grilling | skills/grilling | ours much larger (frontier rounds) |
| productivity/handoff | skills/handoff | already adapted (temp-dir, suggested skills, redaction) |
| productivity/teach | skills/teach | ours larger (workspace/ZPD/learning-records) |
| productivity/wait-what | skills/wait-what | already adapted (CONTEXT.md + context7) |
| productivity/writing-for-agents | skills/writing-skills | ours larger |
| productivity/to-questionnaire | skills/planning (questionnaire mode) | covered |

## new (ported this branch)

| upstream | ours | notes |
|---|---|---|
| engineering/pr | skills/pr (new) | Summary(visual)/Evidence(before-after)/Merge Danger(door+blast radius) |
| engineering/retro | skills/retro (new) | session retro -> env improvements; feeds continuous-improvement; hooks under scripts/+hooks.v1.json |
| misc/setup-pre-commit | skills/setup-pre-commit | was installed-only drift; copied adapted version into repo |

## skip (reason recorded)

| upstream | reason |
|---|---|
| engineering/ask-matt | matt-specific content service, no generic value |
| engineering/setup-matt-pocock-skills | his own installer |
| misc/git-guardrails-claude-code | covered: scripts/destructive-gate.py already blocks force-push/branch -D/rm -rf |
| misc/migrate-to-shoehorn | his shoehorn library, tool-locked |
| misc/scaffold-exercises | his course tooling |
| in-progress/* (7) | unreleased upstream |

## Router

`ask-bundle` gained rows: Write PR body -> `pr`; Session retrospective -> `retro`; Husky/lint-staged -> `setup-pre-commit`.
