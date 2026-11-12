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

## 16:10 — ENCERRADO (adiantado vs 17h)

- Fila serial drenada: 6 PRs merged
- Live sync -Force + audit 0 err / 1 warn + pytest 2478
- Survey e issues fechados no GitHub

## Round 6 (12:00) - permission-gate 2nd-pass review
- reviewer subagent: 10 bypasses (quote-collapse, -u/space-form upload-pack,
  --open-files-in-pager, gh issue develop --checkout) -> fixed in #562 merged
- .devin/agents + apps audit via researcher: clean; "README in VALID_PROFILES"
  flagged but is a real runtime profile -> no defect
- install.sh/install.ps1 laya-tools venv parity confirmed

## Rounds 8-9 (14:00-15:15) - residual vectors + holistic review
- #563 gh -w/--web side-effect blocked; README extensions table 30/30
- #564 whole-day-diff review: hookrun stderr gating, hostname/date
  positional sets, [39] exemption scope, ledger guard boundary, mcp content
- verify: audit 48/48 clean, live probe all vectors, ledger 0 drift

## Closeout (16:15) - estado final
- 15 PRs merged (#534-#564) + tracking issue #565
- audit 48/48 clean | pytest 2491/8skip | validation 332
- live sync + doctor 3/3 | ledger 1427/0 drift
- issues: #431 aguarda decisao usuario (shadow->assist)
- surfaces: todos os items auditados item-a-item + interacoes

## Round 11 (16:55) - gate 4th pass
- #566 merged: 3 critical + 3 important residuals fechados (bundle flags,
  -u attached, brace-expansion, -F<file>, ext-strip, auth -t)
- live probe: 8 bypasses silent, reads intactos
- fim do expediente de auditoria

## Bloco 4 — deep-dive 14 links (13:30-18:00)

- [x] 13:30-14:00 agenda + recon: reels-surveyor, batch-8 dir
- [x] 14:00-14:30 transcricao 12/12 (asr --lang pt, stdout fix meio-caminho)
- [x] 14:30-14:45 fetch 2 web links (odyssey, akita) + map
- [x] 14:45-15:00 survey .devin/research/2026-11-12-reels-batch8-survey.md
- [x] 15:00-15:15 issues #567-#573 + locais
- [x] 15:15-16:30 exec: #573 pins (36 ext, PR #574), #567+#569 (PR #575 merged), #568/#571 covered
- [ ] 16:30-17:30 #574 merge + live sync + close-out; spikes #570/#572 se couber
- [ ] 17:30-18:00 buffer final + report
