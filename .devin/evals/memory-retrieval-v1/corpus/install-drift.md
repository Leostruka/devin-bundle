---
title: install drift vs bundle audit
date: 2026-11-15
session: install
category: pattern
tags: [install, drift, audit]
status: active
cues:
  - keyword: "install drift"
  - path: "install.ps1"
---

Audit check [34] compares installed files under %APPDATA%\devin to the
bundle. Sanitization merged after an install leaves Foreign=N drift.
`install.ps1 -Force -Backup` re-syncs; doctor should read 3/3.
