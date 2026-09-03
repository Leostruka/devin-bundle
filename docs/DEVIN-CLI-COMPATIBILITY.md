# Devin CLI compatibility

## Validated release

The bundle is validated against Devin CLI `3000.6.14`.

### Changes since 3000.6.7

The CLI changelog documents the following stable releases between the previous validated release (`3000.6.7`) and the current one (`3000.6.14`):

- `v3000.6.11` (2026-09-01): MCP connection setup now times out instead of leaving later requests waiting on a stalled server, so a retry can establish a fresh connection. `devin worker start` no longer fails with `HTTP 403 Forbidden` when bootstrapping a personal outpost from an enterprise CLI login.
- `v3000.6.12` (2026-09-02): Repaired a regression connecting to MCP servers via Streamable HTTP that was introduced in `v3000.6.11`.

`v3000.6.13` and `v3000.6.14` have no published changelog entries at the time of validation (the stable changelog page had not been updated past `v3000.6.12`). The installed build reports as `3000.6.14 (18033302)`. No config-schema, hook-contract, or model-registry changes were observed between `3000.6.7` and `3000.6.14`: the eight lifecycle events, the `tools`/`allowed-tools` alias, the plugin interface, and the free-tier model registry are unchanged. The 3000.6.11/12 fixes are CLI-internal runtime behaviour (MCP transport, worker bootstrap) and require no bundle-side change.

Primary verification commands:

```powershell
devin --version
devin models list
devin doctor
python audit.py
python -m pytest
```

## Model policy

`config.json` pins `glm-5-2` as the primary model. `devin models list` in CLI 3000.6.14 reports:

- `glm-5-2`: GLM-5.2 High, 200K context, Free.
- `swe-1-7`: SWE-1.7 Max, 262K context, Free.
- `adaptive`: $0.5 input, $0.1 cached input, and $2 output per million tokens.

Alternatives evaluated:

| Alternative | Result |
|---|---|
| Keep `adaptive` | Valid model, but contradicts the bundle's explicit free-primary policy. |
| Pin `glm-5-2` | Matches the documented policy and the CLI model registry. Selected. |
| Omit the model | Delegates selection to local defaults and makes installs nondeterministic. |

Custom subagents remain pinned to `swe-1-7`. The `tools` frontmatter key is accepted as an alias for `allowed-tools` in 3000.5.20+, but this bundle keeps `allowed-tools` as its canonical spelling.

## Lifecycle hooks

The global installer merges hooks from `config.json` into the user-level configuration. `hooks.v1.json` remains the project-level template.

The eight supported events are:

- `PreToolUse`: `tool_name`, `tool_input`.
- `PostToolUse`: `tool_name`, `tool_input`, `tool_response`.
- `PermissionRequest`: `tool_name`, `tool_input`.
- `UserPromptSubmit`: `prompt`.
- `Stop`: `stop_hook_active`, plus `last_assistant_message` in 3000.5.20+.
- `PostCompaction`: `summary`.
- `SessionStart`: `source`.
- `SessionEnd`: `reason`.

Blocking `PreToolUse` hooks return exit code 2 and a top-level JSON decision containing `decision: block` and a reason. Since 3000.6.2, a blocked call reports its reason while the turn and sibling calls continue.

`memory-stop.py` accepts both `Stop` and `SessionEnd`; it consumes `SessionEnd.reason` without blocking. Stop handlers tolerate `last_assistant_message` without parsing transcripts.

## Plugins

Native plugins and Agent Plugins 1.0.0 are supported in 3000.5.20+. Native plugin manifests use `.devin-plugin/plugin.json`; Agent Plugins use `plugin.json` at the plugin root.

Plugins remain in closed beta. The existing `install.ps1` and `install.sh` workflows remain the distribution mechanism until the official plugin interface leaves closed beta. No external MCP server is required or installed by compatibility tests.

The isolated fixture at `tests/fixtures/devin-plugin-prototype/.devin-plugin/plugin.json` contains no skills or MCP servers. It was accepted by `devin plugins install --local` under CLI 3000.6.7, and a first invocation without `--local` correctly refused to sync a local path to Devin Cloud; the local registration was removed after verification. The plugin interface has no changelog entries between 3000.5.20 and 3000.6.14, so the fixture remains valid under the current CLI.

## Installer verification

Run installers only against redirected temporary homes during automated compatibility checks. A valid simulation installs all 76 skills and leaves the real user configuration untouched.

Windows uses a process-local temporary `APPDATA`. Unix uses a process-local temporary `XDG_CONFIG_HOME` or `HOME`, according to the installer contract.

## Primary sources

- Devin CLI stable changelog: https://docs.devin.ai/cli/changelog/stable
- Plugins: https://docs.devin.ai/cli/extensibility/plugins
- Lifecycle hooks: https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks
