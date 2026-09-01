---
name: improve-codebase-architecture
description: Use when the user wants to evaluate module depth, identify deepening opportunities in a codebase, and act on them.
agent: architect
---
# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

This command is _informed_ by the project's domain model and built on a shared design vocabulary:

- Run the `/codebase-design` skill for the architecture vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles (the deletion test, "the interface is the test surface", "one adapter = hypothetical seam, two = real"). Use these terms exactly in every suggestion — don't drift into "component," "service," "API," or "boundary."
- The domain language in `.devin/CONTEXT.md` gives names to good seams; ADRs in `.devin/adr/` record decisions this command should not re-litigate.

## Deep vs shallow modules

This skill evaluates modules through the lens John Ousterhout uses in *A Philosophy of Software Design*: a module is **deep** when a small interface hides a large amount of functionality, and **shallow** when its interface is almost as large as the functionality it provides. The goal is not to maximize internal size for its own sake — it is to maximize **leverage** for callers and **locality** for maintainers. Use the `/codebase-design` vocabulary for the precise definitions of module, interface, seam, adapter, leverage, and locality.

### Heuristics for spotting shallow modules

When walking the codebase, treat these as symptoms of shallowness. They are not mechanical rules — they are questions to ask the sub-agent:

- **Wide interface, thin implementation.** The module exposes many methods or parameters, but each one does little more than delegate or pass through. The interface does not hide much.
- **Long chains of tiny modules.** Understanding one concept requires reading three or more modules in sequence. The knowledge is sliced too thin.
- **Test explosion with low signal.** There are many unit tests, most of them setup-heavy, because the real behaviour is scattered across many small units and none of them is deep enough to test meaningfully through its interface.
- **Dependency fan-out.** A small module imports or calls many others, so callers must assemble a wide graph of objects just to use it.
- **Repeated caller setup.** Callers duplicate the same five or more parameters, imports, or configuration objects to reach the module's behaviour.

If several of these appear together, the cluster is a strong deepening candidate.

### Refactoring moves that reduce shallow dependencies

Pick the move that matches the dependencies at the seam. See `codebase-design/DEEPENING.md` for the dependency categories (in-process, local-substitutable, ports & adapters, true external) and testing strategy.

1. **Collapse pass-through wrappers.** If deleting a module would just move the same calls to its callers, the module was shallow. Merge it with the module it delegates to and let the interface shrink.
2. **Co-locate decisions.** Move branching, validation, or orchestration that is currently split across modules into one module with a single decision point. The interface becomes the place where the decision is exercised.
3. **Hide parameter clusters.** Replace a multi-parameter method with an object drawn from a small set of well-named constructors or factories. The interface stays small; the object carries the context.
4. **Push I/O to the seam.** Let the deep module hold the decision logic; let an **adapter** handle file, network, or UI calls. Two adapters (production + test) justify the seam.
5. **Delete tests on deleted shallow modules.** Once the deepened module has tests at its interface, the old unit tests on the collapsed wrappers become waste. Do not layer them.

Apply these alongside the existing deletion test and the `codebase-design` principles: the interface is the test surface, and one adapter means a hypothetical seam while two mean a real one.

## Process

### 1. Explore

**Scope before you scan — YAGNI.** Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed. Decide *where* to look before you look:

- If the user named a direction — a module, a subsystem, a pain point — take it, and skip the inference below.
- Otherwise, walk back a good stretch of the commit history (`git log --oneline`) to find the codebase's hot spots — the files and areas that keep coming up — and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

Read the project's domain glossary (`.devin/CONTEXT.md`) and any ADRs in the area you're touching first. If the architecture question is broad or the codebase is large and unfamiliar, invoke `deep-mode` before spawning the sub-agent.

Then spawn a sub-agent to walk the codebase. Don't follow rigid heuristics — explore organically and note where you experience friction. Use the heuristics in **Deep vs shallow modules** as probes:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where do small modules fan out into many dependencies?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present candidates as an HTML report

Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows), and write to `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file. Open it for the user — `xdg-open <path>` on Linux, `open <path>` on macOS, `start <path>` on Windows — and tell them the absolute path.

The report uses **Tailwind via CDN** for layout and styling, and **Mermaid via CDN** for diagrams where a graph/flow/sequence reliably communicates the structure. Mix Mermaid with hand-crafted CSS/SVG visuals — use Mermaid when relationships are graph-shaped (call graphs, dependencies, sequences), and hand-built divs/SVG when you want something more editorial (mass diagrams, cross-sections, collapse animations). Each candidate gets a **before/after visualisation**. Be visual.

For each candidate, render a card with:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality and leverage, and how tests would improve
- **Before / After diagram** — side-by-side, custom-drawn, illustrating the shallowness and the deepening
- **Recommendation strength** — one of `Strong`, `Worth exploring`, `Speculative`, rendered as a badge

End the report with a **Top recommendation** section: which candidate you'd tackle first and why.

**Use `.devin/CONTEXT.md` vocabulary for the domain, and the `/codebase-design` vocabulary for the architecture.** If `.devin/CONTEXT.md` defines "Order," talk about "the Order intake module" — not "the FooBarHandler," and not "the Order service."

**ADR conflicts**: if a candidate contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: _"contradicts ADR-0007 — but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

See [HTML-REPORT.md](HTML-REPORT.md) for the full HTML scaffold, diagram patterns, and styling guidance.

Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, run the `/grilling` skill to walk the decision tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize — run the `/domain-modeling` skill to keep the domain model current as you go:

- **Naming a deepened module after a concept not in `.devin/CONTEXT.md`?** Add the term to `.devin/CONTEXT.md`. Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `.devin/CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR, framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** Run the `/codebase-design` skill and use its design-it-twice parallel sub-agent pattern.

## Cross-skills

- If the improvement is part of a recurring pattern, invoke `continuous-improvement` to run the 10-step loop with held-out validation.
- Use `ai-coding-dictionary` to align architecture terms before proposing a new module.
