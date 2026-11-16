---
title: caldav e2e test is flaky on CI windows
date: 2026-11-15
session: ci-debug
category: lesson
tags: [ci, flake, caldav, windows]
status: active
cues:
  - keyword: "caldav"
  - symbol: "test_caldav.py"
---

test_wrapper_caldav_e2e_freebusy_add_apply fails intermittently on
windows-latest py3.11 runners with returncode 1 and empty stderr while
passing locally and on the same commit in PR CI. Re-run resolves it.
Treat as transient, not a code regression.
