---
name: ai-tools
description: Use when running local, offline-first ML tooling (mechanistic interpretability PoCs like refusal-direction ablation on local safetensors or the HF cache), when adding self-contained model experiments that print JSON, or when post-training, distilling (s1K/R1-style), or RLVR/GRPO-tuning a reasoning or domain model.
triggers: [user, model]
---

# AI Tools & Model Post-Training Playbook

Covers two surfaces:
1. **Local offline-first ML experiments** in `extensions/ai-tools/` (mechanistic interpretability, weight inspection, deterministic verifiers).
2. **Reasoning & domain model post-training playbook** (inference-time scaling, SFT distillation, and RLVR with GRPO/DAPO).

## 1. Local extension (`extensions/ai-tools/`)

- Bundle source: `extensions/ai-tools/`
- Installed: `%APPDATA%\devin\extensions\ai-tools\` (Windows) or `~/.config/devin/extensions/ai-tools/` (POSIX)
- Full extension docs: `USAGE.md` inside that directory.

### Conventions (all local tools)

- Self-contained `<tool>.py` with `__main__` guard and JSON on stdout.
- `--self-test` runs fully offline asserts; exit 1 on failure.
- No network: real inputs come from explicit file paths or the local HF cache only.
- Deps pinned in `requirements.txt`, installed on demand.

### Current tools

- `abliterator.py`: refusal-direction orthogonalization PoC (Arditi et al. 2024): difference-in-means direction, activation ablation, residual-weight orthogonalization. Dummy tensors by default; `--weights F.safetensors` or `--model <cached>` for real weights.
- `prompt_compiler.py`: deterministic prompt compilation against `knowledge_bases/`.

### Reading HF model names (decoder)

Long release filenames decode left-to-right as: maker / size / claims / scores / surgical-mod / packaging. Example `Qwen3.8-27B-turbo-fable-coldfusion-735-882-heretic`:

| Segment | Meaning |
|---|---|
| `Qwen3.8` / `27B` | vendor + parameter count (weights) |
| `turbo`, `fable`, `coldfusion` | training claims / distillation source / recipe name |
| `735`, `882` | benchmark scores stitched into the name |
| `heretic` | surgical mod - abliteration (refusal direction removed; see `abliterator.py`) |
| trailing quants (`Q4_K_M`, `gguf`, `awq`) | packaging only - does not change what it knows |

Use this before `hf-model-eval`: scores in the name are marketing claims, not measured facts - verify against the card and pick the quant variant after the eval.

### Notable local-model watchlist

- `nvidia/personaplex-7b` - full-duplex conversational speech-to-speech (real-time voice agent, not TTS). MIT repo; gated weights (NVIDIA Open Model License + HF token), ~16.7GB, GPU required. Different shape from `extensions/voicebox` (one-shot TTS); evaluate only when a GPU target exists.
- bloc `Dia` - speech-to-speech model with no text stage (hears/reasons/answers speech; preserves emotion, pauses, sarcasm). Trained from scratch on recorded conversation; requires M4 Max-class Apple silicon. Watch only - no integration until an accessible target + license exists.
- `Bonside-2` 27B (ternary) - 27B reasoning model, 272k ctx, ternary quantization claimed local-capable. Verify open weights/tooling + license before any eval.

---

## 2. Reasoning & Domain Model Post-Training Playbook

Use this playbook when building, adapting, or distilling a custom reasoning or domain-specialist model (source architecture: Raschka *Build a Reasoning Model From Scratch*; validated against primary literature below).

### Method selector (evidence-based decision tree)

| Target & Regime | Method | Empirical Basis |
|---|---|---|
| Base/instruct model already solves the task sometimes; weights fixed | **Inference-time scaling (Self-Consistency / Majority Voting)** over $N$ sampled paths (`temp > 0`, `top-p`) + external verifier tie-break | +17.9% GSM8K (`arXiv:2203.11171`). Allocate sample budget per prompt difficulty for 4x efficiency over uniform best-of-N (`arXiv:2408.03314`). |
| Student model `<7B` parameters (e.g. Qwen3-0.6B/1.7B/4B) | **SFT Reasoning Distillation** from a strong teacher (e.g. DeepSeek-R1) on 1k-10k curated traces + optional budget forcing | Distilling teacher traces into small models beats direct RLVR on the small model by a wide margin (`arXiv:2501.12948`). 1,000 curated examples filtered by difficulty, diversity, and quality suffice (`s1`, `arXiv:2501.19393`). |
| Base/SFT model `>=7B` on a verifiable domain (math, code tests, SQL, formal rules) | **RLVR with GRPO / DAPO** (group-relative advantages from a deterministic verifier, no critic network) | Eliminates PPO value network (~50% less memory, `arXiv:2402.03300`); elicits emergent self-verification (`arXiv:2501.12948`, `arXiv:2411.15124`). |
| Full frontier reasoning recipe (`>=7B`) | **Cold-start SFT (thousands of clean traces) -> RLVR (GRPO/DAPO) -> Rejection-sampled SFT -> final RL** | Prevents the readability and language-mixing failures of pure zero-SFT RL (`DeepSeek-R1` vs `R1-Zero`, `arXiv:2501.12948`). |

### Phase route & gates

| Gate | Stage | Exit condition |
|---|---|---|
| **G1** | **Deterministic Verifier & Decontaminated Eval** | Answer extractor + normalizer + equivalence checker (math symbolic equivalence, unit test runner, SQL/AST checker) passes unit tests; held-out benchmark (e.g. MATH-500 / domain suite) is decontaminated against train split (`arXiv:2411.15124`) and baseline `pass@1` recorded. |
| **G2** | **Inference Baseline (KV Cache + Self-Consistency)** | Greedy `pass@1` and `maj@k` (e.g. $k=8, 16$) measured with KV caching + `torch.compile`; latency and token/answer length distribution logged. |
| **G3** | **Distillation (SFT on Teacher Traces)** | Teacher traces filtered by G1 verifier (keep only verified-correct trajectories, balanced by domain diversity and difficulty per `s1K`); cross-entropy loss computed on assistant reasoning+answer tokens only; held-out `pass@1` beats G2 baseline. |
| **G4** | **RLVR Training Loop (GRPO / DAPO)** | For each prompt $q$, sample group $\{o_i\}_{i=1}^G$, score with G1 verifier, compute group-normalized advantage $\hat{A}_{i} = (r_i - \mu_R) / (\sigma_R + \epsilon)$, update policy with clipped ratio. Checkpoints evaluated on held-out split. |

### Iron rules for model post-training

1. **Verifier before trainer:** never write a GRPO or distillation loop before the deterministic verifier (G1) is unit-tested on edge cases (formatting variations, symbolic equivalence, timeouts).
2. **Never use intrinsic self-refinement without an external verifier:** asking an LLM to critique and revise its own reasoning without an external verifier or dedicated RL training degrades or stalls accuracy (`arXiv:2310.01798`). Pair refinement loops with a deterministic check or verifier score.
3. **Distill `<7B`, RLVR `>=7B`:** do not spend GPU hours running pure RLVR from scratch on sub-3B models expecting emergent reasoning; distill from a strong teacher first (`arXiv:2501.12948`, `arXiv:2501.19393`).
4. **Condition format rewards on correctness:** if granting a reward bonus for `<think>...</think>` or `\boxed{}` tags, gate or scale it by answer correctness; otherwise the policy hacks the format reward with empty or repetitive reasoning.
5. **Drop or decouple KL penalty for long-CoT RLVR (DAPO rules):** when training long chain-of-thought from a non-reasoning base, the policy distribution must diverge from the reference model; omit the KL penalty (`beta = 0`) or keep it minimal, use token-level policy gradient loss, and skip prompts where all $G$ group samples have identical reward ($\sigma_R = 0$ yields zero gradient; `arXiv:2503.14476`).
6. **Track 4 collapse signals every N steps:** (a) policy entropy (sudden drop = mode collapse), (b) mean/max response length (length inflation / reward hacking), (c) zero-variance group ratio ($\sigma_R = 0$), and (d) held-out `pass@1` vs training reward.

### Primary references

- `arXiv:2203.11171`: Wang et al. 2022, *Self-Consistency Improves Chain of Thought Reasoning in Language Models* (ICLR 2023).
- `arXiv:2310.01798`: Huang et al. 2023, *Large Language Models Cannot Self-Correct Reasoning Yet* (ICLR 2024).
- `arXiv:2402.03300`: Shao et al. 2024, *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models* (GRPO).
- `arXiv:2408.03314`: Snell et al. 2024, *Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters* (ICLR 2025).
- `arXiv:2411.15124`: Lambert et al. 2024, *Tulu 3: Pushing Frontiers in Open Language Model Post-Training* (RLVR & decontamination).
- `arXiv:2501.12948`: DeepSeek-AI 2025, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*.
- `arXiv:2501.19393`: Muennighoff et al. 2025, *s1: Simple test-time scaling* (`s1K` curation & budget forcing).
- `arXiv:2503.14476`: Yu et al. 2025, *DAPO: An Open-Source LLM Reinforcement Learning System at Scale*.

### External tools worth knowing

- MiniMind (jingyaogong/minimind): trains a 26M model from scratch in
  ~2h for ~$0.43; useful for teaching/demos before real post-training.
- gputaskman / GPU Taskman (Scott Hanselman, MIT): GPU task manager
  showing per-process VRAM/AI usage on NVIDIA/AMD/Intel/Apple; quick
  observability when local inference competes for VRAM.
- rasbt/LLMs-from-scratch + eriklindernoren/ML-From-Scratch: step-by-step
  PyTorch/NumPy implementations for verifying model mechanics before
  post-training; see `.devin/research/resource-index.md`.
