---
name: self-improvement
description: Use when starting a self-improvement session (deep research + validated improvement loop), when capturing recurring failure patterns or reusable tactics as skills/rules/hooks, when researching agent harness design patterns (PrimeAgent/RLM vs Devin CLI), when emulating A2A messaging between subagents, or when deciding whether to dispatch a subagent, which profile, and what budget.
triggers: [user, model]
---

# Self-Improvement & Harness Patterns

Five modes; full detail in `modes/<mode>.md` — read it when you enter.

| If the task is about… | Mode | Detail |
|---|---|---|
| A self-improvement session (deep research + 10-step validated loop) | **Improvement Loop** | `modes/improvement-loop.md` |
| Capturing failure patterns/tactics as skills/rules/hooks (`/refine`) | **Refine** | `modes/refine.md` |
| Comparing Devin CLI to PrimeAgent/RLM, harness design patterns | **Harness Reference** | `modes/harness-reference.md` |
| Subagents communicating across time (A2A mailboxes) | **A2A Messaging** | `modes/a2a-messaging.md` |
| Whether/which subagent to dispatch + budget | **Subagent Router** | `modes/subagent-router.md` |

## Default stance — reference, not default workflow

Opt-in material for the niches where it earns its cost. For the common case,
a single capable agent with tests, review, and project memory beats
orchestration. Evidence:

- **Multi-agent coordination multiplies failure modes** — a 10-step chain at
  90%/step succeeds ~35% (0.9^10). Cognition, "Don't Build Multi-Agents".
- **Multi-agent burns tokens** — ~15x vs chat; token usage explains 80% of
  performance variance; few coding tasks are truly parallelizable
  (Anthropic multi-agent research, 2025-06).
- **Production agents are simple loops** — MAP study (arXiv:2512.04123).

## Non-negotiable guardrails (all modes)

- **Improvement = reproducible reduction of real failures**, validated by
  held-out tests — never tests the agent chose (Rule 16).
- **Every claim needs a reproducible command/path** (Rule 15); phantom
  guardrails are the known failure mode of self-improvement loops.
- **The Factorio lesson** — PrimeAgent's `/refine` found a cheating exploit
  and optimized *cheating* skills. Optimizing a metric without checking the
  strategy is reward hacking. Verify WHAT improved, not just that a number
  moved.
- **Ledger first** — `gates` ledger with `DELEGATION`, `INPUT_REGISTER`,
  `SOURCE_REGISTER`, `VFS`, `SCOPE` before researching or editing.
- **No delegation without authorization** — `DELEGATION: disabled` means no
  `run_subagent`/`read_subagent`.
