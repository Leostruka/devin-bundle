# Knowledge Base: AI Orchestrators (ssp.sh extraction)

Extracted: 2026-10-24 · Method: structured-knowledge-extraction logic (entity +
relation + provenance) · Primary: https://www.ssp.sh/brain/ai-orchestrators/
Substrate (linked notes where the actual patterns live):
- https://www.ssp.sh/brain/data-orchestrators/
- https://www.ssp.sh/brain/are-we-reinventing-the-tools-of-data-engineering-for-ai/

Status of source: "growing note", ~384 words on the target page; the dense
material sits in the linked data-orchestration notes. Extractions below carry
provenance per claim.

## P1: AI orchestration IS data-orchestration work

> "the nature of scheduling, logging the errors, restartability, etc., is all
> the same" (ai-orchestrators, quoting the reinventing-tools note)

Relation: agent orchestration ~is~ job scheduling + dependency modeling +
execution history. Implication for the agency pipeline: do not invent a new
runtime; apply the mature discipline (Dagster/Prefect vocabulary) to our
file-handoff chain.

## P2: Task-centric vs Asset-centric (the core axis)

> "While traditional orchestrators are task-centric, newer ones like Dagster
> emphasize Data Assets and Software-Defined Assets" (data-orchestrators)

- Control-flow (task) model: run step N+1 because step N finished. The
  orchestrator knows nothing about what steps produce. Our current linear
  `cat << 'EOF'` chain is this.
- Asset (state) model: the unit of scheduling is a named, versioned asset
  (`docs/NN_*.md`). The agent is the materialization function; edges are data
  dependencies; the orchestrator re-materializes only assets whose upstream
  inputs changed.
- "Business people don't care about pipelines; they care about data assets":
  stakeholders consume artifacts, not process. Our specs are the assets.

## P3: Orchestrator's three duties + three strengths

Duties (data-orchestrators, verbatim list):
1. Trigger computations at the appropriate moments
2. Model dependencies between computations
3. Track execution history of computations  -> our lineage/upstream_hashes

Excels at:
- Timing of events
- Identifying and addressing errors
- Restoring correct states  -> our checkpointing/rework protocol

## P4: Declarative orchestration

> "we can configure and specify what we want to orchestrate, and isolate the
> how (technical implementation)... version it, rollback in case of error,
> test and automate and apply Software Engineering Best Practices to data
> pipelines" (data-orchestrators)

The WHAT (asset graph, gates, status) must be declarative config; the HOW
(gemma persona internals) stays encapsulated. Enables versioning the pipeline
itself and rollback.

## P5: Data-aware orchestration

> "knows more about the data it runs... can pass around data to the next task,
> without treating it like we know nothing about it" (data-orchestrators)

Handoffs must carry typed, hashed references (file@sha8), not blind text.
Stale-input detection is a data-aware feature, not an agent chore.

## P6: Do not build a parallel stack

> "enhance rather than duplicate existing infrastructure... leverage existing
> tools like orchestration, scheduling, and processing frameworks" (reinventing)

Reuse `.devin/rts/` world state, `prompt_compiler.py`, `laya_cli.py`, git;
the agency DAG is a spec + thin controller, not a new runtime.

## P7: Observability and ops surface are first-class

Tool landscape cited: agtop (top-style monitoring TUI), AgentFS (filesystem
for agents), tmux+git-worktrees for parallel sessions. Observability =
materialization log + per-asset status visible without reading model output.
Our equivalents: `docs/00_PIPELINE_LOG.md`, frontmatter status fields.

## P8: Directed Agentic Graphs (named trajectory)

> "Further Reads: Directed Agentic Graphs" (reinventing-tools)

The reference names the destination: cycles where the domain needs them
(feedback), DAG elsewhere.

## Mapping to the agency pipeline (synthesis, ours)

| ssp concept | Agency mechanism |
|---|---|
| Software-defined asset | `docs/NN_*.md` with frontmatter `{schema_version, upstream_hashes, status, version}` |
| Materialization | One agent run = one asset (re)write; idempotent on unchanged input hash |
| Dependency modeling | READS/upstream_hashes per prompt; controller derives edges |
| Execution history | `docs/00_PIPELINE_LOG.md` append-only + rework_cycle counters |
| Restoring correct states | bounded loop 04->02 via `04_BLOCKERS.md`; escalate at cap |
| Cheap scheduler | transition gates via `laya_cli predict` (router/guard presets), stdlib checks |
| Error handling | typed markers: `[BLOCKED:*]`, `[INGEST-FAILED]`, `[SEMBLE-DOWN]` |
| Observability | frontmatter status + log table readable by humans/Goose without model calls |
| HITL | 2-cycle cap -> operator escalation; gate failures stop the line |

## Open references not fetched (kept as pointers)

- Dagster Software-Defined Assets docs (asset materialization semantics)
- "LLM Apps Are Mostly Data Pipelines" (Meltano blog, linked)
- Trigger.dev / Claude Code Agent Teams / Gastown / Superset.sh / Omnigent
  (implementation references for parallel-agent orchestration)
