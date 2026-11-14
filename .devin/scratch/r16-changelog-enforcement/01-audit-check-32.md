# r16-changelog-enforcement-01: audit check [32] for [Unreleased] merge coverage

## Problem

The `[Unreleased]` changelog gap recurred: R10 added the section covering 21 PRs, R14 found five more merges undocumented (#274-#278). Manual changelog updates drift silently until the next audit round notices.

## Fix

New audit check [32]: every merge commit since the released version tag (`v{manifest.version}`) whose subject ends `(#NNN)` must have its `#NNN` referenced inside `## [Unreleased]`. `docs(changelog)` PRs are exempt (cannot cite their own number pre-merge). Missing refs -> audit error. Caught #280 immediately on first run.

Also added the missing #280 changelog entry this check surfaced.
