---
title: scratch dir tracking policy
date: 2026-11-14
session: pr-614
category: lesson
tags: [scratch, git, merge]
status: active
cues:
  - keyword: "scratch"
  - path: ".devin/scratch"
---

`.devin/scratch/` artifacts ARE tracked once PR #614 landed - removing
them from the index breaks tests that read those fixtures. Untracked
scratch is fine to delete after use; tracked files need care on merge.
