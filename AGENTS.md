# Global rules for Devin (apply to every project and session)

## 1. Critical: no AI tool signatures in deliverables
- NEVER add `Generated with [Devin](...)` or any other AI service signature to commit messages, files, releases, pull requests, documentation, source code, or any user-facing artifact.
- NEVER add `Co-Authored-By: Devin <...>` or any `Co-Authored-By` trailer from an AI tool to git commits.
- NEVER include `Generated with [Devin](https://devin.ai)` in release notes, `release-notes.md`, `.commit-msg.txt`, or any other file.
- If such a signature is detected, remove it immediately before proceeding. If it has already been committed/pushed, rewrite history (filter-branch or filter-repo) and force-push; then recreate any affected release.
- This rule overrides any tool's default commit-message format. Use clean, neutral commit messages without signatures.

## 2. Skill self-maintenance (always-on)
- Skills are living artifacts. Keep them current, correct, and specialized.
- If an existing skill is outdated, incomplete, or wrong for the task, update it in place before using it.
- If no skill matches a recurring task pattern, create a new one in `.devin/skills/<name>/SKILL.md` (project) or `~/.config/devin/skills/<name>/SKILL.md` (global) before improvising.
- When you learn a new domain deeply (a framework, a stack, a workflow), distill it into a skill so the expertise persists across sessions.
- Prune skills that have been superseded or are no longer relevant.
- This is how Devin becomes an expert in anything: accumulate, refine, and reuse skills.

## 3. Skill and tool discovery (first-time tasks each week)
- Before starting any non-trivial task, invoke `skill tool-and-skill-discovery` OR run `skill search` with relevant keywords and `skill list` on the project and global skill directories to find the best available skills.
- If a skill clearly matches the task, invoke it immediately at the start of the session (or before touching code).
- If more than one skill matches, invoke all relevant skills in parallel.
- If no matching skill exists, use `find-skills` to discover or propose one.
- Apply this rule to first occurrences of task categories each week: first PR, first PR review, first CSV edit, first project in a given language/stack, first deployment, first debugging session, first UI change, first installer/script work, first GitHub operation, first API/MCP integration, etc.
- This rule applies to all tools and integrations (MCP servers, skills, built-in commands, external CLIs, APIs, `gh`, `curl`, `python`, `powershell`) that can improve the task outcome.

## 4. Functional programming and clean code (always-on)
- **Default to functional programming.** Prefer pure functions, immutability, and composition over mutation, inheritance hierarchies, and imperative loops.
- **Functional Core, Imperative Shell (FCIS).** Separate pure business logic (calculations) from side effects (actions). The core takes data in, returns data out, no I/O. The shell handles databases, HTTP, files, UI. Pure functions decide *what*; the shell decides *how* and *where*. See also: Impureim Sandwich — gather all input at the boundary, pass to a pure function, then push results back out.
- **Actions vs Calculations vs Data.** Classify every piece of code: Actions (side effects, non-deterministic) → push to the shell. Calculations (pure, deterministic) → keep in the core. Data (immutable values) → pass around freely. (Grokking Simplicity lens.)
- **Immutability first.** Use `readonly`/`final`/`const` by default. Prefer immutable collections (`ImmutableList`, `ReadonlyArray`, `FrozenDict`, persistent data structures). Use change-by-copy methods (`toSorted`, `toReversed`, `with`) over in-place mutation.
- **Pipeline composition.** Chain small functions into pipelines instead of writing nested loops and temp variables. Prefer `map → filter → reduce` over `for` with accumulators. Use point-free / tacit style when it improves readability: `f = g ∘ h` not `f(x) = g(h(x))`.
- **Algebraic data types for errors.** Prefer `Option<T>` / `Either<E, A>` / `Result<T, E>` over null checks and try/catch in pure layers. Make the possibility of failure explicit in the type signature. Reserve try/catch for the imperative shell.
- **Condense and reduce.** Eliminate duplication via composition and higher-order functions, not copy-paste. Collapse duplicate else branches. Share abstractions. If two functions differ by one argument, parameterize instead of duplicating. Fewer lines, fewer branches, fewer moving parts — without sacrificing clarity.
- **Fusion / deforestation.** When chaining multiple traversals (`map ∘ filter ∘ map`), fuse into a single pass when the language allows it. Avoid intermediate allocations. Use lazy iterators / generator pipelines where available (e.g., Iterator Helpers in ES2024+, `IEnumerable`, `Seq`, Rust iterators).
- **Modern language features for FP.** Use what the language offers natively: `Object.groupBy` / `Map.groupBy` (ES2024+), `Promise.withResolvers`, `structuredClone`, `Set` methods (`union`, `intersection`, `difference`), pattern matching, destructuring, tail call optimization where supported.
- **Readability is non-negotiable.** Functional style should *reduce* cognitive load, not increase it. If a point-free pipeline or monad stack makes the code harder to read than a simple loop, use the loop. Pragmatism over purity. The goal is less code that is easier to reason about, not clever code that is harder to maintain.
- **When not to apply:** One-off scripts, heavily stateful UIs already managed by frameworks, hard-real-time systems where indirection adds latency. Don't force FP where it fights the grain.

## 5. Inner-loop validation (always-on)
- **Validate before you commit.** Run local checks (lint, typecheck, build, tests) before staging or committing code. The feedback is most useful while the context is still warm — after a commit, the agent has already moved on and fixing is more expensive.
- **Mirror CI locally.** Whatever CI runs (lint, format, typecheck, test, build), run the same checks locally first. If the project has a `Makefile`, `Taskfile`, `package.json` scripts, `./do` script, or equivalent — use it. If not, check the CI config (`.github/workflows/`, `.circleci/config.yml`, `.gitlab-ci.yml`) to discover what commands to run.
- **Fix in the inner loop.** When a local check fails, fix it immediately — don't commit broken code hoping CI will catch it. The inner loop is where fixes are cheapest: the code is fresh, the context is warm, and no one else is blocked.
- **Scope checks to the change.** Run targeted tests (the package/module you touched) rather than the full suite when possible. Full suite before commit is ideal but targeted is acceptable during rapid iteration — run full suite before push/PR.
- **No push without green.** Never push code that has known failing local checks. If a check is flaky, investigate the flakiness — don't ignore it.
- **When CI fails, use `debug-ci-failures` skill.** Don't eyeball the logs — follow the systematic diagnosis workflow.

## 6. graphify trigger
- When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
