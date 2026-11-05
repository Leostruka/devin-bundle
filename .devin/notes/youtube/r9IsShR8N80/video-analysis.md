# Analise: r9IsShR8N80 -- Agentic Engineering (Pavan Belagatti)

Fonte: https://www.youtube.com/watch?v=r9IsShR8N80 (~20 min, EN).
Tutorial citado: github.com/pavanbelagatti/Agentic-Engineering-Tutorial.
Demo usa Port (SaaS) como context layer; link afiliado na descricao.

## Conteudo

Framework "agentic engineering": humano no topo define intent,
guardrails, success criteria e security checklist; o sistema agentico
embaixo executa coding, testing, review, deploy, ops e incident
response. Nada vai a producao sem human gate.

## Os seis pilares (claims do video)

1. **Context engineering** -- "context lake/layer": quem e dono do
   servico, quem chamar no Slack, dependencias. Sem contexto org,
   agente nao age.
2. **Agent & skill engineering** -- SKILL.md e guidelines que o agente
   segue.
3. **Harness engineering** -- o ecossistema ao redor do agente:
   contexto, guardrails, humanos.
4. **Graph & workflow engineering** -- workflows estruturados com
   dependencias, decision points e human approval gates (grafo tipo
   LangGraph).
5. **Agentic observability & evaluation** -- o que os agentes fazem,
   por que decidem, onde falham.
6. **Governance & security** -- permissoes, accountability,
   auditabilidade, safety, lifecycle de agents e skills.

Distincao-chave do video: AI engineering = construir o agente/modelo
(RAG, inference, prompts). Agentic engineering = delegar trabalho de
engenharia aos agentes (SDLC, CI/CD, review, incident response).

## Demo (incident response)

Payments API simulada. Deploy v2.4.1 reduz pool de conexoes DB ->
falhas. Alerta dispara 3 agentes em paralelo (metrics, logs,
deployments) -> correlation agent sintetiza root cause -> human gate
(approval no Port) -> rollback -> verify agent confirma healthy.
MTTR reportado: 1m55s. Dashboard Port com timeline, evidence e RCA
por incidente.

## Veredito vs bundle

| Pilar | Cobertura no bundle | Status |
|---|---|---|
| Context engineering | `context-folding`, `context-hygiene`, memory hooks, `CONTEXT.md`, manifest | Parcial: contexto repo-local; sem service catalog org-level |
| Skill engineering | 178 SKILL.md, `writing-skills`, `skill-discovery`, TIERS | Coberto -- e o core do bundle |
| Harness engineering | hooks.v1.json (11 entry points), AGENTS rules, gates, stop-guard | Coberto |
| Graph/workflow | `afk-loop` (DAG de issues), plans em waves, subagent profiles | Parcial: DAG declarativo, nao runtime graph; gates via confirmacao |
| Observability & eval | `audit.py`, held-out tests, `drift-report`, `sentinel`, refinements.log | Parcial: eval de repo/push; sem traces de decisao em runtime |
| Governance & security | `security-audit-cf`, deny hooks, regras 2/5/13/25, least privilege | Coberto p/ coding-agent |

Human gate do demo = regra existente (confirmacao p/ acoes destrutivas +
fluxo PR humano). Padrao fan-out specialists -> correlator -> verify =
mesma forma do pipeline reels (transcribe -> survey -> issues -> waves).

## Gaps / oportunidades

- Nada a adotar diretamente: e framework conceitual, nao mecanismo novo.
- O bundle cobre 2/3/4 por completo; 1/5/6 parcialmente por escopo
  (bundle e dev-tooling repo-local, nao plataforma de ops).
- Mapeamento pilar->skill pode virar secao no ARCHETYPE-MAP se houver
  demanda de narrativa publica (site/docs).
