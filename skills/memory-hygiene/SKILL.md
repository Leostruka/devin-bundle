---
name: memory-hygiene
description: Use when deciding whether to use cross-session agent memory (MEMORY.md, auto-memory), when auto-memory seems stale or bloated, when preferences leak across unrelated tasks, or when choosing between stateless and memory-equipped operation. Covers memory accumulation, temporal contamination, reasoning drift, and user-authored vs auto-saved preferences.
---
# Memory Hygiene

Cross-session agent memory is a **contract with the user**, not a black box. Naive accumulation degrades reliability; managed memory helps. The default is **explicit user-authored preferences**, not auto-saved memory.

## Decision framework: stateless vs managed vs naive

| Mode | When | Evidence |
|---|---|---|
| **Stateless** (no cross-session memory) | Default for coding agents. Preferences live in `.devin/global_rules.md` / `.devin/rules/*.md` / skills / repo docs that the user controls. | Most predictable baseline; no drift, no contamination. |
| **Managed memory** (selective add+delete) | Long-horizon tasks where recalling past executions genuinely helps (multi-session chat, long doc analysis). User reviews and prunes periodically. | +10% absolute vs naive growth (arXiv:2505.16067). MemGPT outperforms on multi-session chat (arXiv:2310.08560). |
| **Naive auto-memory** (append-only, no pruning) | Never. | 16-20pp reliability loss (arXiv:2605.07313). Temporal contamination rises with exposure (arXiv:2605.17830). Reasoning drift even when answers look plausible (arXiv:2607.02374). |

**Rule of thumb:** if a preference matters, the user should write it in `.devin/global_rules.md` or a skill. If past executions matter, use managed memory with selective addition and deletion — never append-only growth.

## When to use this skill

- Deciding whether to enable auto-memory / MEMORY.md in an agent.
- Auto-memory file is growing large or old.
- Preferences from one task are leaking into unrelated tasks.
- Choosing between stateless and memory-equipped operation for a new project.
- Reviewing whether an agent's behavior has drifted from its baseline.

## When NOT to use

- Within-session context window management — use `context-window-hygiene` instead.
- Offloading large context to files — use `context-folding`.
- Selective cross-session notes — use `project-memory` for user-approved, plain-text, auditable memory.
- The task is short and self-contained — stateless is correct, no decision needed.

## Rules

1. **Prefer explicit.** User-authored preferences (`.devin/global_rules.md`, `.devin/rules/*.md`, skills, repo docs) over agent-auto-saved memory. The user controls the steering.
2. **Never naive growth.** If auto-memory is used, it must have selective addition AND deletion. Append-only is the anti-pattern.
3. **Audit periodically.** If auto-memory exists, review it manually for stale, large, or drifting entries. Prune aggressively.
4. **Isolate preferences by task.** A preference about feature X should not influence work on feature Y. Auto-memory that globally injects all preferences into every session causes contamination (arXiv:2605.17830).
5. **Preference following <10% at 10 turns** (arXiv:2502.09597). Don't rely on the agent to infer and persist preferences — it won't, reliably. Write them down.
6. **Memory is a contract.** If the agent saves something to memory, the user must be able to view, modify, and delete it (arXiv:2404.15269, CIPHER). Opaque auto-memory violates the contract.

## Anti-patterns

- **Append-only MEMORY.md.** Grows forever, never pruned. Maximizes contamination and drift.
- **Auto-saving every preference.** "The user said they like tabs → save to memory → inject into every future session." Causes a preference about one feature to leak everywhere.
- **Trusting auto-inferred preferences.** Preference following accuracy is <10% at 10 turns zero-shot (arXiv:2502.09597). Auto-inferred preferences are unreliable.
- **"Kill all memory."** The opposite extreme. Managed memory helps (+10% vs naive, arXiv:2505.16067; MemGPT, arXiv:2310.08560). The problem is naive accumulation, not memory itself.
- **Opaque memory.** Auto-memory the user cannot inspect or edit violates the contract.

## Academic basis

- **Memory accumulation degrades reliability.** Shao et al. 2026, "When Stored Evidence Stops Being Usable" (arXiv:2605.07313): HippoRAG loses 16-20 percentage points in budget-compliant reliability as irrelevant sessions accumulate, even with task evidence held fixed.
- **Temporal memory contamination.** Al-Tawaha et al. 2026, "Remembering More, Risking More" (arXiv:2605.17830): memory-induced violation rates show a robust upward trend with exposure length; effect driven by accumulated content, not encounter order. Tested on 8 memory architectures + Claw-like agents.
- **Error propagation + misaligned replay.** Xiong et al. 2025, "How Memory Management Impacts LLM Agents" (arXiv:2505.16067): naive memory growth causes error propagation (inaccuracies compound) and misaligned experience replay (outdated/irrelevant experiences harm current tasks). Selective add+delete yields +10% absolute vs naive growth.
- **Reasoning drift from memory.** Fang et al. 2026, DRIFTLENS (arXiv:2607.02374): user-attribute memory induces medium-to-large reasoning drift above the pragmatic-noise floor, even when final answers remain fluent and plausible. Partly mitigable (GRPO/DPO), not eliminable.
- **Preference following is unreliable.** Zhao et al. 2025, PrefEval (arXiv:2502.09597, ICLR 2025 oral): preference following accuracy <10% at 10 turns (~3k tokens) zero-shot across most models. Even with prompting+retrieval, deteriorates in long context.
- **User-editable preferences improve alignment.** Lin et al. 2024, CIPHER/PRELUDE (arXiv:2404.15269): learning descriptive preferences from user edits, with user view/modify access, outperforms direct edit retrieval and context-agnostic preferences.
- **Managed memory helps.** Packer et al. 2023, MemGPT (arXiv:2310.08560): OS-inspired memory hierarchy outperforms fixed-context LLMs on multi-session chat and document analysis. Wu et al. 2024, LongMemEval (arXiv:2410.10813): optimized memory designs (session decomposition, fact-augmented keys) improve recall and QA; 30% accuracy drop without optimization shows memory is hard but valuable.
- **Excessive retrieval harms agentic tasks.** "Harness the Memory" (arXiv:2608.15008): retrieving more entries helps QA but hurts sequential decision-making — attention shifts from action-critical context to retrieved blocks. Substrate routing is necessary.

## Source

Distilled from "Kill your MEMORY.md" (Matt Pocock, YouTube). Claims verified against primary sources — the video's thesis (A: accumulation pollutes, B: stateless is predictable, C: user-authored > auto-saved) is supported; its conclusion (D: kill all memory) is refuted by MemGPT and managed-memory evidence. The correct prescription is "prefer explicit, allow managed, ban naive."
