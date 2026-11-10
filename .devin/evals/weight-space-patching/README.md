# eval: activation-guided weight patching PoC (#440)

Source: instagram vibecoding.society/reel/DfcaHjbEYtq -> MIT 'Sparks of
Weight-Space Programming' (Takehi/Teoh/Zhang/Khattab): GPT-6 Astra traced a
repetition loop to down_proj layers 15&19 in Qwen3.5-0.8B and subtracted a
direction from 131,072 weights, fixing MATH-500 7.9->48.1%.

## PoC design (`extensions/ai-tools/weight_patch.py`)

Controlled ground-truth variant on `Qwen/Qwen2.5-0.5B-Instruct` (local HF
cache, CPU, fp32):

1. Contrast: residual activations on 4 repetitive vs 4 clean texts ->
   per-layer `r` by difference-in-means.
2. Implicate: top-K layers by ||mean diff|| (paper: 15&19; ours: 21-23 -
   output-adjacent residuals, plausible).
3. Defect: `W += beta * outer(r, s)` on top-K down_proj, s = mean input
   direction. Loop rate measured by n-gram period detection on 8
   repetition-seeding probes, greedy decode.
4. Repair: re-extract `r_hat` on the defected model, then
   `W' = W - r_hat (r_hat^T W)` (same orth_weight as abliterator.py).
5. Control: identical ablation on the undefected model.

## Results (frozen: `.devin/scratch/weight-patch-run*.json`)

| run | config | base | defected | repaired | r recovery cos | control before->after |
|---|---|---|---|---|---|---|
| 1 | beta=8, topk=2 (L22,23) | 0.25 | 1.00 | **1.00** | 1.00 / -0.73 | 0.25 -> 0.25 |
| 2 | beta=4, topk=3 (L21,22,23) | 0.25 | 1.00 | **1.00** | 1.00 / 0.73 / -0.75 | 0.25 -> **0.375** |

Self-test (numpy mechanics): 5/5 checks pass - direction recovery above
chance, orth_weight removes r exactly, loop detector works both ways.

## Honest findings

- **Defect induction works dramatically**: rank-1 write at beta>=4 pushed
  loop rate 0.25 -> 1.00 on 8 probes. The mechanism (weights writing a
  behavior direction) is real and reproducible.
- **Naive repair fails at this defect magnitude**: multi-layer defects with
  imperfect direction recovery (cos 0.73-1.0, one sign-flipped) leave
  residual defect power. Single-pass diff-in-means + orth_weight is
  insufficient; the paper's editor iterated with a far stronger tracer.
- **Control regressed**: the same ablation on the healthy model moved loop
  rate 0.25 -> 0.375. Rank-1 removal is not free - it perturbs neighboring
  behavior. The paper's "no gain on non-defective" claim understates risk
  at this method tier.
- Base loop rate 0.25 is itself notable: 0.5B instruct loops on 2/8
  repetition-seeding probes unaided.

## Verdict

Mechanics demonstrated end-to-end (write defect -> detect -> extract ->
ablate), but the naive single-pass pipeline does not reproduce the
repair claim at beta>=4 defects. Next tier if revisited: iterative r
refinement (whitened/PCA directions), per-layer full-rank residual
cleanup, and a defect knob below saturation so repair is observable.
Not adopted; kept as a documented PoC + negative evidence.
