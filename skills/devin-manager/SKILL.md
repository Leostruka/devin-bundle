---
name: devin-manager
description: Use when auditing or managing a project's `.devin/` configuration, producing deterministic read-only reports, detecting broken references, duplicates, and divergences, and generating plans that only persist under `.devin/` after explicit approval.
version: 1.0.0
---

# devin-manager

Evidence-first, read-only management for a project's `.devin/` directory.

## When to use

- You need to answer "what is in `.devin/`?" with provenance and checksums.
- You need to inventory `.devin/` plus agent profiles (`agents/`) and MCP servers (`mcp_config.json`).
- You suspect stale or broken links between rules, skills, hooks, or memory notes.
- You want a diff between two `.devin/` states before applying changes.
- You need a plan note that records broken references, duplicates, and divergences.
- You are about to edit `.devin/config.json`, `.devin/hooks.v1.json`, or memory and need explicit approval.

## When NOT to use

- The task is to write application code — use `/implement` or `/tdd`.
- The task is to set up `.devin/` from scratch — use `/project-setup`.
- The user has not approved editing configuration or persisting memory.

## Core operations

All operations are deterministic and read-only by default. Generated notes are written only under `.devin/notes/devin-manager/` and only when both `--write` and `--approve` are provided.

| Operation | Purpose | Default output |
|---|---|---|
| `scan` | Inventory `.devin/`, agent profiles (`agents/`), and MCP servers (`mcp_config.json`) with sha256, provenance, frontmatter, headings, and references. | JSON to stdout |
| `explain` | Explain one `.devin/` artifact and its outgoing references. | JSON to stdout |
| `diff` | Compare two project `.devin/` states (and `agents/`/`mcp_config.json`) by hash. | JSON to stdout |
| `doctor` | Report broken references, duplicate content/skill names, and config/hook divergences. | JSON to stdout |
| `plan` | Generate a plan note from doctor findings. | Markdown to stdout; writes note only with `--write --approve` |

## Usage

```bash
python skills/devin-manager/scripts/devin-manager.py scan [PROJECT]
python skills/devin-manager/scripts/devin-manager.py explain [PROJECT] ARTIFACT
python skills/devin-manager/scripts/devin-manager.py diff [PROJECT_A] [PROJECT_B]
python skills/devin-manager/scripts/devin-manager.py doctor [PROJECT]
python skills/devin-manager/scripts/devin-manager.py plan [PROJECT] --write --approve
```

## Rules

1. **Read-only by default.** `scan`, `explain`, `diff`, `doctor`, and `plan` do not edit anything unless `--write` is used.
2. **Write only under `.devin/`.** Generated notes go to `.devin/notes/devin-manager/`. No other files are created or modified.
3. **Explicit approval required.** `--write` must be paired with `--approve` for any persistence. Configuration edits and memory/MOC persistence always require user approval; the tool does **not** auto-update `MOC.md`.
4. **Deterministic and idempotent.** File lists, hashes, and JSON output are sorted; repeated scans are byte-identical. Absolute paths do not appear in outputs or notes.
5. **No external dependencies.** The script uses only the Python standard library. PDF support is explicitly out of core and requires a user-approved, dependency-free extension if ever added.
6. **Provenance for every finding.** Broken references, duplicates, and divergences include the source path.
7. **Reject symlinks and outside-`.devin` references.** Symlinks are skipped in inventory and never resolved; any target that resolves outside `.devin/` is reported as broken.
8. **Malformed JSON as divergence.** Malformed core JSON (`config.json`, `hooks.v1.json`, `manifest.json`, `mcp_config.json`) is reported as a provenance-bearing divergence, not a crash.
9. **Deduplicate references.** When the same source+target is referenced multiple ways, the strongest kind is kept (`source` > `markdown_link` > `wikilink` > `command` > `mention`).

## Source and license attribution

`devin-manager` is conceptually inspired by DeepPaperNote's evidence-first, one-source-at-a-time note workflow. No code, prompts, or templates are copied from DeepPaperNote; this implementation uses only the Python standard library and has no PDF dependency.

- DeepPaperNote (MIT): https://github.com/917Dhj/DeepPaperNote
- README: https://github.com/917Dhj/DeepPaperNote/blob/main/README.md
- Skill principal: https://github.com/917Dhj/DeepPaperNote/blob/main/skills/deeppapernote/SKILL.md
- License: https://github.com/917Dhj/DeepPaperNote/blob/main/LICENSE

## Cross-references

- `/project-setup` — create `.devin/` from scratch.
- `/project-memory` — capture approved project memory.
- `/continuous-improvement` — the 10-step loop that inspired the doctor/plan gate.