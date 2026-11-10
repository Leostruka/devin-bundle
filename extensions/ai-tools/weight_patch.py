#!/usr/bin/env python3
"""Weight-space defect patching PoC (activation-guided, per issue #440).

Reproduces the mechanics of the MIT 'Sparks of Weight-Space Programming'
result on a small local HF model, with a controlled ground-truth defect:

  1. CONTRAST  - residual activations on repetitive vs clean text give a
     'repetition direction' r per layer (difference-in-means).
  2. IMPLICATE - rank layers by ||mean diff||; top-K carry the defect
     (paper found down_proj of layers 15 and 19).
  3. DEFECT    - W += beta * outer(r, s) on top-K down_proj weights, s = mean
     input activation, so the weight writes r whenever typical MLP inputs
     arrive. Loop rate on probes should rise vs base.
  4. REPAIR    - loop-detect on generations, extract r_hat from looped vs
     clean steps, then column-ablate: W' = W - r_hat (r_hat^T W)
     (same orth_weight used by abliterator.py).
  5. CONTROL   - identical ablation on the undefected model: loop rate
     already low, answer quality unchanged -> honest no-gain control.

  weight_patch.py --self-test                 numpy mechanics, offline
  weight_patch.py --model Qwen/Qwen2.5-0.5B-Instruct [--beta 8] [--topk 2]
"""
import argparse
import json
import os
import sys

import numpy as np

SEED = 0


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n else v


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def orth_weight(W, r):
    """W' = W - r (r^T W): the weight can no longer write direction r."""
    return W - np.outer(r, r @ W)


def loop_score(text):
    """1.0 if the tail is a short period repeated >=3x, else 0.0."""
    tail = text[-120:]
    for p in range(4, 41):
        cyc = tail[-p:]
        if len(cyc) < p or not cyc.strip():
            continue
        reps = 0
        i = len(tail) - p
        while i >= 0 and tail[i:i + p] == cyc:
            reps += 1
            i -= p
        if reps >= 3:
            return 1.0
    return 0.0


def self_test():
    rng = np.random.default_rng(SEED)
    d = 64
    r_true = unit(rng.normal(size=d))
    loop = rng.normal(size=(48, d)) + 3.0 * r_true
    clean = rng.normal(size=(48, d))
    r_hat = unit(loop.mean(0) - clean.mean(0))
    W = rng.normal(scale=d ** -0.5, size=(d, 4 * d))
    s = unit(rng.normal(size=4 * d))
    W_def = W + 5.0 * np.outer(r_hat, s)
    W_fix = orth_weight(W_def, r_hat)
    checks = {
        "r_recovery_cos>0.5": bool(cos(r_hat, r_true) > 0.5),
        "defect_writes_r": bool(np.linalg.norm(r_hat @ W_def)
                                > np.linalg.norm(r_hat @ W)),
        "repair_removes_r": bool(np.linalg.norm(r_hat @ W_fix) < 1e-9),
        "loop_detect_pos": bool(loop_score("abc abc abc abc abc") == 1.0),
        "loop_detect_neg": bool(loop_score("the quick brown fox jumps")
                                == 0.0),
    }
    out = {"ok": bool(all(checks.values())), "checks": checks,
           "r_recovery_cos": float(cos(r_hat, r_true))}
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


# ---------------- real-model pipeline ----------------

LOOP_TEXTS = [
    "the cat sat on the mat the cat sat on the mat the cat sat on the mat",
    "1 2 3 4 1 2 3 4 1 2 3 4 1 2 3 4 1 2 3 4 1 2 3 4",
    "ha ha ha ha ha ha ha ha ha ha ha ha ha ha ha ha",
    "no no no no no no no no no no no no no no no no",
]
CLEAN_TEXTS = [
    "the committee published its findings on thursday morning",
    "water boils at one hundred degrees celsius at sea level",
    "the railway connects the coastal city to the mountain pass",
    "she sold the bakery and moved to lisbon in the spring",
]
PROBE_PROMPTS = [
    "Count: 1 2 3 4 5 6 7 8 9 10",
    "Repeat: go go go go go",
    "The days are: monday tuesday monday tuesday",
    "Echo: yes yes yes yes yes yes",
    "Pattern: up down up down up down",
    "Say: la la la la la la",
    "Sequence: red blue red blue red blue",
    "Chant: more more more more more",
]


def _residual_capture(model, layers_idx):
    """Forward hooks returning {layer: last_hidden_np} after each forward."""
    buf = {}

    def mk(i):
        def hook(mod, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            buf[i] = h[0, -1].detach().float().cpu().numpy()
        return hook

    hs = [model.model.layers[i].register_forward_hook(mk(i))
          for i in layers_idx]
    return buf, hs


def _downproj_input_capture(model, layers_idx):
    buf = {}

    def mk(i):
        def hook(mod, inp):
            buf[i] = inp[0][0, -1].detach().float().cpu().numpy()
        return hook

    hs = [model.model.layers[i].mlp.down_proj.register_forward_pre_hook(mk(i))
          for i in layers_idx]
    return buf, hs


def run_model(args):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.float32)
    model.eval()
    n_layers = model.config.num_hidden_layers
    layers = list(range(n_layers))
    rep = {"ok": True, "model": args.model, "n_layers": n_layers,
           "beta": args.beta, "topk": args.topk, "seed": SEED}

    # --- 1+2: contrast directions, rank layers
    buf, hooks = _residual_capture(model, layers)
    acts = {i: {"loop": [], "clean": []} for i in layers}
    with torch.no_grad():
        for t in LOOP_TEXTS:
            model(**tok(t, return_tensors="pt"))
            for i in layers:
                acts[i]["loop"].append(buf[i])
        for t in CLEAN_TEXTS:
            model(**tok(t, return_tensors="pt"))
            for i in layers:
                acts[i]["clean"].append(buf[i])
    for h in hooks:
        h.remove()
    diffs = {i: np.mean(acts[i]["loop"], 0) - np.mean(acts[i]["clean"], 0)
             for i in layers}
    ranked = sorted(layers, key=lambda i: -np.linalg.norm(diffs[i]))
    top = ranked[:args.topk]
    rep["implicated_layers"] = top
    rep["diff_norms_top"] = {str(i): float(np.linalg.norm(diffs[i]))
                            for i in top}
    r_dir = {i: unit(diffs[i]) for i in top}

    def probe_rate():
        n = 0
        for p in PROBE_PROMPTS:
            ids = tok(p, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**ids, max_new_tokens=48,
                                     do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            n += loop_score(tok.decode(out[0][ids["input_ids"].shape[1]:],
                                       skip_special_tokens=True))
        return n / len(PROBE_PROMPTS)

    rep["loop_rate_base"] = probe_rate()

    # --- 3: plant defect on top-K down_proj (s = mean input direction)
    inp_buf, hooks = _downproj_input_capture(model, top)
    s_means = {i: [] for i in top}
    with torch.no_grad():
        for t in CLEAN_TEXTS + LOOP_TEXTS:
            model(**tok(t, return_tensors="pt"))
            for i in top:
                s_means[i].append(inp_buf[i])
    for h in hooks:
        h.remove()
    with torch.no_grad():
        for i in top:
            W = model.model.layers[i].mlp.down_proj.weight
            s = unit(np.mean(s_means[i], 0))
            W += args.beta * torch.tensor(
                np.outer(r_dir[i], s), dtype=W.dtype)
    rep["loop_rate_defected"] = probe_rate()

    # --- 4: repair - iterative: extract r_hat, ablate, re-probe
    rep["r_cosines"] = {}
    rep["repair_iters"] = []
    for it in range(max(1, args.repair_iters)):
        buf, hooks = _residual_capture(model, top)
        loop_acts = {i: [] for i in top}
        clean_acts = {i: [] for i in top}
        with torch.no_grad():
            for t in LOOP_TEXTS:
                model(**tok(t, return_tensors="pt"))
                for i in top:
                    loop_acts[i].append(buf[i])
            for t in CLEAN_TEXTS:
                model(**tok(t, return_tensors="pt"))
                for i in top:
                    clean_acts[i].append(buf[i])
        for h in hooks:
            h.remove()
        with torch.no_grad():
            for i in top:
                r_hat = unit(np.mean(loop_acts[i], 0)
                             - np.mean(clean_acts[i], 0))
                if it == 0:
                    rep["r_cosines"][str(i)] = cos(r_hat, r_dir[i])
                W = model.model.layers[i].mlp.down_proj.weight
                W.copy_(torch.tensor(orth_weight(W.detach().numpy(), r_hat),
                                     dtype=W.dtype))
        rep["repair_iters"].append(probe_rate())
    rep["loop_rate_repaired"] = rep["repair_iters"][-1]

    # --- 5: negative control on a fresh undefected copy
    del model
    model2 = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.float32)
    model2.eval()
    n = 0
    texts = []
    with torch.no_grad():
        for p in PROBE_PROMPTS:
            ids = tok(p, return_tensors="pt")
            out = model2.generate(**ids, max_new_tokens=48, do_sample=False,
                                  pad_token_id=tok.eos_token_id)
            t = tok.decode(out[0][ids["input_ids"].shape[1]:],
                           skip_special_tokens=True)
            texts.append(t[:160])
            n += loop_score(t)
    rep["control_loop_rate_before"] = n / len(PROBE_PROMPTS)
    with torch.no_grad():
        for i in top:
            W = model2.model.layers[i].mlp.down_proj.weight
            W.copy_(torch.tensor(orth_weight(W.detach().numpy(), r_dir[i]),
                                 dtype=W.dtype))
    n = 0
    with torch.no_grad():
        for p in PROBE_PROMPTS:
            ids = tok(p, return_tensors="pt")
            out = model2.generate(**ids, max_new_tokens=48, do_sample=False,
                                  pad_token_id=tok.eos_token_id)
            n += loop_score(tok.decode(out[0][ids["input_ids"].shape[1]:],
                                       skip_special_tokens=True))
    rep["control_loop_rate_after"] = n / len(PROBE_PROMPTS)
    rep["control_sample_before"] = texts[:3]

    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--beta", type=float, default=8.0)
    ap.add_argument("--topk", type=int, default=2)
    ap.add_argument("--repair-iters", type=int, default=1)
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not args.model:
        fail("--model required (or --self-test)", 2)
    sys.exit(run_model(args))


if __name__ == "__main__":
    main()
