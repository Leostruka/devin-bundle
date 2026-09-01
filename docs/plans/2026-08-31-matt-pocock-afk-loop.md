# Plano: AFK loop (Ralph) para execução de issues locais

**Bloqueado por:** [PRD to issues](2026-08-31-matt-pocock-prd-to-issues.md) (precisa de issues locais como entrada).

**Objetivo:** criar um skill/prompt para rodar um agente AFK que consome issues em markdown locais, usa TDD e escolhe a próxima tarefa sozinho.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamps: `00:53:15.839–01:02:20.240`
- Conceitos: AFK vs human-in-the-loop, `once.sh`, `afk.sh`, Ralph loop, DAG de issues.

## Hipóteses a testar

1. O bundle não tem um skill para "noite" (AFK loop).
2. `executing-plans` e `dispatching-parallel-agents` focam em subagentes explícitos, não em loop autônomo sobre arquivos de issue.
3. Pocock separa claramente human-in-the-loop (planning/QA) de AFK (implementação).

## Falha a observar

- Não há skill que leia arquivos `.devin/scratch/<feature>/issues/*.md` e execute em loop.
- Não há prompt para "trabalhe apenas nas issues AFK".

## FASE 0 — obrigatória

- [ ] 0.1 — Ler `skills/executing-plans/SKILL.md` e `skills/dispatching-parallel-agents/SKILL.md`.
- [ ] 0.2 — Verificar se `using-git-worktrees` pode isolar o loop.
- [ ] 0.3 — Pesquisar Sand Castle de Pocock (link no vídeo ou `web_search`).

## FASE 1 — Observar

Comando: `ls .devin/scratch/` ou `grep -r "AFK\|Ralph" skills/`.
Resultado: nenhuma skill com esse foco.

## FASE 2 — Criticar

- Regra violada: Rule 4 (skill discovery) / Rule 10 (execute without planning).
- Comportamento: agente implementa somente quando coordenado manualmente.
- Intenção: não criar loops descontrolados.
- Falha: perde a produtividade de "turno da noite".

## FASE 3 — Gerar alternativas

1. Criar `skills/afk-loop/SKILL.md` com prompt de Ralph.
2. Adicionar seção "AFK mode" em `executing-plans`.
3. Criar script `.ps1`/`.sh` no repo para orquestrar o loop.

## FASE 4 — Revisar

Criar skill `afk-loop` separada para não poluir `executing-plans`.

## FASE 5 — Validar

- Teste: criar issues de teste e invocar `/afk-loop` em worktree.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Usuário dorme enquanto agente trabalha. Ajuda? Sim.
2. Issues vêm de PRD gerado no dia. Ajuda? Sim.
3. Paralelização com múltiplos worktrees. Ajuda? Sim.

## FASE 7 — Ecological check

- Loop AFK não deve rodar sem confirmação de testes/segurança.
- Não commitar automaticamente na main.

## FASE 8 — Simular

- Criar worktree, rodar `/afk-loop`, verificar se ele para em issue vazia.

## FASE 9 — Classificar

Esperada: MELHOROU se o loop processar issues sem intervenção humana.

## Arquivos esperados

- `skills/afk-loop/SKILL.md`
- `scripts/afk-loop.ps1` (opcional)
- `ledgers/afk-loop-pocock.md`
