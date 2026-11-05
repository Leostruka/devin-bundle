---
name: arena
description: Use when one attempt at a non-trivial artifact would lock in the wrong shape. Spawns N parallel candidates at the same task, cross-judges, picks a base, grafts the strongest parts of the losers into it.
disable-model-invocation: true
---

# Arena

Open a todo list with one entry per phase (Frame, Fan out, Cross-judge, Pick, Graft, Verify) before launching anything.

## Phase A: Frame

Every candidate gets the same prompt, so the prompt is the contract.

1. State the artifact each candidate is producing.
2. Derive the rubric: 3-6 concrete gradeable criteria for what success looks like on *this* task. It is the picker's tool in Phase D. Candidates only see the task.
3. Pick the runners. N parallel `run_subagent` candidates (default N=3; N=2 minimum for a real contest). Under the free-model policy all seats run the same model, so differentiate them by *angle*: give each seat a distinct stance in the prompt (minimal-diff, cleanest-boundary, most-general) rather than a model name. Spawn more runners when the arena covers multiple design directions.
4. Give each candidate its own output location: a git worktree under `.worktrees/arena-<n>/` where the artifact is code, otherwise `.devin/scratch/arena-<slug>/candidate-<n>/`. Isolated outputs first, merged by the coordinator, so candidates never contend on shared state.

## Phase B: Fan out

Spawn all N subagents in one message with `is_background: true`, each with the task, the path to the shared grounding, its own output path, and instructions to produce the artifact and a short rationale naming the alternatives it considered and what it rejected.

If a candidate produces no output, proceed with N-1 and note the dropout.

## Phase C: Cross-judge

After all Phase B candidates complete, spawn one read-only `run_subagent` judge. The judge must not have authored any candidate. It sees the rubric and the candidates by path label, scores each criterion, and recommends a base with rationale. It runs in parallel with your reading in Phase D. If no judge subagent can run, skip the judge, pick the base alone in Phase D, and say so.

## Phase D: Pick a base

Read every candidate end to end before picking. Score each against the rubric criterion by criterion, not on holistic feel, and compare with the cross-judge when Phase C ran one. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API (laziness principle).

## Phase E: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand so the result stays coherent under one mental model. Do not paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape; no graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output (run the project checks). If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Do not paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, the cross-judge's verdict or that Phase C skipped the judge, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result.
