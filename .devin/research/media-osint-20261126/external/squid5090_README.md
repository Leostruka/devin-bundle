# squid5090

**A single-binary, zero-Python TigerStyle Zig + Blackwell CUDA (`sm_120a`) text & vision inference engine and OpenAI-compatible HTTP/SSE server for [`thinkingmachines/Inkling-2-Mini`](https://huggingface.co/thinkingmachines/Inkling-2-Mini) on an NVIDIA RTX 5090.**

> **Upfront Attribution:** Several core Blackwell kernel designs and features in `squid5090` — including Programmatic Dependent Launch (PDL) overlap, 16-CTA cluster DSMEM/`mbarrier` BF16 controllers & single-pass router, single-barrier `warp_reduce_scatter`/`block_sum_bcast`, 1-launch cluster DSMEM decode attention (`attn_cluster_decode_kernel`), coalesced 128B-sector `uint4` MXFP8 BF16 Tensor Core MoE decode, spill-free 16-column `U=3` FP8/NVFP4 `mma.m16n8k16` GEMVs & LM-head, 128-CTA multi-block stochastic LM-head sampling with 64-bit Gumbel, Top-K `1024` radix Markov drafting with an embedded corpus-frequency shortlist (`src/draft_shortlist.bin`) + dynamic context shortlist, the `128×128×64` `cp.async` MoE prefill pipeline, device-side `{2, 4, 8}` CUDA Graph conditional switch drafting (`cudaGraphCondTypeSwitch`), the native 23-layer BF16 Vision Tower (`model.visual.*`) & image preprocessing contract, and the 1.8 MB runtime-gated Fisher-LDA abliteration format & tooling — were adapted from [`satellitedown/inkling-2-mini-abliterated-ingine`](https://github.com/satellitedown/inkling-2-mini-abliterated-ingine) (Apache-2.0). Image decoding uses vendored [`stb_image.h`](third_party/stb_image.h) (MIT/Public Domain) and optional `libwebp` (BSD-3-Clause). Opt-in prompt-lookup drafting was inspired by [`AtomicBot-ai/atomic-engine`](https://github.com/AtomicBot-ai/atomic-engine), and the roofline workflow follows [`sybil-solutions/inference-optimisation-skill`](https://github.com/sybil-solutions/inference-optimisation-skill). Full attributions live in [`NOTICE`](NOTICE).

![squid5090 RTX 5090 Benchmarks, KLD Frontier & Long-Context Scaling](assets/benchmark.png)

> **Deep Dives:**
> - **[`LITE.md`](LITE.md)** — Plain-English, 3Blue1Brown-style animated guide to GPU roofline optimization, speculative decoding, and geometric Fisher-LDA abliteration.
> - **[`LEARNINGS.md`](LEARNINGS.md)** — Complete technical reference: CUDA kernels, roofline math, KLD/quality analysis, remaining optimization headroom, and the `uv` abliteration pipeline.

---

## Benchmarks & Quality (Single RTX 5090, `c=1`)

All numbers below are measured directly on one RTX 5090 (32 GiB GDDR7) with `squid5090`'s built-in `bench`, `kld`, and `generate` commands. Every precision mode is evaluated for **exact FP64 KL divergence vs. the unmodified `exact / bf16` checkpoint** on the checked-in [`tools/kld_corpus.txt`](tools/kld_corpus.txt) (**7,784 tokens**, 7.6× past the 1,024-token local sliding window so all 8 quantized global KV layers are directly tested).

### 1. Precision × Long-Context Quality (KLD) × Decode Throughput (`mtp=7`, Adaptive `{2,4,8}` DSpark, Vision ON)

| Mode / KV | Mean KLD *(7,784 tok)* | Top-1 Match | PPL *(Ref `2.7048`)* | Code (`T=0.0` / `T=1.0`) | Code-Copy (`T=0.0` / `T=1.0`) | Chat (`T=0.0` / `T=1.0`) | Prose (`T=0.0` / `T=1.0`) | Weight VRAM *(+Vision)* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`exact / bf16`** *(official)* | **0.0000** | 100.00% | 2.7048 | 246.7 / 225.2 tok/s | 419.2 / 237.2 tok/s | 229.0 / 217.1 tok/s | 201.9 / 191.0 tok/s | 18.28 GiB *(18.88)* |
| `exact / fp8` | 0.0035 | 98.39% | 2.7007 | — | — | — | — | 18.28 GiB *(18.88)* |
| `exact / q4` | 0.0078 | 97.15% | 2.7063 | — | — | — | — | 18.28 GiB *(18.88)* |
| **`fp8 / fp8`** *(default ≤448K)* | **0.0059** | **97.40%** | 2.6981 | **425.6 / 442.5 tok/s** | **545.1 / 477.5 tok/s** | **340.2 / 316.1 tok/s** | **321.3 / 313.2 tok/s** | 17.11 GiB *(17.71)* |
| **`fp8 / q4`** *(default 512K)* | **0.0093** | **96.69%** | 2.7105 | **412.4 / 460.3 tok/s** | **540.5 / 519.4 tok/s** | **334.4 / 333.6 tok/s** | **313.3 / 307.2 tok/s** | 17.11 GiB *(17.71)* |
| `nvfp4 / fp8` | 0.0230 | 94.99% | 2.7485 | — | — | — | — | 14.66 GiB *(15.26)* |
| **`nvfp4 / q4`** *(opt-in max speed / 1M)* | **0.0267** | **94.58%** | 2.7569 | **425.2 / 424.6 tok/s** | **508.4 / 490.9 tok/s** | **398.2 / 350.3 tok/s** | **339.3 / 324.9 tok/s** | 14.66 GiB *(15.26)* |

- **Accuracy-first default (`--mode fp8`):** `squid5090 serve` defaults to **`--mode fp8`** (keeping ALL 24 MoE expert layers in 100% official checkpoint precision — L0–19 NVFP4 + L20–23 MXFP8 via coalesced 128B-sector `uint4` BF16 Tensor Core MMA — plus official BF16 routers/controllers in single-pass 16-CTA DSMEM cluster kernels, 1-launch cluster decode attention, CUDA 13.4+ `L2::evict_first` streaming loads, spill-free 16-col `U=3` FP8 MMA attention + `lm_head`, native `sm_120a` block-scaled MoE + FP8 `cublasLt` prefill, and FP8 DSpark with an **embedded corpus-frequency 32K shortlist (`src/draft_shortlist.bin`) + 16K dynamic context extension** and Top-K `1024` exact BF16 Markov folding). This delivers **`0.0059–0.0093` long-context KLD** (`ΔPPL -0.0068` to `+0.0056` over 7,784 tokens — **9× smaller PPL delta** than 4-bit) while reaching **`545.1 tok/s`** `T=0.0` copy, **`442.5–460.3 tok/s`** `T=1.0` code, **`519.4 tok/s`** `T=1.0` copy (`fp8/q4`), **`29/30` (`96.7%`)** on 30-task reasoning, and **`17,741 tok/s` HTTP** (`18,318 tok/s` CLI, `20,007 tok/s` `B=2048` chunk peak) cold 18.9K prefill!
- **Temperature transparency:** `bench` defaults to `--temp 0.0` (greedy); `serve` defaults to `--temp 1.0 --top-p 0.95` (matching Inkling-2-Mini's official `generation_config.json`), using **exact Leviathan/Chen stochastic rejection sampling** (`q_i(v)` drafted from DSpark + residual resampling from $\mathrm{norm}(\max(0, p - q))$ inside the CUDA Graph). With the embedded corpus-frequency 32K shortlist, pure overlapped DSpark outperforms CPU 3-gram lookup on general workloads, so `--prompt-lookup` is now opt-in for verbatim RAG/copy bursts.
- **Native Vision Tower (`model.visual.*`, ON by default in `serve`):** Loads all 422 BF16 vision tensors (`~609 MiB` inside the single weight `VRAMArena`, zero permanent workspace VRAM) and encodes a `320×200` image in **`4.4 ms`** via cuBLAS BF16 Tensor Core GEMMs, with **automatic `0.0 ms` multi-turn prefix-cache reuse** via content-addressed negative synthetic token IDs. Pass `--no-vision` to save `~609 MiB` VRAM on text-only deployments.
- **Short- vs. long-context KLD:** On 529-token prompts (inside the 1,024-token BF16 local window), KLD is `0.0030` (`fp8/fp8`), `0.0050` (`fp8/q4`), and `0.0184` (`nvfp4/q4`). At 7,784 tokens (7.6× past the local window, shown above), `q4` global KV adds only `+0.0034` KLD over `fp8` KV (`ΔPPL +0.0056` in `fp8/q4`).
- **Choosing a mode:** Keep the default **`--mode fp8`** (`--kv auto` selects `fp8` ≤ 448K and `q4` at 512K–1M) for near-lossless accuracy (`0.0059–0.0093` KLD, `313–545 tok/s`, `512K` + vision in `22.87 GiB` with `--embed-host`); opt in to **`--mode nvfp4 --kv q4`** when you want peak greedy chat speed (`398.2 tok/s`) or 1M context in `23.5 GiB`.

### 2. Real Long-Context Recall vs. Synthetic 1M Step-Latency Scaling (`--mode nvfp4 --kv q4`)

Real prefilled single-needle passkey retrieval (planted at 50% prompt depth) is reported separately from synthetic zeroed-KV step latency (`squid5090 longctx`):

| Context Depth | Test Type | Prefill Latency / Rate | Decode Speed (`c=1`) | Total VRAM (0 spill) | Result / Note |
|---|---|---:|---:|---:|---|
| **20K** (`19,978` tok) | Real cold prefill | `2,282 ms` (`8,755 tok/s`) | 453.6 tok/s | 16.7 GiB | `9,181 tok/s` `B=2048` chunk peak |
| **64K** (`65,530` tok) | **Real prefilled Needle (50% depth)** | `8.46 s` (`7,742 tok/s`) | 318–331 tok/s | 16.7 GiB | **Verbatim recall PASS** |
| **128K** (`131,057` tok) | **Real prefilled Needle (50% depth)** | `21.89 s` (`5,988 tok/s`) | 166.6 tok/s | 17.4 GiB | **Verbatim recall PASS** (`COBALT-FALCON-7492`) |
| **256K** (`262,115` tok) | **Real prefilled Needle (50% depth)** | `57.29 s` (`4,575 tok/s`) | 123.9 tok/s | 17.9 GiB | **Verbatim recall PASS** (`OBSIDIAN-HERON-3815`) |
| **512K** (`523,961` tok) | **Real prefilled Needle (50% depth)** | `171.13 s` (`3,062 tok/s`) | 74.4 tok/s | 20.3 GiB | **Verbatim recall PASS** (`VERMILION-LYNX-9064`) |
| **1M** (`1,048,000` tok) | *Synthetic `longctx` (zeroed KV)* | — | **45.7 tok/s** (`B=1`, `21.86 ms/tok`)<br>*102.4 P1 / 108.0 P0 (`B=4 @dl=2.5`)* | **23.23 GiB** | Real KV allocation & step latency; `@dl=2.5` is synthetic multiplier |
| **Warm 16K / 82.5K turn** | Real HTTP prefix cache | **`71.9 ms` / `62.4 ms`** | 446.7 / 237.5 tok/s | 23.2 GiB | Host-RAM local checkpoints (`0` extra VRAM); `32 MiB` static HTTP buffer |

### 3. LoopCD-Hidden Contrastive Decoding ([`arXiv:2610.02185`](https://arxiv.org/abs/2610.02185))

Inkling-2-Mini runs its 12-layer recurrent core (`L6..L17`) for $R = 3$ passes ($h_1 \to h_2 \to h_3$) before entering the 6-layer Coda (`L18..L23`). `squid5090` implements **LoopCD-Hidden** (Eq. 2 of Liu et al., 2026) directly inside the existing Loop→Coda mega-fusion kernel (`mega_mlp_post_next_depth_norm_kernel` at visit 42) with **zero extra CUDA kernel launches**, **zero extra KV cache**, **zero CUDA Graph rebuilds** on per-request changes, and automatic prefix-cache invalidation whenever `loopcd_omega` or `loopcd_ref` changes:

$$h' = h_3 + \omega\,(h_3 - h_b), \qquad b \in \{1, 2\}$$

- **Zero-overhead & lossless verification:** When $\omega = 0.0$ (default), the kernel skips the `fmaf` cleanly (`0.000000` delta vs. baseline; `fp8/q4` KLD stays `0.009574`). When $\omega > 0$, `exact` mode retains 100% bit-exact `mtp=0 == mtp=7` parity, and `fp8/q4` (`T=1.0`, `mtp=7`) decode throughput stays equal or slightly faster (`247.5 → 260.4 tok/s` at $\omega = 0.2$, `acc: 49.2% → 52.5%`).
- **Empirical RTX 5090 sweep (`fp8/q4`, 30-task Math + Code + Logic benchmark & 7,784-tok KLD):**
  - **Thinking mode (`enable_thinking=true`, default):** $\omega \in \{0.1, 0.2\}$ with $h_b = h_1$ (and $\omega = 0.3$ with $h_2$) lifts accuracy from **`25/30 (83.3%)` → `27/30 (90.0%, +6.7 pts)`** (`10/10` Math, `10/10` Logic, `7/10` Code), with $\omega = 0.1$ using **5.5% fewer thinking tokens** (`11,893` vs `12,584`) and raising 7,784-tok top-1 match (`96.93% → 96.96%`, `ΔPPL +0.0065`). Above $\omega \ge 0.5$, generation degrades (`24/30`), matching Appendix G.1 of the paper.
  - **Direct mode (`enable_thinking=false`):** Unmodified baseline ($\omega = 0.0$) scores `29/30 (96.7%)` vs `27–28/30` at $\omega \in [0.2, 0.5]$, so `squid5090` keeps `--loopcd-omega 0.0` as the opt-in default and exposes `--loopcd-omega` / `--loopcd-ref` on both CLI and per-request HTTP JSON (`"loopcd_omega": 0.1, "loopcd_ref": 1`).

### 4. Live Same-Hardware Cross-Engine Benchmark & Accuracy (1× RTX 5090)

![Live Cross-Engine Benchmark & 30-Task Accuracy on 1× RTX 5090](assets/engine_comparison.png)

> **100% live apples-to-apples methodology:** Every single row below — **`ingine`** (CUDA 13.4), **`basalt v0.5.7`** (`MX8` pack converted directly from the same checkpoint), and all 4 **`squid5090`** modes (CUDA 13.4, native Vision ON) — was measured **live on the exact same RTX 5090** (`driver 590.48.01`, identical unmodified Inkling-2-Mini weights, identical 4 HTTP SSE prompts generating 512 tokens each at `T=0.0` and `T=1.0, top_p=0.95` median of 3 runs, identical cold 18,937-token HTTP SSE prefill, and identical 30-task Math + unit-tested Python Code + Logic accuracy suite at `reasoning_effort = low` and `none`). `squid5090` also passes bit-exact `exact/bf16` parity (`mtp=0 == mtp=7`).

| Engine / Mode (unmodified weights) | Chat `T=0 / T=1` | Prose `T=0 / T=1` | Code `T=0 / T=1` | Copy `T=0 / T=1` | Cold 18.9K HTTP Prefill | 30-Task Acc (`low` / `none`) | VRAM Footprint* | Vision | Max Context (1× 5090) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| **`ingine`** (`fp8/fp8`, CUDA 13.4) | 361.1 / **368.7** | **346.9** / 302.3 | **442.3 / 525.8** | **632.5 / 542.5** | 10,985 tok/s | **29/30** (96.7%) / 27/30 (90.0%) | 20.8 GiB | Yes | 262K (`0` spill) |
| **`basalt v0.5.7`** (`MX8/int8`) | 320.3 / 276.0 | 284.4 / 264.6 | 365.5 / 303.0 | 452.9 / 378.8 | 17,494 tok/s | **29/30** (96.7%) / 28/30 (93.3%) | 19.8 GiB | Yes | 1M *(RAM spill >256K)* |
| **`basalt v0.5.7`** (`MX8/fp8`) | 334.1 / 271.4 | 265.8 / 257.1 | 319.1 / 292.0 | 425.1 / 352.6 | 16,307 tok/s | **29/30** (96.7%) / 27/30 (90.0%) | 19.7 GiB | Yes | 1M *(RAM spill >256K)* |
| **`squid5090`** (`exact/bf16`) | 229.0 / 217.1 | 201.9 / 191.0 | 246.7 / 225.2 | 419.2 / 237.2 | 9,875 tok/s | **29/30** (96.7%) / **29/30 (96.7%)** | 20.7 GiB | Yes | 64K–128K (`0` spill) |
| **`squid5090`** (`fp8/fp8`, ≤448K def.) | 340.2 / 316.1 | 321.3 / 313.2 | 425.6 / 442.5 | 545.1 / 477.5 | **17,741 tok/s** *(CLI: 18,318)* | **29/30** (96.7%) / 28/30 (93.3%) | 19.5 GiB | **Yes** | 256K–448K (`0` spill) |
| **`squid5090`** (`fp8/q4`, 512K def.) | 334.4 / 333.6 | 313.3 / 307.2 | 412.4 / 460.3 | 540.5 / 519.4 | **17,476 tok/s** *(CLI: 18,168)* | 28/30 (93.3%) / 28/30 (93.3%) | 19.2 GiB | **Yes** | **512K** (`22.9 GiB`, `0` spill) |
| **`squid5090`** (`nvfp4/q4`, opt-in 1M) | **398.2** / 350.3 | 339.3 / **324.9** | 425.2 / 424.6 | 508.4 / 490.9 | 14,758 tok/s | 28/30 (93.3%) / 28/30 (93.3%) | **16.8 GiB** | **Yes** | **1,048,576** (`23.5 GiB`, `0` spill) |

*\*VRAM = `squid5090` weight + runtime arenas at 32K ctx with native Vision ON (`-0.60 GiB` with `--no-vision`); `ingine` and `basalt` measured net @64K. Pure `B=1` (`mtp=0`) `squid5090 fp8/fp8` runs at `279.3 tok/s` CLI. For reference, `llama.cpp` (`IQ4_NL` GGUF, no DSpark draft, published in Basalt docs) runs at `92.5–94.5 tok/s` decode and `3,093 tok/s` prefill.*

- **Honest per-engine summary from our live RTX 5090 runs:**
  - **`ingine`** leads peak `fp8/fp8` code/copy decode (`442–526` code, `543–633` copy) and `T=1.0` chat (`369`) — at the cost of slower cold prefill (`10,985 tok/s`), higher VRAM (`20.8 GiB`), and a `262K` context ceiling.
  - **`basalt v0.5.7`** leads multi-feature breadth (constrained JSON grammar, parallel slots, multi-GPU, elastic RAM-spilled 1M context) and strong cold prefill (`17,494 tok/s`).
  - **`squid5090`** now **beats `basalt v0.5.7` on all 8 of 8 decode benchmarks in every single quantized mode (`fp8/fp8`, `fp8/q4`, and `nvfp4/q4`)**, **leads cold 18.9K HTTP prefill (`17,741 tok/s` `fp8/fp8`, `17,476 tok/s` `fp8/q4` — 1.61× faster than `ingine`!)**, **leads greedy chat (`398.2` `nvfp4/q4`) and `T=1.0` prose (`324.9` `nvfp4/q4` / `313.2` `fp8/fp8` vs `ingine` `302.3`)**, **matches `basalt` and beats `ingine` on 30-task accuracy (`29/30` low / `28/30` none in `fp8/fp8`, `29/30` & `29/30` in `exact/bf16`)**, includes **native 23-layer BF16 Vision (`4.4 ms` ViT encode, `0.0 ms` multi-turn prefix cache)**, fits **zero-spill 512K `fp8/q4` (+ Vision!) in `22.87 GiB` and 1M `nvfp4/q4` in `23.5 GiB`**, ships as a **~20 MiB zero-Python single binary** (CUDA `13.0–13.4+`), and adds zero-overhead **LoopCD-Hidden**.

### 5. Native Vision Support (Images + Text)
`squid5090 serve` loads Inkling-2-Mini's built-in 23-layer BF16 Vision Tower (`model.visual.*`, 422 tensors, `~609 MiB` inside the single weight `VRAMArena`, zero permanent workspace VRAM) automatically by default:
- **API formats:** Accepts OpenAI `{"type":"image_url","image_url":{"url":"data:image/...;base64,..."}}`, OpenAI Responses-style `{"type":"input_image","image_url":"..."}`, and Anthropic `{"type":"image","source":{"type":"base64","data":"..."}}` content parts in `user` and `tool` messages.
- **Image formats & preprocessing:** Built-in `stb_image.h` decodes **PNG, JPEG, GIF, BMP**; build with `zig build -Dwebp=true` (requires `libwebp-dev`) to add **WebP & animated WebP** support. Transparent RGBA/GA images are composited onto an 8×8 grey checkerboard (`204`/`153`), oversized images are downscaled with aspect-preserving separable area averaging to `--image-max-tokens` (default `256` tiles of `40×40` px), and embeddings are scattered straight into prefill hidden states skipping `embed_norm`.
- **Automatic `0.0 ms` multi-turn vision prefix caching:** Each decoded image is represented by content-addressed negative synthetic token IDs (`SplitMix64` over final RGB pixels), so follow-up turns referencing the same image hit the host-RAM prefix KV cache automatically (`vis=0.0ms`, `images_encoded=0`).

### Current Scope & Limitations
- **No constrained grammar / JSON-schema decoding** yet (standard OpenAI `tools` / `tool_calls` streaming is supported).
- **Single-user (`c=1`) slot architecture:** Optimized for lowest single-user latency and fitting up to 1M context in 23.5 GiB with `2 cudaMalloc` arenas and zero post-init host `malloc` on text requests; not a multi-user batching server.
- **HTTP request buffer:** Static `32 MiB` request & prompt-render buffers (handles 512K–1M-token JSON and base64 image payloads; returns HTTP `413` above `32 MiB`).

---

## Quickstart (Linux Build & Install)

### 1. Linux Requirements

- **OS:** Linux x86_64 (tested on Ubuntu 24.04 / Debian 12–13)
- **GPU:** NVIDIA Blackwell GPU (`sm_120a`, e.g., RTX 5090) with ≥ 16 GiB free VRAM (≥ 23.5 GiB for full 1M context)
- **NVIDIA Driver:** `580+` (tested on `590.48.01`)
- **CUDA Toolkit:** CUDA `13.0+` with `nvcc` and `cuBLAS` (tested on CUDA `13.1` & `13.4` at `/usr/local/cuda`; CUDA `13.4+` automatically enables `L2::evict_first` streaming weight cache hints)
- **Build Tools:** `g++`, `git`, `curl`, optional `libwebp-dev` (for `-Dwebp=true`), and **Zig `0.17.1+`**

```bash
sudo apt-get update && sudo apt-get install -y build-essential git curl libwebp-dev
export PATH="/usr/local/cuda/bin:$PATH"
nvcc --version && zig version
```

*Runtime links only against `libc`, `libstdc++`, `libcudart`, `libcublas`, `libcublasLt`, `libpthread` (plus `libwebp`/`libwebpdemux` when built with `-Dwebp=true`) — zero Python, CMake, Make, or external packages.*

### 2. Clone, Build & Download Weights

```bash
git clone https://github.com/tensorfish/squid5090.git
cd squid5090
zig build -Dwebp=true         # defaults to -Doptimize=fast (ReleaseFast); omit -Dwebp=true if libwebp-dev isn't installed

uvx --from huggingface-hub hf download thinkingmachines/Inkling-2-Mini \
  --local-dir /opt/models/inkling-2-mini
```

*(Built-in draft shortlist: `squid5090` embeds a corpus-frequency-ranked 32K shortlist [`src/draft_shortlist.bin`](src/draft_shortlist.bin) + 16,384 dynamic context rows directly into the binary — zero external files needed. Set `SQUID_DRAFT_VOCAB=full` to force the full 200K draft vocabulary.)*

### 3. Run the OpenAI API Server, CLI, or KLD Evaluator

```bash
# Default high-accuracy OpenAI HTTP/SSE server (FP8 Tensor Core MMA + official L0-23 MoE, 512K Q4 KV, ~22.6 GiB VRAM, 0.0096 KLD)
./zig-out/bin/squid5090 serve /opt/models/inkling-2-mini \
  --host 0.0.0.0 --port 8000 --mode fp8 --kv q4 --ctx 524288 --mtp 7 --temp 1.0 --top-p 0.95

# Near-lossless 256K FP8 KV (0.0061 long-ctx KLD, dPPL -0.0030, ~22.6 GiB VRAM)
./zig-out/bin/squid5090 serve /opt/models/inkling-2-mini \
  --host 0.0.0.0 --port 8000 --mode fp8 --kv fp8 --ctx 262144 --mtp 7 --temp 1.0 --top-p 0.95

# Opt-in max-speed / 1M context NVFP4 mode (~23.2 GiB at 1M, 0.0263 KLD)
./zig-out/bin/squid5090 serve /opt/models/inkling-2-mini \
  --host 0.0.0.0 --port 8000 --mode nvfp4 --kv q4 --ctx 1048576 --mtp 7 --temp 1.0 --top-p 0.95

# Optional: enable 1.8 MB runtime-gated Fisher-LDA abliteration (zero weight modification)
./zig-out/bin/squid5090 serve /opt/models/inkling-2-mini \
  --host 0.0.0.0 --port 8000 --mode fp8 --kv q4 --ctx 524288 --mtp 7 \
  --ablation /opt/models/inkling-2-mini/inkling-2-mini-abliterated.safetensors

# Benchmark (supports --temp 0.0 or --temp 1.0)
./zig-out/bin/squid5090 bench /opt/models/inkling-2-mini \
  --prompt "Write a Python LRU cache with tests." --mode nvfp4 --kv q4 --mtp 7 --temp 1.0 --max-tokens 1024 --runs 3

# Reproduce exact FP64 long-context KLD (7,784 tokens) vs official exact/bf16
./zig-out/bin/squid5090 logits /opt/models/inkling-2-mini --prompt-file tools/kld_corpus.txt --raw --ctx 8192 --mode exact --kv bf16 --out /tmp/ref.bin
./zig-out/bin/squid5090 kld    /opt/models/inkling-2-mini --prompt-file tools/kld_corpus.txt --raw --ctx 8192 --ref /tmp/ref.bin --mode fp8   --kv q4
./zig-out/bin/squid5090 kld    /opt/models/inkling-2-mini --prompt-file tools/kld_corpus.txt --raw --ctx 8192 --ref /tmp/ref.bin --mode nvfp4 --kv q4
```

**Install as a persistent `systemd` service:**
```bash
sudo cp deploy/squid5090.service /etc/systemd/system/squid5090.service
sudo systemctl daemon-reload && sudo systemctl enable --now squid5090.service
curl -s http://localhost:8000/health
```

### Key CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--mode` | `fp8` (`serve`), `exact` (CLI) | Weight precision: `exact` (BF16 dense) \| `fp8` (FP8 TC MMA dense + official L0–23 MoE, `0.006–0.0096` KLD) \| `nvfp4` (`0.026` KLD, max speed) |
| `--kv` | `auto` | Global KV cache format: `bf16` \| `fp8` \| `q4` (enables up to `1M` context in `23.2 GiB`) |
| `--ctx` | `65536` (`serve`), `8192` (CLI) | Context window size up to `1048576` |
| `--mtp` | `7` (`serve`), `0` (CLI) | DSpark drafter (`0` = off, `7` = adaptive `{2,4,8}` CUDA Graph switch) |
| `--spec-threshold` | `0.80` | Markov confidence threshold for `{2,4,8}` verify width (`0.0` = fixed `B=8`) |
| `--temp` / `--top-p` / `--top-k` | `1.0` / `0.95` / `0` (`serve`), `0.0` (CLI) | GPU sampling & exact Leviathan/Chen rejection sampling defaults (overridable per-request) |
| `--loopcd-omega` / `--loopcd-ref` | `0.0` / `1` | Opt-in LoopCD-Hidden ([arXiv:2610.02185](https://arxiv.org/abs/2610.02185)) strength $\omega \in [-1, 2]$ (try `0.1`–`0.2` for thinking) & ref pass `1` ($h_1$) or `2` ($h_2$); overridable per HTTP request |
| `--max-tokens` | `128` (CLI), `16384` (HTTP fallback) | Max generated tokens per request |
| `--keep-history-thinking` | off | Re-inject prior turns' `reasoning_content` (off by default to prevent multi-turn thinking copy loops) |
| `--prompt-lookup` | off | Opt-in hybrid O(1) prompt-lookup drafter for long verbatim RAG/code-copy bursts |
| `--no-vision` | off (`serve`) | Disable native 23-layer BF16 Vision Tower (`model.visual.*`) to save ~609 MiB VRAM |
| `--image-max-tokens` / `--max-images` | `256` / `16` | Max `40×40` visual tiles per image (aspect-preserving area-average downscale) & max images per request |
| `--ablation` | none | Optional 1.8 MB runtime-gated Fisher-LDA `.safetensors` (see [`tools/ablate.py`](tools/ablate.py)) |
| `--api-key` | `$SQUID_API_KEY` | Optional `Authorization: Bearer <key>` auth for `serve` (constant-time compare, arbitrary key length) |

---

## Documentation & Attribution

- **[`LITE.md`](LITE.md)** — High-level, 3Blue1Brown-style animated guide to LLM optimization and abliteration.
- **[`LEARNINGS.md`](LEARNINGS.md)** — Consolidated technical reference: GPU kernels, KLD analysis, roofline audit, unexploited levers, and the `uv` abliteration pipeline.
- **[`tools/kld_corpus.txt`](tools/kld_corpus.txt)** — Checked-in 7,784-token multi-domain KLD evaluation corpus.
- **[`ledger.jsonl`](ledger.jsonl)** — Machine-readable record of every benchmark, KLD sweep, and needle run.
- **[`LICENSE`](LICENSE)** / **[`NOTICE`](NOTICE)** — Apache-2.0 license and complete open-source attributions.
