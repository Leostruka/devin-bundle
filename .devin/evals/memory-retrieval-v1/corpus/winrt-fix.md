---
title: winrt dependency conflict fix
date: 2026-11-14
session: install-repair
category: decision
tags: [winrt, dependencies, computer-use]
status: active
cues:
  - keyword: "winrt"
  - keyword: "computer-use deps"
---

WinRT packages must share one epoch. Mixed 3.2.1 + 4!10.0.28000.2957 fails
resolution because epoch-4 subpackages require winrt-runtime>=4.1.0,<5.
Fix shipped in PR #638: uniform 4! pins + runtime 4.1.0.
