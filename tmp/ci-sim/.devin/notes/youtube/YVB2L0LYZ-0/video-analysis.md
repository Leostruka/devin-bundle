# Analise: YVB2L0LYZ-0 -- "DeepSeek's God of All Harnesses" (Cloud Codes)

## Fonte

- URL: https://youtu.be/YVB2L0LYZ-0 (publicado 2026-11-02)
- Canal: Cloud Codes. Duracao: 9:46. Ingles.
- Assunto: DeepSeek "Super-agent" -- artigo (2025-10-31) + prototipo
  open-source, analise cetica de terceiro (nao e o proprio DeepSeek).

## Arquitetura descrita (extraida do transcript + contact sheet)

- **Router vs worker**: router session so roteia -- encaminha request
  + routing facts, zero decisoes tecnicas. Worker pensa/le/codifica/
  verifica na sua propria sessao e diretorio.
- **Event records imutaveis** agrupados em threads; follow-ups
  aterrissam junto do report original.
- **Gate em 2 camadas a cada 2s**: condicoes fixas em codigo (barato)
  primeiro; so quem passa chega ao modelo, que pesa contra policies
  do time no prompt.
- **Ticket** = unidade de trabalho com brief escrito, 1 worker.
  Regra: one ticket, one worker.
- **Subscription shortcut**: thread com ticket -> msg nova vai direto
  ao worker, sem re-decisao. Remover isso: +30% decisoes do router.
- **Batching sob carga**: 1->40 msg/min; router agrupou ate ~3
  msgs/request; tempo-de-modelo por decisao caiu 6.4s -> 1.6s.
- **Inferred candidates** (trabalho nao-pedido): 3 gates -- allowlist,
  regras do time, accept mode off/observe/auto. **Ship on observe**;
  would-accept so vai pro log ate revisao.
- **Manners**: respostas de 1 frase, cap 100 palavras, "fixed and
  verified" resolve sem reply, toda msg no GitHub abre com
  disclosure de agente automatizado.
- **Seguranca**: workers rodam comandos sem aprovacao como seu OS
  user e leem home dir -- isolamento = conta dedicada. Auto-merge
  so <200 linhas + required approvals do repo.
- **Cloud loop**: containers stateless + sessoes em DB; daemon leve
  no device so executa comandos. Prototipo publico = daemon local
  apenas; watchdog (sessao que julga progresso real vs drift) NAO
  esta no codigo liberado.

## Ceticismo do canal (honestidade de benchmark)

- Headline "more than doubling" -> real: **1.6x mediana, 1.9x p95**
  (12.4 vs 20.4 min mediana; 15.7 vs 29.5 p95). Teste sintetico,
  ~300 msgs com ~20 requests, mock tool calls, 5 runs.
- **Prompt neutro**: single agent delegou em 0/5 runs -- cada task
  ficou na sessao principal, interrompida pela proxima msg.
  **Delegate-first**: delegou 4/5, mediana 13.8 min. O gap mede
  relutancia em delegar, nao capacidade.
- Tokens: 23M cached vs 6M (ate 11.5M) single session; sem cache
  shortcut, 32M. ~5-10 cents de extras na DeepSeek Flash.
- Custo escondido: cada task extra = mais um resultado pra
  revisar; "restraint move o custo do chat pra review".
- Track record: reporter casou ticket IDs (12 chars) com branch
  names do repo publico: **99 PRs mergeados** set-out (75 em out).

## Mapa conceito -> bundle

| DeepSeek | Bundle |
|---|---|
| router so roteia | controller + `dispatching-parallel-agents` |
| ticket 1 worker dir proprio | fresh subagent por task + `git-workflows` lanes |
| gate 2 camadas codigo->modelo | hooks deterministicos + `skill-picker`/`context-pressure` |
| inferred candidates observe-first | hooks advisory (`stuck-detect`) + `afk-loop` sob demanda |
| subscription shortcut | `.devin/mailboxes/` + ledgers |
| watchdog progresso-vs-drift | `scripts/stuck-detect.py` (deterministico, mais barato) |
| Cooper Bench co-edit ~30% pior | secao "single agent beats" ja cita Cognition/Anthropic/MAP |
| disclosure de agente no GitHub | N/A hoje (PRs autorais do usuario); convencao Rule 2 |
| auto-merge <200 linhas | merge manual por convencao |
| cloud 24/7 + daemon | N/A |

## Melhoria implementada

`skills/dispatching-parallel-agents/SKILL.md` -- evidence block
ganhou 2 entradas:

1. **DeepSeek harness eval**: neutro delegou 0/5, delegate-first
   4/5, mediana 20.4->13.8 min -- sob fila de requests o modo de
   falha inverte: single agent sub-delega. Contraponto evidenciado
   ao vies "fique inline" da secao Early Exit.
2. **Cooper Bench**: agentes co-editando uma task ~30% menos
   sucesso -- reforca one-ticket-one-worker.

Nada mais e portavel: prototipo e produto DeepSeek (daemon local),
watchdog e cloud loop nao existem no codigo publico.
