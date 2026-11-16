---
title: YouTube subtitle 429 fallback via whisper.cpp
date: 2026-11-14
session: yt-batch3
category: pattern
tags: [asr, whisper, youtube, 429]
status: active
cues:
  - keyword: "whisper"
  - path: "extensions/asr"
---

When yt-dlp subtitle endpoints return HTTP 429, download audio and
transcribe locally with whisper.cpp. Model `base` transcribed a 740s
video in ~372s; `small` timed out at 600s on this hardware.
