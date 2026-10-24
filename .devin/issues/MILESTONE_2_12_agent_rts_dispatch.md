# MILESTONE 2 / ISSUE 12: `agent-rts` dispatch lane - intents->spawn, worktree lanes, resume-argv

Status: planned · Source: github.com/stablyai/orca (MIT; `src/relay/protocol.ts`, `agent-hibernation-planner.ts`, hook-ingest PR#14615) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#8/F · Blocked-by: none · Blocks: none

## Contexto & Valor

- `agent-rts` hoje observa e retransmite; "never dispatches" e canon do GDD. Orca mostra o caminho de controle: worktree lanes por agente, hibernacao com `getAgentResumeArgv`, ingest de hooks com token + registro por session-id bounded.
- Valor: lane de dispatch OPT-IN (o usuario aperta o botao; o jogo nunca auto-executa), fleet.json com lanes de worktree reais, resume de subagentes via tabela provider->argv, ingest endurecido.

## Brain (Skill)

- `skills/agent-rts-commander` += secao "dispatch lane": como emitir intent `spawn`, onde o bridge aprovado consome, como lanes aparecem no HUD. Documentar guards herdados do PandaCode (silent->fail, 20min kill, <=20 rounds) como convenção do orquestrador.
- `skills/using-git-worktrees` += comandos de lane register/deregister (`.devin/rts/worktrees.json`); merge-back recusa dirty/conflito.

## Muscle (Extension)

- `extensions/agent-rts/server.py` += `POST /intent {"kind":"spawn"}` -> grava intent file (ja existe o padrao); novo `GET /lanes` lendo `worktrees.json`.
- `extensions/agent-rts/collectors.py` += fleet.json schema: `lane` (path do worktree), `resume_argv`, `hibernated_at`.
- `scripts/rts-intents.py` += `spawn` helper (escreve intent; nao executa).
- `scripts/rts-emit.py` += header `x-agent-hook-token` (lido de env `RTS_HOOK_TOKEN`, nunca hardcoded); registry session-id bounded (512, sweep em exit).
- Bridge de dispatch: `scripts/rts-dispatch.py` NAO auto-roda - executa 1 intent aprovado explicitamente pelo usuario (`--approve i<id>`), delegando a `run_subagent` pela skill; falta de approve = intent expira.

## Step-by-step

0. Schema fleet.json+worktrees.json + `GET /lanes`.
1. Intent spawn + `rts-dispatch.py --approve` manual; prova com 1 subagente real.
2. Token no ingest + registry bounded.
3. Resume-argv table (devin/claude/codex -> comando de resume conhecido).
4. Gate: `pytest` (intent->approve->fleet lane atualizada; sem approve expira; token rejeitado sem env); `selftest.py` da extensao verde; `audit.py` 0 errors.

## Non-goals

Sem auto-exec de intents (canon preservado); sem relay SSH remoto, sem PTY real por agente, sem GUI nova, sem hibernacao real de processo (resume = novo spawn com argv de retomada).
