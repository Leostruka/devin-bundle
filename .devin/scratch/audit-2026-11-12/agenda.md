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

### Bloco 4 - progresso real (vs plano)

- 13:30-14:00 transcrições 12/12 (cp1252 fix mid-flight) + fetch 2 links
- 14:00-14:15 survey + 7 issues GitHub (#567-#573) + 7 locais
- 14:15-14:45 #573: pin transcribe + varredura 35 ext emitters (PR #574 merged)
- 14:15-14:50 #567 perf playbook + #569 glossary (PR #575 merged); #571 COVERED fechada
- 14:50-15:10 pointers duráveis skills (PR #576 merged) + Rune spike VALIDADO (#570 fechada)
- 15:10-15:30 audit [42] novo check + 3 scripts pinados (PR #577) + changelog refs
- Pendente: #572 backlog (GPU), #431 (decisão usuário), merge #577 + sync live

### Bloco 4 - fechamento (15:10)

- Review subagent no bloco: HIGH pins em modulo importavel (mutava stdout do host) -> pins movidos p/ main()/__main__ (29), removidos de 6 sem stdout; [42] detection estendida; fatos corrigidos (MiniMind/gputaskman/ccore); playbook EN
- #572: PoC CPU validado e FECHADO (adapter_expand.py - core frozen bit-identico, loss 5.4->1.3, 0.109% params)
- PRs do bloco: #574 #575 #576 #577 #578 - todos merged
- Estado: audit 49/49 limpo, pytest 2491, ledger 0 drift, live sync
- Restam: #431 (decisao usuario), #565 (tracking intencional)

### Bloco 4 - round skills-utf8 (15:10)

- Gap pos-review: scan [36]-[42] cobria so extensions/+scripts/; estendido p/ skills/
- 16 violacoes reais corrigidas: dma emitters (stdout pin), 5 stdin readers, 8 subprocess encodings, file io em scaffold/memory
- review-package.py:63 foi a ultima warning
- audit 49/49 limpo; pytest 2491/8skip; ledger 1427/0 drift
- PR #579 auto-merge armado (aguardando CI)

### Bloco 4 - round scaffold + ledger (15:50)

- #579 merged. Explorando #580 achou BUG REAL: scaffold.py quebrado desde #55
  (git mv p/ scripts/ deixou skill_dir apontando p/ scripts/, load_template
  404 no primeiro template - nunca funcionou pos-refactor)
- Fix skill_dir + extracao: MERMAID_TEMPLATES(14) + 5 scripts embedded ->
  templates/mermaid/ + templates/vault-scripts/, byte-identico
- Verificacao held-out: golden diff vault antes/depois = identico
- scaffold.py 1204 -> 331 linhas; PR #581 merged, #580 fechada
- Achado 2: install-ledger reconcile MASCARAVA drift - record-all em live
  desatualizado gravava stale rendered + new source -> "Current" falso
  (16 arquivos skills estavam stale no live, reconcile dizia 0 drift)
- Fix: shortcut rendered so vale p/ _RENDERED_FILES (config.json/hooks);
  regression test adicionado. Live sync real feito: 1446 Current/0 drift
- PR #582 em CI

### Bloco 4 - smoke sweep + [43] (16:10)

- #582 merged. Smoke sweep `--help` em TODOS os skill scripts achou:
  - refresh.py (vault template extraido): NameError sys - pin orfao dentro
    da literal; invisivel p/ py_compile enquanto string (#583)
  - scan estatico AST como check [43] -> pegou internal_probe.py (os
    sem import - crash em runtime)
- Audit agora 50 checks; teste e2e scaffold adicionado (roda vault real +
  --help nos 5 scripts gerados - cobre ambos os bugs) - PR #584
- fold_store RC=2 = CLI manual sem --help (documentado, nao bug);
  librosa = dep opcional; templates interativos = esperado

### Bloco 4 - non-ascii emitters (16:45)

- Smoke sweep extensions: grainrad --help crashava UnicodeEncodeError
  (-> em help text, cp1252). Mesma classe dos pins, mas [42] so cobria
  ensure_ascii=False
- AST sweep: 13 CLIs a mais com literais nao-ASCII em print/add_argument
  sem pin -> todos pinados; [42] estendido p/ detectar a classe (AST)
- PR #585 merged; live sync + ledger 1446/0 drift
- Estado final do dia: audit 50/50 limpo, pytest 2491, 0 PRs, CI verde
