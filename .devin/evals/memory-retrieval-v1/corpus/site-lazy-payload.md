---
title: atlas payload split
date: 2026-11-15
session: atlas-ux-loop
category: decision
tags: [site, performance, lazy]
status: active
cues:
  - keyword: "atlas"
  - path: "site/build.py"
---

Skill/agent/doc/adr/app/changelog HTML bodies live in dist/data/*.html,
fetched on demand with a Map cache. index.html dropped 2.09MB -> 134KB.
Skills alone were 69% of the old inline payload.
