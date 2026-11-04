# 42 -- Python version spread (3.11/3.14) with unversioned `python` hook invocations and fail_closed guards

- **Status**: open
- **Category**: adaptability
- **Severity**: P1
- **File**: hooks.v1.json:6-12, install.ps1:644

## Evidence

Hook commands are bare `python scripts/<name>.py` (hooks.v1.json throughout). Risks: (a) on Windows, `python` can resolve to the Store stub, pythonw, or a different minor than the venvs/extensions were built against; (b) `fail_closed: true` on both PreToolUse guards means a broken/missing python makes EVERY `exec`, `write`, `edit` blocked; the guardrail becomes a total outage; (c) test matrix spans 3.11/3.14 but no script declares `python_requires` or checks `sys.version_info`, so a syntax/stdlib bump (e.g. 3.14 changes) can break a guard script at hook time with the same total-block outcome; (d) installers try `py`/`python3` fallbacks (install.ps1:644, install.sh:546) but rendered hook commands keep the bare `python` spelling.

## Recommendation

Render hook commands with the resolved interpreter path at install (the render step already merges into user config), or add a `--selfcheck` fast path to the two guard scripts and have session-start verify `python -c "import sys"` resolves to a supported minor; document the supported floor (>=3.11) in DEVIN-CLI-COMPATIBILITY.md.

## Tradeoffs

- Merits of current `python` spelling: portable across platforms, matches project-relative convention, keeps hooks.v1.json readable; fail_closed correctly prefers blocking over guardrail bypass (verified empirically, COMPATIBILITY.md:99).
- Demerits: availability of the interpreter is now a single point of total failure; absolute interpreter paths in rendered config break on python upgrades/relocation; falling back to fail_open on interpreter-missing reintroduces the bypass the flag was adopted to close; version floor must be enforced somewhere or it is docs-only.
- Better contorno: keep `fail_closed` but render `py -3` on Windows / `python3` on POSIX where available, and ship a `scripts/hook-python-check.py` invoked by session-start that reports a degraded-python warning early rather than discovering it as blocked tool calls.

## Verification

Temporarily rename the python executable in a scratch install; run `devin` and confirm every exec is blocked by the fail_closed guards; check `grep -rn 'version_info' scripts/*.py` for absent version floors.
