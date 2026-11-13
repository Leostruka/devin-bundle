# 04 - web UI MVP

Status: resolved
Blocked by: 01

## Objetivo

Página estática servida pelo rtsd: canvas 2D top-down com sprites placeholder por agente (cor=status), fleet panel (profile/model/task), quest board read-only renderizando issues do esforço ativo (Status/Blocked by), reconnect com snapshot. Sem framework pesado.

## Gate

gate: abrir UI, conectar WS, ver snapshot; matar e religar rtsd mantém estado via events.jsonl replay.
expect: screenshot/inspeção manual + cliente WS log; UI mostra frota e issues reais do scratch.
evidence: captura de tela anexada ao ledger + log do cliente.
