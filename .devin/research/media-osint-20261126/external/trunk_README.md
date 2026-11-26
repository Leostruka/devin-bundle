<div align="center">

# Trunk and Branches (Isaque 2.0)

**Thermodynamic Parsimony, Frozen-Core Cortical Columns, and Non-Destructive Continual Specialization via Orthogonal DoRA and Sparsegen LD-MoLE Routing on Consumer Silicon**

[![CERN Zenodo DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24226537.svg)](https://doi.org/10.5281/zenodo.24226537)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-lcsmotta7%2Ftrunk--and--branches--isaque--2-FFD21E)](https://huggingface.co/lcsmotta7/trunk-and-branches-isaque-2)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0001--3081--5505-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0001-3081-5505)
[![Bitcoin Anchor](https://img.shields.io/badge/Bitcoin_OpenTimestamps-Block_%23975458-F7931A?logo=bitcoin&logoColor=white)](provenance/04-carimbo-de-data.md)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-16324F.svg)](https://creativecommons.org/licenses/by/4.0/)

🌐 **[Ler em Português Brasileiro (PT-BR)](README.pt-BR.md)** · 📄 **[English Monograph PDF (18 pages)](paper/trunk_and_branches_isaque_2_0_en_doi_24221509.pdf)** · 📄 **[Monografia em Português PDF (18 páginas)](paper/tronco_e_ramos_isaque_2_0_pt_br_doi_24221509.pdf)**

*Author:* **Lucas Alves Motta** ([ORCID: 0009-0001-3081-5505](https://orcid.org/0009-0001-3081-5505))  
*Beyond Adonai Research Laboratory · Indaial, Santa Catarina, Brazil · November 2026 (Rev. 5.0 — Pure Audit Edition)*

</div>

---

## Abstract & Core Thesis

Contemporary AI engineering predominantly pursues monolithic scaling: stacking hundreds of billions of mutable parameters and tens of thousands of raw prompt tokens into continuously resident memory hierarchies (*the Monolithic Babel Trap*). Inspired by the **~20 W metabolic budget of the human neocortex**, avian pallial neuron-packing density, Jeff Hawkins's **Thousand Brains Theory** of cortical columns, and Niklaus Wirth's plea for lean software, **Isaque 2.0 (*Trunk and Branches*)** demonstrates a disciplined alternative on consumer silicon:

1. **100% Frozen Hybrid Trunk (`Qwen3.5-4B`):** 24 Gated DeltaNet + 8 Full-Attention layers (`d = 2560`, `248,320` frozen vocabulary tokens verified under SHA-256 invariant `c78988d9...2a34`).
2. **Zero-VRAM Deterministic Vigilance (~98% Dormancy):** Compiled Rust AST/conformal gates (`< 0.5 ms` CPU, `0.015 ms` zero-copy `.mmap` tree lookup, Split Conformal `BAVAR >= 0.90`) keep idle GPU memory at strictly **0 MB**.
3. **16.00 MiB Orthogonal Cortical Cartridges (`DoRA + O-LoRA`):** Specialized procedural columns stored cold on NVMe SSD (`~8.38M` synapses each, capped at `<= 3` sister waves per cartridge) and routed at inference via analytical **Sparsegen LD-MoLE** on the simplex paired with cross-term-free rank concatenation (`PEFT combination_type="cat"`).
4. **Staged Modular DAG Verification & Zero-Swap Windows NTAPI:** Physical reality compilers (headless `Blender 5.2.1 LTS` `bmesh` and `clang++ -std=c++20`) combined with a local `22.02 GB` `Qwen3.5-35B-A3B` (`--cpu-moe`) System-2 critic backed by a 4-stage Windows `NTAPI` lifecycle (`+0.0039 MiB` swap delta).

<p align="center">
  <img src="assets/fig1_en.png" width="94%" alt="Isaque 2.0 Dual-Tier Cortical Topology and Measured Power Telemetry" />
</p>

## Seven Audited Empirical Findings (`NVIDIA GeForce RTX 5060 8 GB`)

| # | Dimension | Measured Result (Stage 1 — `RTX 5060 8 GB`) | Verification Invariant |
| :- | :--- | :--- | :--- |
| **1** | **Thermodynamic Envelope** | **22.3–23.3 W** active 4B inference · **28–31 W** cortical training · **0 MB** idle VRAM | `faixa-A.json` + Win32 Job Object (`compute_procs == 0`) |
| **2** | **Zero-Swap NTAPI & Tokenizer Parity** | `13.50 GiB` MoE streamed @ **1.75 GiB/s** with **+0.0039 MiB** swap delta · **100.0%** byte parity (`248,320` tokens) | 4-stage `VirtualLock` + `NO_BUFFERING` + `DiscardVirtualMemory` (`6.61 us`) |
| **3** | **32-Layer Real Autograd (`H3`)** | **218.36–412.48 tok/s** physical backprop · **-86.76%** private-probe CE loss (`2.429 -> 0.322`) | Step-1 `\|\|grad_A\|\|_2 = 0.0` (`B_0=0`) -> Layers `31..0` active; blind `35B` audit |
| **4** | **Multimodal Procrustes (`VICOP`)** | `mmproj-BF16` (**449 ms**) + `2560 -> 384d` alignment (**Recall@5 = 96.00%** on 600 unseen pairs) | **5.43x** Cognitive Conductivity (`ICC`: `0.5121 -> 2.7828`) |
| **5** | **Causal Synaptic Ablation (`KEV-1.0`)** | Raw 4B + `.mmap` = **0/4** (`1.77/10`) vs. Taught `DoRA+O-LoRA` = **4/4 (100%)** (`9.67/10`) | `0` non-manifold edges, `0.0%` BBox error, `8/8` UE5 C++20 rules (`10.23x–11.95x` ICC) |
| **6** | **10-Wave Continual Rupture Matrix** | Monolithic ruptures at `k=3` (**98.51%**) and collapses to **75.31% acc / 31.37% lik.** at `k=10` | **Surgical LD-MoLE Top-2 (`PEFT cat`) preserves 100.00% across all 10 waves** |
| **7** | **Staged Modular DAG Law** | Token-by-token logit blending across distinct code waves causes Python AST `SyntaxError` | **1 specialist cartridge per causal DAG stage** (`<= 3` sister waves/cartridge) |

<p align="center">
  <img src="assets/fig4_en.png" width="94%" alt="10-Wave Continual Saturation and Rupture Curve" />
</p>

<p align="center">
  <img src="assets/fig5_en.png" width="94%" alt="3-Level Hierarchical Cortical Tree Router and Staged Modular Execution DAG" />
</p>

<p align="center">
  <img src="assets/fig6_en.png" width="94%" alt="Unassisted Token-by-Token Neural 3D Synthesis in Blender 5.2.1 LTS" />
</p>

## Repository Structure

* [`paper/trunk_and_branches_isaque_2_0_en_doi_24221509.pdf`](paper/trunk_and_branches_isaque_2_0_en_doi_24221509.pdf) — Official 18-page English Monograph (`Rev. 5.0`, CERN DOI stamped).
* [`paper/tronco_e_ramos_isaque_2_0_pt_br_doi_24221509.pdf`](paper/tronco_e_ramos_isaque_2_0_pt_br_doi_24221509.pdf) — Complete 18-page Brazilian Portuguese Twin Edition (`Rev. 5.0`, CERN DOI stamped).
* [`paper/latex-en/`](paper/latex-en/) & [`paper/latex-pt-br/`](paper/latex-pt-br/) — Full reproducible TeX Live `pdflatex` sources and vector/high-DPI figures in both languages.
* [`evidence/`](evidence/) — **Open Forensic Evidence & Raw Receipts Archive**: all **195 triangular retention measurements** (`3 x 65` cells in `ato2_escada_ondas_3_a_10.json`), **10/10 solo Isaque-generated 3D/C++20 wave outputs** (`exports == exports_recheck`), unedited negative boundary/collision probes (`DESAFIO-04_C` line 35 & `FUSAO_2_ONDAS_1_3_pass2.py` line 58), and compiled Technical Annexes ([English PDF](paper/annex_forensic_evidence_en_doi_24221509.pdf) · [Portuguese PDF](paper/anexo_evidencias_forenses_pt_br_doi_24221509.pdf)).
* [`provenance/`](provenance/) — Stage-1 SHA-256 manifest (`79602f29...558be5dd`), `5,124`-byte binary OpenTimestamps proof (`.ots`) anchored at **Bitcoin Block `#975458`** (`2026-11-11 14:41 BRT`), and four-calendar blockchain verification log.
* [`CITATION.cff`](CITATION.cff) — Machine-readable citation metadata (activates GitHub's *Cite this repository* button).

## Cryptographic & Bitcoin Blockchain Verification

To verify the Stage-1 OpenTimestamps proof independently against the Bitcoin blockchain:

```bash
pip install opentimestamps-client
sha256sum provenance/03-manifesto-sha256-etapa-1.txt
# Expected: 79602f29a07b8b336e29c887ac1723aa9aea5b710605c67d42b21bc2558be5dd
ots verify provenance/03-manifesto-sha256-etapa-1.txt.ots -f provenance/03-manifesto-sha256-etapa-1.txt
```

## Citation (BibTeX)

```bibtex
@techreport{motta2026isaque,
  author      = {Motta, Lucas Alves},
  title       = {Trunk and Branches: Thermodynamic Parsimony, Frozen-Core Cortical Columns, and Non-Destructive Continual Specialization via Orthogonal {DoRA} and Sparsegen {LD-MoLE} Routing on Consumer Silicon ({Isaque 2.0})},
  institution = {Beyond Adonai Research Laboratory},
  address     = {Indaial, Santa Catarina, Brazil},
  year        = {2026},
  month       = nov,
  number      = {BEYOND-ADONAI-TR-2026-01},
  doi         = {10.5281/zenodo.24221509},
  url         = {https://doi.org/10.5281/zenodo.24221509},
  note        = {ORCID: 0009-0001-3081-5505. Bitcoin OpenTimestamps Anchor: Block \#975458}
}
```

---
<div align="center">
  <i>"Wisdom is rarely found in the noisy accumulation of an unfinished tower; it dwells quietly in the order, parsimony, and faithfulness of small, well-governed foundations." — Soli Deo Gloria</i>
</div>
