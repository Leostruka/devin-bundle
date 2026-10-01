# project-orchestrator: guia de uso

Orquestrador de ponta a ponta: leva um projeto de pasta vazia (ou ideia
difusa) ate produto entregue com CI/CD, coordenando subagentes especialistas
sob contratos de delegacao.

## Quando invocar

- "tire este projeto do papel" / "do zero ao deploy"
- pasta vazia ou apenas uma ideia, sem spec
- projeto que precisa de documentacao de metodologia (RUP / Scrum / hibrido)
  alem do MVP

Nao usar para tarefa unica de codigo; nesses casos o fluxo
`grilling` -> `planning` -> `execution` e mais barato.

## Como funciona

1. **P0 Sessao de analista** (condicional): se nao existe visao/spec ou a
   intencao esta confusa, o orquestrador entrevista voce como um analista de
   sistemas (perguntas assertivas com recomendacao, estilo `grilling`) e
   preenche `.devin/vision.md`. Se ja existe material claro, essa fase so
   valida contra o template.
2. **G0 Inception**: visao completa, sucesso mensuravel, barra de
   conveniencia declarada. Nenhuma tecnologia antes disso.
3. **G1 Metodologia**: `.devin/development-case.md` escolhe RUP, Scrum ou
   hibrido pela regra Cynefin/Stacey + regulacao + tamanho, com artefatos
   incluidos/excluidos justificados.
4. **G2 Pesquisa + Arquitetura**: protocolo PRISMA-lite por area
   (`.devin/research/`), ADRs em `.devin/adr/`, walking skeleton rodando.
5. **G3 Construcao**: fatias verticais (INVEST, prioridade MoSCoW+RICE)
   delegadas sob contrato, cada uma verificada por `qa-ci`.
6. **G4 Transicao**: testes, docs, release semver, CI/CD, metricas DORA e
   golden signals.
7. **G5 Excelencia**: gravacao de tela (`computer-use`, `record.py`) do
   caminho real do usuario, revisada quadro a quadro. Testes verdes nao
   fecham a fase; a experiencia confirmada sim.

## Artefatos produzidos no projeto

```
.devin/vision.md            intake + barra de conveniencia
.devin/development-case.md  metodologia escolhida + tailoring
.devin/adr/NNN-*.md         decisoes arquiteturais
.devin/ledgers/<proj>.md    Task Ledger + Progress Ledger
.devin/raid.md              riscos, premissas, issues, dependencias
.devin/research/<area>.md   logs de pesquisa PRISMA-lite
.devin/handoffs/*.md        contratos e handoffs entre papeis
.devin/team-pack.md         elenco exportavel (papeis + charters + convencoes)
workers/<role>/             uma pasta por papel, com .devin/ proprio
```

O ledger tem secao `## Status` reescrita a cada evento: fase atual, elenco
ativo, escalacoes abertas. Handoffs com `ESCALATE` param o loop e chegam
ate voce.

## Limites

- maximo 3 subagentes em paralelo; budget de fan-out declarado por fase
  com `consumed` registrado por contrato
- papeis novos so com gap real registrado na matriz
- o orquestrador nao escreve codigo de produto; toda implementacao e
  delegada sob contrato
- workers leem docs da raiz somente via `Readable refs` do contrato;
  inputs de spec sao congelados por hash (`Frozen inputs`)
- sem scheduler proprio: checks recorrentes viram itens `every gate` no
  ledger ou issues de `afk-loop`

## Subconsciente (advisor)

Uma sessao `devin` parceira que o orquestrador possui via `computer-use`
(`terminal.py spawn` -> PTY com `devin` dentro) e consulta antes de
decisoes, apos ciclos, e ao replanejar abordagem ou elenco.

- Consulta: o prompt digitado e o gatilho; o conteudo vai por artefatos.
  Resposta no contrato VERDICT / RATIONALE / RISKS / HYGIENE / MEMORY DELTA.
- Estado: `.devin/advisor/` (charter, notas gerenciadas, log de consultas,
  onboarding) escrito pelo proprio advisor.
- Higiene literal: `/clear` digitado no peer reseta; o advisor pode digitar
  um pedido no terminal do orquestrador (`HYGIENE: RESET_ORCHESTRATOR`),
  que chega como mensagem de usuario; quem confirma o `/clear` do
  orquestrador e voce.
- Consultivo apenas: VERDICT nunca executa sozinho; decisao e do
  orquestrador; desacordo em ponto estrutural escala para voce.
- Fallbacks documentados em `reference/advisor-protocol.md`: resume-loop
  (subagente com `resume`, sem CU) e `devin acp` (persistencia alem do
  processo do orquestrador).
