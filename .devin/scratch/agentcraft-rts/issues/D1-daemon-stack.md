# D1 - stack do daemon rtsd

Status: resolved
Tipo: decision

## Decisão

Linguagem/runtime do daemon de estado.

## Opções

- **Python asyncio** (`extensions/rtsd/`): zero toolchain nova; hooks e extensions já são Python; audit.py/pytest cobrem. Carga alvo: dezenas de agentes, KB/s de eventos.
- **Phoenix/Elixir**: OTP superior (GenServer/agente, supervisor/campanha, Channels = transporte pronto, LiveView p/ dashboard); exige toolchain Erlang/Elixir em todos os targets do bundle; UI game ainda precisa de JS/canvas.
- **Node/TypeScript**: stack das duas referências; adiciona package.json ao fluxo Python do bundle.

## Recomendação registrada

Python para o MVP como extension. Phoenix reabre se o overlay virar produto standalone multi-usuário (escopo Alliance Hall).

## Gate

gate: decisão assinada pelo usuário antes do ticket 01.

## Answer

Decidido 2026-10-17 (aprovacao do conjunto): Python asyncio como extension `extensions/rtsd/` no MVP. Phoenix/Elixir reabre apenas se o overlay virar produto standalone multi-usuario.
