---
title: pr-quality workflow requirements
date: 2026-11-15
session: dependabot-batch
category: convention
tags: [ci, pr, quality]
status: active
cues:
  - keyword: "PR checks"
  - symbol: "pr-quality.yml"
---

PR checks gate requires a conventional title AND a `Refs: #N` or
`Closes #N` line in the body. The workflow listens on `edited`, so
updating the body re-triggers it without a new commit.
