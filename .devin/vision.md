# Vision: agent-docs-rag

Track: improve everything related to agent-facing documentation, and add
RAG-creation capability to the bundle. Intake answers recorded 2026-10-05.

## FAQ

- **What ships?** A prioritized audit of agent-facing surfaces with the top
  tier fixed, plus a new `rag` skill that teaches agents to design, build,
  and evaluate retrieval-augmented generation in arbitrary projects.
- **Who is it for?** The Devin CLI agent consuming the bundle (primary), and
  the bundle maintainer keeping docs honest (secondary).
- **Why not a runtime?** The bundle distributes knowledge and process, not
  services. The skill encodes proven RAG technique; consumers pick stacks.
- **How is "better docs" proven?** Deterministic audit before/after, fresh
  subagent pressure tests (correct routing using only the docs), and a
  recorded terminal run of the real user path at the excellence gate.
- **What does "RAG" cover?** Corpus to chunking to embeddings to index to
  retrieval to generation to evaluation, including lexical/hybrid baselines
  and agentic retrieval, at guidance level (no shipped runtime).

## Vision

Agents reading this bundle get accurate, discoverable, minimal-cost
documentation, and gain a reliable path for standing up retrieval over any
project corpus: start lexical-offline, escalate to embeddings only with
evidence.

## Stakeholders

| Stakeholder | Role | Interest | Influence |
|---|---|---|---|
| Bundle maintainer | Owns repo, merges changes | Correctness, low maintenance | High |
| Devin CLI agent | Consumes skills/docs at runtime | Right doc fast, right skill triggered | High |
| Bundle installer | Installs on new machines | No new required deps, works offline | Medium |

## Jobs to be done

- When a task needs retrieval over a project corpus, I want a skill that
  walks me from lexical baseline to embedding tiers, so I build the smallest
  RAG that works.
- When I am unsure which doc or skill applies, I want index docs that route
  me in 2 reads or fewer, so I do not burn context guessing.
- When I audit my project's agent docs, I want a repeatable checklist and
  scriptable checks, so drift is caught mechanically.

## Requirements

### Functional

- FR-1: Audit report covering all agent-facing surfaces: `AGENTS.md`,
  `skills/*/SKILL.md` frontmatter+triggers, `.devin/docs/*`, `CONTEXT.md`,
  `agents/` profiles, `manifest.json` sync; findings ranked
  (severity x reach).
- FR-2: Top-tier findings fixed under contracts; every fix traceable to a
  finding ID.
- FR-3: `skills/rag/SKILL.md` conforming to `writing-skills` (frontmatter as
  discovery triggers, lean body, progressive disclosure via `reference/`).
- FR-4: `manifest.json`, `docs/SKILL-TIERS.md`, and audit wiring updated so
  the skill is discoverable and installable.
- FR-5: Subagent pressure-test evidence that a fresh agent routes to `rag`
  on RAG-shaped prompts and to `knowledge-modeling`/`memory-management` on
  near-neighbor prompts (no trigger collision).

### Non-functional

- NFR-1: Offline-first. Lexical baseline works with zero new deps; any
  embedding/vector tier is opt-in behind `requirements.txt` + consent,
  consistent with the `hyper-extract` plan's direction.
- NFR-2: Provider-neutral. No vendor lock; hosted options documented as
  tiers, not defaults.
- NFR-3: `python audit.py` 0 errors; `pytest -q` green; skill passes
  `scripts/validate-skill-format.py`.
- NFR-4: No AI signatures; English for distributed artifacts; Windows +
  POSIX paths.
- NFR-5: Token cost: SKILL.md <= ~10KB; `.devin/docs/` index docs stay within
  their stated budgets (SKILL-TIERS ~1700 tok).

## Convenience bar

| Feature | Time-to-value target | Max steps | Required config |
|---|---|---|---|
| Find right doc/skill | 2 reads or fewer | SKILL-TIERS -> target | none |
| Invoke rag skill | 1 invocation | none | none |
| First lexical index on a corpus | <=10 min reading + runnable recipe | follow reference/ | none |

## Initial risks

| Risk | Impact | Likelihood | Early signal |
|---|---|---|---|
| RAG claims without verification (fast-moving field) | Skill teaches wrong practice | Med | Claims lacking sources in research file |
| Trigger collision with knowledge-modeling/memory-management/research | Misrouting | Med | Pressure-test misroutes |
| Scope creep across 78 skills | Phase never closes | Med | Findings list >40 items without ranking |
| Dep creep (vector libs in hooks/scripts) | Install bloat, offline break | Low | requirements.txt outside extensions/ |
| pt/en drift in shared docs | Inconsistent voice | Low | Mixed-language diffs |

## Measurable success

- `audit.py` 0 errors; `pytest -q` green on the change scope.
- Audit: 100% of agent-facing surfaces inventoried; every Critical/High
  finding either fixed or recorded with reason.
- Pressure test: >=4/5 fresh subagents route correctly (rag vs neighbors).
- Excellence gate: recorded terminal session, user path "ask a RAG-shaped
  question -> agent invokes skill -> produces a tiered plan", reviewed frame
  by frame, passes the bar.

## Boundaries

- In scope: agent-facing docs inside the bundle; the `rag` skill; wiring
  (manifest, tiers, audit hooks).
- Out of scope: a runtime RAG index over the bundle itself; human-facing
  website/docs; MCP servers; any shipped vector-DB runtime; changes to
  Devin CLI itself.
