# 09 - remote/PWA

Status: resolved
Blocked by: 05

## Answer

- Exposicao: **LAN bind + token + TTL**: listener remoto em 0.0.0.0:port+1 com token de sessao, rebind/deny-safe apos TTL. Sem deps novas.
- Quick-reply: **polling na PWA**: decisoes respondidas pelo podium via HTTP; sem Web Push/VAPID.

## Objetivo

Túnel com TTL (presets 15min-8h), token por sessão, PWA instalável com tabs Agents/Chat/Quests, push quick-reply para decisões. Requer decisão de segurança: expor daemon além de localhost. Referência: Remote Access do idosal.

## Gate

gate: túnel abre, expira no TTL, decisão respondida do telefone.
expect: token único por sessão; deny-safe em expiry.
evidence: teste manual registrado + log de auth.
