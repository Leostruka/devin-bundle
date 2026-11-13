# ADR 001: `{{APPDATA}}/devin` placeholder for cross-platform config paths

## Status

Accepted

## Context

The bundle must install to both Windows (`%APPDATA%/devin`) and Unix
(`~/.config/devin`) live config directories. Hard-coding either path in the
bundle would make the bundle non-portable. Using `~` or `%APPDATA%` inline in
JSON files is not valid JSON.

## Decision

Use a portable placeholder `{{APPDATA}}/devin` in bundle files
(`config.json`, `manifest.json`) and normalize it during install to the
actual platform path. During export, collapse the live path back to the
placeholder.

## Consequences

- Install/export scripts must include placeholder normalization logic.
- The placeholder must not collide with real paths.
- Characters like spaces in the expanded path are handled by quoting in scripts.
