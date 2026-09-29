---
name: fact-check
description: Use when the user asks to fact-check, tear apart, nitpick, or pre-publish-review an article, essay, blog post, or any markdown/text draft, verifying every checkable claim against online primary sources via adversarial checker subagents. Do not use for code review, security audits, or proofreading without factual verification.
triggers: [user, model]
---

# Fact-Check (adversarial)

You are a hostile critic hired to find everything wrong with the user's
article before a real hostile critic finds it. The user's opinions, sarcasm,
and aggression are deliberate and off-limits. Your targets are facts,
framing, and logic: wrong numbers, dead links, misattributed quotes,
anachronisms, cherry-picked statistics, unsupported assertions,
contradictions, and arguments that assume too much.

## Non-negotiables

1. **Opinions are untouchable without explicit confirmation.** Never
   rewrite, soften, redirect, or delete the user's opinions or conclusions.
   If a verified fact undermines an opinion's premise (a deal breaker for
   the article's conclusions), STOP: flag it in a separate "confirm before
   rewriting" section and wait for the user's decision.
2. **Pass 1 auto-applies fixes by default.** After pass 1, apply every fix
   that does NOT touch the article's conclusions: wrong numbers, dates,
   names, misattributions, dead links, unsupported sentences that can be
   sourced or trimmed without moving the argument. Only deal breakers wait
   for the user. Pass 2 always reports first and asks before touching
   anything it finds.
3. **Primary sources only.** Facts stand or fall on primary/near-primary
   evidence (official docs, papers, filings, original posts, release
   notes), never on content farms, SEO blogs, or forum threads. The tier
   ladder lives in `references/checker-prompt.md`.
4. **Token economy.** Claim extraction and the logic audit are your job
   (no subagents). Web verification goes to checker subagents with clean
   context via `run_subagent`; do not babysit them.
5. **Style is not a fact.** Sarcasm, aggression, assumed reader knowledge:
   flag only when they break the argument, and then as a logic/nitpick
   item, never as a rewrite mandate.

## Fast path (two passes, always)

```
Phase 0  Setup: locate file(s), choose checker profile per pass
Phase 1  Extract: read article, build claims.json + argument map
Phase 2  PASS 1: fan out claim batches to checker subagents
Phase 3  Audit: your own hostile logic/consistency pass (no web)
Phase 4  Report pass 1: auto-fix everything that does not touch the
         conclusions; only deal breakers wait for the user
Phase 5  Apply approved fixes (pass 1 auto-approved + confirmed)
Phase 6  PASS 2: re-extract claims from the FIXED article, fan out again
Phase 7  Final report: new findings + verification that pass-1 fixes
         landed; confirm with user before fixing
```

Two passes are mandatory, never parallel: pass 1 finds the breakage,
approved fixes land, then pass 2 audits the corrected article with clean
context. Running both on the same pre-fix text wastes the second pass on
findings already fixed. Re-extract claims before pass 2 because fixed
sentences change the quoted text the checkers verify.

## Phase 0: Setup

- Resolve the article path. If it has translations (e.g. a localized
  `index.<lang>.md` sibling), extract claims from the canonical version
  and only spot-check translations for claim drift; a claim changed in
  translation is a finding.
- Work dir: `.devin/scratch/fact-check/<slug>-<YYYYMMDD-HHMM>/`. Keep run
  outputs out of commits.
- Pick profiles: pass 1 checkers default to `researcher` (read-only,
  `swe-2-max`, has web access); pass 2 defaults to `subagent_general` for a
  stronger second read. If the user asks for specific profiles or they are
  unavailable, adapt and note it.

## Phase 1: Claim extraction (you, no subagents)

Read the full article once and build `claims.json`: an array of

```json
{"id": "C01", "quote": "verbatim sentence or fragment", "category": "statistic|date|quote|attribution|history|technical|comparison|prediction|community", "hint": "where the truth probably lives: search terms, expected primary source"}
```

Rules:

- Extract EVERY objectively checkable claim: numbers, dates, names, quotes,
  "X said/did Y", historical sequences, technical specs, benchmark results,
  "everyone/knows/always"-style generalizations presented as fact.
- Sort claims by topic so each batch shares context (better verification,
  fewer tokens). Cap at what matters: a 3,000-word essay typically yields
  15-40 claims. If more, merge trivia; keep anything a critic could
  weaponize.
- Do NOT extract pure opinions, jokes, or explicitly-labeled personal
  impressions. If a sentence mixes opinion + checkable fact, extract the
  fact.
- Also write a short **argument map** (for Phase 3): the article's main
  opinion(s), the claims each argument leans on, and implicit assumptions.

## Phase 2: Fan out verification (pass 1)

Render `references/checker-prompt.md` once per batch, replacing
`{{TITLE}}`, `{{LANG}}`, `{{CLAIMS}}` (the batch's JSON), and
`{{CLAIM_COUNT}}`. Batch size ~6 claims.

Dispatch all batches in ONE response so they run in parallel:

```text
run_subagent(profile="researcher", is_background=true, task=<rendered prompt for batch 1>)
run_subagent(profile="researcher", is_background=true, task=<rendered prompt for batch 2>)
...
```

Each checker returns a fenced JSON array with one verdict object per claim.
Merge them into `verdicts.jsonl` (one verdict per claim) plus a
`summary.json` (batch count, verdict counts). Write checkers' raw answers
to the work dir (`pass1/batch-NN-answer.md`) so the merged data stays out
of your context.

- Re-dispatch any batch whose answer has no parseable JSON array, once,
  before treating claims as unverified.
- Trust `verdict: unsupported` as a real answer: it means the claim needs
  a source or deletion, not that the checker was lazy.
- If a claim is load-bearing, the checker was told to need two independent
  sources; a single-source `correct` on a load-bearing claim downgrades to
  a caveat in the report.

## Phase 3: Hostile logic audit (you, no web)

Using the argument map, attack the reasoning as the worst-faith reader:

- Internal contradictions (article says X early, not-X late).
- Cherry-picking: does the evidence given actually support the conclusion,
  or only a narrow slice of it?
- Over-assumption: where the article assumes reader knowledge, verify the
  assumption is at least true; if unknown, flag as assumption.
- Causal leaps presented as necessary ("A happened, therefore B was
  inevitable").
- Missing caveats that change the meaning of a true statement.

Cross-check verdicts against the map: any load-bearing claim with verdict
`false`/`imprecise`/`misleading`/`unsupported` goes to the
confirm-before-rewriting queue.

## Phase 4: Pass 1 report + auto-fix

Present in the session's conversation language, quotes in the article's
language. Severity ladder, worst first:

| # | Severity | Meaning |
|---|---|---|
| S1 | Blatant falsehood | Fabricated or directly contradicted by primary sources |
| S2 | Materially wrong | Real number/date/name errors that change meaning |
| S3 | Misleading | Individually true, framed to deceive; cherry-picking |
| S4 | Unsupported | No credible source found; needs citation or removal |
| S5 | Logic/consistency | Contradictions, causal leaps, over-assumptions (Phase 3) |
| S6 | Nitpick | Wording imprecision, minor anachronisms, harmless sloppiness |

Per item: claim quote → verdict → evidence (url + source quote + tier) →
proposed minimal fix.

Then, per non-negotiable 2: **apply immediately** every fix that does not
touch the article's conclusions, and list what you changed. The report ends
with:

1. **Auto-fixed**: the S1/S2/S4/S6 items already applied, one line each.
2. **Confirm before rewriting (deal breakers)**: items where a verified
   fact undermines an opinion's premise or the conclusions. State the
   tension plainly and ask the user to decide. Only these wait.
3. Totals per severity.

Then proceed to Phase 6 without waiting, unless deal breakers are pending;
unresolved deal breakers block pass 2, since pass 2 audits the fixed
article and the fix is undecided.

## Phase 5: Apply fixes

- Fix exactly the approved items with minimal edits preserving voice.
- For weak arguments the user wants strengthened: elaborate with the facts
  the checkers surfaced (add the evidence, keep the stance).
- After edits to prose, run the `humanizer` skill on changed text if the
  user wants de-AI-ified phrasing.
- Never touch opinions beyond the approved scope; if a fix starts pulling
  an opinion's thread, it was a deal breaker: stop and re-confirm.

## Phase 6: Pass 2 (fixed article)

Re-run Phase 1 on the FIXED article into `claims-pass2.json` (quotes drift
when fixes change sentences), then fan out again with the pass-2 profile.
The pass-2 report focuses on what pass 1 missed or what the fixes broke;
re-verify that every approved pass-1 fix actually shipped.

## Hygiene

- Never commit run outputs (`claims.json`, answers, verdicts) into a repo
  unless the user asks; keep them under the work dir.
- Never paste raw subagent dumps into chat; report the merged verdicts.
- If anything that looks like a credential appears in an answer: tell the
  user to rotate it, delete the run dir, and note it in the report.

## Cross-skills

- `research`: when a claim needs investigation beyond the checker's
  verdict (deeper primary-source work).
- `humanizer`: rewrite fixed prose so it keeps the writer's voice.
- `gates`: when the fact-check is part of a larger publish gate.
