# Analise: 1kQ_1_QL5Es -- Microsoft token-economizer plugin

## Conteudo

Review EN (~13 min) do plugin open-source da Microsoft "token
economizer" para Claude Code / Codex / GitHub Copilot. Reduz tokens por
mensagem aprendendo com sessoes anteriores do mesmo projeto.

## Tres mecanismos (claims do video, nao medidos aqui)

1. **Micro-skills** -- erros repetidos do agente viram "fatos" do
   projeto, injetados no session start. OFF por default (custo do modelo
   a cada ~3 sessoes + risco de prompt injection via output de comandos).
2. **Tool pruning** -- tools nao usadas em >=10 mensagens em >=2 sessoes
   sao desligadas por projeto; maior economia (34.3k -> 24.4k tokens/msg,
   ~29%, no demo). `toolprune` lista, `restore` devolve.
3. **Stuck detection** -- hook pos-tool checa se o agente esta preso em
   loop; modelo confirma antes de "cutucar"; nunca mata o agente.

Claims de benchmark (Microsoft): 277 bugs reais, 6 projetos, 5 setups --
Sonnet -23.6%, Opus 4.8 -30.9%, sem regressao de qualidade. Cold start:
custa mais ate ~6a tarefa; nada carrega entre projetos.

## Veredito vs bundle

| Mecanismo | Cobertura no bundle | Gap |
|---|---|---|
| Micro-skills | `memory-*` hooks: cue-anchored retrieval + session-end notes | Parcial (extracao de fatos e manual/nota, nao auto) |
| Tool pruning | `skill-picker.py` injeta ate 3 hints por prompt | Nao mapeia: runtime Devin controla a tool list; skills sao file-discovered |
| Stuck detection | Nada | **Implementado** |

## Implementado

`scripts/stuck-detect.py` -- subset deterministico do mecanismo 3, sem
model call (hooks sao stdlib-only, nunca pagos): se o mesmo comando exec
normalizado falha 3x consecutivas, emite `additionalContext` advisory
uma vez por assinatura. Estado em `.devin/memory/.stuck-detect.json`
(history<=12, warned<=16, escrita atomica), fail-open em todo erro.
Wired in-process em `post-exec.py` via `_hookrun` (sem spawn extra).
Registrado em `manifest.json` com `export_hash`.

Diferenca honesta vs original: o plugin usa um modelo para confirmar
"stuck"; aqui e contador deterministico -- mais simples, zero custo,
cobertura menor (so repeticoes literais, nao loops semanticos).

Nao implementado: micro-skills auto (extracao por modelo = custo;
memoria manual ja existe) e tool-pruning (nao aplicavel ao runtime).
