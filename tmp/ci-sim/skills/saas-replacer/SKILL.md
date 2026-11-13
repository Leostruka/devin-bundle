---
name: saas-replacer
description: Use when auditing paid subscriptions and replacing the replaceable ones with minimal self-hosted clones — inventory -> rank -> clone -> maintain. The cheap sibling of device-repurpose: pure software, zero hardware risk.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, write, edit, exec, webfetch]
---

# saas-replacer

Audit the user's subscriptions and clone the ones where a small
self-hosted replacement beats the monthly bill. Verified basis:
levels.io self-reported purge (~80 bills -> 6).

## Stage 1 — inventory

Build the subscription table from receipts, bank exports, or a CSV the
user provides. Columns: name, cost/mo, category, what it actually does
for the user (not the marketing page — the used features).

## Stage 2 — rank (explicit rubric, not vibes)

Score each candidate 0-5 on four axes:

| Axis | Question |
|---|---|
| Data gravity | Does the service hold data that is hard to export? (higher = harder to replace) |
| API surface | How much of the product does the user actually consume? (smaller = easier) |
| Build cost | Estimated hours for a minimal clone vs 24 months of bills |
| Ops burden | Does the clone need uptime, backups, a domain? (higher = keep paying) |

Replace top scorers only; "keep paying" is a legitimate verdict —
write it down so the audit doesn't repeat.

## Stage 3 — clone

Smallest-viable scope: the used features only, self-hosted (a single
VPS, a NAS, or a spare machine). Emit **one scoped issue per
replacement** — never a mega-build spanning the whole inventory.

## Stage 4 — maintain

Each clone gets: a scheduled-turns upkeep slot (dependency bumps, data
backup check) and a **kill criterion** written at build time (e.g.
"if it rots for 3 months, go back to paying"). A clone without a kill
criterion becomes a second subscription you can't cancel.

## Boundaries

- No account scraping against ToS — inventory comes from exports the
  user provides or documents the user pastes.
- Credential-heavy services (banking, tax) stay commercial unless the
  user explicitly overrides; least-privilege defaults.
