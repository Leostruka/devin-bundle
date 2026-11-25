---
name: primeagent-reference
description: Use when (1) researching agent harness design patterns, comparing Devin CLI to PrimeAgent/RLM architectures, or evaluating which PrimeAgent features could be adapted to Devin CLI; (2) emulating A2A messaging between subagents or between subagents and the parent agent across time within Devin CLI's ephemeral subagent runtime; (3) capturing recurring failure patterns or reusable tactics as skills/rules/hooks via the Continual Harness /refine self-improvement loop; or (4) deciding whether to dispatch a subagent, which profile to use, and how many concurrent agents to run (subagent dispatch profile/budget selection).
triggers: [user, model]
---

# PrimeAgent Reference (Merged Skill)

Four modes; full detail in `modes/<mode>.md`, read it when you enter.

| If the task is about… | Mode | Detail |
|---|---|---|
| Comparing Devin CLI to PrimeAgent/RLM, harness design patterns, adaptation status | **Reference Card** | `modes/reference-card.md` |
| Subagents communicating with each other or the parent across time; emulating PrimeAgent's persistent A2A messaging | **A2A Messaging** | `modes/a2a-messaging.md` |
| Capturing recurring failure patterns or tactics as skills/rules/hooks; self-improving the harness (PrimeAgent `/refine`) | **Refine (Self-improvement)** | `modes/refine.md` |
| Deciding whether to dispatch a subagent, which profile, and what budget preset | **Subagent Router** | `modes/subagent-router.md` |

## Default stance - this is reference, not a default workflow

This skill documents research and patterns. It is **opt-in reference material**,
not the bundle's default operating mode. The heavy machinery - A2A mailboxes,
the duplicated 10-step refinement loop, multi-role subagent sequences - is for
the narrow niches where it earns its cost. For the common case, a single
capable agent with tests, review, and project memory beats orchestration.
Reach for the modes here only when the task genuinely fits the niche each
mode was built for.

Evidence the bundle is aligned with (verified against primary sources):

- **Multi-agent coordination multiplies failure modes.** A 10-step chain at 90%
  per step succeeds ~35% of the time (0.9^10). Cognition's "Don't Build
  Multi-Agents" (Walden Yan, 2025-06-12) shows every action carries implicit
  decisions the other agents cannot see, so subagents diverge even with shared
  context. <https://cognition.com/blog/dont-build-multi-agents>
- **Multi-agent burns tokens for marginal coding gain.** Anthropic's
  multi-agent research post (2025-06-13) reports multi-agent uses ~15x more
  tokens than chat, that token usage alone explains 80% of performance
  variance, and that "most coding tasks involve fewer truly parallelizable
  tasks than research." <https://www.anthropic.com/engineering/multi-agent-research-system>
- **Production agents are simple loops, not constellations.** The MAP study
  (arXiv:2512.04123, ICML 2026 oral) surveyed 86 deployed systems across 26
  domains: 68% execute at most 10 steps before human intervention.
  <https://arxiv.org/abs/2512.04123>
- **Spec-as-source-of-truth does not scale.** Thoughtworks Technology Radar
  (Nov 2025) places spec-driven development in the "Assess" ring and warns
  "we may be relearning a bitter lesson - that handcrafting detailed rules for
  AI ultimately doesn't scale."
  <https://www.thoughtworks.com/radar/techniques/spec-driven-development>

The A2A mailbox pattern and the duplicated 10-step loop in the modes are kept
as reference for the cases that genuinely need them (long-running fleet
operations, genuinely parallel independent work). They are not the path of
least resistance for day-to-day coding. Use `tdd` + `code-review` +
`project-memory` first; reach for this skill when those are insufficient.
