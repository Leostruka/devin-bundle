---
name: ai-tools
description: Use when running local, offline-first ML tooling — mechanistic interpretability PoCs like refusal-direction ablation on local safetensors or the HF cache, or when adding self-contained model experiments that print JSON and never download anything.
triggers: [user]
---

# AI Tools

Local, offline-first ML experiments. The scripts live in the `ai-tools`
extension, not in this skill — this file is only the router pointer.

## Where it is

- Bundle source: `extensions/ai-tools/`
- Installed: `%APPDATA%\devin\extensions\ai-tools\` (Windows) or
  `~/.config/devin/extensions/ai-tools/` (POSIX)
- **Full docs: `USAGE.md` inside that directory** — read it first.

## Conventions (all tools)

- Self-contained `<tool>.py` with `__main__` guard and JSON on stdout.
- `--self-test` runs fully offline asserts; exit 1 on failure.
- No network: real inputs come from explicit file paths or the local HF
  cache only.
- Deps pinned in `requirements.txt`, installed on demand — no installer
  venv (unlike `computer-use`).

## Current tools

- `abliterator.py` — refusal-direction orthogonalization PoC (Arditi et
  al. 2024): difference-in-means direction, activation ablation,
  residual-weight orthogonalization. Dummy tensors by default;
  `--weights F.safetensors` or `--model <cached>` for real weights.
