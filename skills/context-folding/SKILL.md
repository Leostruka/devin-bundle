---
name: context-folding
description: Use when context is growing large (approaching model window limits), when long documents or transcripts need to be processed, or when compaction is losing critical information. Adapts Recursive Language Model (RLM) techniques to the Devin CLI runtime.
---

# Context Folding (RLM-style)

## When to Use

- Context window is filling up and compaction would lose critical detail
- Processing documents, transcripts, or logs longer than ~50k tokens
- Multi-hop reasoning over large context where summarization loses signal
- Before invoking `compact` when dense access to early context is still needed

## When NOT to Use

- Context fits comfortably in the model window — just use it directly
- Task is simple retrieval (one needle, one haystack) — grep is cheaper
- Context is already compacted and the original is gone

## Source

Adapted from Recursive Language Models (Zhang, Kraska, Khattab — MIT CSAIL,
arXiv:2512.24601). The paper shows RLM(GPT-5-mini) outperforms GPT-5 by +34
points (114%) on OOLONG at 132k tokens, at comparable cost ($0.11-$0.99 vs
$0.98-$6.75 for Claude Code). Reproduced independently (arXiv:2603.02615):
depth=1 helps, depth=2+ causes "overthinking" and inflates time from 3.6s to
344.5s. PrimeAgent (PrimeIntellect, MIT-licensed, 16k+ stars) builds on this.

## Core Technique

RLM treats the prompt as a **variable in an environment**, not as direct
input. The model peeks, greps, partitions, and launches recursive sub-queries
over the context instead of reading it all at once. Devin CLI does not have a
persistent Python REPL, but the same effect is achieved with:

1. **Offload to file** — write the large context to a temp file with `write`
2. **Peek** — `read` with `offset`/`limit` to sample structure
3. **Grep** — `grep` with patterns to locate relevant sections
4. **Partition** — split into chunks mentally or via `exec` (e.g. `split`)
5. **Sub-query** — dispatch `researcher` subagents (NOT `subagent_explore` when parent is FREE — that runs on PAID SWE-1.6) over chunks
6. **Synthesize** — combine sub-agent returns into the final answer

## Depth Rule (Critical)

**Use depth=1 only.** The root agent (you) can spawn sub-queries (subagents).
Subagents must NOT spawn their own sub-queries (depth=2).

Evidence (arXiv:2603.02615): depth=2 causes "overthinking" — performance
degrades and execution time inflates from 3.6s to 344.5s (95x slower). The
paper title is "Think, But Don't Overthink."

## Workflow

### Step 1: Offload

If the context is in the conversation, write it to a file:

```
write /tmp/context.md <the large content>
```

If it's already a file, skip this step.

### Step 2: Assess

Check size and structure:

```
exec: wc -l /tmp/context.md
read /tmp/context.md offset=1 limit=50   # peek at start
read /tmp/context.md offset=<mid> limit=50  # peek at middle
```

### Step 3: Locate

Use `grep` to find relevant sections:

```
grep "keyword" /tmp/context.md --context_lines=3
```

### Step 4: Partition (if needed)

If the relevant sections are spread across the file, split it:

```
exec: split -l 500 /tmp/context.md /tmp/chunk_
```

### Step 5: Sub-query (depth=1)

Dispatch `researcher` subagents (NOT `subagent_explore` when parent is FREE — that runs on PAID SWE-1.6) over chunks. Each subagent gets:
- One chunk (or section) to analyze
- A specific question to answer
- Instructions to return findings, not spawn further subagents

```
run_subagent:
  profile: researcher
  task: "Read /tmp/chunk_aa. Find all references to X. Return: file path, line number, and a one-sentence summary of each reference. Do NOT spawn subagents."
```

Dispatch multiple in parallel for independent chunks.

### Step 6: Verify subagent returns

Per Rule 12: do not trust subagent returns without verification. For each
return, spot-check the cited lines in the source file with `read`.

### Step 7: Synthesize

Combine verified findings into the final answer. The root context stays
small — only the synthesis enters it, not the raw chunks.

## Anti-Patterns

- **Don't dump the whole file into context.** That defeats the purpose.
- **Don't let subagents spawn subagents.** Depth=2 causes overthinking.
- **Don't skip verification of subagent returns.** Rule 12 applies.
- **Don't use this for small contexts.** Overhead exceeds value under ~50k tokens.
- **Don't summarize blindly.** RLM's advantage over compaction is dense access — use grep and partition to preserve it.

## Comparison: Context Folding vs Compaction

| Aspect | Compaction (`compact`) | Context Folding (this skill) |
|---|---|---|
| Mechanism | Summarize old context, discard detail | Offload to file, sub-query on demand |
| Information loss | Yes — summary drops details | No — original stays in file |
| Dense access | No — summarized once | Yes — grep/read any section anytime |
| Cost | One large model call | Multiple small sub-agent calls |
| When to use | Context is stale, detail not needed | Detail is needed, context is large |
| Can combine | Yes — fold first, compact the synthesis | Yes |

## Cross-skills

- If the folded context still exceeds the safe window, use `context-window-hygiene` to choose the right model and clearing cadence.
- If the fold is a precursor to exhaustive exploration, use `deep-mode` for the multi-pass search and write findings to a file.

## Evidence Summary

| Claim | Source | Status |
|---|---|---|
| RLM(GPT-5-mini) +34 pts over GPT-5 at 132k | arXiv:2512.24601, blog Zhang | Verified |
| RLM cost $0.11-$0.99 vs Claude Code $0.98-$6.75 | arXiv:2512.24601 Table | Verified |
| depth=1 helps, depth=2 degrades | arXiv:2603.02615 | Verified |
| depth=2 inflates time 3.6s → 344.5s | arXiv:2603.02615 | Verified |
| RLM handles 10M+ tokens | arXiv:2512.24601, blog | Verified |
