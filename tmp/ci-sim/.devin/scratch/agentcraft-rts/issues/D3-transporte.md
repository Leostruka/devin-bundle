# D3 - transporte downstream

Status: resolved
Tipo: decision

## Decisão

WebSocket vs SSE para snapshot+upserts.

## Recomendação registrada

WebSocket (o mesmo canal já carrega intents/decisões; protocolo hello→snapshot→upserts é o das referências). SSE é fallback se WS complicar o MVP.

## Gate

gate: decisão assinada pelo usuário antes do ticket 01.

## Answer

Decidido 2026-10-17: WebSocket localhost (hello -> snapshot -> upserts); SSE e fallback.
