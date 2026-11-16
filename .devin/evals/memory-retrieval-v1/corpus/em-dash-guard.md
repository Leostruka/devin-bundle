---
title: em-dash guard behavior on imported content
date: 2026-11-14
session: phi-browser-import
category: convention
tags: [em-dash, hooks, imports]
status: active
cues:
  - keyword: "em dash"
  - symbol: "no-em-dash.py"
---

Imported vendor files trip the no-em-dash hook. Safe sanitize = replace
only on lines containing the dash, never blanket-collapse whitespace.
A blanket pass once produced an 8994-line diff that had to be reverted.
