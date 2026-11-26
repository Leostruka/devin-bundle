# Media OSINT -> devin-bundle refinement report

Date: 2026-11-26
Input: 2 YouTube URLs in `links.txt`
Evidence base: `cards/`, `frames/`, `captions.md`, `metadata_digest.md`, `external/`, `verify.md`

## Executive synthesis

These two videos are about the same underlying problem from opposite sides:

- **Onlook** reduces design ambiguity by putting the real running product on a spatial canvas, generating variants side by side, and keeping code as the source of truth.
- **Theo/T3** reduces quality ambiguity by turning vague taste into repeated scored feedback, then turning repeated agent mistakes into explicit behavioral evals.

For `devin-bundle`, the strongest lesson is not "copy these products." It is:

> Vague creative and agent-behavior goals become tractable when converted into artifacts, comparisons, cases, baselines, controls, and costed loops.

The bundle already contains important pieces: `prototype`, `frontend-design`, `impeccable`, `arena`, `agent-eval`, `mcp-governance`, `continuous-improvement`, and strict held-out evidence rules. The videos validate those choices. The remaining opportunity is to connect them into sharper protocols.

## Evidence quality summary

| Source | Verdict | Reason |
|---|---|---|
| Onlook video | Strong product-pattern evidence | Repo and README verify the core claims; demo shows real workflows. Analytics caveat is absent from the video. |
| Theo UI hill-climb | Strong process evidence, weak scoring evidence | The workflow and eval PR are real; LLM taste scores are non-deterministic and vulnerable to target leakage. |
| T3 MCP eval | Strong methodological evidence | Merged PR and eval README show source-imported prompts/schemas, real failure cases, controls, baselines, repeated samples, and cost rules. |
| Magic Patterns/MagicOS | Adjacent sponsor evidence | Official docs confirm persistent spatial canvas, variants, repo/screenshot import, and handoff to coding agents. It is sponsor content in the video. |

## Prioritized refinement backlog

### P0 - Add a behavior-eval pattern for MCP tools and agent instructions

**Evidence:** `cards/xq0eB8vxeqk.md`; `external/t3code_evals_README.md`; PR #24635 search evidence.
**Current overlap:** `agent-eval` measures agent output quality; `mcp-governance` audits token cost; `mcp-pin` detects description drift. None fully covers behavioral regression testing of tool use.

Refine the bundle with a reusable `agent-behavior-eval` pattern:

1. Mine real failures from agent histories, reviews, incidents, and support threads.
2. Convert each failure into a small fake case before fixing it.
3. Include controls where ordinary correct behavior must remain unchanged.
4. Import prompts, tool descriptions, and schemas from source. Never copy them into the eval.
5. Run repeated samples because model behavior varies.
6. Compare against a baseline on the same model, not absolute intuition.
7. Keep user data out of fixtures.
8. Unit-test deterministic graders in CI; do not call paid models in CI.
9. Record cost, model, sample count, pass rate, and baseline diff in an append-only ledger.
10. Use compression loops only after correctness is pinned: first perfect behavior, then reduce context while preserving the eval.

Why first: this is directly aligned with lean context, MCP governance, and Rule 15. It produces objective evidence rather than taste claims.

### P0 - Treat LLM taste scores as noisy judges, never ship gates

**Evidence:** transcript lines 482-488 and 804-816; `cards/xq0eB8vxeqk.md`.
Theo shows both the power and the failure mode: repeated model scoring can climb a design hill, but identical screenshots receive different scores and judges may be influenced by knowing the target.

Bundle refinement:

- Keep human approval as the ship gate, already present in `impeccable`.
- Hide numeric targets and desired outcome from judge subagents.
- Give judges a stable evidence packet: current screenshot, previous screenshot, reference screenshots, competitor screenshots, rubric, and explicit dimensions.
- Score by category, not one holistic number.
- Repeat judge passes or use multiple independent judges only when the surface is high-stakes.
- Record disagreement and score variance, not just averages.
- Pair subjective scoring with hard gates: `design_lint.py`, a11y, contrast, reduced motion, state coverage, tests/build.

This strengthens `impeccable` without legitimizing score-chasing as truth.

### P1 - Add a council protocol as an optional high-stakes review mode

**Evidence:** `external/tstack_council_SKILL.md`; contact sheets `xq0eB8vxeqk_06.jpg`, `_10.jpg`, `_14.jpg`.
**Current overlap:** `arena` already uses multiple candidates and a cross-judge. `code-review` uses independent reviewers. The missing piece is a multi-provider review council with rounds and explicit score history.

Portable council rules worth importing:

- delegates are read-only during review;
- one strong model per provider when available;
- start delegates in parallel;
- do not wait idle: verify returned findings while others run;
- do not edit the same checkout while a delegate reviews it;
- non-blocking delegates are explicitly marked and never counted as blocking scores;
- each full pass is a round;
- PR description carries a round-by-round table;
- `no score` is written when missing, never invented;
- repeated review must not cause scope creep.

Cost refinement beyond tstack: use cheap/local reviewers first, then invoke the full council only near the acceptance threshold or for high-risk changes. Theo's roughly $400 / 956.1M-token run is evidence of both possibility and danger, not a default operating mode.

### P1 - Upgrade UI hill-climbing with comparative evidence packets

**Evidence:** `cards/xq0eB8vxeqk.md`; `skills/impeccable/SKILL.md` lines 102-117 already contain a reference bar.
The bundle already has the seed of this method. Sharpen it:

1. Require 3 visual references for high-stakes surfaces when available: prior version, best competitor, chosen design reference.
2. Capture before/after screenshots under the same viewport, data, theme, and navigation state.
3. Generate annotated delta images or structured change notes so reviewers can see what changed.
4. Store score rounds in `.devin/ledgers/design-<surface>.md` with category, judge, evidence hash, cost, and verdict.
5. Stop at budget, plateau, human approval, or hard-gate failure. Never loop only because a score can still rise.
6. Prefer objective measurable hills when available: contrast ratio, layout shift, overflow count, focus visibility, render performance, interaction latency.

### P1 - Import Onlook's artifact and variation-matrix ideas into `prototype`

**Evidence:** `cards/BogcYWf4siM.md`; `external/onlook_README.md`.
**Current overlap:** `prototype` already creates multiple UI variations and treats prototypes as throwaway learning artifacts.

Useful additions:

- produce a variant matrix/contact sheet as a first-class artifact;
- give each variant a stable name, question, verdict, and rejection reason;
- preserve rejected directions in a decision ledger rather than losing them in chat;
- allow reusable self-contained HTML/CSS artifacts when a validated fragment should be referenced across prototypes;
- run prototypes in isolated worktrees by default when real repo mutation is needed;
- export lightweight HTML/PNG evidence for review.

Do not copy the Onlook product or canvas. The bundle only needs the artifact contracts.

### P2 - Persistent spatial context without a GUI

**Evidence:** Onlook canvas; MagicOS official docs/search evidence.
Both products show why linear chat loses design context: variants, references, rejected directions, and final decisions disappear upward.

Bundle-compatible equivalent:

```
.devin/design/<surface>/
  brief.md
  references/
  variants/<name>/
  matrix.html or matrix.png
  decisions.md
  approved/
```

This preserves spatial reasoning in files. It fits the bundle better than building or depending on a visual canvas product.

### P2 - Adopt Onlook's local-first caveats as contact-surface standards

Onlook's strong product constraints are useful examples for agent tooling:

- real repo, not mockup;
- local dev server as source of truth;
- safe worktree copy;
- normal git diff/PR output;
- clear export formats;
- explicit telemetry/opt-out disclosure.

For bundle tools, the transferable standard is: local-first defaults, no hidden mutation, normal reviewable artifacts, and explicit data-collection disclosure.

## Rejected or constrained patterns

- **Do not optimize to LLM score alone.** The video itself demonstrates target leakage and non-determinism.
- **Do not make $400 design loops normal.** Use budget caps, cheap-first escalation, and plateau detection.
- **Do not copy prompts/schemas into evals.** T3's rule to import from source is the correct invariant.
- **Do not add GUI/canvas infrastructure to the bundle.** Extract file-based artifact contracts instead.
- **Do not treat sponsor claims about MagicOS as independent validation.** Use only the documented workflow pattern.

## Suggested next actions

1. Draft a new `agent-behavior-eval` skill or extend `agent-eval` with MCP/tool-use behavior cases.
2. Patch `impeccable` reference-bar guidance with target hiding, comparative evidence packets, variance logging, and budgeted escalation.
3. Add a compact `council` review mode or adapt `arena`/reviewer dispatch with the verified council rules.
4. Extend `prototype` outputs with variant matrix + decision ledger conventions.
5. Validate all changes with held-out tests; subjective improvements remain `INCONCLUSIVE` unless objective or human-approved evidence exists.

## Reproducibility notes

- Metadata: 2/2 `info.json` files present.
- Captions: official/auto captions retrieved for both videos; some language variants hit HTTP 429, but English captions are complete enough for analysis.
- Full video files were not stored because D: had only 43 MiB initially and dropped to 13-16 MiB. Contact sheets were produced by streaming low-resolution video directly through yt-dlp/ffmpeg.
- Audio-only worst-quality files were downloaded for ASR: about 2.8 MiB and 12 MiB.
- Contact sheets generated: 6 for Onlook, 24 for Theo, 30 total.
- ASR was launched locally with `extensions/asr/transcribe.py`; caption evidence remains primary because official English captions exist.
