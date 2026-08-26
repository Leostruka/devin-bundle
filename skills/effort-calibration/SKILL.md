---
name: effort-calibration
description: Use when choosing a reasoning effort level for an LLM coding agent, when a task seems to be over-thinking or spending too many tokens, when deciding whether to raise effort, when writing task specifications that substitute for reasoning budget, or when a simple task is being treated as a codebase audit. Covers overthinking, compute-optimal test-time scaling, prompt-induced waste, and difficulty-matched effort.
---
# Effort Calibration

Reasoning effort (thinking-token budget) is a **scarce resource to match to task difficulty**, not a dial to maximize. Overthinking spends tokens without accuracy gain; under-thinking fails hard tasks. The default is **lowest effort that still uses chain-of-thought**, raised only when verification fails or the task is genuinely hard.

## Decision framework: effort tier by task type

| Tier | When | Evidence |
|---|---|---|
| **Minimum (CoT on, no exploration)** | Default for locate-and-replace, one-line edits, known-pattern changes, mechanical refactors. Spec is clear; success is verifiable by a single test/build. | E3 matches 100% success at 85% cost cut on simple edits (arXiv:2607.13034). Overthinking: 1,953% more tokens on "2+3=?" with no accuracy gain (arXiv:2412.21187). |
| **Medium (CoT + targeted exploration)** | Tasks with ambiguity in scope, multi-file changes with clear dependencies, bugs needing reproduction. Spec is good but not exhaustive. | Compute-optimal allocates per-prompt by difficulty, 4× more efficient than uniform best-of-N (arXiv:2408.03314). |
| **High (deep reasoning + broad exploration)** | Architecture decisions, novel debugging (unfamiliar domain), multi-constraint refactors, tasks that failed at lower effort. | Effort High→xHigh lifted first-try perfect runs 28%→89% on a hard real-time app (arXiv:2607.02436). Use when verification fails at lower tiers. |

**Rule of thumb:** start at minimum, raise one tier only when (a) verification fails, or (b) the task matches the High-tier description. Never start at High for a task you haven't tried at Minimum.

## When to use this skill

- Choosing a reasoning effort level for a coding agent task.
- Agent is spending many tokens on a task that seems simple.
- Deciding whether to raise effort or improve the task specification.
- Writing task specs that reduce the reasoning budget needed.
- Agent is generating multiple solution branches when only one is the deliverable.
- Agent is re-verifying repeatedly without new information.

## When NOT to use

- Within-session context window management — use `context-window-hygiene` instead.
- Deciding whether to use cross-session memory — use `memory-hygiene`.
- Choosing a model — this skill assumes the model is fixed; only effort varies.

## Rules

1. **Improve the spec before raising effort.** Information quality substitutes for reasoning budget. A clearer spec at Minimum effort beats a vague spec at High effort (arXiv:2608.01347: bounded-efficiency instruction preserves diagnosis+validation while avoiding waste).
2. **Start minimal, expand on failure.** E3 (Estimate, Execute, Expand): estimate the task's needs, execute the minimum viable path, expand scope only when verification fails (arXiv:2607.13034). This is the academic form of "start low, crank up."
3. **Never request "multiple approaches" when only one is the deliverable.** Asking the agent to develop and compare approaches multiplies reasoning 2.4-7.4× without improving success — it produces ~3 elaborated-but-discarded branches and exactly 1 implemented approach (arXiv:2608.01347).
4. **Replace certainty language with an executable stop rule.** "Make sure it's correct" / "be thorough" creates verification loops costing up to 18× the clean-run median with no success gradient (arXiv:2608.01347). Instead: "run `npm test` and stop when green" — a verifiable condition, not an open-ended injunction.
5. **Raise effort when verification fails OR the task is genuinely hard.** Effort helps on hard tasks: High→xHigh lifted perfect runs 28%→89% and cut corrective prompts ~5× (arXiv:2607.02436). The signal to raise is a failed verification at the current tier, not a feeling.
6. **Compute-optimal is difficulty-dependent, not maximal.** Uniform max effort is 4× less efficient than difficulty-matched allocation (arXiv:2408.03314). The optimal budget for an easy prompt is small; for a hard prompt, large.
7. **Some chain-of-thought is always needed.** Zero reasoning is suboptimal — CoT enhances the ability to tackle intricate reasoning tasks (arXiv:2412.21187); test-time compute improves outputs on challenging prompts (arXiv:2408.03314). The goal is right-sized CoT, not no CoT.

## Anti-patterns

- **Max effort by default.** "Crank it to max, the charts say it's better." Benchmark charts use static tasks; in practice, improving the spec at lower effort beats max effort on a vague spec (arXiv:2608.01347, arXiv:2408.03314).
- **Branch tournaments.** Requesting "develop several approaches, compare trade-offs" when the deliverable is a single patch. Creates 2.4-7.4× reasoning with no success gain (arXiv:2608.01347).
- **Certainty loops.** "Be absolutely sure this is correct" with no stop rule. Produces repeated tests, extra turns, 18× cost, no success gradient (arXiv:2608.01347).
- **Maximum-context-first.** Re-reading files and dependencies already seen, turning a one-line edit into a codebase audit. E3 cuts this: 92% fewer inspected files at equal success (arXiv:2607.13034).
- **Overthinking simple problems.** o1-like models generate 13 solutions for "2+3=?" — 1,953% more tokens, no accuracy gain (arXiv:2412.21187).
- **Universal minimum.** The opposite extreme. Hard tasks need high effort (28%→89% perfect runs, arXiv:2607.02436). The prescription is difficulty-matched, not minimum-universal.
- **Raising effort to compensate for a bad spec.** A vague spec at High effort costs more and succeeds less than a clear spec at Minimum. Fix the spec first (Rule 1).

## Academic basis

- **Overthinking is a measured phenomenon.** Chen et al. 2024, "Do NOT Think That Much for 2+3=?" (arXiv:2412.21187): o1-like models spend 1,953% more tokens than conventional LLMs on "what is 2 plus 3?", generating up to 13 redundant solutions that "contribute minimally to accuracy and diversity." Streamlining reduces token output 48.6% on MATH500 while maintaining accuracy. First comprehensive study of overthinking in long-reasoning models.
- **Compute-optimal test-time scaling.** Snell et al. 2024, "Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters" (arXiv:2408.03314, ICLR 2025): the effectiveness of test-time compute "critically varies depending on the difficulty of the prompt." A compute-optimal strategy — allocating budget adaptively per prompt — improves efficiency by more than 4× over best-of-N uniform allocation. On problems where a smaller base model has non-trivial success, test-time compute outperforms a 14× larger model.
- **Prompt wording allocates agent work.** Weinberger & Hozez 2026, "Same Task, Different Work: Prompt-Induced Waste in Coding Agents" (arXiv:2608.01347): across 4,644 runs, 24 tasks, 6 models, 2 harnesses — asking for "multiple approaches" multiplies reasoning 2.4-7.4× without improving success (3 elaborated-but-discarded branches, 1 implemented approach). "Max certainty" language creates verification loops costing 18× the clean-run median, 2.5× tool calls, 3× wall-clock, with no success gradient. A "bounded-efficiency" instruction preserves diagnosis and validation while avoiding both waste mechanisms. "Prompt engineering for coding agents is not merely wording optimization: it is the design of what work the agent is asked to perform, how that work propagates through tools, and when it should stop."
- **Task-aware minimum-sufficient execution.** Yin & Feng 2026, "Do AI Agents Know When a Task Is Simple?" (arXiv:2607.13034): agents default to a "maximum-context-first" strategy, "turning a one-line edit into a small code-base audit." E3 (Estimate, Execute, Expand) formalizes minimum-sufficient execution and the Agent Cognitive Redundancy Ratio. On MSE-Bench (121 edits), E3 matches the strongest baseline's 100% success while cutting cost 85%, tokens 91%, inspected files 92%. Gains survive held-out instruction wording. A live gpt-4o harness corroborates: over-reading is "milder but real," E3 is "the leanest and fastest policy at comparable task success."
- **Effort helps on hard tasks (counterpoint).** Mehta 2026, "Reasoning effort, not tool access, buys first-try reliability in agentic code generation" (arXiv:2607.02436): 90 independent runs building the same real-time retrospective board. Raising reasoning effort from High to xHigh lifted first-try perfect runs from 28% to 89% and cut corrective prompts ~5×, for 9-29% more cost. A testing tool raised cost 42-68% without improving score. "Most first run failures came from weak reasoning, which a stronger model or more effort prevents, not from visible flaws a checking tool would catch." The lesson: match the fix to the failure — weak reasoning needs more effort, not more tools.

## Source

Distilled from "Your effort level is TOO DAMN HIGH" (Matt Pocock, YouTube). Claims verified against primary sources — the video's thesis (lower effort = better bang for buck; overthinking wastes tokens; improve the spec instead of raising effort; start low and crank up) is supported by arXiv:2412.21187, arXiv:2408.03314, arXiv:2608.01347, and arXiv:2607.13034. The universal-minimum framing is refined by arXiv:2607.02436 (effort helps on hard tasks). The correct prescription is "difficulty-matched effort, improve spec before raising budget, never start at max."
