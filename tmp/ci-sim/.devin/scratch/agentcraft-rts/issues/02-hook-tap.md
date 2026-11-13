# 02 - hook tap

Status: resolved
Blocked by: 01

## Objetivo

`scripts/rts-emit.py`: lê payload JSON do stdin, POSTa ao rtsd (ou append direto em events.jsonl se daemon offline), sempre fail-open com timeout ≤50ms. Registrar na cadeia `_hookrun` de PostToolUse/UserPromptSubmit/Stop em hooks.v1.json, preservando hooks existentes.

## Gate

gate: turn simulado com hook disparado; evento aparece em events.jsonl e no stream WS.
expect: linha JSONL com `tool`, `ts`, session id; CLI não bloqueia com daemon offline.
evidence: trecho do log + tempo de execução do hook.
