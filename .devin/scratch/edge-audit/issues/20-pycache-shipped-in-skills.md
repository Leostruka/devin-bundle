# 20 -- __pycache__ trees inside skills/ and scripts/ are shipped to install targets
- **Status**: open
- **Category**: organization
- **Severity**: P3
- **File**: skills/context7/scripts/__pycache__/, skills/brag/scripts/__pycache__/, skills/dma/tools/__pycache__/, skills/context-hygiene/scripts/__pycache__/, skills/devin-manager/scripts/__pycache__/, scripts/__pycache__/, __pycache__/ (root)

## Evidence
Multiple skill directories contain committed-present `__pycache__/` dirs with `.cpython-314.pyc` artifacts (untracked per `.gitignore:2` but present in the working tree that installers copy from). Both installers copy skills recursively with no exclusion:

- install.sh line 299: `cp -r "$skill_dir" "$dst_dir"` for new skills; line 292 same for updates.
- install.sh line 415: `cp "$script_file"` copies each top-level file of scripts/ but `scripts/__pycache__/` is a directory so it is skipped there; however skill-level `scripts/__pycache__` dirs ride along with `cp -r`.
- install.ps1: `Install-SkillDir` -> `Copy-FilteredDir` is called for skills with `$exclude = $null` (line 501), so nothing is filtered. The exclude regex `'\.venv\\|\\target\\|\.(pyd|so|dylib)$'` is only applied to extensions (line 631).

Result: stale bytecode lands in `%APPDATA%\devin\skills\...`, wastes space, and can shadow source edits in tools that import from the copied tree.

## Recommendation
Add `__pycache__` and `*.pyc` to the exclusion set for skill and script copies in both installers (extend the extension exclude pattern, or add a shared default-exclude list). Also clean the working tree copies and consider `git clean -fdX` guidance in CONTRIBUTING.md.

## Tradeoffs
Merits: smaller, cleaner installs; avoids stale-bytecode bugs. Demerits: none.

## Verification
`find skills -name __pycache__` lists the dirs; run `./install.ps1 -DryRun` on a fresh target and check `%APPDATA%\devin\skills\brag\scripts\__pycache__` is created by the copy.
