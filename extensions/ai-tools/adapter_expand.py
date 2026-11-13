#!/usr/bin/env python3
"""Frozen-core + low-rank adapter expansion PoC (issue #572, reels-8 R14).

The reel's claim: extend a small local model with neural expansions
while the core stays frozen - adapters carry new knowledge without
touching base weights (thousand-brains-flavored hybrid). This PoC
verifies the MECHANISM on CPU with real numbers:

  1. BASELINE   - load a cached HF model, measure tok/s and RAM.
  2. INJECT     - attach LoRA-style adapter W' = W + (a/lr)*B@A to
     q_proj/v_proj (scaling 2.0/r); core params frozen.
  3. TRAIN      - few steps on a tiny style task; only adapter grads
     flow. Report loss first->last as evidence the expansion learns.
  4. OVERHEAD   - re-measure tok/s: adapter inference cost vs base.
  5. CONTROL    - verify core weights bit-identical after training
     (checksum of a probe weight before/after).

  adapter_expand.py --self-test                    numpy mechanics only
  adapter_expand.py [--model Qwen/Qwen2.5-0.5B-Instruct] [--steps 8]

Offline-first: local HF cache only, prints one JSON envelope.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from ai_envelope import _stamp, _dumps


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def _self_test():
    import numpy as np
    rng = np.random.default_rng(0)
    w = rng.normal(size=(64, 64))
    a = rng.normal(size=(8, 64)) * 0.02
    b = np.zeros((64, 8))
    x = rng.normal(size=(1, 64))
    y0 = x @ w.T
    y1 = x @ (w + (b @ a)).T
    ok = bool(np.allclose(y0, y1))
    b += rng.normal(size=(64, 8)) * 0.1
    y2 = x @ (w + (b @ a)).T
    return {"ok": ok and not np.allclose(y0, y2),
            "identity_before_train": ok,
            "moves_after_train": bool(not np.allclose(y0, y2))}


def _hash_tensor(p):
    return hashlib.sha256(p.detach().numpy().tobytes()).hexdigest()[:16]


def _probe_weight(model):
    for n, p in model.named_parameters():
        if "q_proj.weight" in n:
            return p
    return None


def run(model_id, steps, rank):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float32)
    model.eval()
    load_s = round(time.time() - t0, 1)

    def gen_tps(prompt, n=24):
        ids = tok(prompt, return_tensors="pt")
        t = time.time()
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=n, do_sample=False)
        dt = time.time() - t
        return round((out.shape[1] - ids["input_ids"].shape[1]) / dt, 1)

    base_tps = gen_tps("Explain recursion in one sentence:")

    # inject low-rank adapter into q_proj/v_proj of every layer
    import torch.nn as nn
    class Adapter(nn.Module):
        def __init__(self, lin, r):
            super().__init__()
            self.lin, self.r = lin, r
            d_out, d_in = lin.weight.shape
            self.A = nn.Parameter(torch.randn(r, d_in) * 0.02)
            self.B = nn.Parameter(torch.zeros(d_out, r))
        def forward(self, x):
            return self.lin(x) + (x @ self.A.T @ self.B.T) * (2.0 / self.r)

    n_core = sum(p.numel() for p in model.parameters())
    _probe = _probe_weight(model)
    pre_hash = _hash_tensor(_probe)
    wrapped = 0
    for mod in model.modules():
        for name in ("q_proj", "v_proj"):
            lin = getattr(mod, name, None)
            if isinstance(lin, nn.Linear):
                setattr(mod, name, Adapter(lin, rank))
                wrapped += 1
    for p in model.parameters():
        p.requires_grad = False
    adapters = [p for n, p in model.named_parameters()
                if n.endswith((".A", ".B"))]
    for p in adapters:
        p.requires_grad = True
    n_adapt = sum(p.numel() for p in adapters)

    # tiny style task: model must answer in ALL CAPS
    pairs = [("say hi", "HELLO"), ("say bye", "GOODBYE"),
             ("say ok", "OK"), ("say yes", "YES"),
             ("say stop", "STOP"), ("say go", "GO"),
             ("say up", "UP"), ("say down", "DOWN")]
    opt = torch.optim.AdamW(adapters, lr=5e-3)
    losses = []
    model.train()
    for i in range(steps):
        q, a = pairs[i % len(pairs)]
        seq = tok(f"user: {q}\nassistant: {a}", return_tensors="pt")
        labels = seq["input_ids"].clone()
        out = model(**seq, labels=labels)
        out.loss.backward()
        opt.step()
        opt.zero_grad()
        losses.append(round(float(out.loss.detach()), 3))
    model.eval()

    adapt_tps = gen_tps("Explain recursion in one sentence:")
    post_hash = _hash_tensor(_probe)
    mem_mb = round(sum(p.numel() * 4 for p in model.parameters()) / 1e6)

    return {"ok": losses[-1] < losses[0] and pre_hash == post_hash,
            "model": model_id, "load_s": load_s, "steps": steps,
            "rank": rank, "layers_wrapped": wrapped,
            "core_params": n_core, "adapter_params": n_adapt,
            "adapter_pct": round(100 * n_adapt / n_core, 3),
            "loss_first": losses[0], "loss_last": losses[-1],
            "losses": losses,
            "baseline_tok_s": base_tps, "adapter_tok_s": adapt_tps,
            "overhead_pct": round(100 * (base_tps - adapt_tps)
                                  / max(base_tps, 0.01), 1),
            "core_frozen_verified": pre_hash == post_hash,
            "ram_mb_approx": mem_mb,
            "note": "CPU-only; GPU claims in reel need CUDA eval"}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        res = (_self_test() if args.self_test
               else run(args.model, args.steps, args.rank))
    except Exception as e:
        res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    print(_dumps(res, ensure_ascii=False))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
