# AgentCraft RTS - Fase 4: Roadmap MVP → v1

Tickets rastreáveis em `issues/`; DAG em `map.md`. Cada ticket declara seu gate. Nenhum código nesta fase.

## MVP - frota visível e comandável (tickets 01-06)

| # | Ticket | Entrega | Depende |
|---|---|---|---|
| 01 | rtsd skeleton | `extensions/rtsd/`: append `events.jsonl`, snapshot builder, WS :8797 | - |
| 02 | hook tap | `scripts/rts-emit.py` fail-open + registro em hooks.v1.json | 01 |
| 03 | fleet registry | `fleet.json` + eventos agent.spawned/done via PostToolUse em run_subagent | 02 |
| 04 | web UI MVP | canvas 2D: mapa, fleet panel, quest board read-only, reconnect snapshot | 01 |
| 05 | decision podium | PermissionRequest/ask_user → `decisions/` → resposta UI → stdout do hook | 02 |
| 06 | intent queue | `intents/` spawn/message/goal consumidos pelo orchestrator | 03 |

MVP demo: `leo` despacha 2-3 subagentes num esforço scratch; UI mostra heróis, issues e uma decisão respondida pelo podium.

## v1 - evidência e alcance (tickets 07-10)

| # | Ticket | Entrega | Depende |
|---|---|---|---|
| 07 | TUI view | cliente terminal no mesmo protocolo (referência: `npm run tui` do blendi) | 01 |
| 08 | evidence surfacing | ledgers ligados por task; gate FAIL vira marcador no herói | 04 |
| 09 | remote/PWA | túnel TTL + push quick-reply (exige decisão de exposição do daemon) | 05 |
| 10 | heartbeats v2 | status.json rico por agente (fase/pct/nota) nos delegation contracts | 03 |

## Decision tickets (não-bloqueantes para MVP)

| # | Decisão | Opções | Recomendação atual |
|---|---|---|---|
| D1 | stack do rtsd | Python extension vs Phoenix standalone | Python p/ MVP; Phoenix se virar produto com relay |
| D2 | renderer | canvas 2D → Three.js depois vs Three.js já | canvas 2D (custo); Three.js quando houver skin |
| D3 | transporte downstream | WS vs SSE | WS (bidirecional já cobre intents); SSE se simplificar MVP |

## Pontos de reuso para leo / project-orchestrator

- **leo**: ganha vista de frota em tempo real sem mudar routing; intents chegam como UserPromptSubmit equivalente. Reuso: VF/evidence por ticket alimentam o podium.
- **project-orchestrator**: delegation contracts ganham 1 cláusula (heartbeat path); Progress Ledger já é o feed de gates do UI; worktree lanes viram "território" do herói no mapa. Reuso: `templates/delegation-contract.md` + Progress Ledger.
- **primeagent-reference**: mailboxes continuam o canal de mensagens; UI só escreve/lê arquivos de mailbox.
- **issue-tracker + triage-labels**: Quest Board consome `Status:`/`Blocked by:` sem formato novo.
- **gates**: decision podium é a projeção UI de gates que pedem humano.

## Sequência de execução

01 → 02 → 03 → {04 ∥ 05} → 06 → demo MVP → (v1: 07 ∥ 08 → 09, 10).

## Parada final

Fase 4 concluída. Aguardando aprovação final do conjunto 01-04 + issues.
