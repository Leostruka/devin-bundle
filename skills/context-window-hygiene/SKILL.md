---
name: context-window-hygiene
description: Use when a conversation is getting long and the agent seems to be forgetting earlier instructions, before adding MCP servers or rules files, when deciding whether to clear or compact the chat, or when context window budget feels tight. Covers lost-in-the-middle, clear-vs-compact, and lean-context hygiene.
---

# Context Window Hygiene

## Core Facts

- **Context window = input + output tokens the model sees at once.** Every
  system prompt, rules file, MCP tool definition, message, and tool result
  counts against a hard limit set by the model provider.
- **Hard limit.** Each model has a fixed token ceiling (e.g. 200k, 2M). Hit it
  and the provider errors, or output stops mid-generation.
- **Bigger window ≠ better retrieval.** A 10M-token window that cannot find
  the needle is worse than a 200k window that can. Evaluate retrieval quality,
  not just size. (Llama 4 Scout: 10M window, severe lost-in-the-middle.)
- **Lost in the middle.** In long contexts the attention mechanism
  deprioritizes information in the *middle* of the conversation. Start
  (primacy) and end (recency) dominate. Middle detail has weak impact.

## When to Use

- Conversation is long and the agent is drifting or ignoring early rules.
- Deciding whether to `clear` or `compact`.
- About to add an MCP server, a large rules file, or paste a huge document.
- Choosing a model by context size.

## When NOT to Use

- Context is small and focused — direct work is cheaper.
- You need dense access to early detail — use `context-folding` instead.

## Clear vs Compact

| Action | What it does | When |
|---|---|---|
| `clear` | Wipes history, blank slate | **Default.** Task is done or unrelated to prior chat. |
| `compact` | Summarizes history into a small message | Preserve the *vibes*/intent of the current task while freeing space. Costs tokens + time to generate the summary. |

**Default to `clear`.** Use `compact` only when continuing the same task and
losing the thread would hurt. Compaction drops detail — it preserves intent,
not facts. If dense access to early context is needed, use `context-folding`
(offload to file, grep/read on demand) instead of compacting.

## Lean Context Rules

1. **Clear chats between unrelated tasks.** Refreshes memory, removes
   lost-in-the-middle noise. A fresh thread outperforms a bloated one.
2. **Keep rules files small.** `.devin/global_rules.md` / `.devin/rules/*.md` / cursor rules / claude rules are
   loaded into *every* conversation. A 25k-token rules file is 12% of a 200k
   window before you say a word. Compress, modularize into skills, reference
   instead of inlining. See `writing-for-agents`.
3. **Be paranoid about MCP servers.** Each server injects every tool
   definition into the system prompt. Two servers can eat a third of the
   window before the first message. Audit before adding — use
   `mcp-context-audit`. Keep tool count per server under 10-15.
4. **Don't paste huge documents into chat.** Write to a file with `write`,
   then `read` with offset/limit or `grep` to pull only what's needed. This is
   `context-folding` at its simplest.
5. **Prefer subagents for parallel exploration.** Each subagent has its own
   window; only the synthesis returns to the root. 50-100x context savings.
   See `dispatching-parallel-agents`.
6. **Watch the budget.** Run `context-budget.py` (SessionStart hook) to see
   the token cost of `.devin/global_rules.md` + loaded rules before working.

## Anti-Patterns

- **Keeping one long chat for the whole day.** Maximizes lost-in-the-middle.
- **Adding MCP servers "just in case."** Permanent context tax for unused tools.
- **Writing giant rules files.** Self-defeating: the rules degrade retrieval
  of everything else in context.
- **Pasting a 500k log into chat.** Use a file + grep.
- **Compacting when you need the original detail.** Compaction is lossy.

## Model Selection Heuristic

| Need | Pick |
|---|---|
| Long chat, simple retrieval | Large window *with good needle-in-haystack benchmarks* |
| Precision on early rules | Smaller window, clear often |
| Huge document analysis | `context-folding` on any model; don't rely on window size alone |

## Source

Distilled from "Context Windows Explained for Coding Agents" (Matt Pocock,
AI Hero). Key claims verified against primary sources:
- Lost-in-the-middle: Liu et al. (arXiv:2307.03172).
- Window limits are provider-set and hard: models.dev model cards.
- Compaction is lossy by design: see `context-folding` comparison table.

If the user asks for current context-window limits or model benchmarks, invoke `research` to fetch the latest model cards and papers.
