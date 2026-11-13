---
name: retro
description: Use when conducting a retrospective on a coding session to improve the agent's environment for future runs — navigation pointers, automated guardrails, reviewer standards, rules-file hygiene, tool economy, information access. Lightweight per-session review; deeper self-improvement loops go to continuous-improvement.
triggers: [user]
---

# Retro

Session retrospective: find improvements to the agent's **environment**
(steering files, checks, tooling, information access) that would have
made this session faster or safer. You are improving future runs, not
re-litigating the code.

## Steps

1. Invoke `writing-skills` for the doc-writing style guide.
2. Read the primary sources for the session in question (transcripts,
   ledgers, diffs, command logs). Default to the current session.
3. Hunt candidates in these categories:

- **Navigation** — was finding the right file/section slow? Would a
  navigation pointer in `AGENTS.md` or a doc index help? Use when the
  session burned turns locating information.
- **Automated checks** — could a check have caught an error made?
  Read the repo's own check surface first (lint/typecheck/test
  scripts, CI workflows, hooks): a check that exists but is unwired
  or silently broken is the finding, not a reinvention. A repo with
  no guardrail (no pre-commit hook, no CI job running its checks) is
  itself a finding.
- **Coding standards** — did review miss something a rule or check
  should catch? Classify the violation first: a **mechanical** one
  (banned API, import shape, file-location rule) gets a deterministic
  check — a custom lint rule, a hook script under `scripts/` wired
  into `hooks.v1.json`, or a CI job, whichever is cheapest. Reserve
  written standards for genuine **judgement calls** no guardrail can
  substitute for.
- **Rules-file hygiene** — steering instructions in `AGENTS.md` /
  `.devin/rules/` that should move to docs or a check; no-op
  instructions that don't change behavior. Use when the files are
  large and unwieldy (context tax, Rule 18).
- **Tool economy** — expensive or token-inefficient tool calls that a
  CLI/script/extension could collapse.
- **Information access** — information the agent needed but could not
  reach (logs to tee, read-only API access, missing docs).
4. Present candidates to the user ordered by severity, each with a
   concrete proposed change. Findings that survive triage feed
   `continuous-improvement` (held-out validation) or become issues —
   never edit steering/checks silently inside the retro itself.

## Reference

- Implementation agents carry the most context pressure (exploration,
  coding, debugging); reviewers get a diff and the least pressure, so
  standards enforcement belongs in review (`code-review`), not in the
  implementer's prompts.
- `AGENTS.md` / rules files load into every conversation — keep them
  for pointers and pinned rules only; push detail to docs and skills.
- `CODING_STANDARDS` lives in review tooling (reviewer prompts,
  lint/hook checks), not implementation context.
