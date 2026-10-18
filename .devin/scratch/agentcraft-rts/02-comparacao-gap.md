# AgentCraft RTS - Fase 2: Matriz comparativa + gap analysis

Base: `01-research.md` (fontes citadas lá). Usuário sugeriu Phoenix (Elixir/OTP) como candidato de stack pela proficiência em concorrência/async; avaliação formal fica na Fase 3.

## 1. Feature matrix lado a lado

| Dimensão | idosal/agentcraft (RTS web) | blendi-remade/agentcraft (Minecraft) |
|---|---|---|
| **Runtime do orquestrador** | Servidor local Node (porta 2468), daemon opcional | Foreman Node 22 + TypeScript; mod é só view |
| **Fonte de eventos** | Hooks repo-local do CLI do agente (`.claude/settings.local.json`, `.cursor/hooks.json`, `.codex/hooks.json`, `.opencode/plugins/agentcraft.js`); sessões externas auto-detectadas | Backend interno: Claude Agent SDK `query()` por turn ou `codex app-server` JSON-RPC; MCP tools in-process para o time |
| **Lifecycle de agentes (heróis)** | Spawn via Town Hall (Q/W), kill/dismiss, estados idle/working/awaiting/error; sessões CLI externas aparecem no mapa | `/spawn`, `/pause`, `/resume`, `/stop`; estados + particles/nameplates; workers "off shift" |
| **Task board** | Quest Board (tab Campaign); cards com progresso, verification attempts, PR/CI state | Task Wall kanban físico no HQ; task graph com deps, todo/doing/review/done/blocked |
| **Fluxo de aprovação/decisão** | Push quick-reply, channels Telegram/Discord, UI; Campaign: Refine/Review/Approve/Reject; Approve&Merge/Create PR/Merge PR | Podium + clay `!` + bell + tecla J; `ask_user` bloqueante; decision types question/permission/merge; merge só com clique humano |
| **Isolamento** | Docker ou Apple Containers, rede isolada, mesma porta por agente; worktree por herói | Git worktree por task `agentcraft/<agent>/<task>`; sandbox Codex com grants cirúrgicos; push impossível via git config |
| **Controle remoto** | Túneis com TTL, PWA mobile, push notifications, Telegram/Discord | Nenhum (localhost only, singleplayer) |
| **Multiplayer** | Alliance Hall: relay via Cloudflare Durable Object, heróis remotos semi-transparentes, Notice Board, file-intent warnings | Nenhum |
| **Persistência** | `~/.agentcraft/plan-memory/`, `task-memory/`; missions com resumos IA; Campaign sobrevive restart | Store: JSON atômico + JSONL sob AGENTCRAFT_HOME; sessões Claude resumem por id; memória markdown compartilhada |
| **Verificação/evidência** | Baseline antes de dispatch; screenshots, recordings, relatório; 1 auto-repair por falha | CI detectado por task; lead review de diff; 482 testes no foreman; sim backend p/ QA |
| **Superfície de comando** | UI RTS + CLI (`start/stop/status/logs/open/install/uninstall/restore/logout/doctor`) | Console in-game (`@agent`, `/answer`, `/diff`, `/status`, `/task ...`), right-click agent card, TUI `npm run tui` |
| **Licença/deps** | npm package; Node 18+; CLIs dos providers | MIT; Java 25, Node 22+, Minecraft Java Edition, Gradle |
| **Maturidade** | v0.5.1 publicada, docs extensos, features remotas | "young, used by one person on one machine", dev-client only |

## 2. RTS vs Minecraft: comparação explícita e escolha

| Critério | RTS web (idosal) | Minecraft (blendi) |
|---|---|---|
| Distribuição | `npx` + browser; zero install de jogo | Requer Minecraft licenciado + Java 25 + Gradle build |
| Densidade de comando | Grid de comandos, minimapa, multi-select lógico, filas: modelo feito para 200 unidades | Walk-around 3D: imersivo, porém comandos por proximidade física do avatar |
| Remote/mobile | PWA + túneis + push: controlar do telefone é feature central | Singleplayer local; fechar o jogo não pausa, mas não há acesso remoto |
| Multi-dev | Alliance Hall nativo | Não existe |
| Leitura à distância | Rings, dependency lines, fog of war, status widget | Lamps/beacon/nameplates: bom, mas preso à engine do jogo |
| Fit com o bundle | Browser UI = mais uma extension/web app; consome arquivos .devin | Engine pesada, escopo de jogo inteiro para uma camada de view |

**Justificativa RTS (confirma escolha do usuário):** a camada que interessa ao bundle é *comando e observação*, não imersão. O modelo RTS (zoom out = frota inteira, zoom in = transcript) resolve o problema real do bundle: vários subagentes efêmeros sem visibilidade. Browser + WS casa com a topologia já provada pelas duas referências (servidor de estado + cliente view). Minecraft adiciona dependência de engine/jogo sem ganho de controle; sua contribuição para nós é o *design de estado* do Foreman (snapshot + upserts, decision queue, task graph), que é portável sem o jogo.

## 3. Gap analysis: bundle hoje vs UX RTS

### Já tem (mapeamento direto)

| Conceito RTS | Equivalente bundle | Pronto para UI? |
|---|---|---|
| Task wall / Quest Board | `.devin/scratch/<effort>/issues/` + `map.md` + `Status:` + `Blocked by:` | Sim, arquivo = fonte de verdade; falta watcher |
| Heroes/unidades | `run_subagent` dispatches + `agent_id` | Parcial: existe id, mas sem estado observável mid-run |
| Campanha | `project-orchestrator` phase gates G0-G5 + delegation contracts em `.devin/handoffs/` | Sim como processo; falta projeção em estado |
| Evidência/plan-memory | `.devin/ledgers/<task>.md` (CHECK/EXPECT/EVIDENCE) | Sim |
| Modelo/classe da unidade | `data/bundle-models.json` (effort→modelo) + profile do subagent | Sim (metadados estáticos) |
| Mailbox/mensagens | `.devin/mailboxes/` (primeagent-reference) | Parcial: sequencial, pós-execução |
| Permissões/decisões | `PermissionRequest` hook + `ask_user_question` | Parcial: existe o evento, falta roteá-lo à UI |
| Event tap | hooks.v1.json: PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/Stop/SessionEnd | Sim como attachment point |

### Falta (o que construir)

| Lacuna | Por que importa | Caminho provável |
|---|---|---|
| **Event bus local** | Hooks hoje são fire-and-forget em scripts isolados; nada agrega eventos | Daemon/extension que recebe POST/append dos hooks e serve stream |
| **Estado observável da frota** | `run_subagent` retorna `agent_id` mas não publica lifecycle | Registry file `.devin/rts/fleet.json` escrito pelo orchestrator + hooks |
| **Visibilidade mid-run do subagent** | Interior opaco até retorno | Convenção: subagentes escrevem `status.json`/heartbeat no seu lane; UI lê arquivo (igual mailboxes) |
| **Canal de decisão remoto** | `ask_user_question`/PermissionRequest bloqueiam no terminal | Hook escreve decisão pendente em arquivo; UI responde; hook faz poll com timeout e retorna `decision` |
| **Snapshot + upserts** | UI precisa de estado inicial + deltas (protocolo do Foreman) | Aggregator lê scratch/ledgers/mailboxes/fleet e projeta snapshot; WS/SSE p/ upserts |
| **Comandos remotos** | Hoje só CLI local interativa | Fila de intents em arquivo consumida por hook/orchestrator (ex.: `intent: pause @agent`) ou API local |
| **Isolamento de agente** | Subagentes compartilham workspace | Fora do MVP; worktree lanes já existem no project-orchestrator |
| **Multiplayer/remoto** | Sem equivalente | v1+; túnel + relay ficam fora do MVP |

### Leitura chave

O bundle já tem **a camada de estado** (arquivos) e **a camada de comando** (hooks + orchestrator skills). O que falta é a **camada de transporte/projeção** entre arquivos e UI, e a **convenção de heartbeat** para subagentes efêmeros. Nenhuma das duas exige redesenhar leo/project-orchestrator: a camada RTS consome o que eles já escrevem.

## Checkpoint

Fase 2 concluída. Próximo: Fase 3 (arquitetura + stack, incl. avaliação de Phoenix).
