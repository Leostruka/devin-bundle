---
name: skill-docs
description: Use when searching the installed skill corpus by keyword, reading a skill's docs or frontmatter without loading the whole file, or dumping the machine-readable skill manifest - the "CLI is the docs" companion to ask-bundle/leo routing. Routes to skills/skill-docs/scripts/skill_docs.py, a stdlib-only CLI over skills/*/SKILL.md.
triggers: [user, model]
---

# skill-docs

ask-bundle/leo route by skill name. This CLI answers the questions routing
cannot: "which skills mention X", "what does skill Y say about Z", "give me
the corpus as JSON". One command surface for humans and agents, adapted
from the Astryx pattern where the CLI is the docs.

## Commands

```bash
W={{APPDATA}}/devin/skills/skill-docs/scripts/skill_docs.py   # or skills/skill-docs/scripts/ in the repo

python $W search <query>      # ranked hits: name, tier of match, snippet
python $W get <name>          # full record: frontmatter + body
python $W get <name> --meta   # frontmatter fields only
python $W manifest            # whole corpus as JSON (name, description, files)
python $W doctor              # corpus root, skill count, parse failures
```

Corpus root resolution order: `BUNDLE_SKILLS_DIR` env var -> `skills/` found
walking up from the script -> `~/.config/devin/skills` ->
`%APPDATA%\devin\skills`.

All output is envelope-v2 JSON (`api_version: 2`,
`meta.answered_by.wrapper: "skill-docs"`); `{"ok": false}` exits non-zero.

## When NOT to use

- You already know the skill name and need its workflow: invoke the skill.
- Semantic/fuzzy matching across the corpus: `search` is deterministic
  keyword ranking, not embeddings; use `rag` or `laya-orchestrator` for
  ranking-by-meaning.
