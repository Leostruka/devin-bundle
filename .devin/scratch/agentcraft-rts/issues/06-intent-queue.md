# 06 - intent queue

Status: resolved
Blocked by: 03

## Objetivo

UI escreve `.devin/rts/intents/<id>.json` (`spawn {profile,effort,task}`, `message {@agent,text}` → mailbox, `goal {text}` → spec draft via intake). Orchestrator consome intents na próxima fronteira (UserPromptSubmit hook avisa "N intents pendentes" via additionalContext). Nenhuma intent executa dispatch sozinha: leo decide.

## Gate

gate: intent `spawn` escrita pela UI aparece ao orchestrator; `message` cria arquivo em `.devin/mailboxes/<agent>/inbox/`.
expect: additionalContext lista intent pendente; mailbox file existe e é lido pelo subagent.
evidence: arquivos + saída do hook.
