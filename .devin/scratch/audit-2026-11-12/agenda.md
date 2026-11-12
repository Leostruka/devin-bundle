# Agenda 2026-11-12 - auditoria minuciosa full-bundle (até 17h)

| Bloco | Janela | Conteúdo |
|---|---|---|
| A | 06:15-07:00 | Baseline: audit.py, pytest, doctor, frontier, live install |
| B | 07:00-08:30 | Hooks: 8 eventos, chains, contracts, ordem, error paths |
| C | 08:30-10:30 | Skills ×185: frontmatter, manifest, pointers, dead refs |
| D | 10:30-12:30 | Scripts ×54 + extensions: envelopes, exit codes, UTF-8, docs |
| - | 12:30-13:30 | almoço |
| E | 13:30-15:00 | Interações: hooks→scripts→ext, install↔manifest↔live, CI↔local |
| F | 15:00-15:45 | Workflows/CI, docs consistency, subagent profiles |
| - | 15:45-16:45 | Issues + survey doc + fixes triviais in-loop |
| - | 16:45-17:00 | Closeout: audit final, sync, relatório |

## Loop 11:40-12:00

- operate-spline removal shipped (#540); issues #541 (PermissionRequest), #542 (test hygiene)
- Next: fix #542 cheap items (skip guards -> hard imports, fixture SessionEnd, rename, count parse)

## Loop 13:00-15:00 (remaining)

- PR serial queue babysit: #534 -> #538 -> #539 -> #540 -> #545 (auto-merge armed; update-branch per merge)
- On all merged: changelog backfill refs + install.ps1 live sync + audit full + final survey close-out
- Buffer items se sobrar tempo: #541 spike gate design; push-gate suite perf (#544 follow-up)
