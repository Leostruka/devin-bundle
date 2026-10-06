# Development case - agent-docs-rag

Selection per `methodology-selection.md`:

- **Cynefin domain:** complicated - known unknowns (which RAG practices are
  current enough to teach; which doc surfaces drifted), resolved by research
  + audit, not exploration spikes.
- **Regulation:** low - internal bundle, no compliance forcing function.
- **Size:** medium - two fronts (docs audit+fix; one new skill), ~2-4 roles.

**Selected: hybrid** - RUP-lite intake artifacts (this vision, ADRs for the
tier model, risk register via vision table), Scrum-style execution cadence
(vertical slices in G3, each qa-ci-verified). Justification: the complicated
domain needs inception rigor (research before stack claims) but the artifact
surface does not justify full RUP ceremony; the decision rule's
complicated/low-med/small-med row selects hybrid.

## Artifacts included

| Artifact | Why |
|---|---|
| `.devin/vision.md` | Scope + measurable success + convenience bar |
| `.devin/adr/NNN-*.md` | RAG tier model, skill name, docs-fix policy |
| `.devin/research/rag-*.md` | PRISMA-lite grounding for RAG claims |
| `.devin/handoffs/*` | Delegation contracts + handoff docs |
| `.devin/ledgers/agent-docs-rag.md` | Append-only state |
| `workers/<role>/` | Role charters + accumulated notes |

## Artifacts excluded

| Artifact | Why excluded |
|---|---|
| Use-case model / SRS | No novel UI/user flows; docs+skill deliverable |
| Iteration plans (formal) | Single track; slices sequenced in ledger |
| Risk register separate file | Vision risk table suffices at this size |
| Deployment pipeline changes | Bundle installs via existing installers |
