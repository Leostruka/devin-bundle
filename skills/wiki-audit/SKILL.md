---
name: wiki-audit
description: Use when auditing, validating, or fixing Obsidian project wikis — checks broken wikilinks, source citation adoption, diagram count, sensitive information, and language consistency across one or more wikis.
---
# wiki-audit

Audit and validate Obsidian project wikis against the established standards. Detects broken wikilinks, missing source citations, missing diagrams, sensitive information, and language inconsistencies. Can also fix common template issues.

**Scope:** one or more `_wiki/` directories inside the vault. Read-only by default; fixes require explicit `--fix` flag.

## When to use

- "Audit my wikis"
- "Check for broken links in the vault"
- "Validate source citations across all project wikis"
- "Find sensitive information in the vault"
- "Fix template broken links"
- Before committing or syncing the vault
- After bulk updates to wiki content

## Standards checked

| Check | Target | Description |
|-------|--------|-------------|
| Diagram count | 14 | Must have 01-Context through 14-Architecture |
| Diagram naming | `{NN}-{Name}.md` | Numbered format (not bare `Context.md`) |
| Mermaid syntax | 0 issues | All diagrams must have valid ` ```mermaid ` blocks with no syntax errors (regex + Node mermaid.parse()) |
| Frontmatter | 0 issues | All `.md` files must have valid `---` frontmatter (no backslash-escaped quotes, must close with `---`) |
| Broken wikilinks | 0 | All `[[link]]` must resolve to existing `.md` files |
| Source format adoption | 96%+ | Files with `## Relevant source files` + `source: path:line` |
| Language | EN | Content in English, `wiki-config.json` has `"language": "en"` |
| Sensitive info | 0 | No passwords, API keys, tokens, or credentials in plain text |
| Template links | 0 broken | Media templates must not have broken placeholder links |

## False positives (not counted as broken)

- `[[byte, byte, ...]]` — JSON arrays in code blocks
- `[[:space:]]` — regex patterns in code blocks
- `[[#section]]` — anchor-only links
- Cross-vault links like `[[Trinity-ERP]]` — valid in Obsidian vault context
- Escaped pipes in markdown tables: `[[Functions/Foo\|foo]]` — pipe is separator, not part of target

## Mermaid syntax errors checked

The audit checks each diagram's ` ```mermaid ` block for:

| Error | Description | Fix |
|-------|-------------|-----|
| `NO_MERMAID` | File has no ` ```mermaid ` block | Add Mermaid diagram code |
| `MALFORMED_FENCE` | Uses ``mermaid (single/double backtick) instead of ` ```mermaid ` | Use triple backticks |
| `WRONG_FENCE` | Fence doesn't match ` ``` ` | Use triple backticks on both ends |
| `SOURCES_INSIDE` | `<!-- Sources: -->` HTML comment is inside the Mermaid block | Move it outside, before the block |
| `UNCLOSED_GENERIC` | `Items~` (odd number of `~`) — Mermaid generic syntax not closed | Use `Items[]` or `List~Items~` |
| `BR_TRIPLE_SLASH` | `<br///` (triple slash) instead of `<br/>` | Use `<br/>` |
| `MISSING_STYLE` | `NODE fill:...` without `style` keyword | Add `style` prefix: `style NODE fill:...` |
| `SUBGRAPH_END_MISMATCH` | `subgraph` without matching `end` | Add missing `end` |
| `PARSE_ERROR` | Mermaid `parse()` rejects the diagram | Fix the syntax error reported by mermaid.parse() |

## Frontmatter errors checked

The audit checks each `.md` file's frontmatter for:

| Error | Description | Fix |
|-------|-------------|-----|
| `MISSING_CLOSING` | Frontmatter starts with `---` but has no closing `---` | Add closing `---` after frontmatter fields |
| `BACKSLASH_QUOTE` | `title: \ ... \\`` or `project: \...\\`` (backslashes instead of quotes) | Use double quotes: `title: "..."` |

## Usage

### Audit a single wiki

```bash
python .devin/skills/wiki-audit/audit.py --wiki "G:\Meu Drive\vault\Projetos Web\10-Fingertech\projetos\Trinity-ERP\_wiki"
```

### Audit all wikis in a section

```bash
python .devin/skills/wiki-audit/audit.py --base "G:\Meu Drive\vault\Projetos Web\10-Fingertech\projetos"
```

### Audit all wikis in the vault

```bash
python .devin/skills/wiki-audit/audit.py --vault "G:\Meu Drive\vault\Projetos Web"
```

### Fix template broken links

```bash
python .devin/skills/wiki-audit/fix_templates.py --wiki <wiki-dir>
python .devin/skills/wiki-audit/fix_templates.py --base <projects-dir>
```

### Validate wikilinks only

```bash
python .devin/skills/wiki-audit/validate_links.py --wiki <wiki-dir>
```

### Validate Mermaid syntax only

```bash
python .devin/skills/wiki-audit/validate_mermaid.py --wiki <wiki-dir>
python .devin/skills/wiki-audit/validate_mermaid.py --base <projects-dir>
python .devin/skills/wiki-audit/validate_mermaid.py --vault <vault-dir>
```

### Scan for sensitive information

```bash
python .devin/skills/wiki-audit/scan_secrets.py --wiki <wiki-dir>
python .devin/skills/wiki-audit/scan_secrets.py --vault <vault-dir>
```

## Output format

Audit produces a table:

```
| Wiki | Files | Diagrams | 14-Arch | Mermaid | Frontmatter | Broken | Source % | Lang | Secrets | Status |
|------|-------|----------|---------|---------|-------------|--------|----------|------|---------|--------|
| Trinity-ERP | 116 | 14 | yes | OK | OK | 0 | 97% | EN | 0 | GOOD |
| ML_CRM | 105 | 14 | yes | OK | OK | 0 | 98% | EN | 0 | FIXED |
```

Status values:
- **GOOD** — meets all standards (96%+ source, 0 broken, 14 diagrams, 0 secrets, 0 mermaid/frontmatter issues)
- **FIXED** — was below standards, now fixed
- **CRITICAL** — below 50% source format or 10+ broken links
- **POOR** — below 80% source format or 1-9 broken links or mermaid/frontmatter issues
- **MISSING** — wiki directory not found

## Fix capabilities

When `--fix` is passed, the audit can:

1. **Fix template broken links** — replace placeholder links in `Media/` templates:
   - `[[...]]` → `[[09-Decisions]]`
   - `[[00-SRS]]` → `[[01-SRS]]`
   - `[[01-Architecture]]` → `[[02-Architecture]]`
   - `[[Diagrams/Context]]` → `[[Diagrams/01-Context]]` (all 14 diagrams)
   - `[[Modules/{{MODULE_NAME}}]]` → `_ExampleModule_` (if Auth module doesn't exist)

2. **Redact secrets** — replace credential values with `(REDACTED — see path:line)`

3. **Rename diagrams** — rename bare diagram files to numbered format

## Rules

- **Read-only by default** — fixes require `--fix` flag
- **No AI signatures** — audit scripts do not add signatures to files
- **No sensitive info in output** — secrets are redacted in audit output
- **Verify before claiming** — all line numbers and file paths are checked against actual files
