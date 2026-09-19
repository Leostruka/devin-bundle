---
name: architecture
description: Use when designing modules, seams, and adapters, when evaluating module depth and identifying deepening opportunities in a codebase, or when modernizing legacy code incrementally (strangler-fig, seams, characterization tests, safe extraction).
agent: architect
triggers: [user, model]
---

# Architecture

Design **deep modules** — a lot of behaviour behind a small interface at a
clean seam, testable through that interface. Aim: leverage for callers,
locality for maintainers, testability for everyone.

Reference docs: `reference/DEEPENING.md` (dependency categories + refactor
moves), `reference/DESIGN-IT-TWICE.md`, `reference/HTML-REPORT.md` (report
format).

## Glossary — use these terms exactly

Don't drift into "component," "service," "API," or "boundary."

- **Module** — anything with an interface and an implementation (scale-agnostic).
- **Interface** — everything a caller must know: signature, invariants,
  ordering, error modes, config, performance.
- **Depth** — leverage at the interface: behaviour exercisable per unit of
  interface learned. Deep = small interface + lots of implementation.
- **Seam** (Feathers) — a place you can alter behaviour without editing there.
- **Adapter** — a concrete thing satisfying an interface at a seam (role, not
  substance).
- **Leverage** — what callers get from depth. **Locality** — what maintainers
  get: change and bugs concentrate in one place.

## Principles

- **Depth is a property of the interface**, not the implementation.
- **The deletion test** — delete the module: complexity vanishes →
  pass-through; reappears across callers → earning its keep.
- **The interface is the test surface** — callers and tests cross the same
  seam.
- **One adapter = hypothetical seam; two = real.** Don't add a seam unless
  something varies across it.
- Accept dependencies, don't create them; collapse pass-through wrappers;
  co-locate decisions; hide parameter clusters; push I/O to the seam; delete
  tests on deleted shallow modules.

## Deepening process (evaluate + act)

Symptoms of shallowness: wide interface/thin impl; chains of tiny modules
per concept; setup-heavy test explosion; dependency fan-out; repeated caller
setup. Several together → deepening candidate.

1. **Scope before scanning (YAGNI)** — user direction wins; else walk
   `git log --oneline` for hot spots. Read `.devin/CONTEXT.md` + ADRs first.
   Broad/unfamiliar → `research` deep-mode before the sub-agent.
2. **Explore** with an `architect`/`researcher` sub-agent — organic, noting
   friction; apply the deletion test to suspects.
3. **Present candidates** — self-contained HTML report in OS temp dir
   (`$TMPDIR`/`/tmp`/`%TEMP%`, `architecture-review-<ts>.html`), Tailwind +
   Mermaid via CDN, before/after visuals, per candidate: files, problem,
   solution, locality/leverage benefits, strength badge (Strong / Worth
   exploring / Speculative). Open it for the user.
4. **Act** — pick the refactor move per dependency category
   (`reference/DEEPENING.md`); tests land at the deepened interface.

## Legacy modernization protocol

1. **Characterization tests first** — capture current behavior before touching.
2. **Find seams** — where new code can replace old.
3. **Strangle incrementally** — route small slices through new impls.
4. **Refactor locally** — extract, rename, deduplicate.
5. **Verify each step** — tests + diff-check.
6. **Document** — ADRs for architecture changes and deprecated paths.

Each commit leaves the system testable and no worse than before. Report
before/after: tests, complexity, migration status.
