---
name: context7
description: Use when the user asks about a library, framework, or component and up-to-date docs would help.
allowed-tools: [exec, read]
---

# Context7

## Overview

Retrieve current documentation for a software library using the Context7 API.
There is no built-in `context7` tool; this skill uses the installed helper
script via `exec`.

## Helper

The skill ships with a Python helper located at
`skills/context7/scripts/context7.py` in the bundle. After running the bundle
installer, it is available under the Devin home `skills/context7/scripts/`.

### Windows

```powershell
python "$env:APPDATA/devin/skills/context7/scripts/context7.py" "<libraryName>" "<query>"
```

### Linux / macOS

```bash
python ~/.config/devin/skills/context7/scripts/context7.py "<libraryName>" "<query>"
```

## Output

The helper prints the Context7 documentation text for the requested topic. If
the library is not found, it writes an error message and exits with code 1.

## Fallback (manual curl)

If the helper is not installed, use `curl` directly:

```bash
# 1. Find the library ID
curl -s "https://context7.com/api/v2/libs/search?libraryName=LIBRARY_NAME&query=TOPIC" | jq '.results[0].id'

# 2. Fetch documentation for the topic
curl -s "https://context7.com/api/v2/context?libraryId=LIBRARY_ID&query=TOPIC&type=txt"
```
