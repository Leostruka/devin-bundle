# Model Guide

Bundle model policy, SWE-2 native. Routing is by **effort level** (Medium/High/Max), not model size. Concrete values live in `data/bundle-models.json`; the `BUNDLE_DEFAULT_MODEL`, `BUNDLE_MAX_MODEL` and `BUNDLE_MEDIUM_MODEL` environment variables can override the defaults. The validated CLI version is in `data/bundle-identity.json`.

## Effort levels (SWE-2)

In SWE-2, effort is the reasoning level built into the `model_uid`. It is not a separate config field - the chosen variant defines the effort. The UI offers `Alt+T` to switch.

| Level | model_uid | When to use | Cost |
|---|---|---|---|
| **Medium** | `swe-2-medium` | Simple tasks, spot fixes, isolated scripts, mechanical edits. Clear spec; success verifiable by a single test/build. | **Free** |
| **High** | `swe-2-high` | Tasks spanning multiple files, bounded debugging, decisions with several constraints. **General default.** | **Free** |
| **Max** | `swe-2-max` | Open-ended tasks, global refactors, long-horizon coding, costly/irreversible decisions. | **Free** |

**Rule of thumb:** start at the level matching the task shape. Step up one level when verification fails, not before. See `context-hygiene` for the empirical basis.

## Primary model (parent)

The primary model (parent) is set by `BUNDLE_DEFAULT_MODEL` (or `data/bundle-models.json.default_parent_model`). Bundle default: **`swe-2-high`** (High effort, 262K, free).

| Attribute | Value | Source |
|---|---|---|
| model_uid | `{{BUNDLE_DEFAULT_MODEL}}` | `data/bundle-models.json` / `devin models list` |
| Context window | `context_window` from the registry | `data/bundle-models.json` |
| Effort | defined by the `model_uid` suffix | this table |
| Tool use | native during inference | Devin docs |
| Cost | `cost_tier: free` for the default | `data/bundle-models.json` / `devin models list` |

### Implications for the harness

1. **Native reasoning**: SWE-2 plans and reasons without chain-of-thought
   instructions. Prompts, skills and profiles declare WHAT must be done
   and the acceptance criteria - never HOW to reason ("think step by step",
   "plan before acting" are anti-patterns).

2. **Native tool-use**: the model decides when to invoke tools during
   inference. The harness should not over-specify tool-use rules-
   Rule 17 (verify with tools) aligns naturally.

3. **Prompt caching**: keep AGENTS.md and the system prompt cache-stable. Pinned rules at the top = stable prefix = cache hit. Do not reorder pinned rules frequently.

4. **Lost-in-the-middle (arXiv:2307.03172)**: U-shaped curve confirmed.
   Critical constraints at the start (pinned rules), recent context at the
   end; avoid depending on information in the middle of the context. Constraint-pinning
   (Rule 14) is the correct defense.

5. **Budget**: fixed percentages of the `context_window` in `data/bundle-models.json`
   are consumed by AGENTS.md, SKILL-TIERS.md, invoked skills and tool defs.
   The rest remains available for work.

## Subagent models

Subagents use the same SWE-2 variants, chosen by effort level:

| Field | Description | Effort | Cost | Notes |
|---|---|---|---|---|
| `{{BUNDLE_MAX_MODEL}}` | Max subagent (`swe-2-max`) | max | **Free** | Planning/judgment/review agents |
| `{{BUNDLE_MEDIUM_MODEL}}` | Medium subagent (`swe-2-medium`) | medium | **Free** | Bounded execution agents |
| `{{BUNDLE_DEFAULT_MODEL}}` | Parent (`swe-2-high`) | high | **Free** | Orchestration, diverse reasoning |

**⚠️ CRITICAL**: non-canonical aliases may resolve to a paid model - **do not use** without checking `data/bundle-models.json`.
Agents under agents/ should pin the bundle's canonical variants (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`).

**⚠️ CRITICAL - `subagent_explore` (built-in) may be paid**: the built-in
`subagent_explore` profile runs on the CLI default router, which may charge per token.
There is no local override - only enterprise settings can change that.
**NEVER dispatch `subagent_explore`.** Use the custom `researcher` profile
(`agents/researcher.md`, pin `model: {{BUNDLE_MAX_MODEL}}`, free, see `data/bundle-models.json`),
which has the same read-only capabilities. Source: docs.devin.ai/cli/subagents.

### Self-compaction (key differentiator)

The bundle's subagents are trained to:
1. Write informative, concise summaries of work state.
2. Summarize from those summaries efficiently.

This means subagents preserve constraints better than generic models
during compaction. But Governance Decay (arXiv:2606.22528v2) shows compaction
drops constraints in ALL tested models - constraint-pinning is still needed.

The `constraint-pinning.py` hook has a `summary_retains_constraints()` heuristic that
checks whether key phrases survived. For trained subagents, the summary is more
likely to retain constraints → pinning fires less often → correct behavior
(pin only when needed).

### Implications for subagent dispatch

1. **Context window**: the subagent window is in `data/bundle-models.json` (262K). Subagents can do more work before needing compaction. Economical fan-out.
2. **Self-compaction**: subagents can run longer without context loss. Less need for `context-hygiene` in subagents.
3. **Concise by design**: SWE-2 is trained for concise output. Do not fight it with verbose rules. Rule 8 (telegraphic) aligns.
4. **Coding strength**: for coding tasks (implementation, debugging, refactoring), the parent should delegate to subagents instead of implementing inline.

### Routing matrix: parent inline vs subagent

| Task type | Best function | How to execute | Why |
|---|---|---|---|
| Code implementation | Medium subagent | `implementer` subagent | Spec'd work, bounded execution |
| Code debugging | Medium subagent | `debugger` subagent (parent plans) | Hypothesis iteration |
| Code review | Max subagent | `reviewer` subagent | Independent judgment |
| Research/exploration | Max subagent | `researcher` subagent | High context, free |
| Architecture (routine) | Max subagent | `architect` subagent | Trade-off analysis |
| Architecture (high-stakes) | Parent model | inline or `subagent_general` | Needs parent reasoning |
| Final whole-branch review | Parent model | inline or `subagent_general` | Judgment task, max capability |
| Diverse reasoning | Parent model | inline | Primary model for diverse reasoning |
| Fix-loop escalation (R4-5) | Parent model | `subagent_general` | Fresh eyes + parent reasoning |
| Coordination/orchestration | Parent model | inline (parent) | Parent role, never delegate |

### Subagent vs compaction: when to use each

Source: dreaming.press/posts/subagents-vs-compaction-isolate-context

| Answer | Mechanism | Cost | Survives reset? | When to use |
|---|---|---|---|---|
| **Subagent** | Fresh window, only final message returns | ~15x tokens, no automatic inheritance | N/A - parent never had the garbage | Separable subtask with summarizable result (research sweep, file exploration, parallel review) |
| **Compaction** | Summarizes transcript, drops verbatim | Lossy: omitted specifics gone for good | No - summary still in-window | Continuous reasoning thread that must stay coherent |
| **Context editing** | Evicts old tool results, keeps 3 | Invalidates prompt cache prefix | Partial - results re-fetchable | Live loop that needs recent tool results |

**Composition rule**: subagents keep the orchestrator lean; compaction
keeps each long-lived loop under its cap. Use subagents to keep bulk
work out of the parent window; use compaction when the work
is already in the parent and must continue coherently.

For the parent (`{{BUNDLE_DEFAULT_MODEL}}`) dispatching subagents:
- Extensive research/exploration → `researcher` (Max, free, returns only synthesis)
- Bounded implementation → `implementer` (Medium, free)
- Iterative debugging needing accumulated context → inline + compaction
- Architecture/decision needing to see everything → inline (parent, High)

## Model pin strategy in agents/

| Agent | model: pin | Effort | Rationale |
|---|---|---|---|
| researcher | `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | Read-only, free, high context |
| architect | `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | Trade-off analysis, free |
| reviewer | `{{BUNDLE_MAX_MODEL}}` (`swe-2-max`) | Max | Independent judgment, free |
| debugger | `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | Fast iteration, free |
| implementer | `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | Bounded tasks, free |
| qa-ci | `{{BUNDLE_MEDIUM_MODEL}}` (`swe-2-medium`) | Medium | Gate re-execution, free |

**Why pin and not alias?** Non-canonical aliases may resolve to a paid model.
Use the bundle's canonical variants (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`),
which are free and have the largest `context_window`. Without a pin, the router may
resolve to a paid model. When new versions ship, update the agents/
to the new models listed in `data/bundle-models.json`.

The parent (`{{BUNDLE_DEFAULT_MODEL}}`) does complex work inline. For implementation
that needs the parent, use `subagent_general` (inherits parent, **free**
when the parent is free) or pin `model: {{BUNDLE_DEFAULT_MODEL}}` on the agent.

### Built-in profiles vs custom agents (cost)

| Profile | Model | Cost | When to use |
|---|---|---|---|
| `subagent_general` | Inherits parent (`{{BUNDLE_DEFAULT_MODEL}}`) | **Free** (when parent is free) | Implementation needing the parent, isolated context |
| `subagent_explore` | CLI default router | **PAID** (possible) | **AVOID** - use custom agent `researcher` (free) instead |
| Custom agents (researcher, architect, etc.) | `{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}` (pin) | **Free** (when free in the registry) | Research, architecture, review, debug, implementation |

**⚠️ Never use `subagent_explore`** - it may resolve to a paid model.
Custom agents with the canonical pins are free and have more context.
Source: docs.devin.ai/cli/subagents.

## Paid models - CONDITIONAL policy

**Free** on the subscription are defined in `data/bundle-models.json`
with `cost_tier: free`:

- `{{BUNDLE_DEFAULT_MODEL}}` - parent (default, High)
- `{{BUNDLE_MAX_MODEL}}` - Max subagent
- `{{BUNDLE_MEDIUM_MODEL}}` - Medium subagent

**Paid**: any entries with `cost_tier: paid` in `data/bundle-models.json`,
including aliases/short names. Always check the registry before using a
non-canonical model.

### Policy CONDITIONAL on the parent model

**Case 1 - Parent FREE (`cost_tier: free`): subagents MUST be FREE.**

FREE-ONLY protocol:
1. Parent (`{{BUNDLE_DEFAULT_MODEL}}`, High) - initial attempt
2. Subagent fan-out (`{{BUNDLE_MAX_MODEL}}` Max / `{{BUNDLE_MEDIUM_MODEL}}` Medium) - parallelism
3. Parent at `max` effort (via `Alt+T` or `/model swe-2-max`) - more reasoning, same free model
4. Repeat with cleaner context (`clear` + reload only what is needed)
5. If all free options fail: **stop and report to the user** - do not escalate to paid

In this case: **NEVER use `subagent_explore`**, **NEVER use unverified paid aliases**
without checking `data/bundle-models.json`, **NEVER use paid models** for subagents.

**Case 2 - Parent PAID (user chose a paid model): subagents may use paid.**

The user already opted to pay for the parent. In this case:
- `subagent_explore` (default router, possibly paid) is allowed if cheaper than the parent
- `subagent_general` inherits the parent's paid model (already paid)
- Custom profiles with the canonical pins remain FREE - prefer when possible
- For heavy reasoning, the same parent model can be used via `subagent_general`

**How to detect the case**: check the `cost_tier` of the active parent model in `data/bundle-models.json`. If `free`, it is Case 1 (FREE-ONLY). Any other model is Case 2.

**Rule**: when the parent is on a FREE model (`cost_tier: free`), **NEVER use
paid models** for subagents. The canonical free models cover 100% of cases.
If both fail, report to the user. When the parent is on a PAID model
(user's choice), subagents may use paid models.

## Context budget (parent model)

```
System prompt + tool defs    ~???? tok (Devin runtime, not measurable here)
AGENTS.md                    ~???? tok (measure with context-budget.py)
SKILL-TIERS.md (if read)     ~???? tok
Invoked skills (1-3)         ~1000-9700 tok
MCP tool defs (configured)   ~???? tok (measure with mcp-governance)
─────────────────────────────────────────────
Available for work           see `context_window` in `data/bundle-models.json`
```

> Note: this file (MODEL-GUIDE.md) is optional reading - it does not load automatically.

## Source verification (Rule 12)

Model specifications must be verified against
`data/bundle-models.json`, `devin models list` and the provider sites.

| Citation | Status | Primary URL |
|---|---|---|
| arXiv:2307.03172 (Lost in the Middle) | Verified | aclanthology.org/2024.tacl-1.9 |
| arXiv:2606.22528v2 (Governance Decay) | Verified | arxiv.org/abs/2606.22528v2 |
| arXiv:2607.13083 (Phantom Guardrails) | Verified | arxiv.org/html/2607.13083 |
| arXiv:2606.30317 (MCP Patterns) | Verified | arxiv.org/html/2606.30317 |
| arXiv:2607.25152 (Progress Mirage) | Verified | arxiv.org/abs/2607.25152v1 |
| ICLR 2026 Workshop (Reward Hacking) | Verified | iclr.cc/virtual/2026/10018648 |
| arXiv:2605.10039 (Instruction Adherence) | Verified | arxiv.org/abs/2605.10039 |
| arXiv:2605.21384 (SpecBench) | Verified | arxiv.org/abs/2605.21384 |
| arXiv:2603.15473 (ALTK) | Verified | arxiv.org/abs/2603.15473 |
| arXiv:2607.07405 (Reason Less, Verify More) | Verified | arxiv.org/abs/2607.07405 |
| arXiv:2605.09998 (Continual Harness) | Verified | arxiv.org/abs/2605.09998 |
| arXiv:2607.17641 (VRR-Stop) | Verified | arxiv.org/abs/2607.17641 |
| arXiv:2607.28802 (Model or Harness?) | Verified | arxiv.org/abs/2607.28802 |
| arXiv:2512.24601 (Recursive Language Models) | Verified | arxiv.org/abs/2512.24601 |
| arXiv:2602.03786 (AOrchestra) | Verified | arxiv.org/abs/2602.03786 |
| arXiv:2603.02615 (RLM depth reproduction) | Verified | arxiv.org/abs/2603.02615 |
| arXiv:2606.20629 (AgentCARD) | Verified | arxiv.org/abs/2606.20629 |
| arXiv:2608.03535 (CodeAssay) | Verified | arxiv.org/abs/2608.03535 |
| arXiv:2605.20251 (ProcCtrlBench) | Verified | arxiv.org/abs/2605.20251 |
| arXiv:2607.20972 (Delivery, Not Storage) | Verified | arxiv.org/abs/2607.20972 |
| arXiv:2608.15008 (Harness the Memory) | Verified | arxiv.org/abs/2608.15008 |
| `swe-2-*` variants and cost | Verified | `devin models list` (262K, Free) |
