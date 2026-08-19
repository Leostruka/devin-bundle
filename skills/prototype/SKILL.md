---
name: prototype
description: Use when a throwaway prototype is the fastest way to answer a design question.
---
# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## When to prototype vs discuss vs spec

Design questions live on a **fidelity spectrum**. Match the fidelity to the question:

- **Low fidelity — discuss.** Basic frame, obvious structure ("modal has cancel + confirm"). Resolve in conversation or a grilling session. No code needed.
- **High fidelity — prototype.** "How should it look?", "How should it behave under condition X?", "Does this state model feel right?" These are hard to reason about on paper — build something concrete to react to.
- **Mixed fidelity — prototype then spec.** Resolve the basic frame in discussion, then prototype the uncertain parts. The prototype's validated decisions feed back into the spec.

**Rule of thumb:** if the question is about *structure or behavior you can't picture clearly*, prototype. If you can answer it in a sentence, discuss. Spec-only development skips the fidelity jump that catches design errors early — prototyping is the cheapest way to find out you were wrong.

## Academic basis

Prototyping is not a vibe — it's empirically validated against specifying:

- **Less code, less effort, equivalent quality.** Boehm et al. 1984 (IEEE TSE, "Prototyping Versus Specifying"): 7-team experiment, prototyping yielded ~40% less code and 45% less effort with equivalent performance, higher ease of use and ease of learning. Specifying produced more coherent designs and easier integration — so prototype for uncertainty, spec for integration.
- **Better match with user needs.** Gordon & Bieman 1993 (Software Quality Journal): across reviewed sources, 19 indicate prototyping better matched actual user needs; 16 indicate improved ease of use. "Omissions of function are often difficult for the user to recognize in formal specifications."
- **Spikes reduce risk.** Al Hashimi & Gravell 2020 (CSCI, IEEE): empirical study — primary role of agile spikes is risk management through investigation to reveal uncertainty in user stories.
- **Fidelity is multi-dimensional.** Arnason et al. 2023 (Empirical Software Engineering): Prototyping Aspects Model (PAM) from 33 studies + 12 companies — purpose, scope, media, use, exploration strategy. Mixed-fidelity prototyping outperforms single-fidelity (McCurdy et al. 2006, CHI).

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file — free-play buttons plus tabbed guided walkthroughs — that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

The two branches produce very different artifacts — getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used (next to the module or page it's prototyping for) so context is obvious — but name it so a casual reader can see it's a prototype, not production. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
2. **Trivial to run.** A UI prototype starts from one command in the project's task runner — `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Capture it when done.** Fold any validated decision into the real code, then capture the prototype itself as a **primary source**: commit it to a throwaway branch, out of main, and leave a context pointer to that branch on the implementation issue. Capture the answer too — the verdict and the question it settled — in the issue or a commit. The main branch keeps only the validated decision.
