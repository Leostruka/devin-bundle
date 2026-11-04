# 17 -- Two identical mcp_config.json files with ambiguous authority
- **Status**: open
- **Category**: organization
- **Severity**: P3
- **File**: mcp_config.json, .devin/mcp_config.json, mcp_config.json.example

## Evidence
`diff mcp_config.json .devin/mcp_config.json` produces no output: the two files are byte-identical. The root copy is the distribution artifact that both installers copy to `$DEVIN_HOME/mcp_config.json` (install.ps1:566-580, install.sh:453-479). The `.devin/` copy is the project-level config for this repo itself. A third file, `mcp_config.json.example`, also sits at root.

Nothing documents which file is authoritative. A contributor editing the project-level `.devin/mcp_config.json` will not change what installs on other machines; editing the root copy changes installs but not this repo's runtime behavior. The two copies can silently diverge because no script or test compares them (audit.py does not reference mcp_config.json).

## Recommendation
Pick one source of truth: either keep the root file as the exportable artifact and document in `.devin/CONTEXT.md` that `.devin/mcp_config.json` is a runtime copy, or symlink/generate one from the other in `export.ps1`/`export.sh`. At minimum add a comment-free check in `audit.py` or a note in CONTRIBUTING.md stating the relationship, and state what `mcp_config.json.example` is for (it is not referenced by README quick-start).

## Tradeoffs
Merits: no silent drift between project and distributed config. Demerits: generation/symlink adds a step; Windows symlinks need privileges.

## Verification
`diff mcp_config.json .devin/mcp_config.json`; `grep -rn "mcp_config" audit.py README.md CONTRIBUTING.md` shows no documented ownership.
