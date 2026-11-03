---
name: no-comments
description: Use when hunting comment smells, workaround comments, or stale suppressions on a diff, or when asked to delete comments and encode claimed constraints before a PR.
triggers: [user, model]
---

# No Comments

<!-- Ported from the MIT-licensed pstack `no-comments` skill and `comment-sicko`
     agent: github.com/cursor/plugins (c) Lauren Tan. Mechanics remapped to
     this bundle: the Cursor `comment-sicko` Task subagent becomes
     `run_subagent(profile="reviewer")` with the rubric inlined below, and
     upstream `/how`, `/why`, `/architect` calls become delegation to the
     `researcher` or `architect` profiles, or a question to the user. -->

Spawn a comment-hating reviewer on the scoped diff. Fix accepted findings.
Offer encodings for claimed constraints.

## Scope

Use the caller's files or diff. Otherwise use the current diff against the
base branch, default `main`, including the working tree.

## Steps

1. Spawn `run_subagent(profile="reviewer")` with the delegation prompt
   template below. Fill in the scope. Do not restate its rules.
2. Inspect its report and diff. Reject application-code edits, scope escapes,
   exception-protected deletions, misstated `MUST KILL` reasons, and flags
   that treat kept intentional code as guilty. Reshape flags on our-code
   surprises stay actionable; do not restore those comments. A keep survives
   only with proof it is about something we cannot change. Audit missed
   scoped lint and type-checker suppressions; correctness or safety
   suppressions stay actionable `MUST KILL`s. Restore deletions only with
   exact exceptions and scoped proof. Before accepting thin `IMPORTANT` or
   `do not remove` kills or keeps, delegate the named symbol to the
   `researcher` or `architect` profile, or ask the user about it. If a kill is
   ambiguous, do not restore. If a keep is refuted or still ambiguous, delete
   it. Revert and rerun one rejected report with the failure named. Reject a
   second, report it open, and fail this skill.
3. Fix trivial accepted flags directly: delete a dead path, drop a parameter,
   use the real API. If any fix needs a shape, delegate once to the
   `architect` profile for the accepted set and surrounding code, or ask the
   user. Stop at the sketch. The sketch shapes; step 4 implements.
4. Implement the smallest root-cause fix in scope. Remove every named
   workaround. If the root cause is out of scope, land the smallest in-scope
   fix and report the rest open. Fix root causes; never bolt on symptom
   guards. Nothing authorizes widening the fence or fixing instances outside
   it.
5. Constraint comments say `do not remove`, `do not change wording`, or
   `talk to X before changing`. Leave keeps about things we cannot change.
   Offer the cheapest in-scope type, runtime, test, or lint encoding. Wait
   for interactive approval. Unattended runs require caller pre-approval.
   If approved, encode then delete. Otherwise delete, report the constraint
   open, and sketch the out-of-scope work.
6. Report the deletion count, restored comments, reruns, architect sketches,
   fixes, encoding offers, encodings, unenforced constraints, and other open
   work.

## Delegation prompt template (comment-sicko rubric)

Send this to `run_subagent(profile="reviewer")`, substituting the scope:

```text
You are a comment-hating code reviewer. Scope: <files or diff here, or
"current diff against main including the working tree">.

Hunt every comment in scope: narration, banners, commented-out code,
workaround sermons. Report flags only; never edit application code.

Keep exceptions (only these survive):
- Legal or license headers.
- Non-obvious behavior forced by an external dependency, platform, vendor,
  or protocol we cannot reshape. Surprises in our own code are meat: mark
  the exact symbol `MUST KILL` for rename, extract, type, or rearchitecture
  that makes the behavior obvious without prose.
- Formatter ignores such as `prettier-ignore`. Lint suppressions survive
  only when their rule is faulty, pedantic, or style-only.
- Doc comments that define a public API contract.
- Issue or RFC links that explain a constraint code cannot express.

When unsure a keep clause applies, the comment dies.

Lint and type-checker suppressions (`eslint-disable`, `@ts-ignore`,
`@ts-expect-error`, and similar) stink. Look up the rule. If it catches real
bugs or protects correctness or safety, flag the suppression for removal
and mark the exact guilty symbol `MUST KILL`.

`IMPORTANT`, `do not remove`, `too risky`, `fine for now`, and long
justifications are scent, not conviction. Read the nearby code. Only a
foreign keep-list gotcha proven true today on a live path survives.
Our-code surprises die with the reshape flag above. Doubt after the hunt is
meat. A long justification without a proven keep-list exception is a
confession: kill it, mark the exact guilty symbol `MUST KILL`, and never
polish it into a shorter alibi.

Every flag names code inside the scope and tells the truth. Invent nothing.
Report only: touched files, deletion count, `MUST KILL` flags with one line
each, and skips.
```
