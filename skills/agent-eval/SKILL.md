---
name: agent-eval
description: Use when measuring whether a skill, rule, or tool actually improves agent output - run a fixed held-out prompt set through N configurations, have a judge subagent score the builds, and log every result (including regressions) to an append-only eval ledger. The bundle's held-out validation concept applied to agent work quality, adapted from Astryx-style nightly agent builds.
triggers: [user, model]
---

# Agent Eval

A claim that a skill "helps" is only real with numbers from runs the
agent did not pick. This skill is the protocol: fixed prompts, fixed
harness, blind-ish judging, append-only record. It extends Rule 15
(evidence standards) and `tests/held-out/` thinking to agent output
quality rather than repo checks.

## When to use

- A new/changed skill, rule block, or tool claims better agent output.
- Comparing configurations: with-skill vs without, ours vs a third-party
  skill, cheap vs strong model tier.
- Periodic regression checks on a capability (the nightly-build pattern).

## The bench

Benches live under `.devin/evals/<bench>/` (gitignored, local-only):

- `prompts.md` - a fixed set of >=5 task prompts. Written once, versioned
  by content hash in the ledger. Never tune prompts to make a config win.
- `rubric.md` - the scoring rubric the judge applies (0-100, named
  criteria, pass bar). Also fixed per bench.
- `ledger.jsonl` - append-only results, one JSON line per run.

## Run protocol

1. Freeze inputs: record sha256 of `prompts.md` and `rubric.md` in the
   ledger entry. Any change to them starts a new bench version.
2. Build each configuration: one `implementer` subagent per (prompt x
   config), each in a clean worktree or temp dir. Same tools, same time
   budget; only the evaluated variable differs.
3. Judge: dispatch a `reviewer` (never the builder, never the prompt
   author inline) with the rubric + the produced artifact + the prompt.
   The judge does not see which configuration produced which build
   (shuffle labels, strip mentions).
4. Score and log: append `{"ts", "bench", "prompt_id", "config",
   "score", "criteria": {...}, "artifact", "judge", "build_sha"}` per run.
5. Report the FULL record: mean per config, per-prompt deltas, worst
   regression. Publishing only good nights is fabrication (the Astryx
   team published a 77-score bad night for a reason).

## Stop / escalate

- Judge and builder disagree on artifact correctness -> a human reviews
  the artifact, not another retry.
- A config wins by exploiting the rubric text (literal keyword stuffing,
  copied rubric phrases) -> tighten the rubric, rerun, note it.
- Build infra fails (env, deps) -> that run is `infra_fail`, not a 0;
  log it as such.

## Verification

- Ledger lines parse as JSON and carry all required keys.
- Score claims cite the ledger path and entry range.
- "Improved" requires: same bench, same rubric, higher mean, and no
  per-prompt regression left unexplained.

## Cross-skills

- `/gates` + `/autonomous-gates` - ledger discipline and done-claims.
- `/continuous-improvement` - where eval deltas feed the refine loop.
- `/dispatching-parallel-agents` - builder/judge dispatch mechanics.
- `tests/held-out/` - the repo-side analogue; benches must not reuse
  validation prompts the agent tuned against.
