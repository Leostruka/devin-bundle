---
name: structured-knowledge-extraction
description: Use when extracting entities, relations, evidence, and provenance from Markdown or plain text into a typed, versioned knowledge graph under `.devin/`.
version: 1.0.0
---

# structured-knowledge-extraction

Deterministic, provider-neutral extraction of entities, relations, evidence, and provenance from Markdown or plain text into versioned JSON and relational Markdown under `.devin/`.

## When to use

- You need to turn one or more Markdown/text documents into a typed, mergeable knowledge graph.
- You want every extracted fact to point back to a source file, line, and quote.
- You need incremental updates: merge new sources without duplicating entities or silently overwriting conflicting ones.
- You want a no-API-key, no-LLM baseline for searching the knowledge graph.
- You are evaluating — but not yet installing — Hyper-Extract, embeddings, or MCP integration.

## When NOT to use

- You need full semantic search or vector retrieval today; this skill is a lexical baseline.
- You want automatic conflict resolution; conflicts are reported and require explicit action.
- You want to install external dependencies or MCP servers by default.

## Core operations

All operations use only the Python standard library and stay inside `.devin/`.

| Operation | Purpose | Default output |
|---|---|---|
| `extract` | Extract entities, relations, evidence, and provenance from a Markdown/text source. | JSON to stdout |
| `merge` | Merge a new extraction into an existing `.devin/notes/structured-knowledge-extraction/knowledge.json`. | JSON to stdout |
| `search` | Lexical search over the stored knowledge graph (no API key). | JSON to stdout |
| `plan` | Generate an integration guidance note for optional Hyper-Extract/embeddings/MCP evaluation. | Markdown to stdout; writes note only with `--write --approve` |

## Usage

From the bundle root:

```bash
python skills/structured-knowledge-extraction/scripts/extract.py extract <source> [project] [--write] [--approve]
python skills/structured-knowledge-extraction/scripts/extract.py merge <source> [project] [--write] [--approve]
python skills/structured-knowledge-extraction/scripts/extract.py search <query> [project]
python skills/structured-knowledge-extraction/scripts/extract.py plan [project] [--write] [--approve]
```

After installation the helper is available at `~/.config/devin/skills/structured-knowledge-extraction/scripts/extract.py`.

## Rules

1. **Provider-neutral and stdlib-only.** No LLM, embedding, or external-provider dependency is required for the core path.
2. **Write only under `.devin/`.** Generated artifacts go to `.devin/notes/structured-knowledge-extraction/`. No other files are created or modified.
3. **Explicit approval required.** `--write` must be paired with `--approve` for any persistence.
4. **Every fact has provenance.** Each entity and relation records source, line, and quote.
5. **Incremental merge without silent conflict resolution.** Duplicates are deduplicated; conflicts are reported explicitly and never resolved automatically.
6. **Deterministic and idempotent.** Sorted output, stable hashes, and content-derived timestamps (never mtime) make repeated runs byte-identical for unchanged inputs.
7. **No API key required.** The lexical search baseline works without network, embeddings, or MCP.
8. **Reject symlinks and outside-`.devin` writes.** Symlinked sources are rejected; output paths are verified to stay inside `.devin/`.
9. **Optional integrations only.** Hyper-Extract, embeddings, and MCP are evaluated in isolation and never installed by the core skill.

## Source and license attribution

`structured-knowledge-extraction` is conceptually inspired by Hyper-Extract's typed entities, incremental extraction, and provenance-first design. No code, prompts, or templates are copied from Hyper-Extract. The core implementation uses only the Python standard library.

- Hyper-Extract (Apache-2.0): https://github.com/yifanfeng97/Hyper-Extract
- README: https://github.com/yifanfeng97/Hyper-Extract/blob/main/README.md
- pyproject: https://github.com/yifanfeng97/Hyper-Extract/blob/main/pyproject.toml
- License: https://github.com/yifanfeng97/Hyper-Extract/blob/main/LICENSE

## Cross-references

- `/devin-manager` — audit `.devin/` health before writing.
- `/mcp-context-audit` — measure MCP tool-definition cost before enabling an integration.
- `/research` — verify primary-source claims before adding external integrations.
