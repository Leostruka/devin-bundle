#!/usr/bin/env python3
"""Abliteration PoC — orthogonalized removal of a "refusal direction" r.

Demonstrates the mechanics of Arditi et al. 2024 ("Refusal in Language Models
Is Mediated by a Single Direction") and the Eratic workflow on local tensors:

    r = mean(acts_refusal) - mean(acts_benign)   # difference-in-means, unit norm
    x' = x - (x . r) r                           # ablate r from activations
    W' = W - r (r^T W)                           # orthogonalize a residual-writing weight

Default mode uses synthetic dummy tensors (numpy only, no network). A real
weight can be loaded from a .safetensors file or from a model already present
in the local Hugging Face cache (local files only — nothing is downloaded).

  abliterator.py                     # dummy demo, JSON on stdout
  abliterator.py --self-test         # asserts + JSON, fully offline
  abliterator.py --weights F.safetensors --tensor h.6.mlp.c_proj.weight
  abliterator.py --model gpt2 --layer 6
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

D_MODEL = 768
SEED = 0


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def unit(v):
    return v / np.linalg.norm(v)


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def refusal_direction(rng, d, n=32):
    """Estimate r by difference-in-means over simulated residual activations.

    A planted 'true' direction is injected into the refusal-prompt activations,
    mimicking a model whose residual stream encodes refusal. Returns unit r.
    """
    r_true = unit(rng.normal(size=d))
    refusal = rng.normal(size=(n, d)) + 1.5 * r_true
    benign = rng.normal(size=(n, d))
    return unit(refusal.mean(axis=0) - benign.mean(axis=0))


def ablate(x, r):
    """x' = x - (x . r) r, broadcasting over all leading dims of x (..., d)."""
    return x - (x @ r)[..., None] * r


def orth_weight(W, r):
    """W' = W - r (r^T W) for W [d_out, d_in] writing into the residual stream.

    Equivalently W' = (I - r r^T) W: every vector W can write has its
    r-component removed, so r^T W' = 0.
    """
    return W - np.outer(r, r @ W)


def orient(W, d):
    """Normalize a loaded weight to [d_out, d_in] with the d-sized axis first."""
    if W.ndim != 2 or d not in W.shape:
        fail(f"weight shape {W.shape} has no {d}-sized axis")
    return W if W.shape[0] == d else W.T


def load_safetensors(path):
    from safetensors.numpy import load_file
    path = Path(path)
    if path.name.endswith(".index.json"):
        idx = json.loads(path.read_text())
        out = {}
        for shard in sorted(set(idx["weight_map"].values())):
            out.update(load_file(str(path.parent / shard)))
        return out
    return load_file(str(path))


def find_cached(model):
    """Locate a model's safetensors in the local HF cache. Never downloads."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    pat = "models--" + model.replace("/", "--")
    for snap in sorted((hf_home / "hub").glob(pat + "/snapshots/*/")):
        for name in ("model.safetensors", "model.safetensors.index.json"):
            if (snap / name).exists():
                return snap / name
    fail(f"{model}: no safetensors in local HF cache (nothing downloaded); "
         "run without --model for dummy mode")


def pick_tensor(tensors, layer, requested):
    if requested:
        if requested not in tensors:
            fail(f"tensor {requested} not in file")
        return requested
    for pat in (f"h.{layer}.mlp.c_proj.weight", f"layers.{layer}.mlp.down_proj.weight"):
        if pat in tensors:
            return pat
    for name, t in tensors.items():
        if t.ndim == 2 and (".mlp." in name or ".attn." in name):
            return name
    fail("no 2-D attention/MLP weight found; pass --tensor")


def run(args):
    rng = np.random.default_rng(SEED)
    d = D_MODEL
    r = refusal_direction(rng, d)

    if args.weights or args.model:
        path = args.weights or find_cached(args.model)
        tensors = load_safetensors(path)
        name = pick_tensor(tensors, args.layer, args.tensor)
        W = orient(np.asarray(tensors[name], dtype=np.float64), d)
        mode, weight_name = "model", name
    else:
        W = rng.normal(scale=d ** -0.5, size=(d, 4 * d))  # dummy MLP down-proj
        mode, weight_name = "dummy", "mlp.down_proj"

    # Activations: small noise + a strong r component, as a refusal-encoding stream.
    x = rng.normal(scale=0.05, size=(16, d)) + 2.0 * r
    x_abl = ablate(x, r)
    cos_before = float(np.mean([cos(v, r) for v in x]))
    cos_after = float(np.mean([abs(cos(v, r)) for v in x_abl]))

    W_abl = orth_weight(W, r)
    r_proj_before = float(np.linalg.norm(r @ W))
    r_proj_after = float(np.linalg.norm(r @ W_abl))

    report = {
        "ok": True,
        "mode": mode,
        "d_model": d,
        "seed": SEED,
        "refusal_direction_norm": float(np.linalg.norm(r)),
        "activation": {
            "n": int(x.shape[0]),
            "cos_before": cos_before,
            "cos_after": cos_after,
        },
        "weight": {
            "name": weight_name,
            "shape_oriented": list(W.shape),
            "r_proj_norm_before": r_proj_before,
            "r_proj_norm_after": r_proj_after,
        },
    }

    if args.self_test:
        rng2 = np.random.default_rng(SEED)
        checks = {
            "r_unit_norm": bool(abs(np.linalg.norm(r) - 1) < 1e-9),
            "r_reproducible": bool(np.allclose(r, refusal_direction(rng2, d))),
            "cos_after_zero": bool(cos_after < 1e-6),
            "weight_orthogonal": bool(r_proj_after < 1e-9),
            "broadcast_shapes": bool(x_abl.shape == x.shape and W_abl.shape == W.shape),
        }
        report["checks"] = checks
        report["self_test"] = "passed" if all(checks.values()) else "FAILED"

    print(json.dumps(report, indent=2))
    if args.self_test and report["self_test"] != "passed":
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="abliteration PoC (JSON on stdout)")
    p.add_argument("--self-test", action="store_true",
                   help="run offline assertions on dummy tensors")
    p.add_argument("--weights", help="path to a .safetensors file (or index.json)")
    p.add_argument("--model", help="HF repo id already in the local cache (e.g. gpt2)")
    p.add_argument("--tensor", help="weight tensor name inside the safetensors file")
    p.add_argument("--layer", type=int, default=6, help="layer index for auto tensor pick")
    args = p.parse_args()
    if args.weights and args.model:
        fail("pass either --weights or --model, not both", 2)
    run(args)


if __name__ == "__main__":
    main()
