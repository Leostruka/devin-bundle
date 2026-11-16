---
title: changelog PR-ref gate
date: 2026-11-15
session: ci-debug
category: convention
tags: [changelog, ci, pr-quality]
status: active
cues:
  - keyword: "changelog"
  - symbol: "changelog-refs.py"
---

The static audit requires literal `PR #NNN` references in [Unreleased]
for every PR merged in the last 24h. Issue numbers alone do not satisfy
the gate. Run `scripts/changelog-refs.py --write` to append missing refs.
