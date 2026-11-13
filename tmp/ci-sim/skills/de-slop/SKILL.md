---
name: de-slop
description: Use when cleaning a diff before opening a PR, or when asked to simplify, de-slop, or run the full quality pass on current changes.
triggers: [user, model]
---

# De-Slop

One pass that sequences the bundle's simplification skills over the current
diff or branch before a PR. Each invoked skill keeps its own rules; this
skill only fixes the order and the stop conditions.

## Scope

The current diff against the base branch (default `main`), including the
working tree, or the scope the caller names.

Codebase mode: when the caller names the whole codebase (or a subtree)
instead of a diff - "untangle this codebase", "clean up the accumulated
slop" - hunt what long agent-assisted sessions pile up: duplicated logic
copied instead of shared, wrapper layers that only forward calls,
temporary workarounds left in past their fix, dead paths kept "just in
case". Pair with `big-file-refactor` when a file has crossed ~1k lines;
run the same run order below on the found set, not on a diff.

## Run order

Apply each skill to the scoped diff, in this order:

1. `lean-code`: minimal-code sweep. Delete unneeded code, options, and
   abstractions; prefer the smallest complete change.
2. `no-comments`: comment-smell pass. Hunt comments, apply the
   accept/reject rubric, land smallest root-cause fixes, encode claimed
   constraints as type, test, or lint where approved.
3. `unslop`: prose pass on changed docs, comments that survive, commit
   text, and PR body drafts.
4. `thermo-nuclear-code-quality-review`: structural pass over the whole
   diff. Use `thermos` instead when the dual review is wanted.
5. Conditional language passes, only when the diff touches them:
   - `typescript-best-practices` for `.ts` changes.
   - `vercel-react-best-practices` for `.tsx` or React changes.

Re-read the diff after each step; later passes see the code earlier passes
left behind. Freeze the scope at step 1: new findings outside it are
reported open, not fixed.

## Multi-pass guidance

The skills are non-deterministic: a second run of the whole sequence
catches findings the first run missed. Run the pass, then run it once more
on the resulting diff. A third run is worthwhile only while the previous
run still produced accepted changes.

## Stop conditions

Stop when either holds:

- A full pass produces no new accepted findings or edits.
- The diff is frozen for review (caller says stop, or PR is open).

## Report

After the final pass, report per skill: findings accepted and rejected,
edits made, encodings applied or offered, open work, and which pass
(number) produced each change.
