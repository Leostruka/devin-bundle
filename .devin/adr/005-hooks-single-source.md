# ADR 005: hooks.v1.json as the single source of hook wiring

## Status

Accepted

## Context

Devin CLI reads hook wiring from `config.json.hooks` in the live Devin
home. Two writable surfaces for the same wiring (the repo copy and the
live config) caused a real split-brain incident in 3.18.0 on Windows,
where live edits diverged from the repo and were silently lost or kept
per machine. Hook commands must also point at the installed `scripts/`
directory, which differs per machine, so the repo cannot ship a literal
`config.json` hook block.

## Decision

`hooks.v1.json` at the repo root is the authoritative hook wiring. At
install time `scripts/render-user-hooks.py` renders it into the live
`config.json.hooks`, rewriting command paths for the real Devin home.
Exports strip `config.json.hooks` out of the repo `config.json`, so the
template stays the only versioned surface. The `v1` in the filename is a
schema version marker: if the hook payload/wiring schema ever needs an
incompatible change, a `v2` file supersedes it rather than mutating the
format in place.

## Consequences

- Edits to live `config.json.hooks` are ephemeral; the next install
  overwrites them. Documented in TOOLS-MAP and BUSINESS-LOGIC R4/R8.
- One file diffs cleanly in review; drift between repo and live hooks is
  detectable by re-rendering and comparing.
- Install now depends on Python for the render step; the installers keep
  a degrade path when Python is missing.
- If the CLI gains a native hooks-file import, this ADR must be
  superseded, not silently contradicted.
