# RTSD — AAA Game Architecture, RTS Design Theory & Devin CLI Gamification Plan

## 1. O que o RTSD faz exatamente pela orquestracao de agentes

O `rtsd` transforma o Devin CLI de um console linear em um **Command Center RTS**. Cada elemento do jogo e uma superficie real e operacional do orquestrador, nao uma decoracao:

| Elemento RTS | O que representa no Devin CLI | Como ajuda na orquestracao de agentes |
|---|---|---|
| **Hero (`Far Seer`, `Knight`, `Paladin`...)** | Um agente/subagente real (`product-manager`, `tech-lead`, `implementer`, `reviewer`, `debugger`, `researcher`...) executando uma tarefa | Veja quem esta trabalhando, em qual modulo, com qual modelo/tokens, e despache ordens sem digitar comandos longos. |
| **Spawn Hero (Tavern/Barracks)** | Iniciar um `subagent` com um profile especifico | Clique em um predio para contratar o agente certo para a fase atual (plano, codigo, revisao, auditoria). |
| **Worker / Minion** | Hooks, loops agendados, MCP tools, formatters, tarefas de baixo nivel | Sao as engrenagens que mantem o fluxo de trabalho girando; voce ve a carga e o estado de cada uma. |
| **Quests / Side Quests / Main Quest** | Issues do GitHub, milestones e DAGs de tarefas | A arvore de quests mostra dependencias (`blocked_by`), gates de verificacao e progresso em tempo real. |
| **Lumber / Context %** | Uso da janela de contexto do modelo | Monitora pressao de contexto para evitar perda de instrucoes e compactacao tardia. |
| **Gold / Tokens** | Orcamento de tokens da sessao | Mede o custo de cada ordem, laco ou skill invocada. |
| **Favor (AoM Retold)** | Credito acumulado de verificacoes aprovadas, skills invocadas e quests concluidas | Premia verificacao correta e permite lancar "God Powers" de orquestracao. |
| **God Powers (`Vision`, `Restoration`, `Flaming Weapons`, `Meteor Storm`)** | Macros de alto nivel (`vision` = varredura completa do repositorio; `restoration` = checkpoint/rollback seguro; `flaming_weapons` = pipeline acelerada; `meteor` = auditoria massiva/gate completo) | Executam operacoes complexas com um clique, com custo e cooldown claros. |
| **Age Advance (`I Archaic` -> `V Wonder`)** | Maturidade do sprint/milestone | Cada era desbloqueia novos poderes, unidades e estruturas, espelhando o ciclo de vida real de uma release. |
| **Buildings (`Town Hall`, `Barracks`, `Library`, `Watchtower`, `Runeforge`...)** | Subsistemas do repositorio (core, skills, docs, testes, CI, reviews) | Cada predio guarda dados reais (backlog, diffs, artefatos, alertas) e funciona como ponto de comando para aquela disciplina. |
| **Fog of War** | Estado de conhecimento do orquestrador sobre o codebase | So o que foi explorado/verificado aparece; areas obscuras sinalizam risco e divida desconhecida. |
| **War Council / Decision Podium** | Pedidos de aprovacao, merges, gates, escolhas de arquitetura | Transforma decisoes criticas em eventos visiveis e auditaveis, nao em logs esquecidos. |

Resumindo: em vez de "ficar olhando um terminal", voce **comanda** a frota de agentes como um general — visao de mapa, economia, alertas, ordens e recompensas em uma interface que ja foi desenhada para RTS.

## 2. Fundamentos de pesquisa aplicada (AAA)

### 2.1 Graficos 3D, iluminacao e fisica (fontes renomadas)
- **Physically Based Rendering (PBR)**: referencias de `pbrt.org`, cursos SIGGRAPH de `Hill/Heitz/Hery` e praticas de *Unreal/Unity* mostram que a percepcao de qualidade vem de **normal maps + roughness/metalness + sombras de contato + AO**.
- **Stylized / NPR**: pesquisas SIGGRAPH sobre `toon shading`, `X-toon` e *stylized rendering as expectation* confirmam que o olho humano prefere **coerencia estilistica + controle artistico** a fotorealismo puro — por isso o nosso pipeline mistura PBR com NPR controlado.
- **Iluminacao**: LUTs, tone mapping, key/fill/rim lighting, fog de profundidade, bloom e sombras com cascatas.
- **Animacao & fisica**: kinematics FK/IK, Verlet cloth/hair, ragdolls amortecidos, `spring-damper` para camadas de camera, Gerstner/FFT water, particulas com integracao `dt` e eventos de impacto (screen shake, spark, squash & stretch).

### 2.2 Design de RTS — o que funcionou em Warcraft III, Age of Empires III e StarCraft
- **Feedback loops**: vitorias alimentam economia/mapa, falhas criam contra-pressao. Em `RTSD`, quests completas geram favor e desbloqueiam eras; falhas acendem alertas e exigem retorno ao War Council.
- **Counter-matrix / RPS**: unidades e estrategias se anulam em triangulo. Em `RTSD`, cada classe de agente tem papel dominante contra um tipo de problema (planner vs bugfixer vs auditor).
- **Macro vs Micro**: jogadores alternam entre producao/macromanagement (base, economia, era) e micro (ordens de unidades, god powers, skirmishes). `RTSD` espelha isso com a HUD de cima (economia, idade, God Powers) e a Command Card inferior (micro de unidade).
- **Town Portal / tempo de resposta**: em WC3, o custo de reposicionar tropa nao e instantaneo. No `RTSD`, mover um agente entre modulos consome tempo/tokens e tem custo visivel.
- **Villager Priority / auto-economia (AoM: Retold)**: pre-configuracoes de tarefas automaticas. No `RTSD`, isso vira presets de fluxo (ex.: `Balanced`, `Gold Focus`, `Quest Rush`, `Guard`) para priorizar subagentes.
- **Balance system do StarCraft II**: patchs iterativos, matrizes de counter, resposta a meta. No `RTSD`, mantemos *ledger de pesos* para cada agente/acao, permitindo tune de custo, cooldown e recompensa sem quebrar o jogo.

### 2.3 Game Dev Tycoon / Cafe Mania / Office Simulation para o modo escritorio
- **Idle/tycoon**: barra de progresso continua, ordens em fila, staff com energia/stamina, boosters de cafe, upgrades de estacao de trabalho.
- **Cafe Mania / Game Dev Tycoon**: layout isometrico com mesas, kitchenette, whiteboard, salas de reuniao e zonas de foco; trabalhadores andam entre desks, copa e printers.
- **OfficeMania-like**: needs system (cafe, distracao, energia), shout/boost, upgrades de equipamento e eventos de sprint.

### 2.4 Gameplay aplicado ao Devin CLI
- **Deploy agent = spawn hero** (Tavern/Barracks)
- **Order = comando de CLI** (`/order`, `/plan`, `/build`, `/test`, `/review`, `/fix`, `/docs`)
- **Quest = issue / milestone / DAG**
- **Lumber = context window**
- **Gold = tokens**
- **Favor = verificacoes e skills**
- **God Powers = high-level Devin macros**
- **War Council = approval gates**
- **Office mode = work simulation visivel (Game Dev Tycoon-like)**
- **Replay = event log / audit trail**

## 3. Roadmap de implementacao (Slices 6 a 12)

1. **Slice 6 — Office/Tycoon Mode real**: office layout, staff com stamina/needs, cafe, sprint loop e HR/review flow (Game Dev Tycoon-like).
2. **Slice 7 — Combat & Micro RTS real**: ordens de unidade, status effects, command card avancada, minimap pings e pathfinding.
3. **Slice 8 — Upgrade & Research system**: nivel de unidade, tech tree real, inventory/equipment, reagents/crafting.
4. **Slice 9 — Espionagem, controle de mapa e stealth**: fog of war avancado, scouting, agents stealth mode, campos de visao.
5. **Slice 10 — Gamificacao Devin CLI**: quests geradas por issues reais, XP por merge, medallas, titulos, ranks, e `Trophy PNG` como artefato de release.
6. **Slice 11 — God Powers & Eras completas**: cooldowns reais, custo escalonado, level-up de poderes e `Wonder Age` com buffs persistentes.
7. **Slice 12 — Multiplayer/Co-op operacional**: varios agentes simultaneos, voice commands, hotkeys avancadas, comandos de grupo e replays comparaveis.

## 4. Checklist de qualidade e verificacao

- `selftest.py`, `audit.py`, `stop-guard.py`, `pytest`, `node --check`
- Verificacao live por Chrome CDP: screenshots de Battlefield + Office, 0 erros JS, camera clamp, particulas e HUD
- Cada mecanica nova precisa estar documentada no `CHANGELOG.md` e no `FINAL-REPORT.md`
- Nada de heuristica falsa: cada elemento da UI deve estar vinculado a um endpoint, comando ou estado real do Devin CLI
