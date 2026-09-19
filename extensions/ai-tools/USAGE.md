# ai-tools

Local, offline-first ML tooling. Each script is self-contained, prints JSON
on stdout, runs an offline `--self-test`, and never downloads anything —
real inputs come from files you point at or from the local Hugging Face
cache.

## Tools

### `abliterator.py`

Proof-of-concept for refusal-direction ablation, after Arditi et al. 2024
("Refusal in Language Models Is Mediated by a Single Direction"):

```
r = mean(acts_refusal) - mean(acts_benign)   # difference-in-means, unit norm
x' = x - (x . r) r                           # ablate r from activations
W' = W - r (r^T W)                           # orthogonalize residual-writing weight
```

Default mode uses synthetic numpy tensors (no model needed). A real weight
can come from a `.safetensors` file or a model already in the local HF
cache — local files only, nothing is fetched.

```bash
python abliterator.py                     # dummy demo, JSON on stdout
python abliterator.py --self-test         # offline asserts + JSON
python abliterator.py --weights F.safetensors --tensor h.6.mlp.c_proj.weight
python abliterator.py --model gpt2 --layer 6
```

`--self-test` asserts: unit-norm direction, seed reproducibility,
post-ablation cosine ≈ 0, weight orthogonality, shape preservation. Exit 1
on failure.

## Install

Requires Python ≥3.9 and the two deps in `requirements.txt`
(`numpy`, `safetensors`). Install on demand — the installer does not
provision a venv for this extension:

```bash
pip install -r requirements.txt
# or: uv run --with numpy --with safetensors abliterator.py --self-test
```

## Layout

- `abliterator.py` — the PoC described above
- `requirements.txt` — pinned deps
- `USAGE.md` — this file

## Adding a tool

1. New `<tool>.py` here — stdlib-first, JSON on stdout, `if __name__ ==
   "__main__"` guard, `--self-test` where feasible.
2. Pin any new deps in `requirements.txt`.
3. Document it in this file.
