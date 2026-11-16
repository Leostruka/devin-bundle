---
title: verified commit signing setup
date: 2026-11-14
session: rule-30
category: convention
tags: [git, signing, ssh, verified]
status: active
cues:
  - keyword: "signing"
  - keyword: "verified"
---

Commits sign via `gpg.format=ssh` + `commit.gpgsign=true` +
`user.signingkey` pointing at the .pub file. GitHub needs the key
registered as a Signing Key, which requires the admin:ssh_signing_key
scope - API POST fails without it, manual registration is the fallback.
