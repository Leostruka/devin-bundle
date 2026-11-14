# First-Principles Justification & Master Architecture Playbook

## Purpose

Every decision in the assembled idea must be justified from First Principles (the "ground truth" of the domain) up to its market superiority. No cargo-cult stack choices, no "because it is popular", and no hand-waving.

## The 4-Layer Justification Chain

Every major product and technical decision MUST trace through all four layers:

```
[Layer 1: Domain Axiom / Physical Limit]
       -> [Layer 2: First-Principles Mechanism]
              -> [Layer 3: Architectural & Product Realization]
                     -> [Layer 4: Measurable Market Superiority vs. Incumbents]
```

### Layer 1: Domain Axioms & Universal Laws

Ground the problem in immutable constraints before naming any framework:
- **Compute & Systems Physics**: CPU instruction/cache locality, memory bandwidth, syscall overhead, disk IOPS, network RTT/bandwidth, serialization tax, battery/thermal envelope.
- **Information & LLM Theory**: Shannon entropy, signal-to-noise ratio in context windows, lost-in-the-middle degradation, compute-optimal test-time scaling, deterministic code vs. stochastic inference boundaries.
- **Human Cognitive & Perceptual Bounds**:
  - **Doherty Threshold (<400ms, ideal <100ms)**: system response below 100ms feels instantaneous; above 400ms breaks flow state.
  - **Hick's Law**: decision time grows logarithmically with the number of choices ($T = b \log_2(n + 1)$) - prune options ruthlessly.
  - **Fitts's Law**: acquisition time depends on distance and target size - keep primary actions immediate.
  - **Miller's Law & Working Memory**: humans hold 4-7 chunks at once - progressive disclosure is mandatory.

### Layer 2: Ex-FAANG Product Master Framework

Adopt the rigor of `agents/product-manager.md`:
1. **JTBD (Jobs-to-Be-Done)**:
   - Functional job, emotional job ("feel in total control without fear of breaking state"), and social job.
   - Job Story format: `When <triggering situation>, I want to <action/capability>, so I can <valuable outcome without friction>.`
2. **RICE Scoring Table**:
   - Score every candidate capability with explicit numbers: `Reach`, `Impact` (0.25 to 3.0), `Confidence` (50%-100%), `Effort` (person-weeks or agent-turns), `RICE = (R * I * C) / E`.
3. **Kano Classification**:
   - **Basic (Must-be)**: table stakes; absence causes immediate rejection.
   - **Performance (One-dimensional)**: linear value scaling (faster, cheaper, higher precision).
   - **Delighter (Attractive)**: unexpected capability that creates 10x advocacy and switching momentum.
4. **North Star Metric + Counter-Metric**:
   - Name one primary North Star Metric (e.g., "median time from raw intent to verified output") and one Counter-Metric that prevents destructive optimization (e.g., "defect/rework rate must remain <= 2%").
5. **Aggressive Non-Goals**:
   - Explicitly list what the product will NEVER do to protect focus and surface area.

### Layer 3: Tech Lead & Principal Software Architect Framework

Adopt the rigor of `agents/tech-lead.md` and `skills/architecture/SKILL.md`:
1. **Deep Modules (Ousterhout)**:
   - Module depth = `(Functionality & Invariants Enforced) / (Interface Complexity)`.
   - Reject shallow pass-through wrappers; design modules with narrow, typed interfaces that hide complex mechanics inside.
2. **Clean Architecture & Bounded Contexts (DDD)**:
   - Domain rules never depend on UI, CLI, or database frameworks.
   - Define explicit entity invariants, state transitions, and idempotent boundaries.
3. **ADR Format with Top-2 Debate & Kill Criterion**:
   - Every architectural choice must compare at least 2 viable designs, state why the runner-up was rejected, and declare a quantitative **Kill Criterion** (e.g., "If p95 latency exceeds 150ms on a 10k-node repo, replace SQLite FTS with Rust Tantivy index").
4. **Numeric NFR Budgets**:
   - Latency (p50, p95, p99), memory ceiling (MB), cold start (ms), binary/bundle size, offline capability, and recovery time objective (RTO).

### Layer 4: Alignment with Bundle Philosophies (`AGENTS.md`)

- **Rule 1 (Customer experience first)**: every technical choice must trace to an observable user benefit.
- **Rule 12 (Verify with tools)**: zero speculation; build deterministic verification gates into the architecture.
- **Rule 15 (Reproducible evidence + held-out)**: design evaluation harnesses with held-out test sets from day one.
- **Rule 18 (Lean context & minimum code)**: smallest code footprint that achieves maximum capability; zero bloat.
- **Rule 28 (Hybrid Rust-Python where warranted)**: Python orchestrates high-level workflows; Rust (`PyO3` + `abi3`) handles CPU-tight, memory-tight, or low-latency OS primitives.
