# 24 -- .devin/scratch contains 163 tracked files including one-off probes and gate scripts
- **Status**: resolved
- **Category**: organization
- **Severity**: P3
- **File**: .devin/scratch/ (root-level files: acp_probe.py, acp_probe_load.py, add_manifest_skills.py, reconcile_manifest.py, gate-parse.ps1, gate-pssa.ps1, gate-res.ps1, verify-p01.ps1 through verify-p04.ps1, prompt_spec*.json x5, maestri-raw.md, optimized_ready.md, cu-perception-ready.md, opendots-gap-analysis.md)

## Evidence
`git ls-files .devin/scratch | wc -l` returns 163. While many entries live in per-task subdirectories (audit-r1..r6, r7..r21, edge-audit, agentcraft-rts), ~21 files sit loose at the scratch root: ad-hoc probe scripts, five `prompt_spec_*.json` payloads, gate/verify PowerShell one-offs from prior rounds, and raw notes (`maestri-raw.md`, `optimized_ready.md`).

Per `.devin/global_rules.md`, scratch is the issue/task workspace. Loose root files make it impossible to tell which task each artifact belongs to, and because they are tracked they ship in every clone of the "distribution" repo despite being session debris. `.gitignore` only excludes `.devin/scratch/*-install/`, so nothing prevents the accumulation.

## Recommendation
Move the loose root files into task-named subdirectories (or delete ones superseded by finished rounds r7-r21), and add a `.devin/scratch/README.md` convention line requiring `NN-slug/` or `<task>/` subdirectories for any new artifacts.

## Tradeoffs
Merits: scratch becomes navigable; distribution stays clean. Demerits: historical paths in old ledgers/handoffs may reference the current loose locations.

## Verification
`git ls-files .devin/scratch | awk -F/ 'NF==3'` lists the tracked root-level files; `ls .devin/scratch` shows the same set plus untracked logs like `pytest-128.log` (ignored by `.gitignore:54 *.log`).

## Answer
Moved all 21 loose tracked root files into task-named subdirectories via `git mv` (history preserved):

- `probes/`: acp_probe.py, acp_probe_load.py
- `gate-scripts/`: gate-parse.ps1, gate-pssa.ps1, gate-res.ps1, verify-p01..p04.ps1
- `prompt-specs/`: prompt_spec.json + 4 named variants
- `notes/`: maestri-raw.md, optimized_ready.md, cu-perception-ready.md, opendots-gap-analysis.md
- `tools/`: add_manifest_skills.py, reconcile_manifest.py, Import-DevinFunctions.ps1

Added a convention line to `.devin/scratch/README.md` forbidding new loose files at the scratch root. `git ls-files .devin/scratch | awk -F/ 'NF==3'` now returns only `README.md`. No .gitignore change needed (debris classes like `*.log` already ignored); remaining references are in historical ledgers/plans, left as-is.
