---
name: prompt-compiler
description: Use when the user invokes /prompt or asks to compile, refine, or optimize a prompt before execution — interactive pre-flight optimizer that produces an approved super-prompt and hands off to a fresh local session.
argument-hint: What task should the compiled prompt execute?
triggers: [user]
---

# Prompt Compiler

Pre-flight prompt optimizer. Compiles a rough task into a model-tuned
super-prompt, iterates with the user, then hands off to a **fresh local
session** so planning context never pollutes execution.

## Where it is

- Script: `extensions/ai-tools/prompt_compiler.py` (installed at
  `%APPDATA%\devin\extensions\ai-tools\`)
- Model rules: `extensions/ai-tools/knowledge_bases/<model>.json` —
  populated via the `knowledge-modeling` skill (see its README for the
  extraction pipeline).

## Flow

1. Run the compiler interactively (TTY) so the user drives the loop:

   ```bash
   python extensions/ai-tools/prompt_compiler.py
   ```

   Non-interactive fallback (agent-driven, no `input()`):

   ```bash
   python extensions/ai-tools/prompt_compiler.py --task "<task>" --model <model>
   ```

2. Iterate: present the draft, apply user feedback ("add the testing skill",
   "make scope stricter"), recompile. Loop until the user says `APPROVE`.

3. On approval the script writes `.devin/scratch/optimized_ready.md` and
   prints `{ok, path, sha256}` on stdout — verify `ok: true`.

## Golden Rule — local handoff only

After `optimized_ready.md` exists, end the preparation phase by invoking
**exactly** this command (local compaction — the `handoff` skill):

```
/handoff I have compiled the optimized prompt in .devin/scratch/optimized_ready.md. The next agent should consume this file and execute the task exactly as specified in a fresh context.
```

- **Never** use `/handoff <task description>` cloud routing — that sends the
  work to a remote session and defeats context isolation.
- Do not execute the compiled prompt in the current session.
- Do not paste the prompt into the handoff text — reference the file path.

## Knowledge base upkeep

New prompt-engineering guide arrived? Do not hand-edit JSONs blindly —
invoke `knowledge-modeling` to extract entities/rules from the raw source,
then write `knowledge_bases/<model>.json` per that directory's README schema,
and re-run `prompt_compiler.py --self-test`.
