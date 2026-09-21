# Knowledge Bases — Prompt Compiler

Per-model prompt-engineering rules consumed by `../prompt_compiler.py`.

## Schema

One JSON file per model, named `<model>.json` (lowercase, e.g. `swe-2.json`):

```json
{
  "model": "<model>",
  "template": "Recommended prompt skeleton for this model.",
  "rules": ["Non-negotiable prompt rules."],
  "do":    ["Things that improve results."],
  "dont":  ["Things that degrade results."]
}
```

All keys are required except `do`/`dont` (may be `[]`). `generic.json` is the
fallback when no model file matches — keep it model-agnostic.

## Update pipeline (agent instructions)

When a new raw prompt-engineering guide lands (Markdown/text dropped here or
linked by the user):

1. Invoke the **`knowledge-modeling`** skill (structured knowledge extraction).
2. Extract: model name, prompt template, rules, do's, don'ts — with provenance
   (source file/URL) preserved in the knowledge graph under `.devin/`.
3. Distill into the schema above and write `<model>.json` in this directory.
4. Verify: `python ../prompt_compiler.py --list-models` lists the new model
   and `--self-test` stays green.
5. Raw guides do NOT belong here long-term — this directory holds only the
   compiled JSON. Keep raw sources in `.devin/` per the extraction pipeline.

## Agent contract

- The agent (not the script) runs extraction — `prompt_compiler.py` only reads.
- Never hand-edit a JSON without re-running `--self-test`.
- Add new models as files; do not overload `generic.json`.
