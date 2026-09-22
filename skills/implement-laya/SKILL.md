---
name: implement-laya
description: Use when a task needs fast typed decisions — classification, triage, scoring, guardrails, moderation, or model routing — over text/JSON states, or when integrating the `laya` engine (non-autoregressive decision model) into a user's codebase.
argument-hint: What decision should the engine make?
triggers: [user, model]
---

# Implement Laya

**What it is:** `laya` (PyPI, Apache-2.0) is a non-autoregressive "System 1"
decision engine. It answers typed questions — `choice`, `score`, `noul` —
over any state (text, email, JSON) in **one forward pass** (~33 ms GPU,
~200–460 ms CPU). No text generation → nothing to parse, nothing to
hallucinate. Probabilities are RLCD-calibrated, so `confidence` is safe for
automated gating.

**When to recommend it:** high-frequency classification/routing where an LLM
call is too slow or expensive — ticket triage, jailbreak/injection guards,
content moderation, intent routing, churn scoring. **Not** for >20-option
label spaces without tuning (see Gotchas).

## Where it is

- Extension (self-use): `extensions/laya-tools/laya_cli.py` (installed at
  `%APPDATA%\devin\extensions\laya-tools\`). Deps on demand:
  `python -m pip install -r requirements.txt` inside that dir — better: use a
  local `.venv`. Torch imports lazily; `--self-test`/`--check-questions`/
  `--list-presets` run with zero deps.
- Upstream: `github.com/NandhaKishorM/laya` — `pip install laya`.

## Self-use (agent automation)

```bash
# triage a ticket with the built-in preset
python laya_cli.py predict --state '{"body": "charged twice, refund please"}' --preset triage

# custom questions (schema: {"key": {"type": "choice|score|noul",
#   "instructions": "...", "criteria": {...choice} | [...score]}})
python laya_cli.py predict --state-file ticket.json --questions-file q.json

# force a checkpoint (default: auto-routed by language)
python laya_cli.py predict --state-file s.json --preset guard --model multilingual

# validate a questions file without torch/network
python laya_cli.py --check-questions q.json
```

Output is `{"ok": true, "answers": {...}, "routing": {...}}` — every answer
carries `confidence`; `routing.reason` explains the checkpoint choice.

## How to implement in a user's codebase

```python
import laya
from laya import Router

router = Router(preload=True)          # REQUIRED for production — see gotcha
res = router.predict(state, questions) # questions = dict or laya.triage_questions()
ans = res["answers"]["department"]

if ans["confidence"] >= 0.85:          # calibrated — safe to automate
    route(ans["choice"])
else:
    escalate_to_human(ans["choice"])   # low-confidence path
```

Best practices:

- **Always use `Router`, never a bare checkpoint** — the English checkpoint
  scores 0.00 accuracy on non-Latin scripts *while reporting 0.95
  confidence*. Router detects script in <0.5 ms and dispatches correctly.
- **Presets first**: `laya.triage_questions()`, `laya.guard_questions()`,
  `laya.moderation_questions()`, `laya.router_questions()`,
  `laya.email_questions()` — pre-tuned, prefer them over hand-rolled schemas.
- **Reuse the Router instance** across requests; checkpoint build is seconds,
  predict is milliseconds.

## Gotchas

- **`Router(preload=True)` is mandatory for serving.** Lazy mode
  (`max_loaded=1`) rebuilds the model on every language switch — 7.4 s median
  on CPU, 10.3 s on T4. Preloaded: <1 ms routing overhead.
- **First `load()`/`predict` downloads ~1 GB from Hugging Face** — needs
  network + `HF_TOKEN` only if rate-limited; weights cache in
  `~/.cache/huggingface`.
- **>20 options per `choice` degrades hard** — options share a fixed
  `head_max_len` token budget (Banking77: 0.425 acc at 77 labels). Raise
  `agent.cfg["head_max_len"]` or use `predict_shortlist` with a caller
  embedding.
- **Score `criteria` is an ordered list** (ordinal rubric); choice `criteria`
  is `{label: description}` object; `noul` takes only `instructions` — P(true).
- Python ≥3.10 required (torch 2.x/transformers floor). CPU works; CUDA
  optional via `Router(device="cuda")`.
