---
title: project-memory design constraints
date: 2026-11-13
session: memory-skill
category: decision
tags: [memory, design, retrieval]
status: active
cues:
  - keyword: "memory"
  - keyword: "retrieval"
---

Memory notes are plain Markdown + frontmatter cues (keyword/path/symbol).
No vector DB, no embeddings, no auto-capture - every note requires user
approval. Retrieval is cue-anchored substring scoring, top-3 injection.
Evidence: arXiv:2607.20972 voluntary memory use near zero; arXiv:2608.15008
excessive retrieval hurts sequential tasks.
