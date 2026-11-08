# MiroFish - eval note

Source reel: drclaudiomessias DfcSO5Cj3Su (reels batch-6 survey,
`.devin/research/2026-11-08-reels-batch6-survey.md`). Evaluated
2026-11-08. Issue #416.

## What it is

MiroFish (`github.com/666ghj/MiroFish`, ~84.7k stars, AGPL-3.0, created
2025-11-26): "swarm intelligence engine" - feed it seed material (news,
policy draft, report, novel) and it builds a knowledge graph (GraphRAG +
Zep), generates thousands of persona agents, runs them interacting on two
simulated social platforms (Twitter/Reddit models) via OASIS
(CAMEL-AI), then a ReportAgent writes up emergent outcomes. Shanda Group
incubation (¥30M); FastAPI + Vue app; dual-platform parallel sim.

## Trustworthiness ceiling (the eval question)

The project's own FAQ (#726) states it "must not be equated with a
scientifically calibrated classical ABM" - no calibrated polarization,
opinion drift, prediction confidence, or causal validity. Personas are
LLM-generated from seed docs; emergent "consensus" reflects the seed
corpus + model priors, not market truth. The reel's warning stands:
synthetic users are a thermometer for narrative stress-testing, not
customer evidence. Nothing in the tool measures persona fidelity vs.
real populations.

## Bundle fit

- ux-researcher / data-analyst profiles: do real-user research;
  MiroFish would be a speculative complement at best, and its outputs
  would need the same evidence discipline (claims must cite real
  sources - synthetic personas are not sources).
- Cost shape is wrong for this repo: Zep Cloud dependency, thousands of
  LLM agent-calls per run, AGPL-3.0 (viral on hosted/service use),
  self-hosted infra burden.
- No bundle surface consumes social simulation today.

## Recommendation

**Skip adoption; keep as landscape awareness.** If idea-validation need
ever materializes, the honest use is narrative stress-testing with
explicit "synthetic, uncalibrated" labeling - and even then a handful of
persona prompts beats standing up the full stack. No dependency, no
skill, no eval slot consumed.
