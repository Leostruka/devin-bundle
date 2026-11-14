# Montador de Ideias Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `montador-de-ideias` skill (`skills/montador-de-ideias/`) and wire it into `/leo`, `ask-bundle`, and bundle metadata so any raw project idea or prompt can be expanded into a first-principles investigative dossier and a compiled master prompt without ever mutating the user's original prompt without explicit, option-driven user guidance.

**Spec:**
- What/why (tech-agnostic): Users starting with a seed idea or prompt need a rigorous way to transform it into an indisputable, market-superior project specification and master prompt. The skill combines investigative journalism/OSINT (finding competitor flaws, leaks, fragments, job-posting clues, and user complaints), first-principles grounding across every discipline, Tech Lead + Staff Product/Software Architect decision frameworks, atomic and modular hardening/optimization, and a contact-surface bar focused on facilitating, solving, impressing, and being intuitive - while strictly protecting the user's original prompt behind interactive option gates.
- User stories:
  1. As a creator with a raw project prompt, I want the agent to interview me with concrete ideas, options, and trade-offs before changing a single word of my original prompt, so that my tool's core philosophy, target problem, and user pain point are preserved strictly.
  2. As a product/technical strategist, I want the agent to investigate the market like an investigative journalist (public/semi-public fragments, issues, changelogs, job posts, user complaints, archived docs, package manifests) and justify every architectural and product decision from first principles down to why it beats every competitor on the market.
  3. As a Staff Engineer, I want every component specified with atomic-level and modular-level hardening and optimization, and every contact surface designed to facilitate, solve, impress, and be intuitive, outputting both an Investigative & Architectural Dossier and a Compiled Master Prompt.
  4. As a bundle user, I want to invoke `montador-de-ideias` directly via `/montador-de-ideias` or through `/leo` and `ask-bundle` routing.
- Acceptance criteria:
  1. `skills/montador-de-ideias/SKILL.md` passes `python scripts/validate-skill-format.py` with score 100 and 0 issues.
  2. Reference docs (`journalistic-osint-protocol.md`, `first-principles-justification.md`, `atomic-modular-hardening.md`, `contact-surfaces-excellence.md`) and templates (`idea-dossier.md`, `compiled-prompt.md`) exist under `skills/montador-de-ideias/` and codify all required philosophies.
  3. Original-prompt immutability gate is codified: `original_prompt_sha256` is recorded, original text is preserved verbatim, and every proposed change requires `ask_user_question` approval with options and trade-offs.
  4. `skills/leo/SKILL.md`, `skills/ask-bundle/SKILL.md`, and `skills/ask-bundle/modes/flows-detail.md` route raw idea assembly and prompt elevation to `montador-de-ideias` (both Situation Router and Quick-start menu).
  5. `manifest.json`, `README.md`, `.devin/docs/SKILL-TIERS.md`, and `.devin/docs/TOOLS-MAP.md` are synchronized (`184` -> `185` skills), and `python audit.py` + `python -m pytest` pass with 0 errors.

**Architecture:** A modular, progressive-disclosure skill under `skills/montador-de-ideias/`. `SKILL.md` (<10KB) holds the 6-phase execution pipeline, hard gates (original-prompt protection + `ask_user_question` alignment rounds), subagent delegation rules (`researcher` on `swe-2-max`), and verification gates. Four reference modules under `reference/` hold the deep playbooks (Journalistic OSINT, First-Principles + Tech Lead/Staff Architect Justification, Atomic/Modular Hardening & Optimization, Contact Surfaces Excellence), and two templates under `templates/` define the exact schemas for `.devin/specs/<slug>-idea-dossier.md` and `.devin/specs/<slug>-compiled-prompt.md`.

**Tech Stack:** Markdown skill/reference/template artifacts, Python 3.11+ (`pytest`, `audit.py`, `scripts/validate-skill-format.py`), JSON (`manifest.json`).

## Global Constraints

- Zero AI service signatures or trailers in any file or commit (Rule 2).
- Zero em-dashes (U+2014) or en-dashes (U+2013) in any file; use ASCII `-` or `->` (`scripts/no-em-dash.py` PreToolUse hook enforces this).
- All text-mode file I/O in Python tests/scripts must pin `encoding="utf-8"` and `subprocess.run(..., text=True, encoding="utf-8", errors="replace")` (Rule / audit check [37]-[38]).
- Python 3.11 compatibility floor (no `Path.read_text(newline=)`, `itertools.batched`, or `Path.walk()`).
- Subagent references must use bundle-approved free profiles (`researcher`, `architect`, `security-auditor`, `qa-ci` on `swe-2-max` / `swe-2-flash-high` / `swe-2-flash-medium`; never `subagent_explore` or paid model aliases per Rule 20).
- `SKILL.md` frontmatter `description` must start with `Use when` and match `manifest.json` `skills[].purpose` after whitespace normalization (audit check [26]).
- Every task must pass its Verification Function (`gate:` / `expect:` / `evidence:`) before marking `completed`.

## Proposed Modules and Interfaces

| Path | Lifespan | Responsibility |
|---|---|---|
| `skills/montador-de-ideias/SKILL.md` | Living | Core 6-phase pipeline, hard gates, `ask_user_question` protocol for prompt changes, subagent dispatch, and output verification. |
| `skills/montador-de-ideias/reference/journalistic-osint-protocol.md` | Living | Investigative journalism & ethical OSINT protocol: public/semi-public channels, fragment triangulation, competitor teardown, PRISMA-lite + lateral reading. |
| `skills/montador-de-ideias/reference/first-principles-justification.md` | Living | Universal truth / first-principles derivation framework: physical/theoretical limits, Staff PM (JTBD, RICE, Kano, North Star), Tech Lead/Principal Architect (Deep Modules, ADRs + kill criteria, NFR budgets), and bundle rules. |
| `skills/montador-de-ideias/reference/atomic-modular-hardening.md` | Living | Atomic-level and modular-level hardening + optimization matrices and checklists. |
| `skills/montador-de-ideias/reference/contact-surfaces-excellence.md` | Living | Contact surface design bar across UI, CLI, API, Docs, and Onboarding: Facilitar, Resolver, Impressionar, Ser Intuitivo. |
| `skills/montador-de-ideias/templates/idea-dossier.md` | Living | Output template for `.devin/specs/<slug>-idea-dossier.md`. |
| `skills/montador-de-ideias/templates/compiled-prompt.md` | Living | Output template for `.devin/specs/<slug>-compiled-prompt.md` (with verbatim original prompt, `original_prompt_sha256`, and approved delta table). |
| `skills/leo/SKILL.md` | Living | Universal orchestrator router updated with `montador-de-ideias` in Situation Router and Quick-start menu. |
| `skills/ask-bundle/SKILL.md` | Living | Meta-router updated with `montador-de-ideias` in Situation Router, main flow, and Quick-start menu. |
| `skills/ask-bundle/modes/flows-detail.md` | Living | Detailed flow map updated with `montador-de-ideias` as upstream idea-assembly on-ramp. |
| `.devin/docs/SKILL-TIERS.md` | Living | Tier index updated with `montador-de-ideias` under `Planejamento/decisão` and count `184` -> `185`. |
| `.devin/docs/TOOLS-MAP.md` | Living | Skills count updated `184 skills` -> `185 skills`. |
| `README.md` | Living | Skills badge and prose counts updated `184` -> `185`. |
| `manifest.json` | Living | `skill_count` `184` -> `185` and `montador-de-ideias` skill entry added in alphabetical order. |
| `tests/validation/test_montador_de_ideias.py` | Living | Contract test suite for `montador-de-ideias` and its router bindings. |
| `tests/validation/test_ask_bundle_router.py` | Living | Router contract test updated to assert `montador-de-ideias`. |

---

### Task 1: Core Skill & Original-Prompt Protection Gate (`skills/montador-de-ideias/SKILL.md`)

**Files:**
- Create (living): `skills/montador-de-ideias/SKILL.md`
- Create (living): `tests/validation/test_montador_de_ideias.py`

**Interfaces:**
- Consumes: user's seed idea or original prompt; `ask_user_question` tool; `run_subagent` (`researcher`).
- Produces: `skills/montador-de-ideias/SKILL.md` defining the 6-phase pipeline (`P0 Anchor & Philosophy Interview` -> `P1 Journalistic OSINT & Competitor Teardown` -> `P2 First-Principles & Architectural Truth` -> `P3 Atomic & Modular Hardening/Optimization` -> `P4 Contact Surfaces Excellence` -> `P5 Prompt Delta Approval & Compilation`).

**Verification Function (VF):**
- `gate:` `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_skill_frontmatter_and_core_pipeline" -v && python scripts/validate-skill-format.py skills`
- `expect:` Exit code 0; `1 passed` in pytest; `[PASS] montador-de-ideias\SKILL.md (score: 100)` and `Failing: 0` in `validate-skill-format.py`.
- `evidence:` Pytest and `validate-skill-format.py` stdout captured in session output.

- [ ] **Step 1: Write the failing contract test for `SKILL.md` frontmatter and core pipeline**

Create `tests/validation/test_montador_de_ideias.py`:

```python
"""Contract tests for skills/montador-de-ideias and its /leo + ask-bundle routing."""
from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILL_DIR = ROOT / "skills" / "montador-de-ideias"
SKILL_MD = SKILL_DIR / "SKILL.md"

REFERENCES = [
    "journalistic-osint-protocol.md",
    "first-principles-justification.md",
    "atomic-modular-hardening.md",
    "contact-surfaces-excellence.md",
]

TEMPLATES = [
    "idea-dossier.md",
    "compiled-prompt.md",
]


def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_skill_frontmatter_and_core_pipeline():
    assert SKILL_MD.is_file(), "skills/montador-de-ideias/SKILL.md missing"
    text = skill_text()
    assert text.startswith("---\n"), "missing YAML frontmatter start"
    parts = text.split("---", 2)
    assert len(parts) >= 3, "unclosed YAML frontmatter"
    fm = parts[1]
    assert "name: montador-de-ideias" in fm
    desc_lines = [line for line in fm.splitlines() if line.startswith("description:")]
    assert len(desc_lines) == 1
    assert "Use when" in desc_lines[0]
    assert "triggers: [user, model]" in fm

    for required_token in (
        "original_prompt_sha256",
        "ask_user_question",
        "HARD-GATE",
        "journalistic-osint-protocol.md",
        "first-principles-justification.md",
        "atomic-modular-hardening.md",
        "contact-surfaces-excellence.md",
        "idea-dossier.md",
        "compiled-prompt.md",
        "Facilitar",
        "Resolver",
        "Impressionar",
        "Ser Intuitivo",
        "researcher",
    ):
        assert required_token in text, f"SKILL.md missing required token: {required_token}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_skill_frontmatter_and_core_pipeline" -v`
Expected: FAIL with `AssertionError: skills/montador-de-ideias/SKILL.md missing`

- [ ] **Step 3: Create `skills/montador-de-ideias/SKILL.md`**

Create `skills/montador-de-ideias/SKILL.md`:

```markdown
---
name: montador-de-ideias
description: Use when assembling, expanding, or elevating a raw project idea or initial prompt into an ultra-detailed, first-principles dossier and compiled master prompt with journalistic OSINT market research, Tech Lead and Staff Architect justifications, atomic and modular hardening/optimization, and high-impact contact surfaces.
triggers: [user, model]
---

# Montador de Ideias

## Overview

Transform any seed project idea or raw prompt into two verified, traceable artifacts:
1. **Investigative & First-Principles Dossier** (`.devin/specs/<slug>-idea-dossier.md`)
2. **Compiled Master Prompt** (`.devin/specs/<slug>-compiled-prompt.md`)

Every proposal is grounded in the fundamental axioms of each involved discipline (physical/compute limits, cognitive psychology, economics, software architecture, security, UX) and competitive OSINT evidence proving why and how the design outperforms market incumbents across every axis.

Detail playbooks (load on demand):
- `reference/journalistic-osint-protocol.md` - investigative journalism, public/semi-public leak/fragment mining, competitor teardown, PRISMA-lite + lateral reading.
- `reference/first-principles-justification.md` - first-principles derivation + Ex-FAANG PM (JTBD/RICE/Kano) + Principal Tech Lead/Architect (Deep Modules, ADRs with kill criteria, NFR budgets) + bundle philosophies.
- `reference/atomic-modular-hardening.md` - atomic-level and modular-level hardening and optimization matrices.
- `reference/contact-surfaces-excellence.md` - contact surface design bar: **Facilitar, Resolver, Impressionar, Ser Intuitivo**.
- `templates/idea-dossier.md` and `templates/compiled-prompt.md` - mandatory output schemas.

<HARD-GATE>
1. ORIGINAL PROMPT IMMUTABILITY: Compute `original_prompt_sha256` of the user's seed prompt immediately and store the verbatim text in a frozen block. NEVER alter, delete, dilute, or silently reinterpret any requirement from the original prompt.
2. GUIDANCE BEFORE ANY PROMPT CHANGE: Before adding, modifying, or reframing any part of the original prompt, you MUST ask the user via `ask_user_question` (1-4 questions per call, 2-4 concrete options with trade-offs + recommended stance) to align on the tool's philosophy, the core problem it solves, the acute pain point it heals, and which proposed expansions they approve.
3. NO DEDUCTION WITHOUT EVIDENCE: Competitor weaknesses, technical limits, and architectural trade-offs must be verified with tools (`researcher` subagent, `agent-reach`, `scrape-tools`, `web_search`, `webfetch`, `grep`, `read`) before being stated as fact (Rule 12).
</HARD-GATE>

## Pipeline (6 Atomic Phases)

### Phase 0: Anchor & Philosophy Alignment (`ask_user_question`)

1. Capture the verbatim seed prompt and compute `original_prompt_sha256`.
2. Extract what is already explicit vs. what is underspecified across four axes:
   - **Filosofia da Ferramenta**: worldview, non-negotiable principles, identity.
   - **Problema Raiz**: structural cause vs. symptom.
   - **Dor Real (Pain Point)**: who suffers, how often, cost of inaction, why current workarounds fail.
   - **Restrições Inegociáveis**: stack, privacy/local-first, latency, budget, platform.
3. Run frontier rounds with `ask_user_question` (1-4 questions per call, 2-4 options + recommendation). Do not proceed until the user confirms the philosophy and pain-point anchor.

### Phase 1: Journalistic OSINT & Competitor Teardown

Read `reference/journalistic-osint-protocol.md`. Dispatch `researcher` (`model: swe-2-max`, free) and/or run `agent-reach`, `scrape-tools`, `web_search`, and `webfetch` to investigate the problem space like an investigative journalist:

- **Direct & Adjacent Competitors**: map market leaders, open-source challengers, and abandoned tools.
- **Furos, Fragmentos & Sinais Semi-Públicos (OSINT)**:
  - GitHub issues/PRs/commits sorted by reactions, bug labels, and unresolved architectural bottlenecks.
  - Job postings & engineering blogs of closed competitors (exposing internal tech debt, scaling ceilings, and stack dependencies).
  - Changelogs, postmortems, CVE advisories, Wayback Machine diffs, public API payloads, and package manifests.
  - User frustration mining (1-3 star reviews, Reddit/HN/X migration threads, "why I quit X" posts) to capture exact pain vocabulary.
  - Local binary/package inspection via `binary-triage` when authorized local artifacts exist.
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

1. Present a **Prompt Evolution Table** to the user via `ask_user_question`:
   - Show each proposed addition, refinement, or structural expansion relative to the original prompt.
   - Let the user approve, amend, or reject each delta while guaranteeing 100% fidelity to the original philosophy.
2. Write `.devin/specs/<slug>-idea-dossier.md` using `templates/idea-dossier.md`.
3. Write `.devin/specs/<slug>-compiled-prompt.md` using `templates/compiled-prompt.md` (containing the verbatim original prompt + `original_prompt_sha256` + approved delta log + the self-contained Master Prompt).
4. Verify both files exist, are non-empty, contain zero placeholders (`TBD`/`TODO`), and offer the downstream handoff (`project-orchestrator`, `planning`, or `grilling`).

## Cross-Skills

- Upstream entry: `/leo` or `ask-bundle` routes raw ideas and prompt-elevation requests here.
- During execution: invokes `research` / `agent-reach` / `scrape-tools` / `binary-triage` for Phase 1 OSINT; applies `architecture`, `security`, `performance`, `lean-code`, and `impeccable` principles in Phases 2-4.
- Downstream handoff: feeds `.devin/specs/<slug>-idea-dossier.md` and `.devin/specs/<slug>-compiled-prompt.md` into `project-orchestrator` (skips P0 Analyst if vision is complete), `planning` (Spec / Plan-doc / Tickets), or the 7-persona Agency Pipeline (`product-manager` -> `tech-lead` -> `art-director` -> `security-auditor` -> `scrum-master` -> `copywriter`).
```

- [ ] **Step 4: Run test and skill format validator to verify they pass**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_skill_frontmatter_and_core_pipeline" -v && python scripts/validate-skill-format.py skills`
Expected: PASS (`1 passed`, `Failing: 0`)

---

### Task 2: Reference Playbooks (`reference/*.md`) for OSINT, First Principles, Hardening/Optimization, and Contact Surfaces

**Files:**
- Create (living): `skills/montador-de-ideias/reference/journalistic-osint-protocol.md`
- Create (living): `skills/montador-de-ideias/reference/first-principles-justification.md`
- Create (living): `skills/montador-de-ideias/reference/atomic-modular-hardening.md`
- Create (living): `skills/montador-de-ideias/reference/contact-surfaces-excellence.md`
- Modify: `tests/validation/test_montador_de_ideias.py`

**Interfaces:**
- Consumes: `skills/montador-de-ideias/SKILL.md` pointers.
- Produces: The 4 deep reference documents required by Phases 1-4 of `montador-de-ideias`.

**Verification Function (VF):**
- `gate:` `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_reference_playbooks_complete" -v`
- `expect:` Exit code 0; all 4 reference files exist and contain their domain-specific protocols, tables, and checklists.
- `evidence:` Pytest output showing `test_reference_playbooks_complete PASSED`.

- [ ] **Step 1: Add the failing test `test_reference_playbooks_complete` to `tests/validation/test_montador_de_ideias.py`**

Append to `tests/validation/test_montador_de_ideias.py`:

```python
def test_reference_playbooks_complete():
    for name in REFERENCES:
        path = SKILL_DIR / "reference" / name
        assert path.is_file(), f"missing reference playbook: {name}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 800, f"reference playbook too short: {name}"

    osint = (SKILL_DIR / "reference" / "journalistic-osint-protocol.md").read_text(encoding="utf-8")
    for token in ("PRISMA-lite", "lateral reading", "changelogs", "job postings", "Wayback", "binary-triage"):
        assert token in osint, f"journalistic-osint-protocol.md missing {token}"

    fp = (SKILL_DIR / "reference" / "first-principles-justification.md").read_text(encoding="utf-8")
    for token in ("First Principles", "RICE", "Kano", "JTBD", "Deep Modules", "Kill Criterion", "NFR"):
        assert token in fp, f"first-principles-justification.md missing {token}"

    hardening = (SKILL_DIR / "reference" / "atomic-modular-hardening.md").read_text(encoding="utf-8")
    for token in ("Atomic Hardening", "Atomic Optimization", "Modular Hardening", "Modular Optimization", "Envelope v2", "ADR-003"):
        assert token in hardening, f"atomic-modular-hardening.md missing {token}"

    surfaces = (SKILL_DIR / "reference" / "contact-surfaces-excellence.md").read_text(encoding="utf-8")
    for token in ("Facilitar", "Resolver", "Impressionar", "Ser Intuitivo", "Time-to-Value", "Nielsen", "Doherty"):
        assert token in surfaces, f"contact-surfaces-excellence.md missing {token}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_reference_playbooks_complete" -v`
Expected: FAIL with `AssertionError: missing reference playbook: journalistic-osint-protocol.md`

- [ ] **Step 3: Create the 4 reference playbooks under `skills/montador-de-ideias/reference/`**

Create `skills/montador-de-ideias/reference/journalistic-osint-protocol.md`:

```markdown
# Journalistic OSINT & Competitive Intelligence Protocol

## Purpose

Investigate the problem space and competing products like an investigative tech journalist combined with a Staff Reverse-Engineering & Product Analyst. Never accept a competitor's landing page at face value. When a competitor is closed-source or private, reconstruct its architecture, bottlenecks, and blind spots from public and semi-public fragments.

## Rules of Engagement (Ethical OSINT & Primary-Source Discipline)

- Operate strictly on public, semi-public, or user-provided/authorized artifacts (Rule 13 & Safety rules: never harvest private credentials, cookies, or unauthorized endpoints).
- Apply **PRISMA-lite** and **lateral reading**: log every search query, cross-check vendor claims against independent sources, and verify both existence and entailment of every cited source.
- Never deduce what a competitor does when a tool (`web_search`, `webfetch`, `agent-reach`, `scrape-tools`, `binary-triage`) can observe it directly.

## The 7 Investigative Channels (Fragment Triangulation)

| Channel | What to Hunt ("Furos & Fragmentos") | Tools | Strategic Signal Extracted |
|---|---|---|---|
| **1. Issue Trackers, PRs & Changelogs** | Most-upvoted open issues, recurring regressions, "wontfix" architectural limits, breaking-change release notes. | `gh`, `web_search`, `webfetch` | Structural ceilings the incumbent cannot fix without rewriting their core. |
| **2. Engineering Job Postings & Tech Blogs** | Required skills in Senior/Staff roles (e.g., "experience migrating from X to Y", "fixing memory leaks in Electron/Python"), conference talks, postmortems. | `web_search`, `scrape-tools` | Unannounced stack debt, scaling pain points, and internal roadmap direction of private companies. |
| **3. User Pain & Migration Forensics** | 1-3 star reviews (G2, Capterra, App Store, Play Store, Chrome Web Store), Reddit/HN/X threads ("switching from X", "X is slow/broken when..."). | `agent-reach`, `scrape-tools`, `web_search` | Exact verbatim pain vocabulary, broken workflows, pricing resentment, and unmet edge cases. |
| **4. Historical Diffs & Pricing/Docs Drift** | Wayback Machine snapshots of docs, pricing pages, terms of service, and deprecated API pages; removed features or silent enterprise paywalls. | `webfetch`, `web_search` | Features users lost, dark patterns introduced, and commoditized vs. gated capabilities. |
| **5. Public Artifacts, Packages & Schemas** | Published npm/PyPI/Cargo manifests, OpenAPI/GraphQL schemas, public bundle size (Bundlephobia), source maps, public telemetry/benchmarks. | `web_search`, `webfetch`, `exec` | Dependency bloat, real runtime footprint, API contract rigidity, and attack surface. |
| **6. Patents, Papers & Standards** | ArXiv papers cited by founders, patent filings, RFCs, and regulatory filings. | `web_search`, `webfetch` | Core algorithmic assumptions and theoretical limits of their approach. |
| **7. Authorized Local Binary/App Triage** | When a local binary/installer/package is legitimately present in the workspace: symbol tables, exported functions, embedded strings, engine versions. | `binary-triage` | Exact native dependencies, runtime engine, and architectural seams without guesswork. |

## Competitor Teardown Synthesis Table

Every `montador-de-ideias` dossier MUST include a filled table with at least 3 incumbents or adjacent workarounds:

| Incumbent / Workaround | Core Architecture (Observed via OSINT) | Verified Structural Flaw / Bottleneck (Cited Source) | User Pain Caused | How Our Design Eliminates This at the Root |
|---|---|---|---|---|
| `<Competitor A>` | `<Observed stack/model>` | `<Issue/Job post/Benchmark link + quote>` | `<Pain metric>` | `<First-principles counter-architecture>` |

## Coverage Self-Quiz (Gate Before Leaving Phase 1)

1. Did I name at least 3 real competitors or existing user workarounds?
2. Does every critical claim about a competitor cite a verifiable primary or OSINT source (not vendor marketing)?
3. Can I state in one sentence the single structural reason why incumbents fail to heal the user's acute pain?
```

Create `skills/montador-de-ideias/reference/first-principles-justification.md`:

```markdown
# First-Principles Justification & Master Architecture Playbook

## Purpose

Every decision in the assembled idea must be justified from the "ground truth" of the domain up to its market superiority. No cargo-cult stack choices, no "because it is popular", and no hand-waving.

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
```

Create `skills/montador-de-ideias/reference/atomic-modular-hardening.md`:

```markdown
# Atomic & Modular Hardening and Optimization Matrix

## Purpose

Ensure every idea assembled by `montador-de-ideias` is engineered for extreme robustness (hardening) and peak efficiency (optimization) at two distinct scales: **Atomic Level** (the smallest unit of execution/data) and **Modular Level** (the composition of subsystems and boundaries).

## 1. Atomic Level (Functions, Data Types, Inputs, Queries, Prompts, Syscalls)

### 1.1 Atomic Hardening Checklist

Every atomic unit in the specification must enforce:
1. **Parse, Don't Validate**: untrusted inputs (CLI args, JSON payloads, web responses, user text, file paths) are parsed into strict, immutable types at the entry boundary; raw strings/dicts never propagate inward.
2. **Minimize Contact Surface (`sec-needs`)**: every line of code and every input field is attack surface. Strip unused fields, sanitize paths against traversal (`..`, symlink escapes), and bound string/payload lengths.
3. **Safe File & Output Semantics**:
   - User-named output paths (`--out`, `-o`, `dst`) refuse to overwrite existing files unless `--force` is explicitly passed (`O_EXCL` / pre-flight check, exit code 2).
   - Atomic writes via temp-file + rename when state corruption on crash is possible.
   - Explicit `encoding="utf-8"` on all text I/O and `errors="replace"` on subprocess streams.
4. **Timeouts & Resource Bounds**: zero unbounded network calls, regexes, loops, or subprocesses; every external operation declares an explicit timeout and max-bytes ceiling.
5. **Secret & Side-Channel Hygiene**:
   - Never log, print, or serialize secrets, tokens, or raw credentials in error traces.
   - Constant-time comparison (`hmac.compare_digest`) for tokens/hashes/signatures to prevent timing side-channels.
6. **Deterministic Error Taxonomy**: every failure returns a typed error envelope (`{"ok": false, "error": ..., "code": ...}`) and exits non-zero; zero silent `except: pass`.

### 1.2 Atomic Optimization Checklist

Every hot-path atomic unit must specify:
1. **Algorithmic Complexity Floor**: state time and space complexity ($O(1)$, $O(\log n)$, $O(n)$); ban accidental $O(n^2)$ scans, repeated regex compilations, or redundant AST/JSON parses.
2. **Zero-Waste Memory & I/O**: stream or chunk large inputs instead of loading whole files into memory; reuse buffers/connections; avoid intermediate copies.
3. **Stdlib-First & Native Acceleration (ADR-003)**:
   - Prefer zero-dependency stdlib primitives over heavy third-party packages.
   - When an atomic operation is CPU-bound, latency-critical (<10ms), or memory-intensive, specify a Rust `PyO3` (`abi3`) extension crate with a clean Python fallback.
4. **Token & Prompt Density (for AI-native units)**: compress schemas, support `--detail brief|compact|full` output tiers, and eliminate redundant prose in agent-consumed outputs.

---

## 2. Modular Level (Subsystems, Seams, APIs, Storage, Multi-Agent Flows)

### 2.1 Modular Hardening Checklist

Every module and inter-module boundary must enforce:
1. **Deep Modules & Narrow Seams**: modules expose a minimal, stable contract and encapsulate all internal state, retry logic, and platform quirks.
2. **Least Privilege & Network Isolation**: each service, worker, or subagent receives only the exact permissions, tools, and file scopes required for its contract (private VPC/localhost by default; public endpoints require explicit justification and auth).
3. **Fail-Closed Gates & Circuit Breakers**:
   - When a validator, guard, or upstream dependency fails or abstains, default to `BLOCKED` / deny - never silently promote unverified state.
   - Bound retry loops (e.g., max 2 rework cycles before escalating to the human operator).
4. **Provenance & Contract Envelopes (Envelope v2)**:
   - Inter-module and CLI JSON outputs carry `api_version: 2` and `meta.answered_by: {bundle, wrapper}` plus content hashes (`sha256` / `sha8`) of upstream inputs so stale or drifted state is detected immediately.
5. **Blast-Radius Isolation**:
   - Writing workers operate in isolated git worktrees or sandboxed containers.
   - Append-only state ledgers ensure crashes never corrupt historical progress.

### 2.2 Modular Optimization Checklist

Every subsystem topology must specify:
1. **Critical-Path Compression**: identify the longest sequential chain in the DAG; parallelize independent nodes (capped at 1-3 concurrent subagents to control token/compute cost).
2. **Batch Perceive-Act-Verify Cycles**: collapse chatty multi-round IPC, N+1 DB queries, or screenshot-per-click loops into batched atomic transactions.
3. **Lazy Enablement & Progressive Disclosure**: load heavy plugins, MCP servers, models, or reference docs only when their trigger predicate fires; keep cold-start near zero.
4. **Idempotent Caching & Content-Addressed Skip**: if an artifact exists and its `upstream_hashes` match current inputs, skip recomputation in $O(1)$.
```

Create `skills/montador-de-ideias/reference/contact-surfaces-excellence.md`:

```markdown
# Contact Surfaces Excellence: Facilitar, Resolver, Impressionar, Ser Intuitivo

## Purpose

A contact surface is any boundary where a user, developer, operator, or agent touches the product: GUI, CLI, API/SDK, configuration file, onboarding flow, error message, notification, or documentation. In `montador-de-ideias`, every contact surface must be explicitly inventoried and engineered against four non-negotiable imperatives: **Facilitar, Resolver, Impressionar, e Ser Intuitivo**.

## The 4 Imperatives Matrix

| Imperative | Engineering Definition | Measurable Bar | Anti-Pattern (Forbidden) |
|---|---|---|---|
| **1. Facilitar** (Frictionless Convenience) | Eliminate setup ceremony, manual configuration, and cognitive tax between intent and result. | Time-to-Value (TTV) <= 60s (CLI/tool) or <= 3 clicks (UI); zero required config files for the default happy path. | Requiring the user to read 5 pages of docs, edit 3 YAML files, or pass 8 mandatory flags before the first successful run. |
| **2. Resolver** (End-to-End Resolution) | Solve the complete root problem, including edge cases and recovery, without dumping half-finished output on the user. | 100% of common failure modes emit root cause + exact copy-pasteable remediation command; zero dead-end states. | Returning partial/raw data that requires the user to write glue scripts, or emitting generic errors like `Invalid input` / `Error 500`. |
| **3. Impressionar** (Craft, Speed & Delight) | Deliver responsiveness, visual/structural clarity, and capability depth that feel a generation ahead of market alternatives. | Perceived feedback <= 100ms (Doherty threshold); Web Vitals LCP <= 2.5s, INP <= 200ms, CLS <= 0.1; crisp typography/ASCII/JSON ergonomics. | Sluggish unbuffered output, generic AI-slop UI templates, layout shifts, or verbose walls of unstructured text. |
| **4. Ser Intuitivo** (Zero-Manual Mental Model) | Align the interface with the user's existing mental model so the right action is obvious and mistakes are prevented by design (poka-yoke). | First-time user completes primary journey without external docs; 10/10 Nielsen heuristics pass; destructive actions require explicit `--confirm` / preview diff. | Hidden modes, surprising side effects, inconsistent verb/flag naming, or destructive defaults without dry-run preview. |

## Contact Surface Inventory Template

For every project assembled by `montador-de-ideias`, enumerate all active surfaces and fill this specification table:

| Surface | Target Actor (Human / Agent) | Como Vai Facilitar (TTV & Steps) | Como Vai Resolver (End-to-End Outcome & Error Recovery) | Como Vai Impressionar (Speed, Craft, Delighter) | Como Sera Intuitivo (Mental Model & Poka-Yoke) |
|---|---|---|---|---|---|
| **Onboarding / First Run** | Human / Dev | One-command install + auto-doctor check; <= 60s to first result. | Auto-detects environment gaps and offers exact fix commands. | Instant diagnostic summary with clear status badges. | Zero config required for default local workflow. |
| **Primary Interface (UI / CLI / API)** | Human / Agent | Sensible defaults; progressive flags (`--detail brief\|compact\|full`). | Executes full workflow and verifies output integrity automatically. | Sub-100ms feedback; structured deterministic output. | Verb-first grammar matching domain mental model; `--dry-run` support. |
| **Error & Edge Recovery** | Human / Agent | Pinpoints exact file/line/field that failed. | Provides copy-pasteable recovery command or safe rollback. | Clean, structured error card/JSON without noisy stack dumps. | Fails closed before any partial destructive side effect. |

## Verification via Excellence Gate

In downstream implementation (`project-orchestrator` G5), every contact surface declared here is verified not just by unit tests, but by walking and recording the real user path (`computer-use` `record.py` for GUI or terminal path walkthrough for CLI/API) and reviewing frame-by-frame against the 4 imperatives above.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_reference_playbooks_complete" -v`
Expected: PASS (`1 passed`)

---

### Task 3: Output Templates (`templates/idea-dossier.md` and `templates/compiled-prompt.md`)

**Files:**
- Create (living): `skills/montador-de-ideias/templates/idea-dossier.md`
- Create (living): `skills/montador-de-ideias/templates/compiled-prompt.md`
- Modify: `tests/validation/test_montador_de_ideias.py`

**Interfaces:**
- Consumes: Phases 0-5 outputs of `skills/montador-de-ideias/SKILL.md`.
- Produces: The two standardized deliverable templates for `.devin/specs/<slug>-idea-dossier.md` and `.devin/specs/<slug>-compiled-prompt.md`.

**Verification Function (VF):**
- `gate:` `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_templates_complete" -v`
- `expect:` Exit code 0; both templates exist and contain all required sections (including `original_prompt_sha256`, verbatim original prompt block, approved delta table, OSINT teardown, first-principles matrix, atomic/modular hardening & optimization, and contact surfaces table).
- `evidence:` Pytest output showing `test_templates_complete PASSED`.

- [ ] **Step 1: Add the failing test `test_templates_complete` to `tests/validation/test_montador_de_ideias.py`**

Append to `tests/validation/test_montador_de_ideias.py`:

```python
def test_templates_complete():
    for name in TEMPLATES:
        path = SKILL_DIR / "templates" / name
        assert path.is_file(), f"missing template: {name}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 600, f"template too short: {name}"

    dossier = (SKILL_DIR / "templates" / "idea-dossier.md").read_text(encoding="utf-8")
    for section in (
        "original_prompt_sha256",
        "## 1. Filosofia, Problema Raiz e Dor",
        "## 2. Dossie Investigativo & OSINT de Mercado",
        "## 3. Justificativa por Primeiros Principios",
        "## 4. Arquitetura Master (Product Manager + Tech Lead + Staff Architect)",
        "## 5. Hardening e Otimizacao (Nivel Atomico e Nivel Modular)",
        "## 6. Superficies de Contato (Facilitar, Resolver, Impressionar, Ser Intuitivo)",
    ):
        assert section in dossier, f"idea-dossier.md missing section: {section}"

    compiled = (SKILL_DIR / "templates" / "compiled-prompt.md").read_text(encoding="utf-8")
    for section in (
        "original_prompt_sha256",
        "## 1. Prompt Original (Preservado Intacto)",
        "## 2. Registro de Mudancas Aprovadas pelo Usuario",
        "## 3. Super-Prompt Compilado (Pronto para Execucao)",
    ):
        assert section in compiled, f"compiled-prompt.md missing section: {section}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_templates_complete" -v`
Expected: FAIL with `AssertionError: missing template: idea-dossier.md`

- [ ] **Step 3: Create `skills/montador-de-ideias/templates/idea-dossier.md` and `skills/montador-de-ideias/templates/compiled-prompt.md`**

Create `skills/montador-de-ideias/templates/idea-dossier.md`:

```markdown
---
schema_version: 1
artifact: .devin/specs/<slug>-idea-dossier.md
skill: montador-de-ideias
original_prompt_sha256: <sha256_of_verbatim_seed_prompt>
status: APPROVED
date: YYYY-MM-DD
---

# Dossie Mestre da Ideia: <Project Name>

## 1. Filosofia, Problema Raiz e Dor (Alinhado com o Usuario)

- **Filosofia Central e Visao de Mundo**: <core philosophy confirmed via ask_user_question>
- **Problema Raiz (Causa Estrutural vs. Sintoma)**: <root problem statement>
- **Dor Aguda a Sanar (Quem sofre, frequencia, custo atual)**: <pain point profile>
- **North Star Metric**: <primary measurable metric>
- **Counter-Metric (Guardrail de Qualidade)**: <counter-metric that prevents gaming>
- **Non-Goals (O que a ferramenta se recusa a ser)**:
  - <Non-goal 1>
  - <Non-goal 2>

## 2. Dossie Investigativo & OSINT de Mercado ("Olhar de Jornalista")

### 2.1 Fontes Primarias, Fragmentos e Furos Investigados

| Fonte / Canal OSINT | Tipo (Issue, Vaga, Changelog, Review, Pacote, Wayback) | Evidencia Verificada (URL / Citacao / Hash) | O que Revela sobre o Mercado |
|---|---|---|---|
| `<Source 1>` | `<Type>` | `<Evidence>` | `<Insight>` |

### 2.2 Teardown Competitivo e Matriz de Superioridade Absoluta

| Concorrente / Alternativa | Arquitetura Real Observada | Falha Estrutural / Gargalo Provado | Dor Gerada no Usuario | Nossa Vantagem Estrutural + Metrica de Superioridade |
|---|---|---|---|---|
| `<Incumbent 1>` | `<Observed architecture>` | `<Cited bottleneck>` | `<User pain>` | `<Why and how we beat it measurably>` |

## 3. Justificativa por Primeiros Principios (Verdade Fundamental de Cada Area)

| Decisao / Pilar do Produto | Axioma Fisico, Matematico ou Cognitivo (Fundamento da Area) | Derivacao por Primeiros Principios | Por que Vence Qualquer Abordagem Convencional |
|---|---|---|---|
| `<Decision 1>` | `<Doherty / Cache locality / Shannon / etc.>` | `<Mechanism>` | `<Measurable proof>` |

## 4. Arquitetura Master (Product Manager + Tech Lead + Staff Architect)

### 4.1 JTBD & Backlog Priorizado (RICE + Kano)

| ID | Job Story (JTBD) | Kano (Basic / Performance / Delighter) | Reach | Impact | Confidence | Effort | RICE Score | Criterio de Sucesso Mensuravel |
|---|---|---|---|---|---|---|---|---|
| F1 | `When ..., I want ..., so I can ...` | `<Class>` | `<R>` | `<I>` | `<C>` | `<E>` | `<Score>` | `<Pass/fail metric>` |

### 4.2 Deep Modules, Fronteiras e Contratos

| Modulo | Interface Publica (Minima e Tipada) | Complexidade Encapsulada Internamente | Invariantes Garantidos |
|---|---|---|---|
| `<Module 1>` | `<Signatures / CLI / API>` | `<Internal mechanics>` | `<Invariants>` |

### 4.3 ADRs com Alternativa Rejeitada e Kill Criterion

- **ADR-01: <Decision Title>**
  - **Contexto**: <problem and constraints>
  - **Decisao**: <chosen architecture>
  - **Alternativa Rejeitada**: <runner-up option and why it lost>
  - **Kill Criterion**: <exact quantitative threshold that forces revisiting this ADR>

### 4.4 Orcamentos de Requisitos Nao-Funcionais (NFR Budgets)

| Eixo | Meta (p50) | Teto Maximo (p95 / p99) | Como Sera Medido (VF) |
|---|---|---|---|
| Latencia / Tempo de Resposta | `<val>` | `<val>` | `<command/probe>` |
| Consumo de Memoria / Recursos | `<val>` | `<val>` | `<command/probe>` |
| Time-to-Value (Onboarding) | `<val>` | `<val>` | `<command/probe>` |

## 5. Hardening e Otimizacao (Nivel Atomico e Nivel Modular)

### 5.1 Nivel Atomico (Funcoes, Inputs, Queries, Payloads, I/O)

| Componente Atomico | Hardening (Sanitizacao, Tipos, Timeouts, Segredos, Idempotencia) | Otimizacao (Complexidade, Memoria, Streaming, Rust/Stdlib) | Gate de Verificacao |
|---|---|---|---|
| `<Atom 1>` | `<Atomic hardening controls>` | `<Atomic optimization controls>` | `<Test / command>` |

### 5.2 Nivel Modular (Subsistemas, Seams, IPC, Isolamento, DAG)

| Fronteira Modular | Hardening (Least Privilege, Fail-Closed, Envelope v2, Bulkhead) | Otimizacao (Caminho Critico, Batching, Cache Conteudo-Enderecado) | Gate de Verificacao |
|---|---|---|---|
| `<Module Boundary 1>` | `<Modular hardening controls>` | `<Modular optimization controls>` | `<Test / command>` |

## 6. Superficies de Contato (Facilitar, Resolver, Impressionar, Ser Intuitivo)

| Superficie de Contato | Ator | Como Vai Facilitar (TTV e Zero-Config) | Como Vai Resolver (Ponta a Ponta + Recuperacao de Erro) | Como Vai Impressionar (Velocidade, Craft e Delight) | Como Sera Intuitivo (Modelo Mental e Poka-Yoke) |
|---|---|---|---|---|---|
| `<Surface 1: CLI / UI / API / Onboarding>` | `<Human / Agent>` | `<Facilitate spec>` | `<Resolve spec>` | `<Impress spec>` | `<Intuitive spec>` |
```

Create `skills/montador-de-ideias/templates/compiled-prompt.md`:

```markdown
---
schema_version: 1
artifact: .devin/specs/<slug>-compiled-prompt.md
dossier_ref: .devin/specs/<slug>-idea-dossier.md
original_prompt_sha256: <sha256_of_verbatim_seed_prompt>
status: APPROVED
date: YYYY-MM-DD
---

# Super-Prompt Compilado: <Project Name>

## 1. Prompt Original (Preservado Intacto)

> SHA-256: `<sha256_of_verbatim_seed_prompt>`

```text
<EXACT_VERBATIM_USER_PROMPT_WITHOUT_ANY_MODIFICATION>
```

## 2. Registro de Mudancas Aprovadas pelo Usuario

Todas as expansoes e refinamentos abaixo foram submetidos ao usuario via `ask_user_question` com opcoes e trade-offs antes de compilar o prompt final:

| ID | Trecho / Ideia Original | Expansao / Refinamento Proposto | Opcao Escolhida pelo Usuario | Justificativa (Filosofia + Dor + Primeiros Principios) |
|---|---|---|---|---|
| D1 | `<Original excerpt or implicit gap>` | `<Proposed refinement>` | `<Approved option>` | `<Why this honors the philosophy and heals the pain>` |

## 3. Super-Prompt Compilado (Pronto para Execucao)

```markdown
# Nivel de Esforco Obrigatorio: MAX
# Perfil Operacional: Staff Product Architect + Principal Tech Lead + Security & Performance Engineer
# Referencia de Dossie: .devin/specs/<slug>-idea-dossier.md

## 1. Missao, Filosofia Inegociavel e Dor a Sanar
<Compiled mission, philosophy, root problem, acute pain point, North Star metric, counter-metric, and aggressive non-goals>

## 2. Superioridade de Mercado e Evidencia OSINT
<Synthesized competitive teardown rules: competitor traps to avoid and structural advantages to enforce>

## 3. Arquitetura de Primeiros Principios, Modulos Profundos e NFR Budgets
<Deep modules, bounded contexts, ADRs with kill criteria, and strict numeric NFR budgets>

## 4. Requisitos Obrigatorios de Hardening e Otimizacao Atomica
<Parse-don't-validate boundaries, timeouts, overwrite refusal, UTF-8 pinning, secret hygiene, complexity floors, streaming, and native acceleration rules>

## 5. Requisitos Obrigatorios de Hardening e Otimizacao Modular
<Narrow seams, fail-closed gates, Envelope v2 provenance, blast-radius isolation, batching, and critical-path rules>

## 6. Especificacao de Cada Superficie de Contato (Facilitar, Resolver, Impressionar, Ser Intuitivo)
<Per-surface requirements with TTV targets, step-count caps, error recovery messages, and UX/DX craft bar>

## 7. Criterios de Aceite e Verification Functions (VFs)
<Numbered acceptance criteria with exact gate/expect/evidence commands and held-out verification>
```
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_templates_complete" -v`
Expected: PASS (`1 passed`)

---

### Task 4: Wire `/leo` and `ask-bundle` Entry Points (Slash + Situation Router + Quick-Start Menu)

**Files:**
- Modify: `skills/leo/SKILL.md:95-160`
- Modify: `skills/ask-bundle/SKILL.md:25-105`
- Modify: `skills/ask-bundle/modes/flows-detail.md:13-35`
- Modify: `tests/validation/test_ask_bundle_router.py`
- Modify: `tests/validation/test_montador_de_ideias.py`

**Interfaces:**
- Consumes: `skills/montador-de-ideias/SKILL.md`.
- Produces: Direct routing from `/leo` and `ask-bundle` (both Situation Router table and Quick-start menu, keeping Quick-start menu within the 4-option limit of `ask_user_question`).

**Verification Function (VF):**
- `gate:` `python -m pytest tests/validation/test_ask_bundle_router.py tests/validation/test_montador_de_ideias.py -v && python scripts/validate-skill-format.py skills`
- `expect:` Exit code 0; all tests in `test_ask_bundle_router.py` and `test_montador_de_ideias.py` pass; `Failing: 0` in `validate-skill-format.py`.
- `evidence:` Pytest and `validate-skill-format.py` stdout.

- [ ] **Step 1: Add failing router tests to `tests/validation/test_montador_de_ideias.py` and `tests/validation/test_ask_bundle_router.py`**

Append to `tests/validation/test_montador_de_ideias.py`:

```python
def test_leo_and_ask_bundle_route_to_montador_de_ideias():
    leo_text = (ROOT / "skills" / "leo" / "SKILL.md").read_text(encoding="utf-8")
    ask_text = (ROOT / "skills" / "ask-bundle" / "SKILL.md").read_text(encoding="utf-8")
    flows_text = (ROOT / "skills" / "ask-bundle" / "modes" / "flows-detail.md").read_text(encoding="utf-8")

    assert "`montador-de-ideias`" in leo_text, "leo SKILL.md missing montador-de-ideias route"
    assert "`montador-de-ideias`" in ask_text, "ask-bundle SKILL.md missing montador-de-ideias route"
    assert "`montador-de-ideias`" in flows_text, "flows-detail.md missing montador-de-ideias"

    # Quick-start menu must expose montador-de-ideias and stay within 4 bullets
    leo_qs = leo_text.split("## Quick-start menu", 1)[1].split("## Quick AFK issue creation", 1)[0]
    assert "`montador-de-ideias`" in leo_qs, "leo Quick-start menu missing montador-de-ideias"
    leo_bullets = [line for line in leo_qs.splitlines() if line.strip().startswith("- **")]
    assert 2 <= len(leo_bullets) <= 4, f"leo Quick-start menu must have 2-4 options, found {len(leo_bullets)}"


def test_no_em_dashes_in_montador_de_ideias():
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)
    for f in SKILL_DIR.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        assert em_dash not in text and en_dash not in text, f"Forbidden dash found in {f}"
```

And in `tests/validation/test_ask_bundle_router.py`, add `"montador-de-ideias"` to `test_router_covers_specialist_domains()`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/validation/test_ask_bundle_router.py tests/validation/test_montador_de_ideias.py -v`
Expected: FAIL with `AssertionError: leo SKILL.md missing montador-de-ideias route`

- [ ] **Step 3: Update `skills/leo/SKILL.md`, `skills/ask-bundle/SKILL.md`, and `skills/ask-bundle/modes/flows-detail.md`**

1. In `skills/leo/SKILL.md`:
   - In `## Situation router` table (right before `| Build / change / implement something |`), add:
     ```markdown
     | Assemble / expand / elevate a raw project idea or prompt with OSINT teardown, first principles, and atomic/modular hardening | `montador-de-ideias` | -> `project-orchestrator` or `grilling` -> `planning-pipeline` |
     ```
   - In `## Quick-start menu`, update the first bullet (keeping 4 bullets total so `ask_user_question` stays within its 4-option ceiling):
     ```markdown
     - **Assemble a raw idea / prompt, or build / change something in the repo** -> `montador-de-ideias` to expand and blindar a seed idea/prompt with OSINT + first principles, `grilling` (With-docs) if design decisions remain, or `review-cadence` if trivial
     ```

2. In `skills/ask-bundle/SKILL.md`:
   - In `## Situation router` table (right before `| Build/change something |`), add:
     ```markdown
     | Assemble / expand a raw idea or prompt (OSINT + first principles + super-prompt) | `montador-de-ideias` | -> `project-orchestrator` or `grilling` -> `planning` |
     ```
   - In `## The main flow: idea -> ship`, add Step 0 before `1. grilling (with-docs)`:
     ```markdown
     0. **`montador-de-ideias` (optional upstream)** - when starting from a raw seed idea or prompt that needs journalistic OSINT market teardown, first-principles justification, atomic/modular hardening, contact-surface design, and an approved super-prompt in `.devin/specs/`.
     ```
   - In `## Quick-start menu (vague request)`, update the first bullet (keeping 4 bullets total):
     ```markdown
     - Assemble an idea/prompt or build/change something -> `montador-de-ideias`, `grilling`, or `execution` cadence
     ```

3. In `skills/ask-bundle/modes/flows-detail.md`:
   - Under `## The main flow: idea -> ship`, document **`montador-de-ideias`** as the upstream idea-assembly entry point before `grilling (With-docs mode)` when the user wants a full investigative OSINT teardown, first-principles dossier, and compiled super-prompt without mutating their original prompt without consent.

- [ ] **Step 4: Run router tests and skill format validator to verify they pass**

Run: `python -m pytest tests/validation/test_ask_bundle_router.py tests/validation/test_montador_de_ideias.py -v && python scripts/validate-skill-format.py skills`
Expected: PASS (`all passed`, `Failing: 0`)

---

### Task 5: Synchronize Bundle Inventory (`manifest.json`, `README.md`, `SKILL-TIERS.md`, `TOOLS-MAP.md`) and Run Full Verification Gate

**Files:**
- Modify: `manifest.json` (`skill_count`: `184` -> `185`, add `montador-de-ideias` entry in `skills[]`)
- Modify: `.devin/docs/SKILL-TIERS.md` (update `184` -> `185` on line 5, add `montador-de-ideias` row under `## Planejamento/decisão`)
- Modify: `.devin/docs/TOOLS-MAP.md` (update `184 skills` -> `185 skills` on line 167)
- Modify: `README.md` (update `skills-184-blue.svg` -> `skills-185-blue.svg` on line 5, `184 skills` -> `185 skills` on lines 142 and 636)
- Modify: `tests/validation/test_montador_de_ideias.py`

**Interfaces:**
- Consumes: `skills/montador-de-ideias/SKILL.md` frontmatter `description`.
- Produces: Full bundle consistency across `manifest.json`, `README.md`, `.devin/docs/SKILL-TIERS.md`, and `.devin/docs/TOOLS-MAP.md`, passing all 52 checks in `audit.py` and the full `pytest` suite.

**Verification Function (VF):**
- `gate:` `python audit.py && python -m pytest -q`
- `expect:` `audit.py` exits 0 with `0 errors`; `pytest` exits 0 with 0 failures.
- `evidence:` Full `audit.py` summary and `pytest` summary output.

- [ ] **Step 1: Add the manifest and audit sync test to `tests/validation/test_montador_de_ideias.py`**

Append to `tests/validation/test_montador_de_ideias.py`:

```python
import json


def test_manifest_and_skill_tiers_include_montador_de_ideias():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8-sig"))
    skills_by_name = {s["name"]: s for s in manifest.get("skills", [])}
    assert "montador-de-ideias" in skills_by_name, "montador-de-ideias missing from manifest.json"
    entry = skills_by_name["montador-de-ideias"]
    assert entry["purpose"].startswith("Use when assembling, expanding, or elevating a raw project idea")

    tiers = (ROOT / ".devin" / "docs" / "SKILL-TIERS.md").read_text(encoding="utf-8")
    assert "`montador-de-ideias`" in tiers, "SKILL-TIERS.md missing montador-de-ideias"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/validation/test_montador_de_ideias.py -k "test_manifest_and_skill_tiers_include_montador_de_ideias" -v`
Expected: FAIL with `AssertionError: montador-de-ideias missing from manifest.json`

- [ ] **Step 3: Update `manifest.json`, `.devin/docs/SKILL-TIERS.md`, `.devin/docs/TOOLS-MAP.md`, and `README.md`**

1. In `manifest.json`:
   - Add entry to `skills` array (in alphabetical order between `mobile-probe` and `mutation-testing`):
     ```json
     {
       "name": "montador-de-ideias",
       "source": "custom",
       "original_path": "C:\\Users\\leand\\AppData\\Roaming\\devin\\skills\\montador-de-ideias",
       "purpose": "Use when assembling, expanding, or elevating a raw project idea or initial prompt into an ultra-detailed, first-principles dossier and compiled master prompt with journalistic OSINT market research, Tech Lead and Staff Architect justifications, atomic and modular hardening/optimization, and high-impact contact surfaces."
     }
     ```
   - Update `"skill_count": 184` -> `"skill_count": 185`.

2. In `.devin/docs/SKILL-TIERS.md`:
   - Update `o índice completo das 184 é` -> `o índice completo das 185 é`.
   - Under `## Planejamento/decisão`, add:
     ```markdown
     | `montador-de-ideias` | Monta/expande ideia crua em dossiê OSINT + primeiros princípios + super-prompt sem alterar original sem aval (+6k defer) | ~1100 | Ideia crua -> super-prompt blindado e dossiê de mercado |
     ```

3. In `.devin/docs/TOOLS-MAP.md`:
   - Update `| skills/ | ./skills/ | ~/.config/devin/skills/ | 184 skills |` -> `| skills/ | ./skills/ | ~/.config/devin/skills/ | 185 skills |`.

4. In `README.md`:
   - Line 5: `skills-184-blue.svg` -> `skills-185-blue.svg`
   - Line 142: `As 184 skills` -> `As 185 skills`
   - Line 636: `Inventário e metadados das 184 skills` -> `Inventário e metadados das 185 skills`

- [ ] **Step 4: Run `audit.py`, `validate-skill-format.py`, and `pytest` to verify green state**

Run: `python scripts/validate-skill-format.py skills && python -m pytest tests/validation/test_montador_de_ideias.py tests/validation/test_ask_bundle_router.py tests/validation/test_skill_format_passes.py -v && python audit.py`
Expected: PASS (`0 errors` in `audit.py` for bundle consistency checks, all validation tests green). Note: if check `[16] Skills live vs bundle sync` or `[34] Install drift ledger` flags the new skill before live install, run `pwsh -NoProfile -File install.ps1 -Force` (or sync live skill copy + `python scripts/install-ledger.py snapshot`) and re-run `python audit.py` to achieve `52/52, 0 errors, 0 warnings`.
