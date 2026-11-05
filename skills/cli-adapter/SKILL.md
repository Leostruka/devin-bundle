---
name: cli-adapter
description: Use when a tool or app has no MCP server or official connector, when the user asks the agent to control an application, or when a thin CLI wrapper is the cheapest integration path.
disable-model-invocation: true
---

# CLI adapter

When no MCP server or official connector exists for a tool, the agent builds the connector itself: a thin CLI wrapper that exposes the app's real surface. Reference implementation: `extensions/agent-reach/wrapper.py` (whitelist-passthrough CLI adapter).

## Decision order

1. **Official MCP/connector exists?** Use it. `mcp-governance` for selection.
2. **App exposes CLI/args already?** Wrap it directly - this skill.
3. **API/library only?** Write a thin CLI over the API, then wrap.
4. **GUI only?** `computer-use`/`cu-realtime` instead - no adapter.

## Build the wrapper

- Subprocess list-form only - never `shell=True`, never string interpolation of args into a command line.
- Whitelist the verb surface: map allowed subcommands explicitly; reject everything else with a clear error (see the credential-channel rejection in `extensions/agent-reach/wrapper.py`).
- Arg-contract: flags and positional args validated against the tool's own `--help` output before first real call.
- JSON envelope on stdout: `{status, command, stdout, stderr, duration_s}` - machine-readable so callers can branch on `status`.
- Bounded: hard timeout per call, capped stdout/stderr size.
- Missing binary/toolchain returns `{"status": "missing"}` with the install hint - never fabricate output.

## Prove it before trusting it

- Smoke-test READ-ONLY calls first (`--version`, `--help`, list/status verbs) before any mutating verb.
- Mutating verbs get the destructive-ops treatment: dry-run flag if the tool has one, explicit confirmation boundary in the wrapper's doc, and a recorded contract of what each verb changes.
- The DAW pattern (reel source): "describe the change, agent controls the whole app" is the goal - but every button the wrapper can press is a liability surface. Keep the verb whitelist as small as the task allows.

## Where it lives

- Reusable across sessions: `extensions/<name>/wrapper.py` + a skill entry.
- Project-local: `.devin/tools/<name>.py` + usage note in the task doc.
- Document the adapter's verb surface and failure modes in the skill that invokes it - callers should not read the wrapper source to know what exists.
