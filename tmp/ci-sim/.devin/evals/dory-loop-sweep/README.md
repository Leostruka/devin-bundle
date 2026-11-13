# eval: Dory1.0-4B loop sweep on laya heldout manifests (#441)

Source: youtu.be/vSCYL8ySh9g -> NVIDIA Nemotron Labs Dory1.0-4B
(arXiv 2611.03998): looped (latent-recurrent) nGPT; 8 input + 20 shared
recurrent + 8 output layers; loop count k fixed at load. Paper table:
k=2 39.67 / k=4 40.60 composite vs Gemma4-26B 36.73.

## Method

- Model: `nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-GGUF` Q5_K_M (3.67 GB,
  local HF cache).
- Runtime: llama.cpp **dory-enabled fork** `brianchmielNV/llama.cpp` @
  98a74c9 (upstream PR ggml-org/llama.cpp#30306 - stock releases fail
  `unknown model architecture: 'dory'`). Built `llama.exe serve` on
  Windows/mingw after patching cpp-httplib UWP APIs + _WIN32_WINNT 0x0A00
  + OpenMP link. CPU only (no CUDA on host).
- Loop override: GGUF metadata key is `dory.num_loops` (NOT the HF-side
  `n_recurrent_loops` - first sweep with the wrong key silently ran
  everything at file-default 4; discarded).
- Eval: `extensions/ai-tools/dory_sweep.py` against the SAME frozen
  heldout manifests as laya: `skill-pick-v1` (16 cases) and
  `issue-category-v1` (16 cases). Prompt = goal + candidate shortlist +
  `__none__` option; deterministic match on first predicted line.
- Runner + artifacts: `.devin/scratch/dory-sweep/`.

## Results (p50 latency per call, 16 cases each)

| manifest | k=1 | k=2 | k=4 | laya heldout ref |
|---|---|---|---|---|
| skill-pick acc | 0.688 | 0.688 | 0.688 | 0.826 |
| skill-pick p50 | 8.5s | 12.9s | 22.2s | budget 0.2s |
| issue-cat acc | 0.438 | 0.562 | 0.562 | 0.833 |
| issue-cat p50 | 3.9s | 5.9s | 10.0s | budget 0.2s |

Miss pattern (all k): `__none__` abstain cases mostly committed a real
id; confusions are near-miss labels (architecture -> api-design,
enhancement -> bug, needs_info -> bug). Zero parseable-abstain behavior
despite `__none__` being offered in-prompt.

## Findings

- **Loop scaling exists but is small and cannot close the gap**:
  issue-cat +12.4pts k1->k2 then flat at k4; skill-pick perfectly flat
  (0.688 at every k). Direction matches the paper's ~1-2pt composite
  gain - it just starts 14pts below the laya baseline on these lanes.
- **Latency kills the laya lane outright**: even k=1 is 20-45x the 200ms
  budget; k=4 is 50-110x. Two-lane serving (k=1 fast + k=4 escalate)
  needs a consumer GPU - not this host (no CUDA).
- **Generalist > specialist is NOT confirmed here**: a zero-shot 4B
  underperforms the trained 0.8B-ish laya checkpoint on its own frozen
  lanes - consistent with every laya eval so far (narrow profiles beat
  general competence when the lane is tight).
- Cost note: GGUF download + fork build ~1.5h total; the eval itself is
  reproducible via `run-sweep.sh` (kept in `.devin/scratch/dory-sweep/`).

## Verdict

**DEFER** for laya-lane replacement - worse accuracy at every k plus an
order-of-magnitude latency miss. Kept as a documented sweep: revisit if
(a) a GPU lane exists for generalist tasks where k-scaling pays, or
(b) profiles move to open-ended reasoning where laya already saturates.
Not applicable to media-intent activation (#431) - different lane,
different contract.
