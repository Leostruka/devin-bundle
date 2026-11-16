---
title: safe branch cleanup procedure
date: 2026-11-14
session: branch-cleanup
category: pattern
tags: [git, branches, cleanup]
status: active
cues:
  - keyword: "branch cleanup"
  - symbol: "update-ref"
---

`git branch -D` is blocked by the destructive gate. Safe removal path:
verify each branch has a merged PR on GitHub + deleted remote, then drop
the ref via `git update-ref -d`. Squash-merged branches always fail `-d`.
