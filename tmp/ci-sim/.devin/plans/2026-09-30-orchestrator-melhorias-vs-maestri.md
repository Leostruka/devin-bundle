# Melhorias do project-orchestrator a partir do Maestri - plano priorizado

> **For agentic workers:** este plano so executa apos aprovacao. REQUISITO:
> /dispatching-parallel-agents ou /executing-plans para implementar task a task.

**Goal:** incorporar ao `skills/project-orchestrator/` as capacidades de
orquestracao observadas no Maestri que fazem sentido numa skill de CLI
(arquivos, nao GUI), mantendo nossos diferenciais (gates, metodologia,
verificacao independente).

**Fonte:** `.devin/research/maestri.md` (dossier + matriz). Toda motivacao cita
a evidencia la.

**Arquitetura:** tudo continua file-based e dentro da skill existente;
templates ganham campos, SKILL.md ganha convencoes, o teste de contrato ganha
tokens. Nenhum runtime novo (iron rule: "compose the bundle; build no new
runtime").

## Global Constraints

- Sem edicao antes de aprovacao (spec `.devin/scratch/optimized_ready.md` AC6).
- Sem em/en-dash em qualquer markdown (teste `test_no_em_dashes` ja existe).
- Sem assinatura AI em nenhum artefato.
- `python -m pytest tests/validation/test_project_orchestrator.py -q` verde ao
  fim de cada task; suite completa `python -m pytest tests -q` no fechamento.
- So modelos free (swe-2 max/medium) nos subagentes de execucao.
- Mudancas preservam o formato do ledger: append-only, uma linha por evento.

## O que NAO adotar (registrado para nao re-avaliar)

- Canvas GUI, Metal, Wire protocol, Remote iOS, Portals: fora da natureza de
  uma skill CLI. [dossier sec. 6-8]
- Fan-out ilimitado e decisao dispersa entre agentes: contraindicated por
  Cognition "Don't Build Multi-Agents" (citado no design doc do advisor).
  Adotamos so *consulta* peer bounded, nao decisao peer.
- Routines como scheduler real: fora de escopo de uma skill; a cobertura
  equivalente e afk-loop (evento) + gates. Documentado como item opcional I10.

## Lista de melhorias (gap -> mudanca -> beneficio -> esforco)

### I1. Status surface + flag de escalacao (gap: UX/observabilidade, escalacao)

- **Gap:** Maestri empurra estado ao usuario (attention dot, notificacao,
  Ombro resume passivo). No nosso, o usuario precisa abrir ledger/handoffs.
  [dossier sec. 6, 9; matriz UX/escalacao]
- **Mudanca:** `templates/handoff-doc.md` ganha linha `ESCALATE: <razao> |
  none`; SKILL.md ganha convencao: ao receber handoff com ESCALATE, parar o
  loop e apresentar ao usuario (ja coberto parcialmente por stop conditions -
  estender); `templates/ledger.md` ganha secao `## Status` (ultima fase, roster
  ativo, escalacoes abertas, budget consumido) reescrita a cada evento - unica
  secao do ledger que nao e append-only.
- **Beneficio:** o usuario ve estado do enxame num arquivo so; escalacao vira
  sinal explicito do worker, nao so julgamento do orquestrador.
- **Esforco:** P (pequeno). Templates + 2 paragrafos de SKILL.md + tokens.
- **Pronto quando:** teste passa com tokens `ESCALATE`, `## Status`;
  handoff-doc tem o campo; ledger.md documenta a excecao a append-only.

### I2. Inputs congelados por contrato (gap: integridade de spec)

- **Gap:** Maestri tem nota bloqueada (agente le, nao escreve) como spec
  pinning [dossier sec. 4; docs/notes]. No nosso, boundary do contrato e
  convencao - worker pode editar vision.md/contrato sem quebra detectavel.
- **Mudanca:** `templates/delegation-contract.md` ganha campo `Frozen inputs:`
  com `sha256` por arquivo; SKILL.md delegation loop ganha: registrar hash no
  dispatch, re-hash no verify - divergencia = falha do contrato (registrar no
  Progress Ledger). Sem codigo novo: `certutil -hashfile` (Windows) /
  `shasum` (POSIX) ja bastam.
- **Beneficio:** deriva de spec por worker vira falha verificavel, nao
  convencao.
- **Esforco:** P.
- **Pronto quando:** contrato template tem `Frozen inputs`; SKILL.md descreve
  check; tokens no teste.

### I3. Handles de worker no ledger (gap: re-entrada de transcript)

- **Gap:** Maestri guarda o registro da thread no host e o agente o rele apos
  restart/compaction [dossier sec. 4; docs/chat]. Nos temos `resume` verificado
  funcionando pos-conclusao e `devin acp session/load`, mas nao ha convencao de
  registrar o handle para reuso.
- **Mudanca:** `templates/ledger.md` Progress line ganha campo `handle:
  <agent_id|sid>`; SKILL.md delegation contract ganha: registrar agent_id de
  cada dispatch; `resume` permitido para follow-up bounded (<=2 perguntas) alem
  do fix loop, contando no budget.
- **Beneficio:** perguntas de esclarecimento a um worker nao pagam dispatch
  novo nem re-leitura fria de artefatos.
- **Esforco:** P.
- **Pronto quando:** ledger template mostra `handle:`; SKILL.md define o
  bounded follow-up e o custo.

### I4. Convencao de reatribuicao de papel (gap: team design dinamico)

- **Gap:** Maestri reatribui responsabilidade ao vivo preservando posicao e
  conexoes [dossier sec. 2; docs/maestro]. Equivalente natural nosso: editar
  `workers/<role>/role.md` + novo dispatch - existe mas nao esta nomeado.
- **Mudanca:** SKILL.md secao Roles ganha 2 linhas: "Reatribuir = editar o
  charter + dispatch fresco com standing-context; registrar `reassign:` no
  ledger." `templates/role-matrix.md` ganha acao `reassign` na coluna Action.
- **Beneficio:** nomeia e audita uma operacao que hoje e tacita.
- **Esforco:** PP (trivial).
- **Pronto quando:** tokens `reassign` no teste; matrix template lista a acao.

### I5. Budget real consumido (gap: custo declarado vs real)

- **Gap:** Maestri mostra aneis de uso por provider [dossier sec. 6]. Nos
  declaramos budget por fase mas nao registramos consumo por contrato.
- **Mudanca:** `templates/ledger.md` Progress line ganha `spent: <turns>/<min>`
  e Task Ledger `Budget:` ganha linha `consumed:` acumulada por fase.
- **Beneficio:** estouro de budget vira observavel antes de escalar ao usuario;
  baseia decisao de fan-out em dados.
- **Esforco:** PP.
- **Pronto quando:** template atualizado; SKILL.md iron rule 6 referencia o
  campo `consumed`.

### I6. Gatilhos de consulta ao advisor (gap: advisor pull-only vs Ombro push)

- **Gap:** Ombro observa passivamente e empurra resumo + proximo passo [dossier
  sec. 6; docs/ombro]. Nosso advisor so responde quando consultado; HYGIENE
  flags existem mas nada agenda consultas.
- **Mudanca:** `reference/advisor-protocol.md` ganha tabela de gatilhos:
  apos cada outcome de gate G*; a cada N contratos (default 3); em qualquer
  handoff com ESCALATE; em RESET_WORKER flag. Cada gatilho = 1 consulta, conta
  no budget da fase. Continua pull (orquestrador inicia), mas dirigido por
  evento e nao por juizo.
- **Beneficio:** o subconsciente vigia de fato; pega deriva entre gates sem
  depender do orquestrador lembrar.
- **Esforco:** P.
- **Depende de:** I1 (flag ESCALATE alimenta um dos gatilhos).
- **Pronto quando:** advisor-protocol lista gatilhos com custo; tokens no
  teste (`trigger` ou `gatilho`).

### I7. Hooks de ciclo de vida da lane (gap: lanes sem setup)

- **Gap:** Andares tem hooks setup/run/teardown com `$MAESTRI_*` env vars
  [dossier sec. 7; docs/floors]. Nossas worktree lanes nao tem setup - worker
  reinstala deps ou falha em lane nova.
- **Mudanca:** `templates/delegation-contract.md` ganha `Lane setup:` e
  `Lane teardown:` (comandos, default none); SKILL.md Isolation rules ganha:
  orquestrador roda setup ao criar lane, teardown ao aterrissar; variaveis
  `$LANE_PATH`, `$BRANCH`, `$ROOT`.
- **Beneficio:** lanes funcionais no primeiro dispatch; cleanup declarado.
- **Esforco:** P.
- **Pronto quando:** contrato template tem os campos; SKILL.md lista as vars;
  tokens no teste.

### I8. Consulta peer bounded entre workers (gap: mensageria worker<->worker)

- **Gap:** Maestri `maestri ask` liga quaisquer dois agentes conectados, com
  ask --batch e ask-back chains [dossier sec. 2, 5]. No nosso, reviewer que
  duvida do implementer tem que voltar ao orquestrador.
- **Mudanca:** `templates/delegation-contract.md` ganha `Peer consults:
  [<role>] max <N>`; handoff-doc ganha `CONSULT: <role>: <pergunta>` que o
  orquestrador resolve de dois jeitos: (a) `resume` no handle do peer quando
  registrado (I3), cap 2 trocas; (b) dispatch de micro-contrato de consulta. O
  worker nunca ganha canal direto: o orquestrador continua sendo o roteador
  (preserva a decisao arquitetural contra decisao dispersa).
- **Beneficio:** cobre o caso real (reviewer pergunta ao implementer) sem abrir
  mensageria livre; cada consulta e auditavel no ledger.
- **Esforco:** M (medio - toca contrato, handoff, loop, teste).
- **Depende de:** I3 (handles habilitam o caminho barato).
- **Pronto quando:** contrato + handoff tem os campos; SKILL.md descreve o
  relay; teste cobre tokens `Peer consults`, `CONSULT`.

### I9. Team pack exportavel (gap: Partitura analog)

- **Gap:** Maestri exporta time+layout como `.maestripartitura` compartilhavel
  com revisao de import [dossier sec. 4; docs/partituras]. Nosso role-matrix +
  charters ficam presos ao projeto.
- **Mudanca:** novo `templates/team-pack.md` + convencao: `.devin/team-pack.md`
  agrega role-matrix + worker charters + convencoes de contrato de um projeto,
  importavel em outro projeto pela skill (le, resolve conflitos de nome,
  instancia workers/). Sem binario, sem layout - so os artefatos textuais.
- **Beneficio:** rosters provados viram ativo reutilizavel (o depoimento do
  dept. de vendas de 8 agentes e exatamente esse caso de uso).
- **Esforco:** M.
- **Pronto quando:** template existe; SKILL.md lista team-pack nos artefatos;
  teste cobre existencia + token.

### I10. Cobertura documental de rotinas (opcional)

- **Gap:** Maestri Rotinas = prompts agendados por intervalo [dossier sec. 5].
- **Mudanca:** USAGE.pt.md/SKILL.md ganham nota: checks recorrentes viram
  itens `every gate` no ledger ou issues de afk-loop; sem scheduler proprio
  (YAGNI para skill CLI).
- **Beneficio:** fecha a pergunta "e se eu quiser recorrencia?" sem runtime
  novo.
- **Esforco:** PP.
- **Pronto quando:** nota presente; sem tokens novos.

## Fases e dependencias

```
Fase A (quick wins, independentes):     I1 -> I2 -> I4 -> I5
Fase B (mecanicas):                     I3 -> I6(dep I1) -> I7
Fase C (estruturais):                   I8(dep I3) -> I9 -> I10
```

Ordem racional: A primeiro porque sao campos/convencoes baratos com retorno
imediato e criam pre-requisitos (I1 alimenta I6). B consolida mecanica de
runtime. C so depois de A+B estarem verdes - I8 e I9 sao os que mais mudam
semantica.

Cada item = 1 task com ciclo proprio: editar template/SKILL.md -> estender
tokens em `tests/validation/test_project_orchestrator.py` -> rodar teste ->
commit. Ordem interna TDD: escrever o token no teste primeiro (vermelho),
depois a mudanca (verde).

## Gates do plano (executar na implementacao)

- [ ] GP-A: apos cada item de Fase A
  CHECK: `python -m pytest tests/validation/test_project_orchestrator.py -q`
  EXPECT: 0 falhas, tokens novos cobertos
- [ ] GP-B: apos cada item de Fase B
  CHECK: idem + `python scripts/validate-skill-format.py` (se existir no repo)
  EXPECT: skill format PASS
- [ ] GP-FINAL: fechamento
  CHECK: `python -m pytest tests -q` + `python audit.py` (se existir)
  EXPECT: suite verde como em d67e018 (1488 passed baseline)
- [ ] GP-STYLE: estilo
  CHECK: `git diff` sem em/en-dash nos arquivos tocados; sem assinatura AI
  EXPECT: test_no_em_dashes verde

## Aprovacao

PARE aqui. Itens aprovados viram execucao numa sessao seguinte (Fase 4 da spec
origem). Para aprovar parcial, indicar IDs (I1..I10).
