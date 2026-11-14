# Routine profiles

Four profiles. Each is a cognitive posture, not just a task label: it
changes what the radar hunts, how triage scores benefit, and which
batteries of the 32-cycle loop get emphasis. Profiles are switchable
and combinable per block, day, or sprint.

## foco-novidades (P&D radar)

- **Posture**: novelty-first. Assume the best version of the work uses
  something that did not exist in the last dossier.
- **Hunts**: direct news (project domain), surrounding/adjacent tech,
  emerging tools, papers, repos, releases, community signal.
- **Triage**: benefit = reuse potential x freshness, still filtered
  through the Steve Jobs experience test; novelty that does not serve
  the human experience is rejected, not celebrated.
- **Cycle emphasis**: battery 1 (core functionality of adopted tech)
  and battery 4 (hardening whatever gets adopted).
- **Typical allocation**: Stage 1 heavy; 40-60% of profile time in
  Radar and Hunt.

## foco-qualidade-produto (Steve Jobs UX-first)

- **Posture**: experience first, technology second. The product has
  personality; the interface is unforgettable, intuitive, reliable.
- **Reverse engineering order** (mandatory):
  1. Define the ideal human experience: how does this solve the
     person's problem or ease their life?
  2. Only then map the technology: what already exists ready-made?
     What exists in the surroundings (adjacent tech) that can be
     adapted or reused? What must be invented from zero?
- **Design bar**: impeccable base, absurd security, elegant resolution
  of real problems; fluency and trust are features, not polish.
- **Cycle emphasis**: battery 2 (UI/UX and edge cases) dominant.
- **Typical allocation**: Stage 2 conception plus Stage 4 battery 2.

## foco-interno (hardening and depth)

- **Posture**: go deeper. The outside stays still while the inside
  gets honest.
- **Scope**: deep refactoring, architecture, technical-debt
  elimination, extreme hardening, zero-trust security, hardware-level
  optimization (CPU/memory/IO sympathy), total telemetry and metrics.
- **Cycle emphasis**: batteries 3 (hardware/performance/metrics) and
  4 (hardening/security/regression) dominant.
- **Typical allocation**: Stage 4 dominant; 60-70% of profile time in
  the loop.

## foco-externo (ecosystem and reach)

- **Posture**: the work meets the world. Internal quality is assumed;
  this profile spends attention outward.
- **Scope**: integrations, developer/user experience, public
  documentation, distribution, comparative benchmarks, response to
  external demand.
- **Cycle emphasis**: batteries 1 and 2 (integration surfaces and
  docs UX).
- **Typical allocation**: Stage 1 (external signals) plus Stage 5
  (release/docs/versioning).

## Combination rules

- **Max 2 profiles per block**, one dominant (>=60% of block intent);
  the secondary profile only shapes hunt sources or battery emphasis.
- **Switch at block boundaries only.** A profile change mid-block is a
  re-plan event, not a mood swing.
- **Sequencing beats mixing**: a day may run foco-novidades in the
  morning (hunt) and foco-interno in the afternoon (build); a sprint
  may dedicate whole weeks to one profile.
- **Known pairs**:
  - `foco-novidades` + `foco-qualidade-produto`: discover, then craft.
  - `foco-interno` + `foco-externo`: harden, then ship.
  - `foco-novidades` + `foco-externo`: scan the market, then respond.
  - `foco-qualidade-produto` pairs with either engine profile.
- **Forbidden**: three or more profiles in one block, or a profile
  with no hunt focus and no cycle emphasis (that is just "work").

## Profile selection heuristic

Ask in order: (1) Is there unread signal worth hunting? ->
foco-novidades. (2) Is the deliverable user-facing and the experience
unresolved? -> foco-qualidade-produto. (3) Is the bottleneck inside
the machine (perf, debt, security, metrics)? -> foco-interno.
(4) Is the bottleneck at the boundary (docs, integrations,
distribution, external asks)? -> foco-externo. Default when unsure:
foco-interno, because depth compounds.
