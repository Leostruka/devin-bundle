---
title: "{{PROJECT_NAME}} - Configuration"
project: "{{PROJECT_NAME}}"
tags:
  - config
  - {{PROJECT_TAG}}
---

# Configuration

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `3000` | Server port |

## Config files

| File | Format | Purpose |
|------|--------|---------|
| `config.json` | JSON | Runtime settings |

## Feature flags

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_X` | `false` | Toggles feature X |

## Secrets management
_How secrets are stored and rotated._
