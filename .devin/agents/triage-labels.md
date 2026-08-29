---
name: triage-labels
model: swe-1-7
description: Use when mapping canonical triage roles to local issue status values.
allowed-tools:
  - read
  - grep
  - glob
  - find_file_by_name
---

# Triage labels

| Canonical role | Local status | Meaning |
|---|---|---|
| `needs-triage` | `needs-triage` | Maintainer evaluation required. |
| `needs-info` | `needs-info` | More information required. |
| `ready-for-agent` | `ready-for-agent` | Fully specified for agent execution. |
| `ready-for-human` | `ready-for-human` | Human implementation required. |
| `wontfix` | `wontfix` | Will not be actioned. |

Use the local status in each issue file's `Status:` field.
