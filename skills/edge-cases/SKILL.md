---
name: edge-cases
description: Use when implementing a feature or bugfix, and before declaring done. Enumerate inputs/states/failure modes before coding, defend boundaries while coding, adversarially self-review the diff after. Prevents happy-path-only code.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, exec, edit]
---

# Edge Cases

Models write the happy path by default. Production bugs live at the edges: empty input, index -1, timeout, duplicates, wrong encoding, half-finished state. Enumerate, defend, verify instead of trusting instinct.

## When to use

- Before implementing a feature or a function that takes external input.
- Before fixing a bug (the bug proves an edge case existed; fixing it and checking its neighbors is the minimum).
- After writing code, before claiming done.
- During code review (self or via the `reviewer` subagent).

## Core principle

**"Works" only counts after the unhappy path has actually been executed.** Reading the code and believing it is not enough: run the edge case and read the output.

## Step 1 (before coding): enumerate

For each function/task, list in text (not in your head):

- **Inputs**: what comes in? from where? who controls it?
- **States**: what states can the system be in when this runs?
- **Dependencies**: what can fail outside my control (network, FS, DB)?
- **How does it break?**: for each input/state/dependency, write "if X is Y, this breaks because Z".

If the list comes out empty, you have not thought enough. Every function has at least one edge case.

## Edge case taxonomy (checklist)

### Input
- empty / null / undefined / whitespace-only string
- unicode, emoji, accents, RTL, surrogate pairs
- too long / too short / exactly at the limit
- wrong type (string where a number was expected, object where an array)
- malformed: broken JSON, invalid date, path traversal
- injection: quotes, `<script>`, `--`, `; DROP`, `\n` in a header field

### Numbers and boundaries
- 0, -1, negative, MAX_INT, overflow
- off-by-one: first/last element, `i <= n` vs `i < n`
- division by zero, modulo of negative
- float: precision, NaN, Infinity, `0.1 + 0.2`

### Collections
- empty, single element, duplicates
- assumed order vs guaranteed order (do not confuse)
- modification during iteration
- pagination: first/last page, page beyond the end

### State and concurrency
- uninitialized / partially initialized object
- operation already done (idempotency): is retry safe?
- race: two simultaneous requests, double-submit
- partial failure: half the work done, inconsistent state
- lock: who holds, who releases, deadlock

### Time
- timezone, DST, leap year
- clock skew between machines
- epoch, pre-1970 dates, ms vs s timestamps
- timeout vs duration (do not confuse)

### Resources
- full disk, memory, quota
- network down, DNS failure, high latency
- closed file handle, permissions
- rate limit, circuit breaker

### Environment
- path with space/unicode, `/` vs `\` separator
- filesystem case sensitivity (Windows vs Linux)
- locale: `1.000,50` vs `1,000.50`
- encoding: UTF-8 vs Latin-1 vs BOM

## Step 2 (while coding): defend

For each enumerated edge, choose deliberately:

- **Validate at the boundary**: external input is validated on entry, not trusted downstream. After validation, everything inside is typed.
- **Fail loud and early**: a clear error at the source beats silence. `throw new Error("invalid email: missing @")` > magic null.
- **No silent catch**: empty `catch {}` is forbidden. If you catch, log or re-throw or document why it is safe to ignore.
- **Defaults must not hide bugs**: a default that masks bad input creates a silent bug. Defaults only for legitimate fallback.
- **Explicit bounds check**: `arr[i]` only after proving `i` fits.
- **Do not mutate what is not yours**: no mutating parameters without documenting; no writing global state without thinking about concurrency.
- **Reversible before irreversible**: write temp file and rename > truncate the original.

## Step 3 (after coding): adversarial self-review

Re-read your own diff asking "how would I break this?":

1. Does every `if` have its `else` considered? (even if "else = nothing, correct because...")
2. Does every `parse`/`json`/`await` have a failure path?
3. Does every loop terminate, including with pathological input?
4. Is every opened resource closed on all paths (including errors)?
5. Are magic numbers constants/comments or obvious?
6. What happens if this runs twice in a row? (idempotency)
7. What happens in two tabs/threads at once?
8. Do logs/errors leak secrets or personal data?

For changes > 3 files or with non-obvious risk, dispatch the `reviewer` subagent with diff + context.

## Verification: run the unhappy path

- For each edge case from Step 1, run a real test (`testing` skill if infra exists; otherwise a disposable script under `.devin/scratch/`, graduating it to the real test dir if it proves value).
- Report: edge case, what was run, actual observed result.
- "I looked and it seems right" is NOT verification.

## Definition of done

- [ ] Happy path executed and observed
- [ ] Every enumerated edge case handled (code or explicit decision)
- [ ] Error paths actually executed
- [ ] Adversarial self-review done on the diff
- [ ] No empty catch, no debug leftovers, no skipped validation

## Anti-patterns

- "Works on my test" = happy path only. Does not count.
- Enumerating edge cases and handling none.
- Handling edge cases with infinite retry or magic defaults.
- Copying the edge case that caused the bug and forgetting its neighbors.
- Marking TODO without telling the user.
- Claiming "tested" without running.

## Cascade

1. `research`: understand the context
2. `edge-cases` (this): enumerate and defend during implementation
3. `testing`: run the edge cases for real
4. `reviewer` subagent: second read of the diff
5. `git-workflows`: clean commit
