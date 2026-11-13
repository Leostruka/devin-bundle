# Issue #169: Comparacao Completa (`rtsd` v3.8.0 vs `getagentcraft.com/docs`) e Plano de Resolucao

## 1. Matriz Comparativa Verificada (22 Superficies de `getagentcraft.com/docs`)

| # | Feature (`getagentcraft.com/docs`) | AgentCraft (`@idosal/agentcraft` v0.5.0) | Nosso `rtsd` (`milestone/v3.8.0`) | Status / Gap |
|---|---|---|---|---|
| 0 | **3D Graphics Engine, Models & Skeletal Animations** | **Motor 3D WebGL (Three.js)** com camera RTS em perspectiva (~50 deg), terreno 3D com relevo, modelos 3D reais para 8 predios, 20 herois (5x4 faccoes) e workers, **animacoes esqueleticas 3D reais** (`Idle`, `Walk`, `Run`, `Attack`, `Cast`, `Wave`, `Jump`, `Dance`) com rotacao de corpo na direcao do movimento (`atan2`), shadow maps 3D e post-processing (`RenderPass -> FogPass -> OutputPass`) | **Canvas 2D ortografico chapado**: tiles planos 2D, predios e unidades sao sprites 2D (`arc`/`fillRect`) sem perspectiva 3D, unidades nao giram em 3D para encarar o caminho e "animam" apenas subindo/descendo 2px (`Math.sin(t)`) | **GAP CRITICO #1: Motor 3D WebGL + Rigs Esqueleticos 3D Articulados + Animacoes 3D Reais** |
| 1 | **Multi-Agent Heroes & Classes** | 5 slots por faccao (Chieftain/Shaman/Archer/Grunt/Warrior) | **22 classes reais** derivadas de `agents/*.md` (`kit` por `allowed-tools`, `tier` por `bundle-models.json`), mas ainda renderizadas como icones 2D chapados | **Bom modelo de dados, mas precisa de malhas e rigs 3D reais** |
| 2 | **Buildings / Structures** | 8 predios 3D por faccao (throne, banner, mine, engineering, archives, recon, analysis, settings) | **11 predios reais** com dados de `/buildings/<id>`, mas ainda desenhados como quadrados/triangulos 2D em Canvas | **Bom backend, mas precisa de modelos arquitetonicos 3D reais** |
| 3 | **World Map & Fog of War** | Mapa 3D fixo; `V` liga/desliga FogPass; `H` heatmap | **Voronoi ponderado deterministico** dos diretorios reais do repo (`map.json`), 3 estados de fog (`shroud/explored/lit`) + Line-of-Sight dinamica + rios/pontes/estradas + `M_CONTESTED` | **Paridade + falta tecla `V` toggle fog e `H` heatmap** |
| 4 | **Weather & Environment Physics** | Nao possui clima real nem fisica de vento | **Previsao local real (Open-Meteo + geo IP)** dirigindo ondas de Gerstner, arvores, folhas, capas, bandeiras, chuva/tempestade/neve/neblina + ciclo dia/noite | **Exclusivo nosso** |
| 5 | **Tech Tree & RAG Doctrines** | Nao possui Tech Tree de skills/RAG | **83 skills reais em 6 escolas** (`K`), spellbook por heroi, Armory model pin e 8 doutrinas RAG verificadas por evidencia | **Exclusivo nosso** |
| 6 | **Replay & Deterministic Event Sourcing** | Apenas `mission-history.json` (ate 200 missoes) | **Event-sourcing puro (`events.jsonl`)**, `--replay` (1x/2x/4x/seek), paridade byte-a-byte, `/score` Victory Screen e `/sessions` Match History | **Nosso supera** |
| 7 | **Sound Effects & Music** | Playlist sequencial com ducking (`Music` toggle) | **WebAudio DSP procedural** (pink noise vento/chuva, Karplus-Strong, FM metalica por predio/classe, foley Office); **falta gerador de trilha musical ambiente c/ ducking** | **Gap parcial: Ambient Music Generator + Ducking** |
| 8 | **Race Skins** | 4 faccoes (`Orc`, `Human`, `Elf`, `Undead`) trocando paleta/modelos/terreno | Temos `battlefield` vs `office` (isometrico), mas **faltam faccoes RTS (`Human`, `Orc`, `Elf`, `Undead`)** | **Gap: 4 Race Faction Skins** |
| 9 | **Side Panel (`Enter`: Chat / Git Codex / Files)** | `Enter` abre Side Panel com 3 abas: **Chat** (streaming + operation ticker + `@file` autocomplete + Plan Review), **Git (Codex)** (arquivos alterados + diff viewer por arquivo), **Files** (arvore recursiva com badges TS/JS/PY/RS/MD + busca) | Temos Comms Feed + Inspector no rodape, mas **nao temos as abas `Git Diffs (Codex)` nem `File Explorer` com busca/badges + `@file` autocomplete no composer** | **Gap Alto: Side Panel (Chat / Git Diffs / File Explorer + `@file`)** |
| 10 | **Integrated PTY Terminal (`Ctrl+T` / `F`)** | Terminal multi-tab no HUD inferior preservando sessao | Temos `extensions/computer-use/cu_terminal.py` no bundle, mas **nao exposto como terminal multi-tab no HUD do `rtsd`** | **Gap Alto: Integrated Terminal Drawer (`Ctrl+T`)** |
| 11 | **Git Management & Worktrees** | Detecta `git worktree list`, mostra worktree por heroi, **Stash Manager** (create/apply/pop/drop) e **Branch Switcher / Commit History** | Vault mostra apenas `git log -n 5`; **faltam Worktree scanner, Branch list e Stash Manager na UI** | **Gap Medio: Git Worktrees + Stash/Branch Manager no Vault** |
| 12 | **Skill Scrolls (Collectibles on Map)** | 5 pergaminhos dourados flutuantes no mapa; heroi caminha ate o scroll -> modal da skill | Temos 83 skills em `skills/`, mas **nao espalhamos Skill Scrolls colecionaveis no mapa para descoberta/inspecao** | **Gap Medio: Collectible Skill Scrolls no Mapa** |
| 13 | **Achievements (Hall of Glory + Trophy PNG)** | ~30 conquistas (`Discovery`, `Mastery`, `Secret`), raridades (`Common..Legendary`), herois dancam/pulam + confetti + **Trophy Card PNG 600x315 compartilhavel** | `trophy-hall` lista gates verdes dos ledgers, mas **nao tem sistema de Achievements nem exportacao de Trophy Card PNG** | **Gap Medio: Achievements + Trophy Card PNG 600x315** |
| 14 | **Scheduled Tasks (Active Loops + Campaign Delegation)** | Painel `Active Loops` (1m/5m/15m/30m/1h), contagem de iteracoes, `Trigger now`, `Stop`, delegacao para Campaign | Temos `scheduled-turns` skill, mas **sem painel `Active Loops` no `rtsd`** | **Gap Medio: Scheduled Loops Panel (`/loops`)** |
| 15 | **Campaigns (Spec -> Plan -> Review -> Worktree Dispatch -> Merge)** | Fluxo end-to-end na aba Campaign (`+ Submit Feature`, Refine/Review/Approve, rings/dependency lines no mapa, Review & Merge diff) | Temos Quest DAG (`#130`) e `goal` intent, mas **falta o fluxo visual de Campaign (Submit Spec, Dependency Lines no mapa, Review & Merge diff)** | **Gap Alto: Campaign Pipeline & Map Dependency Lines** |
| 16 | **Voice Input (Web Speech API)** | Botao de microfone no composer (`SpeechRecognition`), transcricao real-time + auto-send no silencio | **Nao implementado no `#cmd` composer** | **Gap Rapido: Voice Input Mic Button (`SpeechRecognition`)** |
| 17 | **Keyboard Shortcuts Parity** | `V` toggle fog, `H` heatmap / handoff, `Shift+H` fork, `F9` quest log, `F12` message log, `` ` `` war table (file activity), `Ctrl+F` cross-agent search, `Y/N` approve/deny permission | Temos `QWER/ASDF/ZXCV`, `0-9`, `F1-F4`, `F10`, `T`, `N`, `K`, `M`, `.`, `SPACE`, `?`; **faltam `Y/N` para War Council, `V` fog toggle, `H` heatmap, `` ` `` War Table, `F9`/`F12`** | **Gap Rapido: Paridade de Hotkeys (`Y/N`, `V`, `H`, `` ` ``, `F9`, `F12`)** |
| 18 | **Interactive First-Launch Tutorial & War Advisor** | Tutorial interativo em 6 passos + dicas do War Advisor | Temos apenas o card estatico `?` (`#help`) | **Gap Baixo: Interactive Tutorial + War Advisor** |
| 19 | **Agent Teams (Lead Star + Colored Party Rings)** | Agrupa time com borda colorida, estrela no Lead e anel da cor do time no mapa/minimapa | Temos tint de lane por territorio, mas **sem agrupamento Lead/Party com estrela e anel de equipe** | **Gap Baixo: Agent Teams Party Grouping** |
| 20 | **Remote Access / Spectator / Mobile PWA** | Tuneis com TTL + PWA mobile + push | `--remote MIN` com token + spectator token read-only + PWA (`sw.js`) + `#mtabs` + `Notification` API | **Paridade Completa** |

---

## 2. Plano Sistematico de Resolucao (6 Fatias Verticais na `milestone/v3.8.0`)

Seguindo o padrao da milestone (`1 issue -> branch rts-v2/<issue>-<slug> -> gates -> PR -> squash-merge em milestone/v3.8.0`), atacamos primeiro o **Gap Grafico e de Animacao 3D (Fatia 0)** e em seguida as 5 fatias funcionais:

### Fatia 0 (Prioridade Maxima): `feat(rts): Real 3D WebGL Engine, 3D Terrain Mesh, Articulated 3D Hero/Building Models & Skeletal Animations`
- **Diagnostico Honesto do Problema Atual**:
  - Nosso `engine.js` atual usa `canvas.getContext("2d")` puramente bidimensional: camera 90 graus reta de cima, predios feitos de `fillRect` + `arc` 2D, arvores de circulos empilhados e unidades que apenas sobem e descem 2 pixels (`dy = Math.sin(t)`) sem rotacionar o corpo em 3D (`yaw`), sem articulacao 3D de quadril/joelho/ombro/cotovelo/cabeca e sem profundidade (`Z-buffer`).
- **Solucao 3D Real (`engine3d.js` + `models3d.js` integrados ao `engine.js`)**:
  1. **Pipeline 3D WebGL com Perspectiva RTS Real**:
     - Camera RTS 3D em perspectiva (`FOV 42 deg`, inclinacao `pitch ~52 deg`, `yaw` rotacionavel com `Q/E` ou mouse medio, zoom suave ao cursor e `Raycaster` 3D exato no plano do terreno e nas bounding boxes das malhas 3D).
     - Iluminacao 3D fisica: `DirectionalLight` solar/lunar com **Shadow Maps 3D reais** (`castShadow` / `receiveShadow` em todos os predios, arvores e unidades), `HemisphereLight` de ceu/chao e `PointLights` dinamicas nos braseiros, fornalha do Runeforge, vorticie do Portal e janelas noturnas.
  2. **Terreno 3D com Relevo (Heightmap Mesh), Penhascos e Agua 3D**:
     - Malha 3D triangulada com elevacao real (colinas, depressao de rios/lagos, rampas e penhascos rochosos nas bordas), estradas em relevo, pontes 3D com arcos e pilares sobre a agua, e plano de agua 3D com ondas vertex/fragment, reflexo especular e espuma na margem.
  3. **Modelos 3D Volumétricos Reais para as 11 Estruturas e Elementos do Mapa**:
     - Cada uma das 11 estruturas construida como hierarquia de malhas 3D reais (torres cilindricas/octogonais 3D com ameias, telhados piramidais/conicos 3D, muralhas, arcos de portao, colunas do Pantheon, domo 3D da Library, fornalha 3D com bigorna, obeliscos 3D do Portal com aneis girando em 3 eixos, tendas 3D do Marketplace e estatua 3D no Altar).
     - Arvores 3D reais (troncos cilindricos + copas em camadas conicas/esfericas 3D balancando nos eixos X/Z com o vento), rochas 3D facetadas, cristais 3D nas minas de ouro e fogueiras 3D nos acampamentos.
  4. **Esqueleto 3D Articulado (14 Juntas 3D) e Maquina de Estados de Animacao 3D**:
     - Cada Heroi, Worker e Minion possui uma hierarquia 3D completa com 14 nos articulados (`Root -> Pelvis -> Torso -> Neck -> Head/Helm`, `ClavicleL/R -> UpperArmL/R -> ForearmL/R -> HandL/R (Shield/Weapon)`, `ThighL/R -> ShinL/R -> FootL/R`, `CapeChain1..3`).
     - **Rotacao de Direcao (`Yaw` 3D)**: a unidade gira suavemente no eixo Y (`atan2(dx, dz)`) para encarar a direcao em que caminha, ataca ou interage.
     - **8 Clips de Animacao Esqueletica 3D Reais** interpolados por quaternion/angulo de junta:
       - `Idle (Stand-1)`: respiracao 3D do torax, transferencia de peso no quadril, balanco suave dos bracos e cabeca olhando ao redor (`Stand-2`).
       - `Walk / Run`: ciclo completo de passada 3D (flexao de coxa $\pm 38^\circ$, dobra de joelho $0..55^\circ$, plantio de calcanhar, contra-rotacao da cintura e balanco oposto dos bracos + capa esvoacando em 3D).
       - `Attack (Slash / Shoot / Thrust)`: rotacao de tronco + levantamento de ombro/cotovelo + golpe de espada/martelo de $120^\circ$ em 3D (ou puxada de arco / disparo de flecha 3D).
       - `Cast / Channel`: ambos os bracos erguidos em 3D, cajado/runas levitando e girando ao redor do heroi.
       - `Gather (Mine / Chop)`: inclinacao de tronco a $40^\circ$ + golpe ritmico de picareta/machado na jazida 3D + saco de ouro/toras nas costas no retorno.
       - `Celebrate (Wave / Jump / Dance)`: animacoes 3D de aceno, salto e danca sincronizada (como nos Achievements do AgentCraft!).
       - `Death / Dissipate`: queda articulada do corpo ao chao + ascensao eterea da alma do heroi.
- **Gate**: renderizacao 3D a `>=60 fps`, picking 3D por raycast verificado em todas as unidades/predios, `selftest.py` `ALL PASS` e inspecao visual em Chrome via CDP.

### Fatia 1 (Issue #170): `feat(rts): Explorer, Git Codex & Worktree Manager (/files, /git, @file autocomplete)`
- **Backend (`rtsd.py` + `world.py`)**:
  - `GET /files`: arvore recursiva do repositorio (ignorando `.git`/`node_modules`/`__pycache__`) com tamanho e badge de extensao (`PY`, `JS`, `MD`, `JSON`, `RS`, `HTML`, `CSS`, `SH`), mais lista plana para `@file` autocomplete no composer.
  - `GET /git`: status completo (`git status --porcelain`), diff por arquivo (`GET /git/diff?path=...`), `git worktree list`, branches (`git branch -a`), commits recentes e stashes (`git stash list`).
  - `POST /git`: operacoes seguras de stash (`create`, `apply`, `pop`) criadas como eventos auditaveis.
- **Frontend (`index.html` + `app.js`)**:
  - Aba/Drawer **Explorer & Git Codex** (`Enter` ou botao no topo): abas `Files` (busca em tempo real + badges coloridos + click para ver diff), `Git Codex` (arquivos alterados + visualizador de diff red/green + Worktrees + Stashes + Branches).
  - **Autocomplete `@file`** no input `#msg` ao digitar `@` + caminho, e botao de **Voice Input (Microfone Web Speech API)** ao lado do botao `send`!
- **Gate**: `selftest.py` valida `GET /files`, `GET /git`, `GET /git/diff` e `POST /git` stash.

### Fatia 2 (Issue #171): `feat(rts): Race Skins (Human, Orc, Elf, Undead) + Fog Toggle (V), Heatmap (H) & Hotkey Parity`
- **Visual & Temas (`theme.js` + `engine.js`)**:
  - Adiciona as **4 Faccoes RTS (`Human`, `Orc`, `Elf`, `Undead`)** alem do modo `Office`, transformando paleta de terreno, agua, arvores, arquitetura dos 11 predios e armaduras/silhuetas dos herois (persistido em `localStorage` e selecionavel no `Menu F10`).
  - **Fog of War Toggle (`V`)**: alterna entre Fog of War estrito e visao clara (color-neutral).
  - **Territory Heatmap (`H` sem unidade selecionada)**: overlay termico de atividade de arquivos/commits por territorio e tile.
  - **War Table Overlay (`` ` `` backtick)** + atalhos **`Y` / `N`** para aprovar/negar imediatamente a decisao ativa do War Council, **`F9`** (Quest Log) e **`F12`** (Comms Log).
- **Gate**: `node --check` + `selftest.py` + verificacao visual das 4 faccoes e heatmap via Chrome CDP.

### Fatia 3 (Issue #172): `feat(rts): Collectible Skill Scrolls on Map + Achievements (Hall of Glory & Trophy Card PNG)`
- **Skill Scrolls (`world.py` + `engine.js` + `app.js`)**:
  - 5 **Pergaminhos Dourados Flutuantes (`Skill Scrolls`)** sorteados dentre as 83 skills reais do bundle aparecem no mapa e no minimapa com anel dourado giratorio.
  - Quando um heroi caminha ate um pergaminho (clique/right-click), abre o card da skill (lendo a descricao real do `SKILL.md`) com botao para **Equipar / Cast** no heroi!
- **Achievements & Hall of Glory (`world.py` + `app.js`)**:
  - ~20 conquistas reais divididas em `Discovery`, `Mastery` e `Secret` across 4 raridades (`Common`, `Uncommon`, `Rare`, `Legendary`), desbloqueadas por metricas reais da sessao (`War Council`, `Grand Army`, `Speed Run`, `Token Whale`, `Gatekeeper`, `Cartographer`, `Scroll Seeker`, `Completionist`).
  - Celebracao no mapa (confetti, flash dourado/azul, herois comemoram) + galeria **Hall of Glory** + gerador Canvas de **Trophy Card PNG (`600x315px`)** para download/copia!
- **Gate**: `selftest.py` verifica catalogo de Skill Scrolls e calculo de Achievements em `/snapshot`.

### Fatia 4 (Issue #173): `feat(rts): Campaigns (DAG Lines on Map + Review & Merge View) & Scheduled Loops Panel`
- **Campaigns (`world.py` + `engine.js` + `app.js`)**:
  - Desenha **Linhas de Dependencia do DAG (`blocked_by`)** no mapa entre marcadores de Quest e aneis de grupo nos herois da campanha.
  - Modal **Campaign Review & Merge**: exibe o diff combinado do branch, status dos gates de todos os ledgers, resumo das missoes e botoes de intent para `Approve`, `Create PR` ou `Request Repair`.
- **Scheduled Loops (`/loops` em `rtsd.py` + painel `Active Loops`)**:
  - `GET/POST/DELETE /loops`: agenda prompts recorrentes (`1m`, `5m`, `15m`, `30m`, `1h`) que emitem intents reais a cada intervalo, com contador de iteracoes, `Trigger Now`, `Stop` e delegacao para Campaign.
- **Gate**: `selftest.py` testa criacao, trigger e parada de `/loops`.

### Fatia 5 (Issue #174): `feat(rts): Integrated Multi-Tab Terminal Drawer (Ctrl+T), Procedural Ambient Music & Interactive Tutorial`
- **Integrated Terminal (`rtsd.py` + `app.js`)**:
  - Endpoint `POST /terminal` (ou sessoes shell gerenciadas localmente em loopback, bloqueado para spectators/replay!) + drawer multi-tab no HUD inferior (`Ctrl+T` / botao `Term`) para rodar comandos no workspace sem sair do RTS.
- **Procedural Ambient Music & Audio Ducking (`app.js`)**:
  - Gerador musical ambiente procedural em WebAudio (acordes modais lentos estilo tavern/orchestral + silencio entre faixas + **audio ducking automatico** quando um alerta ou voz toca).
- **Interactive First-Launch Tutorial & War Advisor**:
  - Passo-a-passo interativo em 5 etapas guiadas pelo **War Advisor** + agrupamento visual de **Agent Teams** (estrela no Lead + anel de equipe).
- **Gate**: `selftest.py` (incluindo bloqueio 403 para spectator em `/terminal`) + `audit.py` + `pytest`.
