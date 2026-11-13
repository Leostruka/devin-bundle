# 05 - decision podium

Status: resolved
Blocked by: 02

## Objetivo

Hook de decisão (PermissionRequest / ponto de ask_user do orchestrator): escreve `.devin/rts/decisions/<id>.json` (pending, opções, timeout); UI lista e responde; hook faz poll na resposta até timeout e emite `decision`/contexto no stdout do hook protocol. Fila oldest-first, estilo `/answer` do blendi.

## Gate

gate: decisão fake pendente → respondida pela UI → hook retorna resposta correta; timeout → default deny-safe.
expect: JSON de resposta correto no stdout do hook; CLI destrava.
evidence: decisão + resposta registradas no ledger.
