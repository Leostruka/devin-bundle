# Third-Party Notices

This bundle includes content adapted from or inspired by third-party work,
used under the terms of its original license. Per-file provenance is also
recorded in `manifest.json` (`source` field) and inline in each SKILL.md.

## Adapted works (content carried into this repo)

### pbakaus/impeccable — Apache License 2.0

`skills/impeccable/` is adapted for Devin CLI from
https://github.com/pbakaus/impeccable by Paul Bakaus.
Upstream license: https://github.com/pbakaus/impeccable/blob/main/LICENSE

Upstream NOTICE (carried per Apache-2.0 §4d): the upstream project includes
content derived from ehmo's `platform-design-skills` (Apple Human Interface
Guidelines and Material Design 3 rules), rewritten in Impeccable's voice.
- Original work: https://github.com/ehmo/platform-design-skills
- Original license: MIT — Author: ehmo

### JimmySadek/youtube-fetcher-to-markdown — MIT

`skills/youtube-fetcher/` is a conceptual adaptation — no code, prompts, or
templates were copied from the upstream project; the implementation uses only
the Python standard library.
- Upstream: https://github.com/JimmySadek/youtube-fetcher-to-markdown
- License: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/LICENSE

## Conceptual inspiration (no code copied)

- **DeepPaperNote** (MIT) — evidence-first workflow inspired `devin-config`.
  https://github.com/917Dhj/DeepPaperNote
- **Hyper-Extract** (Apache-2.0) — inspired `knowledge-modeling` extraction
  pipeline. https://github.com/yifanfeng97/Hyper-Extract

## Runtime dependencies (consumed, not vendored)

- **laya** (Apache-2.0) — non-autoregressive decision engine wrapped by
  `extensions/laya-tools/`. https://github.com/NandhaKishorM/laya

## Research references (cited, not consumed)

- PrimeAgent / Continual Harness — PrimeIntellect, arXiv:2605.09998
  (`self-improvement` refine mode)
- Recursive Language Models — arXiv:2512.24601 (`context-hygiene`)
- Constitutional AI (Anthropic, 2022) and RISE (arXiv:2407.18219)
  (`self-improvement` improvement-loop)
- Anthropic multi-agent research, 2025-06 (`dispatching-parallel-agents`)
