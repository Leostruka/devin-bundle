# AgentCraft RTS overlay - spec do esforço

Objetivo: camada de visualização e comando estilo RTS sobre o Devin CLI, consumindo o que o bundle já produz (hooks, subagent dispatches, scratch issues, ledgers, mailboxes, bundle-models). Análise e plano apenas nesta fase; implementação acontece nos tickets.

Docs da análise:
- `01-research.md`: referências verificadas (idosal RTS, blendi Minecraft) + inventário do bundle.
- `02-comparacao-gap.md`: feature matrix, RTS vs Minecraft, gap analysis.
- `03-arquitetura.md`: rtsd daemon, protocolo snapshot+upserts, convenção de heartbeat, decisão de stack.
- `04-roadmap.md`: fases MVP→v1 e ordem dos tickets.
- `map.md`: DAG de tickets.
- `issues/`: tickets `NN-slug.md` (convenção `.devin/agents/issue-tracker.md`).

Não-objetivos: redesenhar leo/project-orchestrator; multiplayer/relay remoto no MVP; engine de jogo.
