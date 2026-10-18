# 03 - fleet registry

Status: resolved
Blocked by: 02

## Objetivo

`.devin/rts/fleet.json` single-writer (rtsd). Eventos `agent.spawned` (PostToolUse sobre run_subagent: agent_id, profile, task title), `agent.done/failed` (completion), heartbeat via `status.json` do lane do agente. Enriquecer com model/effort de bundle-models.json.

## Gate

gate: dispatch real de 1 subagent background; fleet.json mostra spawned→done; snapshot reflete estado.
expect: transições corretas sem intervenção do subagent; ausência de heartbeat degrada para "dispatched (no heartbeat)".
evidence: fleet.json + snapshot capturados.
