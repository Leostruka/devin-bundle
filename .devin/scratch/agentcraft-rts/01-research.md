# AgentCraft RTS - Fase 1: Pesquisa verificada

Data: 2026-10-17. Todas as afirmações verificadas via webfetch/web_search nas fontes citadas ou por leitura direta dos arquivos do bundle.

## Fonte A: idosal/agentcraft (getagentcraft.com), referência principal (RTS)

Pacote `npx @idosal/agentcraft` (npm v0.5.1, atualizado 2026-08-21; repo github.com/idosal/agentcraft). Requer Node 18+.

### Arquitetura observável

- **Servidor local na porta 2468** + UI de jogo 3D no browser (`app.agentcraft.gg` para a versão hospedada). Servidor roda foreground ou daemon (`start -d`/`stop`/`status`/`logs`/`open`/`doctor`).
- **Instrumentação via hooks repo-local do CLI do agente**: instala e preserva entradas em `.claude/settings.local.json`, `.cursor/hooks.json`, `.codex/hooks.json`, `.opencode/plugins/agentcraft.js`. Hooks reportam eventos de sessão ao servidor; agentes externos iniciados em terminal separado são auto-detectados e aparecem no mapa.
- Multi-repo: lançar de pasta-pai descobre repositórios git aninhados (até 3 níveis); Spawn Options escolhe repo/worktree por herói. Escopo por repo git.
- CLI: `install` (só hooks, `--force`), `uninstall` (`--dry-run`; managed set: `.campaign/`, `.agentcraft/`, entradas de hook; preserva hooks do usuário), `restore` (manifest de backup com timestamp), `logout`, `doctor` (CLIs, auth, hooks, porta, containers, sandbox).

### UX RTS (features reais nos docs)

- Heróis no mapa 3D + minimapa; estados idle/working/awaiting/error; glow amarelo indica que precisa de input; activity bubbles.
- Town Hall command grid: **Q** Spawn Options (provider/repo/worktree/template/isolamento), **W** quick-spawn, **E** sessões ativas, **F** terminal PTY integrado multi-tab. **V** fog of war. Side panel com file explorer e integração com IDE.
- Race skins (Orc/Human/Elf/Undead: prédios, heróis, terreno, portraits), música ambiente, achievements, Skill Scrolls (instalam skills reais do skills.sh), tutorial interativo e "War Advisor".
- Missions persistem entre restarts com resumos gerados por IA.

### Campaigns (0.5.0), pipeline análogo ao nosso orchestrator

Spec → planning agent decompõe → review do plano (**Refine** conversacional / **Review** edita tasks / **Approve** / **Reject**) → tasks despachadas cada uma em git worktree própria → merge sequencial na Campaign branch → verificação final com evidência (screenshots, recordings, relatório em `~/.agentcraft/plan-memory/<planId>/`; task evidence em `~/.agentcraft/task-memory/`) → **Approve & Merge** local / **Create PR** / **Merge PR**. Controles: pause, resume, cancel, retry/edit/cancel/review por task, +task, chat com o orchestrator, 1 auto-repair task por verificação falha. Loop delegation: scheduled loops podem submeter spec de Campaign (deduplicada). Estado sobrevive restart do servidor.

### Remoto e multiplayer

- Remote Access: túneis seguros com TTL (15min/1h/4h/8h), token por sessão, proxy direto sem persistência; PWA instalável mobile (tabs Agents/Chat/Quests); push notifications com quick-reply (aprovar plano, permissão, responder mensagem).
- Channels: DM por Telegram/Discord para prompts, aprovação de planos e permissões.
- Alliance Hall: cada dev roda seu servidor; Cloudflare Durable Object relaya eventos; heróis remotos semi-transparentes (state, missão, file activity, transcript read-only); Notice Board (**B**); file-intent soft warnings; conversation sharing ligado por default (desligável, sem recall do já enviado).
- Isolated Agent Containers: Docker ou Apple Containers, isolamento de rede completo, dev servers na mesma porta com sessões de browser separadas.

Fontes: getagentcraft.com (home), /docs, /docs/getting-started, /docs/features/campaigns, /docs/features/remote-access, /docs/features/hall, /docs/cli; registry.npmjs.org/@idosal/agentcraft.

## Fonte B: blendi-remade/agentcraft (Minecraft mod), referência secundária

MIT, 819 stars, 103 commits. Fabric mod para Minecraft 26.3 (Java 25) + **Foreman** (Node 22 + TypeScript) + `tools/` launcher + `sandbox/`. Claude Agent SDK; também backend Codex (app-server JSON-RPC stdio). Requer cópia do Minecraft.

### Arquitetura (foreman/README.md + docs/protocol.md)

- **Mod é só view/controle.** O Foreman detém todo o estado: `TaskGraph` (deps, todo/doing/review/done/blocked), `MessageBus` (agent↔agent, agent↔user), `Memory` (markdown compartilhado + por agente), `DecisionQueue` (question|permission|merge), `RepoManager` (worktrees, diffs, merges guarded), `Notifier` (desktop + bell), `Store` (JSON atômico + JSONL sob AGENTCRAFT_HOME).
- **Transporte: WebSocket localhost-only `ws://127.0.0.1:7878`, protocol v1.** Cliente manda `hello`, recebe **snapshot**, depois **upserts**. O mesmo protocolo serve o mod e `npm run tui` (cliente terminal).
- Sessões Claude resumem por id; kill hard perde no máximo ~100ms de estado. Jogo fechado, trabalho continua; reabriu, snapshot catch-up. Foreman offline→online, time retoma.
- Backend claude: um `query()` do Agent SDK por turn; tools de time via MCP server in-process (`send_message`, `ask_user` bloqueante, `write/read_memory`, `update_task`, `report_status`, `list_tasks`; lead-only `create_task`, `request_merge`); todo tool call passa por `canUseTool` + policy. Mensagens não-lidas piggyback em tool results; mensagem para agente ocupado vira follow-up turn.
- Backend codex: `codex app-server` por turn, thread durável, `approvalPolicy: untrusted`, sandbox por worktree com grants cirúrgicos (objects/, refs próprias, git dir do worktree; nunca `.git` inteiro).
- **Segurança git**: cada task em worktree `agentcraft/<agent>/<task>`; merge só com aprovação humana (recusado se checkout sujo); conflito volta ao worker; **push impossível** (enforced dentro do git via config, não por filtro de comando); autoria `AgentCraft <Name>`; CI detectado roda após cada task (falha → worker 1x → review).
- UX in-game: console (`` ` ``) com @agent + Tab, Task Wall kanban, podium de decisão (clay `!` + bell + J), monitors com live log (tool calls, diffs red/green), diff review real (file list, line numbers, collapsed context), Goal Atrium (progress ring, contagens, decisões pendentes), lamps/beacon de status à distância, nameplates de perto, monitor de perto. Comandos: `/answer /diff /status /pause /resume /stop /spawn /repo /task cancel|retry|prioritize|reassign`.
- Custos medidos: ~$6 para 3 goals pequenos em settings baratos. Sim backend (time scriptado, git real, sem API) para demo/QA; DevBridge = API localhost no mod para screenshots scriptados.
- Status: Windows+macOS, singleplayer, dev-client only, 482 testes no foreman.

Fontes: github.com/blendi-remade/agentcraft README.md e foreman/README.md (lidos integralmente via webfetch).

## Inventário do bundle (verificado por leitura direta)

| Capacidade | Onde | Notas |
|---|---|---|
| Lifecycle hooks do Devin CLI | `hooks.v1.json` + `scripts/` | PreToolUse/PostToolUse (matcher regex por tool), UserPromptSubmit, SessionStart, Stop, SessionEnd, PostCompaction, **PermissionRequest**. Protocolo: JSON no stdin, resposta hook-protocol no stdout (`decision: block`, `additionalContext`, `updatedInput`, exit 2). `_hookrun.py` consolida N scripts por spawn (fail-open). Mesmo modelo de instrumentação que idosal usa. |
| Dispatch de subagentes | `run_subagent` (tool nativa) | Profiles (leo, project-orchestrator, implementer, researcher, qa-ci, debugger, domain, architect, reviewer...). `is_background` retorna `agent_id`; `read_subagent` faz poll; `resume` para follow-up. Efêmero: sem handle persistente, sem eventos mid-run; completion notification só no fim. |
| Issue tracker local | `.devin/agents/issue-tracker.md` | `.devin/scratch/<effort>/spec.md`, `issues/<NN>-<slug>.md`, `map.md`, `Status:`, `Blocked by:`, `## Comments`/`## Answer`. |
| Triage labels | `.devin/agents/triage-labels.md` | needs-triage/needs-info/ready-for-agent/ready-for-human/wontfix. |
| Gates ledgers | `gates` skill + `.devin/ledgers/` | CHECK/EXPECT/EVIDENCE por gate; ABANDON explícito. |
| Model routing | `data/bundle-models.json` | effort medium/high/max → swe-2-*; env overrides `BUNDLE_*`. |
| A2A emulation | `primeagent-reference` skill | `.devin/mailboxes/` filesystem broker; limitações documentadas (sem real-time, sem bidirectional mid-run). |
| Orchestrators | `leo`, `project-orchestrator` skills | leo: router + VFs + qa-ci independente. project-orchestrator: delegation contracts em `.devin/handoffs/`, `workers/<role>/` homes, worktree lanes, Progress Ledger, gates G0 a G5, subconscious advisor via computer-use PTY, research protocol antes de decisão de stack. |
| Extensions headless | `extensions/` | Wrappers python/CLI (blender, godot, spline, system-control, computer-use, craft-bridge, scrape-tools). Padrão: wrapper.py + ops_map. |
| UI gráfica | (não existe) | Orquestração 100% via prompts/skills/CLI. |

### Gap estrutural principal (confirmado)

idosal e blendi assumem **sessões de agente persistentes e observáveis** (CLI hooks emitindo eventos; SDK `query()` por turn com tool-call stream). O bundle tem hooks no **parent** Devin CLI, que vê os tool calls do parent, incluindo `run_subagent`, mas o interior de um subagent é opaco até o retorno: só ledgers/mailboxes/issues escritos por ele são observáveis. Event streaming para RTS UI precisa então de: (a) taps nos hooks do parent, (b) convenção de escrita de status pelos subagents em arquivos, ou (c) ambos.

## Checkpoint

Fase 1 concluída. Aguardando aprovação para Fase 2 (matriz comparativa + gap analysis).
