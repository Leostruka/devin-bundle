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

## Behavioral tool-use evals (MCP schemas, instructions, tool text)

A different eval type from quality benches: not "is the output good" but
"does the agent use the tool correctly in scenario X". Use it whenever a
change edits what a model sees or does: agent instructions, MCP tool
descriptions and schemas, tool result text, generated titles. A unit test
cannot catch these regressions because model output varies run to run and
a small copy change can move it. Pattern verified from T3 Code's merged
evals package (PR #24635, evidence
`.devin/research/media-osint-20261126-yt2/external/t3code_evals_README.md`).

Rules for behavioral cases:

1. **Cases come from real failures.** Mine agent histories, review
   threads, and incidents. Each case names its source (PR, issue, thread).
   A case reproduces a real bad experience or guards a real good one.
2. **Add the case before the fix.** It must fail on the old text and pass
   on the new. Prefer fixing the tool text over loosening the case.
3. **Controls are mandatory.** Cases where the correct action is ordinary
   work catch fixes that overcorrect (a fix that makes the agent use the
   tool everywhere is not a fix).
4. **Import from source, never copy.** The eval imports prompts, tool
   descriptions, and schemas from the code under test. Copied text makes
   the eval test a snapshot, not the current behavior.
5. **Repeated samples.** Model output varies; run each case several
   times. A case fails when half or more of its samples fail.
6. **Compare against a baseline on the same model**, never against an
   absolute intuition or a different model's numbers.
7. **No user data in fixtures.** Synthetic paths and accounts only; read
   every captured fixture before committing it.
8. **Graders are plain logic tested in CI.** CI unit-tests the grader and
   typechecks the harness; CI never calls paid models.
9. **Cost accounting.** Record model, sample count, and cost per run in
   the ledger. Run only the cases a change touches until they pass, then
   one full run per model before merge.
10. **Compress last.** When trimming tool descriptions for context
    savings, correctness pins first: behavior green on the full text, then
    compress, then re-run the same cases. Context reduction without the
    behavioral gate is how tools silently stop being used correctly.

## Harness: scripts/behavioral-eval.py

The deterministic core is implemented; it never calls models (CI rule 8):

- `validate <case.json>...` - schema-check cases in CI.
- `grade --case C --sample F` - grade one sampled output file.
- `record --case --model --run --idx --passed [--cost]` - append-only ledger
  `.devin/ledgers/behavioral-eval.jsonl` with cost accounting (rule 9).
- `compare --baseline R1 --candidate R2` - per-case pass rates, same-model
  enforced, exits non-zero on regression.

Cases live in `evals/cases/*.case.json`. Graders import live tool text via
`${import:name}` placeholders resolved from the case's `imports` map -
never paste tool text into a case (rule 4). A case fails when half or
more of its samples fail (rule 5).

Sampling has two paths:

- `sample --case C --run R [--model M]` - the bundled NON-CI driver: runs
  N `devin -p` sessions (the case's exact `prompt`, isolated temp
  workspaces, live hooks apply inside samples just as in real work),
  synthesizes transcript + artifact digest (`### path` markers), grades
  and records each sample automatically. Never run this in CI - it calls
  models. Parallelism is capped at 3. Known limitation: `devin -p` does
  not expose token usage in machine-readable output, so cost_tokens is
  recorded as 0 until a usage source exists; wall time and pass/fail are
  still ledgered.

  Isolation contract (hardened 2026-11-26 after adversarial review):
  `workspace_files` keys must be strictly relative - absolute paths and
  `..` are skipped, never written; sessions run
  `--process-model=in-process` so the timeout is a real wall-clock cap;
  the synthesized grading output is persisted per sample as
  `.beval-output.txt` beside the artifacts, and ledger entries carry
  workspace/timed_out/wall_sec/detail/evidence. The digest excludes
  `.devin` (hook state contains the prompt verbatim and would false-pass
  content graders) and normalizes artifact paths to forward slashes, so
  case regexes are portable across sampling hosts.

  Sample workspaces inject a minimal `.devin/ARCHITECTURE_MANIFEST.md`
  by default: without it the architecture gate blocks all file creation
  and samples measure gate friction instead of the case's behavior
  (observed split in the first baseline - most agents adapt and write
  the manifest, some stall asking a user who never answers in headless
  mode). Cases measuring gate adaptation itself set
  `inject_manifest: false`; for those, the artifact existing at all in
  the digest proves adaptation happened, since creation is impossible
  otherwise.
- External/manual: run the scenario N times through whatever model path
  is under test, save each output to a file, then grade + record. Use
  this when the system under test is not the local devin CLI.

Graders see both behavior (transcript) and outcome (workspace artifacts);
anchor artifact assertions on the `### filename` digest markers so
transcript mentions cannot false-positive a content check.

## Cross-skills

- `/gates` + `/autonomous-gates` - ledger discipline and done-claims.
- `/continuous-improvement` - where eval deltas feed the refine loop.
- `/dispatching-parallel-agents` - builder/judge dispatch mechanics.
- `tests/held-out/` - the repo-side analogue; benches must not reuse
  validation prompts the agent tuned against.
- `mcp-governance` + `mcp-pin` - the context-cost and drift-detection
  halves of MCP stewardship; this skill adds the behavioral half.
