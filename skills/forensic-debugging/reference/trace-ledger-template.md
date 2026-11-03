# Debug ledger: <slug>

Status: REPRODUCED | LOCALIZING | ISOLATED | FIX-UNVERIFIED | VERIFIED
Started: <ts>  Target: <file/func/commit>  Owner: <agent>

## Repro kernel

Command: `<exact command>`
Input: `<minimal input / file>`
Env: <seeds, clocks, flags>  Fails: <always | rate + conditions>

## Invariants (I#)

| I# | Invariant | Holds where | First violated at |
|----|-----------|-------------|-------------------|
| I1 | e.g. output count == input count | stage2 exit | - |

## Probes (P#)

| P# | Location | Asserts | Emits |
|----|----------|---------|-------|
| P1 | func_x entry | I1 | in-shape dump |

## Hypotheses + Experiments (H#/E#)

| H# | Claim | E# experiment | Predicted | Observed | Verdict |
|----|-------|---------------|-----------|----------|---------|
| H1 | off-by-one on last elem | E1: run n=1 input | crash at idx | ... | REFUTED |

## Observations (O#)

| O# | Observation | Explained by |
|----|-------------|--------------|
| O1 | stderr has stray null byte | - |

## Root cause (candidate -> proven)

Chain: <input> -> <mechanism> -> <symptom>
Falsification: predicted <X> under input <Y>, observed <Y-result>. PROVEN.

## Postmortem

Root cause: <one line>  Fix: <commit>  Regression test: <path::name>
Open anomalies: <O# list or none>
