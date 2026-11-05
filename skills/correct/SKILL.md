---
name: correct
description: Use when the operator corrects an agent mistake in the repo, or when hardening the project so a repeated agent mistake class cannot happen again.
disable-model-invocation: true
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent cannot make them.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

First, read recent commits, reverts, review comments, `AGENTS.md` and `.devin/global_rules.md`, and comments that explain workarounds. Group the mistakes into classes. A class counts once it has happened twice.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state cannot be written.** If bad code still compiles, add a lint, hook script, or CI check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or flag any test that still passes when the behavior it checks breaks, or that fails when only the internals change. Keep it in `tests/validation` when it guards a rule and `tests/held-out` when it guards an agent behavior (Rule 15).
4. **Write docs or agent rules last, only for judgment calls.** Nothing fails when an agent skips them.

## Fix and prove

Fix the most frequent classes now, one commit each (own branch and PR under the protected-main flow). Prove each new check fails on a real past mistake: reproduce the old failure mode, show the new check catching it. Run the same command locally and in CI. Exceptions go on the offending line with a reason, an expiry date, and a human's approval.

## Keep the rule table

Keep a table in the agent instruction file that pairs each rule with what enforces it. When the operator corrects you, fix the mistake and add the rule. If the rule was already there and nothing enforces it, that is a repeat, so fix it at the highest level in the same change. Drop a rule once its mistake cannot happen.

**Reply:** each class with its evidence, the level you picked, and why a higher level did not work.
