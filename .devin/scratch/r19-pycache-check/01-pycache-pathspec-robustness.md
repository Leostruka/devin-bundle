# r19-pycache-check-01: audit [11] pycache pathspec robustness

## What happened

Initial read suggested tracked `.pyc` files in `.devin/scratch/__pycache__/`. On re-verification that was a false positive: the paths seen came from `grep -rln` output (binary .pyc files contain the source filename) and from `git check-ignore`'s path echo, not from `git ls-files`. `git log` shows the path was never committed; `.gitignore` covers it.

## Real residual issue

Audit check [11] used `git ls-files -- '*__pycache__*'`. Pathspec `*` semantics depend on git wildmatch and are easy to get subtly wrong (a pattern that fails to match nested dirs would silently skip the check). Replaced with full `git ls-files` + Python-side `'__pycache__' in path` filter: provably matches any depth, no pathspec semantics to reason about.

## Fix

- `audit.py` [11]: pattern replaced by Python-side filter
- No tracked .pyc existed to remove (verified via `git log -- <path>` = empty)
