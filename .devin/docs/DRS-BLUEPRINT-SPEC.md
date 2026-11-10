# DRS blueprint spec - devin-bundle (draft, platform-blocked)

Issue #456. `devin cloud drs` surface verified 2026-11-10 (CLI 3000.12.43):
`whoami` OK (org + api_key_set), but `blueprint-list` fails
`Organization not found` - this org has no DRS entitlement. Live
verification (sandbox-create + run) is deferred until DRS access exists.

This spec maps the local installer (`install.sh`, POSIX lane) to a
draft `environment.yaml` blueprint so a cloud session can reproduce the
bundle environment. Everything below is unverified against a real box.

## What the installer actually does (install.sh)

1. Sync bundle files to `$DEVIN_HOME` (`~/.config/devin/` on Linux,
   `%APPDATA%\devin` on Windows): skills/, extensions/, hooks/, docs/,
   scripts/, mcp_config.json (skipped when secrets are MASKED).
2. Render `{{APPDATA}}`/`{{HOME}}` templates in hook configs.
3. Create per-extension `.venv` (computer-use, scrape-tools, ai-tools,
   image-forensics, laya-tools, media-tools, ppisp-prep) and pip install
   each `requirements.txt`; stamp `.deps.sha256`.
4. Build `extensions/rust-core` crates with cargo (abi3 artifacts).
5. Install `credentials.toml` only when unmasked (never via blueprint -
   secrets belong to `drs secret-create`).
6. Post-install `devin doctor` smoke.

## Draft environment.yaml (unverified)

```yaml
# blueprint seed for: devin cloud drs blueprint-create \
#   --repo Leostruka/devin-bundle --from-file environment.yaml
system_dependencies:
  - python3 >= 3.11
  - python3-venv
  - pip
  - git
  - ffmpeg            # asr/media-tools
  - cargo             # rust-core abi3 build (optional lane)
setup_commands:
  - git clone https://github.com/Leostruka/devin-bundle.git bundle
  - cd bundle && bash install.sh -Force -Backup
  # per-extension venvs are created by the installer itself
  - devin doctor
environment_variables:
  DEVIN_HOME: ~/.config/devin
secrets:
  # org-level via `devin cloud drs secret-create`; consumed by
  # credentials.toml template - never embedded in the blueprint
  - GOOGLE_OAUTH_TOKEN   # gcal extension (optional)
```

## Open questions for live verification

- Does the blueprint schema match this shape (`system_dependencies`,
  `setup_commands`, `secrets` keys)? Confirm against `blueprint-create`
  on an entitled org, or `devin cloud drs run` output of a sandbox.
- Cloud boxes are Linux: `install.sh` lane only; the `{{APPDATA}}`
  template renders to `~/.config/devin` - verify hook paths post-install.
- Model caches (laya HF cache, dory GGUF) are multi-GB and NOT part of
  the blueprint - document as post-boot warm steps or leave lazy.
- `drs secret-create` is org-wide: name keys `BUNDLE_*` to avoid
  collisions with unrelated org secrets.

## Verification plan (when entitled)

1. `devin cloud drs blueprint-create --repo Leostruka/devin-bundle --from-file environment.yaml`
2. `devin cloud drs sandbox-create --repo Leostruka/devin-bundle`
3. `devin cloud drs run -- <cmd>`: `devin doctor` must report all lanes;
   `python scripts/pulse.py --dry-run` must emit ok:true.
4. Diff bundle `manifest.json` hashes on the box vs local checkout.
