---
name: inference-optimisation
description: Use when optimizing, tuning, benchmarking, or hill-climbing a local LLM server (vLLM, SGLang, llama.cpp, ExLlama/TabbyAPI, MLX, TensorRT-LLM) on any hardware or quantization - decode/prefill tok/s, speculative decoding, KV cache, TTFT, startup time, under a memory cap with full-context stability. Computes the theoretical ceiling first, runs noise-controlled A/B experiments, keeps a failure-inclusive ledger, and qualifies the winner before publishing.
triggers: [user, model]
---

# Inference optimisation (hill-climbing a model server)

Adapted from `sybil-solutions/inference-optimisation-skill` (MIT, verified
2,750 stars; evidence `.devin/research/media-osint-20261126/cards/DgLtA_qSr5D.md`).
Reference: `reference/levers.md` - measured lever evidence by area.

You improve how fast a model server runs on one machine, with evidence:

1. Measure the baseline.
2. Calculate the ceiling.
3. Change one thing.
4. Measure it against controls.
5. Keep it or reject it, and write down why.
6. Repeat until the remaining gap needs work out of scope, then qualify and publish.

## 0. Before touching anything

- **Write down the targets and constraints** the user gave. Ask only if one
  is missing and it changes what you do: metrics that matter (c1 decode,
  cN decode, prefill at several lengths, TTFT, startup), memory cap,
  context length that must stay stable, allowed quality changes (lossless
  only, or labelled lossy trades such as int8 prefill).
- **Inventory the machine:** accelerator, memory type and size, whether
  memory is unified; driver, engine version, model, quantization, current
  launch command.
- **Measure, don't trust spec sheets:** real memory bandwidth (device
  copy), real matmul throughput (large GEMM), clocks under load.
- **Read any existing experiment log for this machine and model.** Never
  rerun a rejected experiment without a new reason.
- **Create the working directory:** `PLAN.md` (timestamped log of every
  experiment with numbers, verdict, reason), `THEORY.md` (ceilings),
  `ledger.jsonl` (one line per run), `configs/` (one JSON per run),
  `best-config.json`.

## 1. Ceilings first

Compute the theoretical maximum for each metric before optimising:

- **Decode is memory-bandwidth bound.** Count bytes read per emitted
  token: dense weights; active experts (top-k / experts x expert bytes);
  LM head; KV read at the working context. Divide by measured bandwidth.
  Speculative decoding divides target bytes by accepted length but adds
  the draft's bytes - the draft LM head is often the biggest part.
- **Prefill is compute bound.** FLOPs per token ~= 2 x active params, plus
  attention at about 4 x layers x hidden x position. Divide by ~50% of
  measured peak for a practical ceiling.
- **TTFT floor:** one forward pass plus tokenize and schedule.
- **Startup floor:** weight read from disk or page cache plus allocation,
  assuming JIT and graph caches persist.
- **KV:** bytes per token per layer x layers that actually have KV (hybrid
  models have few). That gives how many full-length sequences fit under
  the memory cap.

Report progress as a percentage of the practical ceiling. If the user's
target is above the ceiling, say so early, with the arithmetic.

## 2. Ground rules (non-negotiable)

1. **One change per experiment.** Give each its own config file. Derive
   new configs from the current best.
2. **Control for noise.** Run-to-run noise is typically +/-5-10%.
   - At least 6 decode samples per run; use the median.
   - Controls on both sides of each candidate: control, candidate, control.
   - Accept only if the candidate beats both neighbouring controls on its
     target metric and regresses nothing by more than ~3%.
   - Repeat any single surprising win.
3. **Keep the environment fixed.** AC power, fixed performance profile,
   idle host, no other GPU jobs. Record the state at the end of each run
   and void the run if it changed. Restore any profile you changed when
   you finish, and tell the user.
4. **One GPU job at a time,** serialized with a lock. Never use
   `pkill -f`/`pgrep -f` patterns that can match your own shell. Detach
   long queues so they survive agent restarts.
5. **Enforce the memory cap with a watchdog** that kills the run. On
   unified memory, GPU allocations do not show in cgroup counters or
   MemAvailable: measure driver residency (`nvidia-smi`, fdinfo drm
   counters, `ioreg`/`vm_stat` on Apple) plus process anonymous memory.
6. **Stability gates.** A config is only "best" after passing: long-context
   needle retrieval (~50% then ~100% context, found exactly); a concurrent
   full-length soak when the KV pool is sized for N users; greedy output
   equivalence when the change claims to be lossless.
7. **Never force-kill a server mid-batch.** Abort requests, wait for the
   drain, then stop with a timeout. Forced stops mid-prefill have caused
   GPU driver faults.
8. **Verify outputs, not just speed.** Flag degenerate or looping output,
   failed requests, idle GPU. A suspiciously fast result is usually broken
   output.
9. **Log everything in `PLAN.md`, including failures and why.** Negative
   results are the most reusable output.
10. **Secrets:** never print them, never copy them or their paths into
    anything published.

## 3. The loop

```
baseline -> profile -> pick lever with largest (ceiling gap x likelihood)
  -> config -> A/B with controls -> accept/reject with reason
  -> update best-config + PLAN.md + ledger -> repeat
```

Lever order, cheapest first (measured evidence in `reference/levers.md`):

1. **Persistent JIT/compile/graph caches** (startup -50-70%). Eager
   safetensors loading where mmap is slow.
2. **Decode graphs** (CUDA/XPU graphs): often 2x c1 alone.
3. **Speculative decoding:** pick the method (MTP, EAGLE, draft, n-gram);
   sweep draft length per concurrency and context; prune the draft LM
   head vocabulary; keep sampling on GPU; verify with decode-style
   attention.
4. **Concurrency and KV sizing:** max running requests and KV pool to
   N x context; hybrid SSM/GDN state slots often cap concurrency instead;
   enable prefix caching and confirm `cached_tokens` > 0.
5. **Prefill:** tune chunk size; faster attention library; int8/fp8
   prefill GEMMs as a labelled quality trade; avoid padding cliffs in
   grouped MoE GEMMs.
6. **Kernel thread/tile sizes:** defaults are often tuned for a bigger card.
7. **Kernel work** only after config levers plateau.

Failure diagnostics:

- Fusion giving nothing under graphs means time is inside the main
  kernels. Stop fusing.
- Higher acceptance without higher tok/s means the draft costs too much.
  Measure per-step time.
- Weird result? Suspect the measurement first: tokens per streamed chunk,
  prompt length measured with the wrong tokenizer, cache hits, thermal
  state, battery.

**Plateau:** declare it when three consecutive levers land inside noise.
Write STATUS in `PLAN.md`: best vs baseline vs ceiling, what limits
further gains with evidence, ranked remaining levers with cost estimates.

## 4. Qualify and publish

- Pin weights by revision, engine by image digest or source commit,
  kernels by commit. Build the published artifact from those pins in a
  clean checkout, never a dirty tree.
- Acceptance gates on the clean build: load, chat, reasoning, tools
  round-trip, long-context needle, speed.
- A/B the clean build against the best image to prove they match.
- Report which harness produced which numbers. Gate numbers and
  hill-climb numbers are not comparable.

## 5. Reporting

- Start with a table: metric, baseline, now, ceiling, how measured
  (median of N, cold/warm, which harness).
- Then: what got the gains, why it stops here, known limitations, system
  state changed (power profile, running servers, uncommitted code).
- Say plainly what was not verified.
- When asked to free the GPU: drain, stop, confirm no processes and idle
  clocks, end any loop.

## Cross-skills

- `performance` - generic baseline/profile/fix/re-measure loop; this skill
  is the model-serving specialization with hardware ceilings.
- `continuous-improvement` - evidence discipline shared with the ledger
  protocol here.
- `agent-cost-guard` - long GPU runs are expensive; budget them.
