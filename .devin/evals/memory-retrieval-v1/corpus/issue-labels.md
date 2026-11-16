---
title: GitHub label vocabulary
date: 2026-11-15
session: issue-639
category: convention
tags: [github, labels, issues]
status: active
cues:
  - keyword: "labels"
  - keyword: "issue labels"
---

Not every label exists on the repo - `type:eval` does not. Query valid
labels with `gh label list` before applying; issue creation proceeds
without invalid labels rather than failing.
