# AgentCraft RTS - Fase 3: Arquitetura proposta

Base: `01-research.md`, `02-comparacao-gap.md`. Padrão arquitetural copiado das duas referências: **daemon de estado + view desacoplada via stream** (Foreman↔mod; server↔browser).

## 1. Visão geral

```
 Devin CLI (parent)                RTS overlay
+-----------------+     hooks     +----------------------+
| orchestrator     | ------------> | rtsd (daemon local)  |
| (leo/proj-orch)  |  JSON stdin   |  registry + bus +     |
|  run_subagent --|--o (dispatch)  |  snapshot/upserts     |
|  ephemeral subs  |              +----------+-----------+
|  write status/   |  file state  |          | WS/SSE :PORT
|  heartbeats -----|------------> |          v
|  scratch/ledgers |  watches     |  web UI (canvas 2D,   |
+-----------------+               |  Three.js opt.)       |
        ^                         +----------+-----------+
        |   intents/decisions (arquivos)       |
        +--------------------------------------+
```

Princípio das duas referências mantido: **UI fecha, trabalho continua**; UI reconecta e recebe snapshot.

## 2. Componentes

### 2.1 rtsd - daemon de estado (o "Foreman" do bundle)

Responsabilidades:

1. **Ingestão de eventos**: hooks existentes ganham um tap extra (script `scripts/rts-emit.py` registrado via `_hookrun` ou entrada própria em hooks.v1.json) que POSTa o payload JSON do hook para `http://127.0.0.1:<port>/event` ou faz append direto em `.devin/rts/events.jsonl` se o daemon estiver fora (fail-open, timeout curto; mesma política dos hooks atuais).
2. **Fleet registry**: `.devin/rts/fleet.json` com `{agent_id, profile, model_effort, task, lane, spawned_at, status, last_heartbeat}`. Escrito pelo orchestrator no dispatch (uma linha de instrução nos contratos) e atualizado por heartbeats.
3. **Snapshot builder**: lê scratch issues/map, ledgers, mailboxes, fleet.json e projeta `snapshot` (agents, tasks, decisions, goal).
4. **Stream**: WebSocket (ou SSE) localhost-only; protocolo hello → snapshot → upserts, idêntico ao do Foreman (protocol v1 deles é referência de schema).
5. **Decision queue**: `PermissionRequest` hook e decisões de gates escrevem `.devin/rts/decisions/<id>.json` (pending); UI responde; hook faz poll no arquivo resposta até timeout e devolve `decision` no stdout do hook.
6. **Intent queue**: UI escreve `.devin/rts/intents/<id>.json` (`spawn`, `message`, `pause`, `answer`, `goal`). UserPromptSubmit hook ou o próprio orchestrator consome intents na próxima fronteira de decisão.
7. **Event log**: `.devin/rts/events.jsonl` append-only, replayável (fonte para rebuild do estado, igual JSONL do Foreman Store).

Fronteiras: rtsd **não** dispara subagentes nem executa código de projeto; ele observa, projeta e enfileira. Dispatch continua com leo/project-orchestrator via `run_subagent`.

### 2.2 Convenção de heartbeat (cobre o gap do subagent efêmero)

- Delegation contracts do project-orchestrator ganham cláusula: "a cada marco, escreva `.devin/rts/agents/<agent_id>/status.json` com `{phase, pct?, note, ts}`".
- Subagentes de skills existentes recebem a mesma instrução no prompt de dispatch (uma linha, zero redesenho).
- Se o subagent não escrever nada: fleet mostra `status: dispatched` + timestamp; UI degrada graciosamente (silhueta cinza, sem log interno).
- Completion: notification do `run_subagent` + PostToolUse hook marcam `done/failed`.

### 2.3 UI RTS (view)

- **Browser app**: mapa 2D top-down em canvas para MVP;Three.js isométrico como upgrade de skin. Hierarquia de leitura copiada do blendi: longe = cor/estado; perto = nome+task; zoom/click = transcript+ledger do agente.
- **Widgets mínimos**: Quest Board (lista issues do esforço ativo com Status/Blocked by), Decision Podium (fila de decisões pendentes com countdown de timeout), Fleet panel (agentes + model/effort do bundle-models), Goal ring (progresso do esforço).
- **Comandos**: spawn (escolhe profile+modelo, escreve intent), message (@agent → mailbox), answer (resolve decision), goal (novo esforço → spec.md via intake).
- **Assets/skins**: placeholder shapes no MVP; race skins ficam para v1+.

### 2.4 Persistência

| Dado | Onde | Dono |
|---|---|---|
| Event log | `.devin/rts/events.jsonl` | rtsd |
| Fleet registry | `.devin/rts/fleet.json` | rtsd + orchestrator |
| Decisões pendentes | `.devin/rts/decisions/` | hooks + UI |
| Intents | `.devin/rts/intents/` | UI + orchestrator |
| Issues/tasks | `.devin/scratch/<effort>/` (existente) | issue-tracker |
| Evidência/gates | `.devin/ledgers/` (existente) | gates skill |
| Mailboxes A2A | `.devin/mailboxes/` (existente) | primeagent-reference |

Sem DB no MVP: arquivos já são a fonte de verdade do bundle; rtsd mantém só projeção em memória + log. SQLite opcional se o log crescer (v1+).

## 3. Recomendação de stack

| Camada | Recomendado | Alternativas avaliadas |
|---|---|---|
| UI | **Browser: canvas 2D (MVP) → Three.js (skin 3D)** | Godot headless **rejeitado**: headless não renderiza; export de cliente Godot adiciona toolchain de engine para uma view. Electron/Tauri **rejeitado**: duplica o browser; remoto exige web de qualquer forma. TUI (Textual) **mantido como view secundária** sobre o mesmo protocolo (igual `npm run tui` do blendi). |
| Daemon (rtsd) | **Python (asyncio + websockets/aiohttp), distribuído como `extensions/rtsd/`** | Ver seção 3.1 (Phoenix, Node). |
| Transporte | **WebSocket localhost** (hello→snapshot→upserts) | SSE aceitável p/ MVP (só downstream; intents sobem por POST). Long-poll rejeitado. |
| Persistência | Arquivos `.devin/rts/` + JSONL | SQLite quando queries de histórico pesarem. |

### 3.1 Avaliação do candidato Phoenix (sugestão do usuário)

**Pontos fortes reais**: OTP é a melhor modelagem do domínio na planilha: GenServer por agente, supervisor por campanha, PubSub interno, Phoenix Channels já são o transporte snapshot+upserts, LiveView cobriria dashboard 2D sem JS, e a tolerância a crash supera qualquer opção.

**Custos para este bundle**: (a) adiciona toolchain Erlang/Elixir inteira a um bundle cujos hooks e extensions são Python e que instala em Windows/Linux/macOS/WSL; (b) a parte game-feel da UI (sprites, câmera, animações, fog) precisa de canvas/WebGL de qualquer forma, então LiveView não elimina o JS; (c) a carga real é pequena: dezenas de agentes, eventos em KB/s, arquivos locais. A vantagem de concorrência do OTP é real porém subutilizada nessa escala.

**Veredito**: para o RTS overlay como *extension do bundle*, Python asyncio entrega o mesmo desenho com zero toolchain nova. **Phoenix vira a recomendação se o RTS virar produto standalone** com server próprio, múltiplos usuários e relay remoto (escopo do Alliance Hall). Registrado como decision ticket no roadmap (não fechado).

### 3.2 Node/TypeScript (a escolha das duas referências)

Também viável (as duas fontes provam), mas rejeitado por consistência: hooks/scripts/extensions do bundle são Python; manter rtsd em `extensions/` segue o padrão wrapper.py existente e não adiciona `package.json` ao fluxo de audit/pytest.

## 4. Integração com orchestrator existente

| Ponto | Como consome |
|---|---|
| `run_subagent` | PostToolUse hook captura dispatch (`agent_id`, profile) → evento `agent.spawned`; completion notification → `agent.done`. Sem mudança na tool. |
| Delegation contracts | Uma cláusula nova: heartbeat path + lane. Contrato continua soberano. |
| scratch issues | Quest Board renderiza `Status:`/`Blocked by:` direto; intents de repriorização viram edição de `Status:` (via orchestrator, nunca pela UI direto). |
| ledgers | UI linka evidência por task; gates falhos viram marcador vermelho no herói. |
| bundle-models.json | Spawn dialog oferece effort→modelo; nameplate mostra swe-2-medium/max. |
| mailboxes | Message intent vira `msg-*.json` no inbox do agente (padrão já documentado). |
| PermissionRequest | Hook consulta daemon: decisão pendente vira card no podium; resposta do UI preenche `decision`. |

Nada redesenha leo/project-orchestrator: eles ganham um *reporter* (hooks + convenção de status) e um *inbox de comandos* (intents).

## 5. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Subagent nunca escreve status (opaco) | UI mostra "dispatched, sem heartbeat" explicitamente; não simular progresso |
| Hook timeout bloqueia CLI | tap fail-open ≤50ms; decisões têm timeout e default deny-safe |
| Dois writers no fleet.json | single-writer: só rtsd escreve; orchestrator publica via endpoint/evento |
| Escopo creep para multiplayer | Alliance Hall-like fica fora do v1; protocolo de eventos já é relay-friendly |

## Checkpoint

Próximo: Fase 4 (roadmap MVP→v1 + tickets). Stop final após Fase 4.
