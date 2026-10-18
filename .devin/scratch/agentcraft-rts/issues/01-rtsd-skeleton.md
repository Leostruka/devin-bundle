# 01 - rtsd skeleton

Status: resolved
Blocked by: -

## Objetivo

Daemon local `extensions/rtsd/` (Python asyncio) com: endpoint `/event` (POST JSON), append em `.devin/rts/events.jsonl`, snapshot builder lendo scratch/ledgers/mailboxes/fleet, WS `ws://127.0.0.1:8797` servindo hello→snapshot→upserts.

## Gate

gate: `python extensions/rtsd/doctor.py` (ou equivalente) sobe, aceita POST /event, e um cliente WS recebe snapshot vazio + 1 upsert após POST.
expect: exit 0; snapshot JSON contém chaves agents/tasks/decisions.
evidence: saída do cliente de teste registrada no ledger `.devin/ledgers/agentcraft-rts.md`.
