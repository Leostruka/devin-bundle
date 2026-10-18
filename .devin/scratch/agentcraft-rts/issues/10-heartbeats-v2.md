# 10 - heartbeats v2

Status: resolved
Blocked by: 03

## Objetivo

Cláusula padrão nos delegation contracts + dispatch prompts: subagent escreve `.devin/rts/agents/<id>/status.json` `{phase, pct, note, ts}` por marco. rtsd projeta last_heartbeat/phase na UI. Cobre visibilidade mid-run dentro do possível para subagentes efêmeros.

## Gate

gate: subagent instrumentado emite ≥2 heartbeats durante execução real.
expect: UI mostra fase/nota atualizando sem refresh.
evidence: status.json + timestamps no event log.
