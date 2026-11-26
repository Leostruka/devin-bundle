# Ledger: self-improvement 2026-11-26 (deadline 18:00 BRT)

DELEGATION: disabled
INPUT_REGISTER:
- IN-1: objetivo /goal (rodar planejamento de melhoria dos videos + self-improvement ate 18h BRT, versionar)
- IN-2: batch1 report (.devin/research/media-osint-20261126/bundle_refinement_report.md)
- IN-3: batch2 report (.devin/research/media-osint-20261126-yt2/bundle_refinement_report.md)
SOURCE_REGISTER: ambos os reports aceitos (evidencia primaria em cards/ e external/)
VFS: audit.py verde; pytest verde; por item ver seu bloco
SCOPE: skills/, scripts/, config.json, data/, tests/ aditivos, .devin/plans/

## FASE 0.6 baseline
OUTCOME: estado inicial reproduzivel
CHECK: python audit.py; python -m pytest -q --co
EXPECT: coleta sem erros
EVIDENCE: 3689 testes coletados 4.35s; audit avisa live!=bundle pre-existente (nao regressao); tests/held-out existe; gpgsign=true

## Itens
(estado por item: pending/applied/deferred/rejected/blocked + evidencia)

- I-01 applied (commit 0ebd4c0; grep evidence 0->1 match; 80 skill tests pass; classe INCONCLUSIVO comportamental, gap fechado verificavel)
- I-02 applied (commit c6a9f5a; 87 testes passam; classe INCONCLUSIVO comportamental, disciplina de juiz endurecida)
- I-03 applied (commit com I-02+; variant matrix + decisions.md; testes skill passam)
- I-04 applied (commit com council; skill nova + manifest 194; 80 testes skill passam; audit sem FAIL)
- I-05 applied (commit; behavioral tool-use eval no agent-eval; testes passam)
- I-06 applied (commit; 7 licoes operacionais codificadas + drift de hashes reparado)
- I-07 applied (commit; VIDEO.md+slop corpus+preview loop+video-fixer; audit rc=0; 25 contract tests passam)
- I-08 applied (commit; skill vendored MIT adaptada; audit rc=0; 80 testes passam)
- I-09 applied (commit; coreografia + break-ui importados; Sakuga deferido com razao)
- I-10 applied (commit com I-11; resume+checksum+frame-accurate clipping)
- I-11 applied (commit com I-10; convencao .devin/design/<surface> compartilhada prototype+impeccable)

## I-12 (descoberto durante validacao): manifest drift automation
OUTCOME: skill export_hash drift invisivel; 73 entries stale
CHECK: python scripts/sync-manifest.py --check; audit c9d
EXPECT: rc=0 drift=0 apos repair
EVIDENCE: 5/5 validation tests; probe CRLF tolerance; audit rc=0 zero FAILs
CLASSE: MELHOROU-candidato (gate novo com probe adversarial incluido)

## Candidatos deferidos com razao
- D-1 destructive-gate FP em `git show HEAD:arquivo` (bloqueio falso-positivo observado 1x; regexes ADS nao reproduzem match isolado; editar gate de seguranca exige campanha de probes dedicada - ROI baixo para frequencia baixa). Workaround documentado: script em arquivo.
- D-2 em-dash hook bloqueia carryover de texto existente com em-dash (custo ~2 tool calls; deteccao diff-aware complexa; frequencia baixa).
- D-3 Sakuga rest/anticipation/hit: sobreposicao com gramatica anticipation/release/smear existente em animation-direction.
- D-4 rust-core cargo build falha no install (GNU link.exe de Git Bash shadowing MSVC link; fast_math.pyd pre-existente funcional; fix exige deteccao de toolchain MSVC - deferido ambiental pre-existente)

## Estado 08:25 (pre-compaction snapshot)
- install.ps1 -Force -Backup CONCLUIDO: 70 overwritten, backup dir ~/.devin-import-backup-20261126-080106, doctor 3/3
- video-fixer VALID_PROFILES fix commitado (b65ae54) - full regression tinha 1 falha, corrigida
- destructive-gate gate-10 agora inclui matched text no block reason - 115/115 testes gate passam
- refinements.log.jsonl: 111/111 valid, 0 phantom (validator verde)
- full pytest rodando em background desde 08:16 (shell a77df0, log /tmp/fullpytest.log)
- PENDENTE: push de 14+ commits para origin/main quando suite verde (Rule 5)
- live sync: validate-tool-args.py e destructive-gate.py copiados manualmente pos-install
- PUSH 08:30: 3ee3c5b..d5c9c2c main (15 commits), full suite 3631 passed 0 failed
- CI rodando: run 45811099316 (CI) + pages

## CI-linux-red campaign 08:55
- ci healing round 1 pushed: 098c4d9 (A fixture identity, B skipif nul/reserved, C egm files force-added)
- CI run novo vai rodar ~10min: verificar gh run list --branch main --limit 2
- WSL repro: branch_d passa 9/9 em py3.10 local - falhas CI sao ambientais; se round 1 nao curar merged-branch assert, proximo passo: ler gate7 cherry logic no destructive-gate e logar stderr do gate nos testes
- cluster D (test_msys_drive_translation_is_nt_scoped) NAO corrigido - precisa ler _abs_targets em scripts/architecture-gate.py
- test_doc_coverage_map jev pode precisar de mais arquivos force-added
- reviewer subagent 750c1924 despachado para revisar diff 3ee3c5b..d5c9c2c - ler resultado com read_subagent

## REVIEW-FIX EM ANDAMENTO 09:10 - NAO COMMITADO AINDA
Reviewer 750c1924 achou 6 issues no diff 3ee3c5b..d5c9c2c. Estado do fix:
- FEITO: sync-manifest.py estendido p/ scripts (.py+.js; .js excluido de script_count), ok=not changes and not problems, counts=canon auditoria (disk), apply cobre scripts
- FEITO: video-fixer original_path control-chars corrigido no manifest.json (%APPDATA%\devin\agents\video-fixer.md)
- FEITO: drift zero verificado --check ok:true
- PENDENTE 1: 4/5 testes tests/validation/test_sync_manifest.py FALHAM - testam semantica antiga (counts por entries do manifest; unlisted-skill nao falhava check). Atualizar testes p/ nova semantica: unlisted skill => rc1 ok:false; counts seguem disco.
- PENDENTE 2 (reviewer 4): c9d em audit_checks/m_manifest.py pula export_hash falsy e imprime OK - deveria flagar missing hash como warning
- PENDENTE 3 (reviewer 6): test_unlisted_skill_reported_not_added ignora resultado do subprocess apply - tighten; ADS matched-output em destructive-gate sem regression assert
- PENDENTE 4: rodar audit.py + commitar + push (CI healing round 1 098c4d9 ja foi pushed, verificar gh run list)
- CI healing round1: verificar resultado - gh run list --branch main
- cluster D msys translation ainda nao corrigido
- 09:20 review-fix commitado+pushed (d01180): sync-manifest scripts coverage/structural-drift/counts/video-fixer path. 5/5 testes passam
- RESTA reviewer: item4 c9d missing-hash warning, item6 ADS regression assert, cluster D msys, CI verify

- D-1 ROOT CAUSE CONFIRMADO 09:30: gate 10 escaneia heredoc bodies como texto shell; strings python contendo padrao redirect+dois-pontos (ex: shell-redirect simulado em dados) disparam ADS. Narrowing correto exige parser de heredoc interpreter-aware - deferido; workaround documentado: write tool
- reviewer item 4 FEITO: c9d flaga missing export_hash (warning) e reporta categorias independentes
- reviewer item 6 FEITO: test_ads_block_reason_includes_matched_text (64/64 nul tests)

## 09:55 checkpoint
- heredoc narrowing pushed 326ea6e - FP class eliminada, verificado live
- healing round 2 CI em andamento (45818772973) - branch_d instrumentado vai revelar cherry
- proximo grande alvo: behavioral eval runner (yt2 P0) - docs em agent-eval, sem implementacao

## 10:20 checkpoint
- behavioral-eval harness pushed (9e265cc): validate/grade/record/compare, 8/8 testes, envelope probe
- artefatos research versionados localmente (37 arquivos textuais, meta/frames excluidos) - commit local, push retido p/ batching
- no-em-dash carryover exemption commit local - 36/36 testes
- CI 45820793998 em andamento - contem branch_d instrumentado
- security review heredoc narrowing: subagent 2eab2849 em andamento
- pushes pendentes: artifact commit + em-dash commit

## 10:50 checkpoint
- batch pushed e8d323c (4 commits: artifacts research, em-dash carryover, branch_d fixture hardening, push-cadence lesson)
- drift pre-existente RESOLVIDO: montador-de-ideias/pr-review/prompt-compiler/self-extend live == repo (install reconciliou; backup existe)
- CI cycle em andamento p/ e8d323c
- security review narrowing: subagent 2eab2849 ainda rodando (30min+)
- aprendizado operacional: NAO pushear em rajada - cancel-in-progress mata verificacao (ja codificado no skill github-actions)
- config.json hooks diff = benigno (repo vazio by-design, live renderizado por render-user-hooks)
- inference-optimisation dogfood INVIAVEL: nenhum servidor LLM local (11434/8000/5000 vazios) + disco critico
- behavioral-eval caso real: autoria adiada - artefato de output do modelo precisa de pipeline de amostragem definido; harness validado como infra
- sync-manifest live copy DESATUALIZADA vs repo (review fixes) - reconciliar no install final do dia

## 11:35 - INCIDENTE DE SEGURANCA: narrowing heredoc revertido
- council/reviewer 2eab2849 retornou UNSAFE no commit 326ea6e com 7 bypasses verificados por probes reais (artefatos nul/ADS criados): fake-op em comentario/quote, truncamento de delimitador, multi-heredocs, recipiente shell indireto, recipiente cmd, sintese deescape-union
- premissa "dados inertes" FALSA: stdin de interpretador e codigo executavel (os.system)
- ACAO: revert completo aplicado, gates 9/10 voltam a escanear bodies; 134/134 testes passam; live hook re-sincronizado (estava enfraquecido)
- licoes: (1) narrowing de gate de seguranca exige review adversarial ANTES do merge, nao depois; (2) regex nao substitui parser shell-aware; (3) o council dogfood pagou - pegou regressao real que 125 testes verdes nao pegaram
- bypasses convertidos em regressoes permanentes must-block; FP aceito documentado com workaround write-tool
- regra futura: qualquer narrowing em destructive-gate exige probes adversariais verificados + review externo

## CI mystery RESOLVIDO: shallow checkout
- diagnostico instrumentado revelou: `fatal: not a valid object name: HEAD~1` - o job Tests usava checkout shallow (depth 1)
- fix: fetch-depth: 2 no job Tests + whitespace trailing removido dos artefatos de pesquisa (static checks)
- licenca de instrumentacao confirmada: asserts com output do gate revelaram em 1 ciclo o que 5 ciclos de teorizacao nao revelaram
- licao gitignore: .devin/ e catch-all ignore (linha 86) por design - curadoria explicita via force-add de paths PRECISOS; `git add -f .devin/research` como dir sweep pegou gitlink aninhado + logs (commit desfeito antes do push). Nunca force-add em diretorio, so em arquivos nomeados

## 12:40 checkpoint
- push be015f9: revert seguranca + fetch-depth 2 + whitespace + yt2 evidence (suite local 3663/3663 verde antes do push)
- commits locais nao pushados: council mandatory-triggers + gate message write-tool workaround (aguardando CI - licao de cadencia)
- install rodado, doctor 3/3, live sincronizado (hook-drift confirma zero drift)
- hook-drift mystery resolvido - rodar a copia LIVE, nao a do repo (repo copy no-ops por design); silencio = sincronizado
- refinements 119/119 validos, 0 phantom
- FP ao vivo documentado: o proprio gate bloqueou esta ledger entry (verbo install + texto com colon); workaround write-tool funcionou - a mensagem nova se pagou em minutos
- aguardando CI 45828702156 para veredicto final da campanha de cura

- FINDING empirico (ads_probe.py): target com stream vazio (name: trailing-colon) FALHA ALTO no Windows (filename syntax incorrect, rc=1) - nao ha desvio silencioso, logo o match do regex nesse caso e over-inclusive (FP de precisao, nao narrowing). Candidato futuro a correcao de precisao COM council pre-merge (trigger mandatorio). Custo FP hoje: ~2 blocos/dia, workaround trivial. ADIADO com evidencia

## MARCOS 11:00 - CI 100% VERDE
- CI run 45828702156: SUCCESS em todos os 13 jobs (6 tests matrix, static, installers x3, rust, changes, pages)
- campanha de cura CI COMPLETA - 21 falhas preexistentes viraram zero; validado com precisao (branch_d 9/9 ubuntu py3.14, nao skip)
- push final e5bdf93 (council mandatory triggers + gate message); novo ciclo CI em andamento
- estado git limpo, tudo pushado

## ESTADO PARA RETOMADA (pos-compactacao)
- repo D:/Programing/ai_workspace/devin-bundle branch main, tudo pushado ate e5bdf93
- live config sincronizado (doctor 3/3) + cp manual do gate
- pendencia de verificacao: CI run do push e5bdf93 (deve ficar verde - mudancas doc/message-only)
- candidato tarde: correcao de PRECISAO do ADS regex p/ trailing-colon-empty-stream (evidencia empirica em .devin/scratch/ads_probe.py). Exige probe de bash semantics (unverified) + council pre-merge. NAO urgente
- deadline 18:00 Brasilia (=21:00 UTC). Relatorio final devido antes disso
- licoes-chave do dia no ledger acima + refinements.log.jsonl C118-C143 (119/119 validos)

## 12:20 - BEHAVIORAL-EVAL LOOP FECHADO (yt2 P0 completo)
- sample command implementado: devin -p em workspaces isolados, hooks live aplicam dentro das amostras, digest transcript+artifacts com marcadores ###, grade+record automatico, paralelismo cap 3
- primeiro caso real minerado: gate-sensitive-file-creation (da friccao reproduzida 4x hoje)
- baseline R1-20261126: 3/3 PASS, verificado por inspecao direta de artifacts (36 bytes verbatim em todos)
- valor: regressao comportamental de tool-use agora e testavel; baseline verde significa que agents atuais ja usam write-tool corretamente
- 10/10 testes harness (deterministicos, zero modelos em CI); commit dcfbf0d local
- finding secundario: agents amostrados NUNCA tentaram heredoc primeiro - write-tool e o caminho natural; o caso protege contra regressao futura (ex: troca de modelo)

- REFUTADO o candidato de precisao trailing-colon: probe bash (.devin/scratch/ads_bash_probe.py) mostrou que Git Bash NAO falha - converte : em U+F03a silenciosamente, criando arquivo com nome mangled invisivel (probe.txt). Mesma classe de wrong-state que ADS. Gate esta CORRETO em bloquear; nao existe correcao de precisao segura. Custo FP aceito definitivamente; licao: probes de 10min economizaram council + mudanca errada

## CHECKPOINT 11:05 BRT - TUDO PUSHADO ATE b75670c
- suite local 3665/3665 verde; pushed e5bdf93..b75670c (behavioral-eval loop + cost limitation doc)
- compare end-to-end exercitado em dados reais: baseline 1.0 vs candidate 1.0 verdict improved-or-equal
- decisao documentada: encoded-exec gate friction (python -c multiline) NAO e candidato a narrowing - a friccao empurra para write-tool/script-file que e melhor engenharia; FP e forcing function
- CI ciclando p/ b75670c
- RESTANTE ATE 18:00: verificar CI final, relatorio final abrangente, melhorias leves conforme contexto permitir
- plano mestre .devin/plans/2026-11-26-video-self-improvement.md atualizado com status completo

## CLOSEOUT CHECKLIST (executar antes das 18:00)
1. CI final verde p/ ultimo push
2. push do commit de telemetria (local, aguardando cadencia)
3. install final -Force -Backup + doctor 3/3
4. hook-drift zero confirmado na copia LIVE
5. suite completa final (se houve mudanca desde a ultima)
6. relatorio final atualizado com numeros definitivos
7. ledger de refinements validado (validate-refinement-evidence)


## Independent review findings resolved (14:40)

Reviewer be0e17c8 verdict ISSUES-FOUND: 1 critical + 7 important + 4 minor. Resolution commit (this batch):

| # | sev | finding | resolution |
|---|-----|---------|------------|
| 1 | crit | workspace escape via absolute/.. keys | keys validated; probe-verified blocked |
| 2 | imp | .devin contamination false-passed content graders | digest excludes .devin + end-delimits; probe-verified, no overcorrection |
| 3 | imp | imports absolute-path read + empty-needle green pass | cwd/tempdir sandbox + unmatchable sentinel + empty fails visibly |
| 4 | imp | daemon mode outlives timeout | --process-model=in-process |
| 5 | imp | sample evidence ephemeral | .beval-output.txt persisted; ledger carries workspace/timed_out/wall/detail/evidence |
| 6 | imp | no executable control case | control-trivial-bugfix-no-ceremony authored + validates |
| 7 | imp | tracebacks on foreseeable failures | stamped ok:false envelopes in both CLIs |
| 8 | imp | yt2 evidence incompletely versioned | 7 textual artifacts curated and committed |
| 9 | imp | changed instruction docs lack validation contracts | ACCEPTED DEBT - process-level item, doc_coverage mapping is a larger design task; recorded for post-deadline |
| 10 | min | NOTICE attribution incomplete | inference-optimisation entry added |
| 11 | min | stale counts | 22/195/29 corrected in README+TOOLS-MAP |
| 12 | min | plan overstates I-09 | corrected: learn-taste/Sakuga honestly deferred |
| 13 | min | stale narrowing comment in gate | removed |

Tests: 8 new regression tests in tests/test_behavioral_eval_sandbox.py encode the exploit shapes (must stay fixed). 18/18 behavioral eval tests pass. 85/85 gate tests pass. audit rc=0.


## CHECKPOINT pos-review completo (~15:25)

- Push final: 56fdba8 (3 commits: fix review findings + equals-form + ledgers)
- Suite local: 3676 passed, 66 skipped
- CI rodando para 56fdba8 - verificar com: gh run list --limit 3
- Reviewer be0e17c8: 13 findings, 12 resolvidos + probes adversariais, #9 divida aceita documentada
- RESTA para closeout: (1) CI verde confirmar, (2) relatorio final commit final, (3) install final doctor 3/3, (4) encerrar as 18h ou antes se contexto esgotar
- Deadline: 18:00 Brasilia. Contexto critico - trabalhar enxuto.
