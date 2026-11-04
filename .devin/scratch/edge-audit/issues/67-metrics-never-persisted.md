# 67 -- Metrics are written to stderr and never read; no per-skill or hook telemetry exists

- **Status**: open
- **Category**: metrics
- **Severity**: P2
- **File**: scripts/context-budget.py:1-7, scripts/memory-stop.py:31-32

## Evidence

Everything the bundle "measures" is ephemeral:

- context-budget.py reports token estimates to stderr only (docstring lines
  1-7: "writes to STDERR only"); nothing is persisted, so context-cost trends
  across releases cannot be computed.
- memory-stop.py logs memory counts to stderr on SessionEnd (line 32, 58);
  no file accumulates them.
- refine-review-prompt mentions `.devin/refinements.log.jsonl` in prompt text
  (line 58) but no script ever writes it; validate-refinement-evidence.py
  reads a file that only exists if the agent hand-creates it.
- Missing entirely: per-skill invocation counts, hook failure/timeout rates,
  gate latency, drift-check frequency. For a 140+-skill bundle there is no
  data path to identify dead skills or slow hooks.

## Recommendation

Add a single append-only JSONL metric sink (e.g. `.devin/metrics.jsonl`)
written by the consolidated _hookrun wrapper with event, hook, duration, and
exit code; have context-budget and memory-stop append their numbers there.
That one change makes hook-bench, skill usage, and gate latency derivable.

## Tradeoffs

Metrics inside `.devin/` per project are dev-only artifacts; keeping the sink
gitignored avoids repo noise but loses cross-machine history.

## Verification

`grep -rn "open(.*a\b\|json.dump" scripts/context-budget.py scripts/memory-stop.py`
returns nothing; stderr is the only output channel.
