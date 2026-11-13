# GATES: research-or-ask behavior improvement

## FASE 0 — Deep Research

- [x] F0.1: Devin CLI docs confirm rule/skill loading
  CHECK: web_search docs.devin.ai "AGENTS.md rules" "skills directory" + webfetch https://docs.devin.ai/cli/extensibility/rules
  EXPECT: at least one official source URL describing how rules/skills are loaded
  EVIDENCE: docs.devin.ai/cli/extensibility/rules confirms AGENTS.md is always-on, .devin/rules/*.md can use triggers, skills are preferred over rules for cost/ability (docs.devin.ai/cli/extensibility/skills/overview)

- [x] F0.2: Local bundle structure matches docs
  CHECK: Get-ChildItem skills/continuous-improvement/; Test-Path AGENTS.md; Test-Path .devin/ledgers
  EXPECT: SKILL.md exists; AGENTS.md exists; .devin/ledgers exists
  EVIDENCE: skills/continuous-improvement/SKILL.md exists (12508 bytes), AGENTS.md exists, .devin/ledgers directory exists

- [x] F0.3: Research exists on agent "research vs ask" behavior
  CHECK: web_search arXiv "When Should LLMs Search" + "Ask Early Ask Late Ask Right" + "Value of Information human-agent communication"
  EXPECT: at least one primary source (paper or official doc) with actionable insight
  EVIDENCE:
  - arXiv:2607.05752 (When Should LLMs Search?) — search routing: NO_SEARCH vs SEARCH vs UNSOLVED; search only when it improves task success; false-premise/underspecified questions better resolved by clarification than search.
  - arXiv:2605.07937 (Ask Early, Ask Late, Ask Right) — timing of clarification matters; 52% over-asking, some never asking; goal clarification is early, input/constraint clarification has wider windows.
  - ACL 2026 doi:10.18653/v1/2026.acl-long.1987 (Value of Information) — agents should ask when expected utility gain justifies user effort, balancing task risk, ambiguity, user cost.

- [x] F0.4: Baseline behavior documented
  CHECK: read AGENTS.md rules 3, 10, 11, 17
  EXPECT: current rules already push for skill discovery and tool verification, but no explicit "when uncertain: research first, ask second" directive
  EVIDENCE:
  - Rule 3: create skills for recurring patterns; Rule 4: invoke matching skills before touching code; Rule 10: don't execute without planning, don't declare without verifying; Rule 11: never fail from failures (search certified sources until coherent); Rule 17: don't deduce, verify with tools.
  - No explicit rule maps "uncertainty → research first → ask second". Rule 11 says "search certified sources until the answer is coherent", but does not trigger when the answer is inherently user-specific.

- [x] F0.5: History of similar changes reviewed
  CHECK: git log --oneline -20 -- AGENTS.md
  EXPECT: list of recent AGENTS.md edits with any reverts/fixes
  EVIDENCE:
  - f13a7f7 unlazy skill + continuous-improvement directive + AGENTS.md ledger rules
  - 2451629 fix: conditional paid-model policy
  - 1fba4c0 fix: critical cost bug
  - d7fd02e v2.5.1 GLM-5.2 + SWE-1.7 optimization
  - c984271 revert: everything to 3ee0a72 except obsidian-workflow
  - 545862c add Rule 20, Rule 21
  - ede5882 add Rule 19
  Pattern: rules are added incrementally; revert c984271 shows overreach can be reverted.

- [x] F0.6: Held-out test baseline captured
  CHECK: python -m pytest tests/held-out/ -q
  EXPECT: all tests passing or baseline failures recorded
  EVIDENCE: 135 passed in 6.11s; python audit.py: ALL 31 CHECKS PASSED, 0 errors, 0 warnings.

- [x] F0.7: Synthesis of improvement candidates
  CHECK: none (manual gate)
  EXPECT: prioritized list of concrete changes with evidence
  EVIDENCE:
  - Candidate 1 (highest): add a pinned or non-pinned rule in AGENTS.md that explicitly disambiguates "research first, ask second".
    Rationale: Rule 11 already says "search certified sources until answer is coherent" but does not carve out user-specific questions; Rule 4 says invoke skills before touching code but does not cover all uncertainty. A new rule closes the gap.
  - Candidate 2: create a skill `research-or-ask` invoked when the model is uncertain.
    Rationale: skills are cheaper and only loaded when needed (docs recommend skills over rules), but the user explicitly requested AGENTS.md and the behavior is meant to be always-on.
  - Candidate 3: add a hook on UserPromptSubmit to nudge the model.
    Rationale: more invasive, context-costly, and harder to validate; not chosen.

## LOOP — Improvement

- [x] P1: Reproduce a concrete failure
  CHECK: grep -i "research.*ask|ask.*research|uncertain|doubt|quando.*dúvida|não sabe" AGENTS.md
  EXPECT: no relevant rule found, confirming the gap
  EVIDENCE: grep returned "No matches found" in AGENTS.md. Also, subagent pressure tests (baseline) showed the agent can reason about research/ask, but only as an emergent interpretation of Rule 11/17; no explicit directive maps "uncertainty → research first, ask second".

- [x] P2: Critique the failure
  CHECK: none (manual gate)
  EXPECT: rule violated, current behavior, positive intention, and why it fails
  EVIDENCE:
  - Rule violated: Rule 11 (Never fail from failures) + Rule 17 (Don't deduce) are under-specified for the case "I don't know and it is user-specific". Rule 11 says search certified sources, but user-specific business rules are not in certified sources.
  - Current behavior: agent may spend reasoning tokens trying to infer an answer instead of using `web_search`/`webfetch`/skill discovery (for factual/library/domain uncertainty) or `ask_user_question` (for user-specific/business-rule/case-of-use uncertainty).
  - Positive intention: the agent wants to be helpful and fast, to avoid bothering the user, and to act on partial information. The rules file wants to stay lean.
  - Why it fails despite the intention: research (arXiv:2607.05752) shows that answering when parametric knowledge is insufficient produces plausible-but-wrong results; arXiv:2605.07937 shows that asking late or never causes irreversible trajectory errors. Lean rules are good, but a missing rule for a recurring failure mode is a gap.

- [x] P3: Generate 3+ alternatives
  CHECK: none (manual gate)
  EXPECT: table with 3 alternatives, risks, and probabilities
  EVIDENCE:
  | Alt | Description | Risk | Prob. real improvement |
  |-----|-------------|------|------------------------|
  | 1 | Add a new pinned Rule 21+ (or renumber) in AGENTS.md: "Research first, ask second" with explicit heuristics. | Adds tokens to always-on context; if too long, may dilute other rules. | High — directly addresses the gap and is always loaded. |
  | 2 | Add a `.devin/rules/research-or-ask.md` with `trigger: agent` or `always_on`. | Slightly less visible; may not be discovered as reliably as AGENTS.md; requires frontmatter. | Medium — same content, different loading path. |
  | 3 | Create a skill `research-or-ask` and add a short pointer in AGENTS.md Rule 4/11. | Skills are cheaper but only loaded when invoked; this behavior is meant to be default, not conditional. | Low — user asked for AGENTS.md and always-on behavior. |

- [x] P4: Apply best alternative
  CHECK: edit AGENTS.md to add Rule 21 pinned; update README.md and audit.py counts
  EXPECT: AGENTS.md contains Rule 21; README reflects 20 rules; audit.py checks 1-21
  EVIDENCE: Rule 21 added to AGENTS.md pinned section and rule summary; README badge/count/diagram/table updated; audit.py range(1,22) and expected 20 rules.

- [x] P5: Validate with tests
  CHECK: python -m pytest tests/held-out/ tests/validation/ -q
  EXPECT: no new failures vs baseline
  EVIDENCE: 139 passed in 7.58s (baseline was 135 held-out passed; added 4 validation tests). python audit.py: ALL 31 CHECKS PASSED, 0 errors.

- [x] P6: Future pace
  CHECK: manual — project 3 hypothetical scenarios
  EXPECT: ≥2/3 scenarios benefit
  EVIDENCE:
  - Scenario 1: user asks "integrate LuminaDB driver". With Rule 21, agent research first (web_search/webfetch) instead of reasoning. Benefit: avoids plausible-but-wrong API guesses.
  - Scenario 2: user asks "use fiscal quarters". With Rule 21, agent asks first (ask_user_question) because the definition is user-specific. Benefit: prevents wrong Q3 date range and wasted compute.
  - Scenario 3: user asks "what's the latest Python version". With Rule 21, agent web_search instead of relying on parametric knowledge. Benefit: correct, current answer.
  → 3/3 benefit.

- [x] P7: Ecological check
  CHECK: manual — check side effects on other rules/skills/context budget
  EXPECT: no negative side effects
  EVIDENCE:
  - Other rules: Rule 21 reinforces Rule 11 (search certified sources) and Rule 17 (verify with tools); no conflict. Rule 4 (skill discovery) is a subset of research.
  - Context budget: AGENTS.md ~6043 tokens (3.02% of 200K); new rule added ~120 tokens; negligible.
  - Skills: no skill description or manifest changed; no new skill.
  - Tests: all pass.
  - Side effect: audit.py and README had to be updated to count 20 rules, but this is expected bookkeeping.

- [x] P8: Simulate impact
  CHECK: run audit.py, context-budget.py, and subagent pressure tests with updated rules
  EXPECT: audit green; subagent behavior shows rule is active
  EVIDENCE:
  - python audit.py: ALL 31 CHECKS PASSED, 0 errors.
  - context-budget.py: AGENTS.md ~6043 tokens (3.02% / 200K), acceptable.
  - Subagent post-rule tests: factual-uncertainty case (LuminaDB) proposed web_search/webfetch first; user-specific case (fiscal quarters) proposed ask_user_question first. Both aligned with Rule 21.

- [x] P9: Classify result
  CHECK: manual
  EXPECT: one of MELHOROU/PIOROU/NEUTRO/INCONCLUSIVO
  EVIDENCE:
  - CLASSIFICAÇÃO: MELHOROU
  - Métrica real: AGENTS.md now has explicit Rule 21; audit passes; 139 tests pass; subagent behavior shifted from emergent reasoning to explicit research/ask fork.
  - HELD_OUT: passou (no regression vs baseline)
  - SIMULAÇÃO: audit green, context budget stable, subagent behavior aligned.
  - ARQUIVOS_ALTERADOS: AGENTS.md, README.md, audit.py, ledgers/research-or-ask.md
  - PUSH_COMMIT: não feito
