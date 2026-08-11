---
name: memory-bridge
description: Use when the user wants to compare wiki knowledge by source session or source type and surface cross-session blind spots.
---
# Memory Bridge — Cross-Session Knowledge Browser

You help the user browse and compare their Obsidian wiki knowledge filtered by its source provenance. The wiki tracks provenance in `.manifest.json` and page `sources:` frontmatter — this skill surfaces that metadata as a navigable view.

## Before You Start

1. **Resolve config** — follow the Config Resolution Protocol in `llm-wiki/SKILL.md` (inline `@name` override → walk up CWD for `.env` → `~/.obsidian-wiki/config` → prompt setup). This gives `OBSIDIAN_VAULT_PATH`.
2. Read `$OBSIDIAN_VAULT_PATH/.manifest.json` — source-of-truth for what session/type produced what.
3. Read `$OBSIDIAN_VAULT_PATH/index.md` for page titles and one-line descriptions.

## Commands

Parse the user's invocation to determine mode:

| Invocation | Mode |
|---|---|
| `/memory-bridge <source>` | **Browse** — list all wiki pages from `<source>` |
| `/memory-bridge <source> "<topic>"` | **Search** — pages from `<source>` mentioning `<topic>` |
| `/memory-bridge diff` | **Diff** — pages unique to each source; overlap; blind spots |
| `/memory-bridge diff <source-a> <source-b>` | **Diff** — compare two specific sources |
| `/memory-bridge map` | **Map** — full origin matrix: every page × each source that touched it |

Recognized source types: `devin_session`, `manual` (hand-written), `ingest` (wiki-ingest documents).

## Step 1: Build the Source Map

Read `.manifest.json`. For each source entry, extract:

- `source_type` — maps to source name:
  - `devin_conversation`, `devin_session`, `devin_audit_log`, `devin_desktop_session` → `devin_session`
  - `document` → `ingest`
  - anything else → `manual`
- `pages_created` and `pages_updated` — the wiki pages produced by this source

Build a map:

```
tool_pages = {
  "devin_session": set(pages created/updated by devin sources),
  "manual": set(pages created/updated manually),
  "ingest": set(pages created/updated by wiki ingest),
}
```

A page can appear in multiple source sets if multiple sources contributed.

## Step 2: Execute the Mode

### Browse Mode

Filter `tool_pages[<source>]` and present as a grouped list:

```
## Knowledge from <source> (<N> pages)

### By category
- concepts/ — N pages
- entities/ — N pages
- skills/   — N pages
...

### Pages
| Page | Category | Tags | Last updated |
|------|----------|------|--------------|
| [[page-name]] | concept | tag1, tag2 | 2026-04-10 |
...
```

Read frontmatter for the listed pages (grep for `^(title|category|tags|updated):`) — do not read full page bodies unless the user asks.

### Search Mode

Within the filtered page set, run:

```
rg -l "<topic>" <pages in source set>
```

Then grep section headers (`^##`) around matches to give context without full reads. Present results as a ranked list with the matching excerpt.

### Diff Mode

Compute:

- `only_in_a` = `tool_pages[a]` − `tool_pages[b]`
- `only_in_b` = `tool_pages[b]` − `tool_pages[a]`
- `shared` = `tool_pages[a]` ∩ `tool_pages[b]`

If no specific sources are given, compare all sources pairwise (limit to pairs with >0 overlap or unique pages to keep output concise).

Present:

```
## Memory Bridge Diff — <source-a> vs <source-b>

### Only in <source-a> (<N> pages)
These concepts exist in your wiki from <source-a> sessions but <source-b> has never touched them.
<list with one-line descriptions from index.md>

### Only in <source-b> (<N> pages)
<list>

### Shared (<N> pages)
Both sources have contributed to these pages.
<list — only show if ≤15; otherwise just the count>

### Notable gaps
<highlight the most interesting asymmetries — e.g. "devin_session has 12 pages on build tooling that manual has never seen">
```

### Map Mode

Build a matrix showing every page and which sources have touched it. Cap at 50 rows; sort by number of contributing sources descending (most cross-source pages first — these are the richest nodes).

```
| Page | devin_session | manual | ingest |
|------|---------------|--------|--------|
| [[react-patterns]] | ✓ | ✓ | — |
| [[rust-ownership]] | — | ✓ | — |
```

## Step 3: Validate

After generating output, spawn a `subagent_general` or `subagent_explore` subagent to review:

```
Goal: "Browse/diff wiki knowledge by source and surface cross-session blind spots."
Artifacts: [the output you just generated]
Checks:
- Did you correctly parse source_type from .manifest.json?
- Are page counts plausible (not 0 unless vault is empty)?
- Is the diff symmetric (a−b and b−a are disjoint)?
- Did you avoid reading full page bodies when not needed?
```

Apply any issues it surfaces before presenting output to the user.

## Step 4: Log

Append to `$OBSIDIAN_VAULT_PATH/log.md`:

```
- [TIMESTAMP] MEMORY-BRIDGE mode=<browse|search|diff|map> source=<source> pages_shown=N
```

## Output Conventions

- Always show page counts so the user can calibrate how much knowledge is in each source's silo.
- Use `[[wikilinks]]` for page references (or standard Markdown links if `OBSIDIAN_LINK_FORMAT=markdown` is set).
- In diff mode, call out the most *surprising* asymmetry explicitly — that's the insight the user came for.
- If `.manifest.json` is empty or missing, say so clearly and suggest running `/wiki-history-ingest` first.
