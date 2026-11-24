---
name: montador-de-ideias
description: Use when assembling, expanding, or elevating a raw project idea or initial prompt into an ultra-detailed, first-principles dossier and compiled master prompt with journalistic OSINT market research, Tech Lead and Staff Architect justifications, atomic and modular hardening/optimization, and high-impact contact surfaces.
triggers: [user, model]
---

# Montador de Ideias

## Overview

Transform any seed project idea or raw prompt into two verified, traceable artifacts (MACRO track; MICRO seeds skip artifacts, see Scope Triage):
1. **Investigative & First-Principles Dossier** (`.devin/specs/<slug>-idea-dossier.md`)
2. **Compiled Master Prompt** (`.devin/specs/<slug>-compiled-prompt.md`)

Every proposal is grounded in the fundamental axioms of each involved discipline (physical/compute limits, cognitive psychology, economics, software architecture, security, UX) and competitive OSINT or adjacent-pattern evidence proving why and how the design outperforms incumbents and prior art across every axis.

Detail playbooks (load on demand):
- `reference/journalistic-osint-protocol.md` - investigative journalism, public/semi-public leak/fragment mining, competitor teardown, PRISMA-lite + lateral reading.
- `reference/first-principles-justification.md` - first-principles derivation + Ex-FAANG PM (JTBD/RICE/Kano) + Principal Tech Lead/Architect (Deep Modules, ADRs with kill criteria, NFR budgets) + bundle philosophies.
- `reference/atomic-modular-hardening.md` - atomic-level and modular-level hardening and optimization matrices.
- `reference/contact-surfaces-excellence.md` - contact surface design bar: **Facilitar, Resolver, Impressionar, Ser Intuitivo**.
- `templates/idea-dossier.md` and `templates/compiled-prompt.md` - mandatory output schemas.

## Scope Triage (run BEFORE the pipeline)

Size the seed like `task-sizer`; wrong sizing is the main way this skill wastes effort:

| Track | Trigger | What Runs | Output |
|---|---|---|---|
| **MICRO** | Bugfix, single-feature change, copy/design tweak inside an existing codebase | Phase 0 verbatim capture + first-principles justification inline; skip Phases 1-5 | The design rationale lands directly in code/commit. NO dossier artifacts |
| **MACRO** | New product/tool/agent, multi-system capability, "turn this idea into a spec" | All phases 0-5 | Both `.devin/specs/` artifacts |

Never run the MACRO pipeline on a MICRO seed: a dossier for a one-file fix is token waste and process theater.

<HARD-GATE>
1. ORIGINAL PROMPT IMMUTABILITY: Write the verbatim seed to `.devin/specs/<slug>-seed.txt`, then compute `original_prompt_sha256` over that file (exact command below). NEVER alter, delete, dilute, or silently reinterpret any requirement from the original prompt.
   - `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" .devin/specs/<slug>-seed.txt`
2. GUIDANCE BEFORE ANY PROMPT CHANGE: Before adding, modifying, or reframing any part of the original prompt, you MUST ask the user via `ask_user_question` (1-4 questions per call, 2-4 concrete options with trade-offs + recommended stance) to align on the tool's philosophy, the core problem it solves, the acute pain point it heals, and which proposed expansions they approve.
   - BATCH: collect ALL Phase-0 questions into the fewest `ask_user_question` calls possible (max 4 questions/call is a ceiling, not a quota). Same for Phase 5: one Prompt Evolution Table round, not a drip-feed.
   - AFK/AUTONOMOUS (`/goal`, `afk-loop`, unattended): user gates cannot block. Mark the dossier `status: DRAFT-AUTO`, record every unapproved delta in section 2 of the compiled prompt as `PENDING-APPROVAL`, and proceed with the option you recommend. The next interactive session converts PENDING rows via a single `ask_user_question` round.
3. NO DEDUCTION WITHOUT EVIDENCE: Competitor weaknesses, technical limits, and architectural trade-offs must be verified with tools (`researcher` subagent, `agent-reach`, `scrape-tools`, `web_search`, `webfetch`, `grep`, `read`) before being stated as fact (Rule 12).
4. IDEMPOTENT RESUME: before Phase 1, if `.devin/specs/<slug>-idea-dossier.md` exists, hash the current seed and compare with `original_prompt_sha256` inside it. Same hash -> resume from the last incomplete phase (don't re-run OSINT). Different hash -> archive the old dossier (`-vN` suffix) and restart.
</HARD-GATE>

## Pipeline (6 Atomic Phases)

### Phase 0: Anchor & Philosophy Alignment (`ask_user_question`)

1. Write the verbatim seed to `.devin/specs/<slug>-seed.txt` and compute `original_prompt_sha256` over that file (HARD-GATE command).
2. Extract what is already explicit vs. what is underspecified across four axes:
   - **Filosofia da Ferramenta**: worldview, non-negotiable principles, identity.
   - **Problema Raiz**: structural cause vs. symptom.
   - **Dor Real (Pain Point)**: who suffers, how often, cost of inaction, why current workarounds fail.
   - **Restrições Inegociáveis**: stack, privacy/local-first, latency, budget, platform.
3. Run ONE batched frontier round with `ask_user_question` (up to 4 questions, 2-4 options + recommendation). Do not proceed until the user confirms the philosophy and pain-point anchor. AFK/unattended: proceed with recommended options, mark deltas `PENDING-APPROVAL`, dossier `status: DRAFT-AUTO`.

### Phase 1: Journalistic OSINT & Competitor Teardown

**SKIP-GATE**: for internal/personal tools with no market axis (private automations, single-user companions, internal CLIs), replace competitor teardown with *adjacent-pattern recon*: mine the local codebase (`grep`/`glob`), public repos solving the same sub-problem, and postmortems of similar architectures. Still cite sources; still fill the matrix with at least 3 adjacent implementations or prior-art approaches.

Read `reference/journalistic-osint-protocol.md`. Dispatch `researcher` (`model: swe-2-max`, free) and/or run `agent-reach`, `scrape-tools`, `web_search`, and `webfetch` to investigate the problem space like an investigative journalist:

- **Direct & Adjacent Competitors**: map market leaders, open-source challengers, and abandoned tools.
- **Furos, Fragmentos & Sinais Semi-Públicos (OSINT)**:
  - GitHub issues/PRs/commits sorted by reactions, bug labels, and unresolved architectural bottlenecks.
  - Job postings & engineering blogs of closed competitors (exposing internal tech debt, scaling ceilings, and stack dependencies).
  - Changelogs, postmortems, CVE advisories, Wayback Machine diffs, public API payloads, and package manifests.
  - User frustration mining (1-3 star reviews, Reddit/HN/X migration threads, "why I quit X" posts) to capture exact pain vocabulary.
  - Local binary/package inspection via `binary-triage` when authorized local artifacts exist.
- **Coverage strata (mandatory before synthesis)** - walk all five; each stratum is either cited or explicitly declared absent, no silent gaps:
  1. **Mainstream** sources (official docs, major publications, top repos/forums).
  2. **Academic / papers** (arXiv, conference sources, papers-with-code).
  3. **Surface-web long-tail** (blogs, Tumblr, Reddit, GitHub issues, changelogs, forums).
  4. **Multilingual / non-English** (at least one non-English pass when the topic has global uptake).
  5. **Diagonal synthesis** separating *evidence* (cited, observed) from *inference* (labeled as such).
  Self-quiz: every stratum cited or declared absent before synthesis.
- **Output**: Competitor Weakness & Opportunity Matrix with primary-source citations.

### Phase 2: First-Principles Truth & Master Architecture Justification

Read `reference/first-principles-justification.md`. Justify every feature and architectural choice from universal fundamentals down to concrete implementation:

1. **Axiomas & Limites Fundamentais da Área**:
   - Compute/hardware physics (CPU cache, RAM footprint, disk IOPS, network RTT, token/context entropy).
   - Human cognitive bounds (Doherty threshold <400ms, Hick's Law, Fitts's Law, Miller's Law, zero-manual mental model).
   - Domain-specific mathematical/economic laws.
2. **Product Master Layer (Ex-FAANG PM / Staff Product Architect)**:
   - JTBD job stories (`When <situation>, I want to <motivation>, so I can <outcome>`).
   - Feature table with explicit **RICE** scores (`Reach * Impact * Confidence / Effort`) and **Kano** class (`Basic`, `Performance`, `Delighter`).
   - North Star Metric + Counter-Metric (to prevent gaming).
   - Aggressive Non-Goals (what the tool refuses to be).
   - **Why Better Than Every Market Alternative**: per-feature proof linking competitor failure mode -> first-principles insight -> our structural advantage -> measurable superiority metric.
3. **Tech Lead & Senior/Principal Software Architect Layer**:
   - Deep Modules (Ousterhout): maximum power behind minimal interface surface.
   - Bounded contexts, data ownership, state machine, and error taxonomy.
   - ADRs with **Top-2 Debate**, **Rejected Alternative**, and explicit **Kill Criterion** (what measurement would force revisiting the decision).
   - Numeric NFR budgets (p50/p95/p99 latency, memory ceiling, cold-start time, failure recovery time).

### Phase 3: Atomic & Modular Hardening + Optimization

Read `reference/atomic-modular-hardening.md`. Specify concrete engineering controls at both granularities:

| Granularity | Hardening (Security, Resilience, Invariants) | Optimization (Latency, Memory, Throughput, Lean Code) |
|---|---|---|
| **Atomic Level** (functions, parsers, queries, I/O calls, prompts, state transitions) | Parse-don't-validate at boundaries; strict schema types; explicit timeouts on all I/O; idempotency keys; overwrite refusal (`--out` guard / `O_EXCL`); constant-time secret checks; UTF-8 pinning; zero secret logging; deterministic exit/error codes. | Algorithmic floor ($O(1)$ / $O(n)$); zero redundant allocations/serialization; streaming over full-file buffering; stdlib-first minimal deps; Rust PyO3 `abi3` core (ADR-003) when CPU/memory-tight. |
| **Modular Level** (modules, seams, IPC/APIs, subagent DAGs, storage layers) | Narrow module seams; contract tests at boundaries; blast-radius isolation (bulkheads/worktrees); fail-closed gates; Envelope v2 provenance (`api_version: 2`, `meta.answered_by`); append-only ledgers; zero circular dependencies. | Critical-path minimization; lazy loading / progressive disclosure; batch perceive-act-verify cycles; zero N+1 queries or chatty IPC; bounded concurrency with backpressure. |

### Phase 4: Contact Surfaces Excellence

Read `reference/contact-surfaces-excellence.md`. Enumerate every surface where a human or agent interacts with the system (CLI, UI/UX, API/SDK, Onboarding/Setup, Error/Recovery messages, Documentation) and design each surface against the 4 mandatory imperatives:

1. **Facilitar**: minimize Time-to-Value (TTV), step count, and cognitive load; zero-config sensible defaults; one-command or one-click happy path.
2. **Resolver**: close the user's loop end-to-end without leaving manual glue steps; errors state exact cause + copy-pasteable fix command.
3. **Impressionar**: sub-100ms feedback where possible, distinctive intentional craft (`impeccable` / `frontend-design`), high-signal telemetry/output that feels 10x sharper than incumbents.
4. **Ser Intuitivo**: zero-manual discoverability, Nielsen heuristics compliance, poka-yoke guardrails that make the wrong action hard and the right action obvious.

### Phase 5: Prompt Delta Approval & Artifact Materialization

1. Present a **Prompt Evolution Table** to the user via `ask_user_question` (one batched round; AFK mode: mark `PENDING-APPROVAL`, proceed with recommendation):
   - Show each proposed addition, refinement, or structural expansion relative to the original prompt.
   - Let the user approve, amend, or reject each delta while guaranteeing 100% fidelity to the original philosophy.
2. Write `.devin/specs/<slug>-idea-dossier.md` using `templates/idea-dossier.md`.
3. Write `.devin/specs/<slug>-compiled-prompt.md` using `templates/compiled-prompt.md` (containing the verbatim original prompt + `original_prompt_sha256` + approved delta log + the self-contained Master Prompt).
4. Verify with commands, not inspection (Rule 15):
   - Recompute the seed hash and prove the verbatim block inside the compiled prompt matches the frozen seed:
     `python -c "import hashlib;print(hashlib.sha256(open('.devin/specs/<slug>-seed.txt','rb').read()).hexdigest())"`
     must equal `original_prompt_sha256` in both artifact frontmatters.
   - `rg -n "TBD|TODO|<[A-Z_]+>" .devin/specs/<slug>-*.md` must return nothing outside the frozen original prompt block.
   - Both files exist and are non-empty; `status:` reflects reality (`APPROVED` only after user approval; `DRAFT-AUTO` if AFK).
5. Offer the downstream handoff (`project-orchestrator`, `planning`, or `grilling`).

## Cross-Skills

- Upstream entry: `/leo` or `ask-bundle` routes raw ideas and prompt-elevation requests here.
- During execution: invokes `research` / `agent-reach` / `scrape-tools` / `binary-triage` for Phase 1 OSINT; applies `architecture`, `security`, `performance`, `lean-code`, and `impeccable` principles in Phases 2-4.
- Downstream handoff: feeds `.devin/specs/<slug>-idea-dossier.md` and `.devin/specs/<slug>-compiled-prompt.md` into `project-orchestrator` (skips P0 Analyst if vision is complete), `planning` (Spec / Plan-doc / Tickets), or the 7-persona Agency Pipeline (`product-manager` -> `tech-lead` -> `art-director` -> `security-auditor` -> `scrum-master` -> `copywriter`).
