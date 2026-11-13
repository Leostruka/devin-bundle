# Dossier: Maestri (themaestri.app)

Pesquisa externa do produto Maestri como orquestrador de agentes, para comparacao
com `skills/project-orchestrator/`. Toda afirmacao de capacidade carrega fonte.
Itens sem confirmacao de fonte estao marcados `nao verificado`.
Data da pesquisa: 2026-09-30. Versao observada no changelog: 0.48.2 (2026-09-24).

## 1. O que e

App desktop nativo que e uma **camada de canvas e orquestracao em volta de
agentes de CLI** que o usuario ja tem instalados (Claude Code, Codex, OpenCode,
Antigravity, ou shell puro). O proprio docs diz: "O Maestri nao e um agente de
IA em si. Ele e a camada de canvas e orquestracao que fica em volta dos seus
agentes." [fonte: https://www.themaestri.app/pt-br/docs]

Sequia: "o primeiro canvas infinito feito para orquestrar agentes. Cada um
ganha um papel, todos conversam entre si e a operacao inteira fica a sua
frente." [fonte: https://www.themaestri.app/pt-br]

Stack: Swift + SwiftUI + AppKit, canvas acelerado por Metal, design Liquid
Glass. Requer macOS 15.4+ Apple Silicon na pagina principal; versoes para
Windows e Linux existem (paginas dedicadas). [fonte:
https://www.themaestri.app/pt-br; https://www.themaestri.app/pt-br/docs/terminals]

Privacidade como feature: zero telemetria, tudo local, sem conta, config em
JSON puro, notas em Markdown. [fonte: https://www.themaestri.app/pt-br]

## 2. Paradigma de orquestracao

**Canvas espacial + PTY**. Cada agente roda num terminal real desenhado no
canvas; conexoes sao cabos animados entre nos. A comunicacao entre agentes
acontece no nivel de CLI: conectar dois terminais instala uma "Maestri Agent
Skill" em cada um, que ensina o agente a enviar instrucoes e receber respostas
de qualquer agente conectado. Agnostico de agente: Claude Code fala com Codex,
OpenCode com Claude, etc. [fonte: https://www.themaestri.app/pt-br/docs/connections]

O Maestri detecta termino de turno do agente receptor **somente quando ele nao
esta selecionado** (selecionado = humano no controle), e entao devolve a
resposta ao agente origem. [fonte: https://www.themaestri.app/pt-br/docs/connections]

Testemunho citado no site descreve o mecanismo: "every terminal is a node -
you drag agents around, connect them with lines, and they talk to each other
through PTY. No API glue, no middleware. Just one agent typing into another's
terminal." (@yrzhe_top) [fonte: https://www.themaestri.app/pt-br, link para
https://x.com/yrzhe_top/status/2037581353458212914]

O **Modo Maestro** promove um terminal a gerente: o agente ganha a skill
`/maestri-manager` e passa a poder recrutar (criar terminal conectado abaixo de
si com agente + responsabilidade), conectar recrutas a notas (fonte de verdade
compartilhada), reatribuir responsabilidades e editar prompts ao vivo (reinicia
o processo preservando posicao/nome/conexoes), dispensar (fechar terminal),
provisionar workspaces e andares (capacidade exclusiva de Maestro ou do
humano), e mandar notificacao de sistema. Por padrao recruta copias de si
mesmo; equipes mistas por prompt ("o Codex seja o revisor, o Claude seja o
desenvolvedor"). Auto-layout dos recrutas abaixo do Maestro. Recruta enxerga o
proprio nome, responsabilidade e conexoes. [fonte:
https://www.themaestri.app/pt-br/docs/maestro]

Enderecamento: `@Maestro` no composer carrega a skill de gerente; agentes de
outro workspace sao enderecados como "Nome @ Workspace". [fonte:
https://www.themaestri.app/pt-br/docs/prompt-composer;
https://www.themaestri.app/pt-br/docs/connections]

Mecanismo observado em hands-on independente: ao conectar dois terminais, o
agente carrega `Skill(maestri)` e roda `Bash(maestri list)` para ver os pares
conectados e `Bash(maestri ask "Claude Code #6" "...")` para enviar prompt; a
resposta volta ao contexto de quem perguntou. Padroes suportados citados no
changelog: concurrent asks, ask-back chains, circular relays, `maestri ask
--batch`. Outros comandos do CLI: `maestri routine`, `maestri floor land`,
`maestri floor delete`, `maestri portal resize`. Permissao de execucao fica no
harness do agente (ex.: allowlist `Bash(maestri:*)` no Claude Code), nao numa
camada propria do Maestri. [fonte:
https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en;
https://www.themaestri.app/en/changelog]

## 3. Papeis / agentes

**Responsibilities**: conjuntos nomeados de instrucoes (nome, cor de badge,
prompt) injetados automaticamente quando o agente inicia. Exemplos da doc:
Lider, Desenvolvedor, Revisor, Testador. Gerenciadas em Configuracoes ->
Agentes. [fonte: https://www.themaestri.app/pt-br/docs/terminals]

Persistencia portatil: a responsabilidade roda o agente num subdiretorio do
projeto com seu proprio CLAUDE.md/AGENTS.md, e um sidecar `role.json` (nome,
cor, prompt) viaja com o diretorio entre workspaces e maquinas. Botao
"Descobrir Responsabilidades" varre o working dir atras de role.json, inclusive
via SSH/Docker/Sandbox. [fonte: https://www.themaestri.app/pt-br/docs/terminals]

Sem role pre-definida de verificador/QA independente nem contrato de aceitacao:
o comportamento de cada papel e definido pelo texto da responsabilidade que o
usuario escreve. (inferencia a partir da doc; a doc nao descreve papel de QA
embutido - verificar em uso real: nao verificado)

## 4. Memoria e contexto

- **Canvas como memoria espacial**: "o canvas guarda esse mapa" do estado do
  projeto (caminho de cada agente, o que foi descartado, colisoes). [fonte:
  https://www.themaestri.app/pt-br]
- **Notas = arquivos .md reais** que agentes leem e escrevem via CLI do
  Maestri quando conectados; sobrevivem sessoes e restarts. Notas podem ser
  **bloqueadas** (agente le mas nao escreve - spec pinning). [fonte:
  https://www.themaestri.app/pt-br/docs/notes]
- **Cadeias de notas**: nota conectada a nota forma hierarquia/mapa mental que
  o agente percorre a partir da nota de entrada. [fonte:
  https://www.themaestri.app/pt-br/docs/connections]
- **Ficharios**: pastas com abas que agrupam notas; agente conectado acessa
  todas as paginas; paginas individuais bloqueaveis; fichario nomeado persiste
  vazio (kanban: Backlog/Fazendo/Revisao/Entregue). [fonte:
  https://www.themaestri.app/pt-br/docs/ficharios]
- **Chat com 7 threads por terminal**: cada terminal guarda sete threads
  coloridas (cor = identidade; mensagens chegam ao agente marcadas com a
  thread). O registro da thread e guardado pelo proprio Maestri e o agente
  consegue le-lo de volta (ultimos turnos, uma semana, intervalo de datas):
  thread sobrevive a restart, contexto compactado e processo de agente novo.
  [fonte: https://www.themaestri.app/pt-br/docs/chat]
- **Partituras**: snapshot de um arranjo do canvas (terminais + agentes +
  responsabilidades + notas + portais + desenhos + conexoes) num unico JSON
  `.maestripartitura` em `~/.maestri/partituras/`; compartilhavel, com tela de
  revisao de importacao e resolucao de conflitos de responsabilidade por
  id/nome. Molde, nao backup: stripa scrollback, env vars sobrescritas, paths
  absolutos. [fonte: https://www.themaestri.app/pt-br/docs/partituras]
- **Workspaces** persistem layout e retomam onde parou; `CLAUDE.md`/`AGENTS.md`
  por workspace com opcao de sincronizar os dois. [fonte:
  https://www.themaestri.app/pt-br/docs/workspaces]

Sem evidencia publica de: curadoria de memoria (add/update/archive), orcamento
de contexto por agente, ou protocolo de reset/higiene de contexto. A doc cobre
"compactar o contexto" como acao do usuario dentro da CLI do agente. [fonte:
https://www.themaestri.app/pt-br/docs/chat]

## 5. Delegacao

- **Humano -> agente**: Prompt Composer com @ mencoes a terminais, notas,
  portais, arquivos (# picker), @Maestro, acoes (@New Note, @New Portal, @New
  Device Portal); imagens coladas chegam como pixels em CLIs que suportam;
  colagens grandes viram pills. [fonte:
  https://www.themaestri.app/pt-br/docs/prompt-composer]
- **Agente -> agente**: via skill Maestri instalada na conexao; delegacao e
  conversacao pelo proprio terminal (peer-to-peer), nao por contrato formal de
  dispatch. [fonte: https://www.themaestri.app/pt-br/docs/connections]
- **Maestro -> recrutas**: recrutamento com agente + responsabilidade +
  conexao a notas; reatribuicao ao vivo; dispensa. [fonte:
  https://www.themaestri.app/pt-br/docs/maestro]
- **Rotinas**: prompts agendados por intervalo para um terminal, com
  encadeamento `&&` (cada prompt so dispara apos o anterior concluir),
  pause/resume/edit/delete, indicador visual. Casos de uso documentados:
  testes continuos, monitoramento, ciclos de revisao, scraping agendado.
  [fonte: https://www.themaestri.app/pt-br/docs/routines]
- **Cross-workspace**: conexao e recrutamento entre workspaces; o recruta roda
  "onde aquele workspace roda" (inclusive remoto). [fonte:
  https://www.themaestri.app/pt-br/docs/maestro]

## 6. UX / superficie

- Canvas infinito com zoom, fisica de cordas (ou estilo circuito), abracadeiras
  para agrupar cabos, minimapa; grupos, desenhos a mao, blocos de texto.
  [fonte: https://www.themaestri.app/pt-br/docs/connections;
  https://www.themaestri.app/pt-br]
- Maestri Chat: face de chat por terminal com transcript limpo (o agente
  entrega o que quer dizer, nao o stdout); terminal vivo por baixo; anexos de
  arquivo arrastaveis; badge de nao lidas. [fonte:
  https://www.themaestri.app/pt-br/docs/chat]
- **Atencao**: ponto vermelho no header do terminal quando o agente para de
  produzir (esperando decisao ou fim de turno); Ctrl+Shift+A cicla; opcao de
  notificacao de sistema que foca o terminal certo ao clicar. [fonte:
  https://www.themaestri.app/pt-br/docs/terminals]
- **Ombro**: companheiro on-device (Apple Foundation Models, macOS 26+) em
  janela flutuante fora do app; observa agentes passivamente, notifica com
  resumo + preview do estado do terminal + sugestao de proximo passo;
  respondendo a perguntas de status; escreve "Ombro Notes"; resume notas do
  workspace. [fonte: https://www.themaestri.app/pt-br/docs/ombro]
- **Batuta Search**: busca global incluindo dentro de threads de chat em todos
  os workspaces e andares, com navegacao ate a mensagem. [fonte:
  https://www.themaestri.app/pt-br/changelog (0.47.2); indice de docs]
- **Uso dos agentes**: aneis por provedor (Claude, Codex, Antigravity) com
  fracao do plano, janelas de reset; pergunta a CLI de cada agente, nunca le
  tokens; provedores customizaveis via JSON em ~/.maestri/usage/providers/.
  [fonte: https://www.themaestri.app/pt-br/docs/terminals]
- **Portais**: janelas embutidas (site, iOS Simulator, emulador Android,
  celular real); agente conectado clica/digita/desliza lendo a arvore de
  elementos real, nao pixels; Design Mode desenha sobre o portal para enviar
  regiao como contexto. [fonte: https://www.themaestri.app/pt-br;
  https://www.themaestri.app/pt-br/changelog (0.46.0)]
- Arvore de arquivos navegavel no canvas com menu git (diffs, commit, push,
  branches, stash); preview de midia. [fonte: indice de docs + changelog
  0.45.2]
- Navegacao por teclado estilo tmux; Ctrl+numero foca terminal; Spotlight
  indexa workspaces (macOS). [fonte:
  https://www.themaestri.app/pt-br/docs/workspaces;
  https://www.themaestri.app/pt-br/docs/terminals]

## 7. Isolamento e ambientes

- **Andares (Floors)**: copia instantanea isolada do workspace. macOS: clone
  copy-on-write APFS com branch proprio; Windows: isolamento por branch git.
  Landing = `git fetch` do clone + merge com preview de conflitos (resolucao de
  conflitos fora do app). Hooks de ciclo de vida: setup/run/teardown com
  `$MAESTRI_FLOOR_NAME`, `$MAESTRI_BRANCH_NAME`, `$MAESTRI_FLOOR_PATH`,
  `$MAESTRI_ROOT_PATH`, `$MAESTRI_PROJECT_NAME`. Guardados em
  `.maestri/floors`. [fonte: https://www.themaestri.app/pt-br/docs/floors]
- **Ambientes**: Local / Local (tmux, sobrevive ao app fechar) / WSL / SSH
  (OpenSSH + tunel reverso para Bridge port 7433; instala CLI wrapper + skills
  + responsabilidades no host; auth por chave, nao interativa) / Docker
  Container (`docker exec`, nunca cria/deleta) / Docker Sandbox (`sbx exec`) /
  Custom Runtime (exec-style). Skills, CLI, responsabilidades, uploads,
  comunicacao entre agentes, recrutamento e andares seguem o ambiente.
  [fonte: https://www.themaestri.app/pt-br/docs/environments]

## 8. Integracoes e extensibilidade

- Agentes: qualquer CLI que carregue skill e rode comando de shell (Claude
  Code, Codex, OpenCode, Antigravity citados). [fonte:
  https://www.themaestri.app/pt-br/docs/chat;
  https://www.themaestri.app/pt-br/docs/terminals]
- **Maestri Wire**: protocolo documentado (beta) para outros dispositivos
  controlarem o host: HTTPS+WSS na porta 7434, cert autoassinado com pin de
  SHA-256 SPKI, pareamento por QR/codigo de 6 digitos ou senha -> token de
  dispositivo (host guarda so o SHA-256), papeis owner/guest, capabilities
  versionadas, feed WebSocket de estado + stream WebSocket de PTY, rate
  limiting, sem CORS. [fonte: https://www.themaestri.app/pt-br/docs/wire]
- **Maestri Remote**: app iPhone/iPad (TestFlight publico) sobre o Wire: ver
  todos os agentes ao vivo, aprovar/recusar prompts, terminal real transmitido
  do PTY, chat ao vivo, file tree com git. [fonte:
  https://www.themaestri.app/pt-br/remote; changelog 0.45.0]
- CLI `maestri` instalada (ex.: renomear workspace). [fonte: changelog 0.47.2]
- Temas customizados (formato Ghostty em ~/.maestri/terminal/themes/);
  provedores de uso customizados via JSON. [fonte:
  https://www.themaestri.app/pt-br/docs/terminals]
- Discord da comunidade. [fonte: https://www.themaestri.app/pt-br/docs]

## 9. Posicionamento e preco

- Gratis: $0 para sempre - 1 workspace, agentes ilimitados, todos os recursos
  incluido Ombro. Pro: R$95 pagamento unico na pagina pt-br / $18 lifetime na
  pagina EN e no comentario do autor no Product Hunt - workspaces ilimitados,
  2 Macs, trial de 7 dias. [fonte: https://www.themaestri.app/pt-br#pricing;
  https://hunted.space/product/maestri/launches/maestri]
- Empresa: Evercraft Labs (privacy policy), desenvolvido no Brasil. Fundador:
  Evert Junior, solo dev, Brasilia DF (@evertjr). [fonte:
  https://www.themaestri.app/en/privacy via researcher;
  https://hunted.space/product/maestri/launches/maestri;
  https://github.com/evertjr]
- Lancamento Product Hunt: 2026-03-24, 177 upvotes, 18 comentarios, #8 do
  dia; self-hunted pelo autor. [fonte:
  https://hunted.space/product/maestri/launches/maestri]
- Bug reports: bugs@themaestri.app; vendas em /buy; Discord oficial. [fonte:
  https://www.themaestri.app/pt-br/changelog + footer]
- Posicionamento explicito contra "chatbot com caixa de entrada": o estado do
  projeto vive no canvas, nao na cabeca do usuario; "voce e o maestro". Quote
  do autor: "an infinite canvas where each terminal is a node... agent-to-agent
  communication. Drag a line between two terminals and they collaborate. No
  APIs, no middleware, just PTY orchestration." [fonte:
  https://www.themaestri.app/pt-br;
  https://hunted.space/product/maestri/launches/maestri]
- Product Hunt: badge "Maestri - An infinite canvas where coding agents work
  in concert". [fonte: https://www.producthunt.com/products/maestri embed na
  pagina principal]
- Changelog ativo: 0.45.x a 0.48.x entre 2026-08-26 e 2026-09-24 (cadencia
  semanal+). [fonte: https://www.themaestri.app/pt-br/changelog]

## 10. Sinais externos

Depoimentos na pagina principal (todos linkados para X):
swarm noturno (@zsbenke), mecanismo PTY (@yrzhe_top), qualidade de UI nativa
(@usagimaruma), "killed excalidraw, normal terminals" (@nicolettiFPS),
departamento de vendas com 8 agentes orquestrados (CRO, VP, RevOps, BDR, SDR,
Sales Engineer, Closer, Partner - @kaduveronez), site inteiro "vibecoded" sem
abrir IDE (@ducaswtf). [fonte: https://www.themaestri.app/pt-br com links para
status no X]

Hands-on e reviews independentes localizados pelo researcher (amostra
verificada: zenn.dev):
- Hands-on tecnico com prova do mecanismo CLI (`Skill(maestri)`, `maestri
  list`, `maestri ask`, `Bash(maestri:*)` allowlist, `$MAESTRI_CLI`):
  https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en [verificado]
- Uso real com orquestrador Codex + executor Grok via `maestri ask`:
  https://ranimontagna.com/en/blog/do-terminal-ao-cockpit-orca-superset-maestri
  [reportado pelo researcher, nao re-aberto pelo orquestrador]
- Reviews: makerstack.co 7.9/10, macaiapps.com, coding4food.com, somi.ai,
  fyve.co.jp, clauday.com. [reportado pelo researcher; nao re-abertos]
- Product Hunt 403 no fetch direto; dados de lancamento via mirror
  hunted.space (177 upvotes, #8 do dia, 2026-03-24). [verificado]

## 11. Nao verificado / ausente (buscado, nao encontrado)

- Gates formais de qualidade (aceitacao por criterio, testes como gate de fase,
  verificacao independente anti-gaming): a doc nao descreve; a UX de aprovacao
  e o humano clicando. Rotinas podem montar loop de teste, mas nao ha gate
  semantico documentado. **nao verificado** (ausencia de evidencia, nao
  evidencia de ausencia absoluta - uso real poderia revelar)
- Metodologia de projeto (RUP/Scrum/templates de artefatos): nao descrito.
- Orcamento/cap de fan-out ou custo por fase: nao descrito (aneis de uso medem
  plano do provedor, nao budget do enxame).
- Revisao por agente verificador independente (qa-ci equivalente): nao
  descrito.
- Persistencia de longo prazo alem de notas/threads/partituras (ex.: memoria
  curada cross-projeto): nao descrito.
- Comportamento interno exato da Maestri Agent Skill (formato das mensagens
  entre agentes): parcialmente observado via hands-on de terceiro
  (`maestri list`/`ask`); implementacao interna completa so no app instalado.
  **parcialmente verificado**
- MCP first-party e integracao com issue trackers (Linear/Jira/GitHub Issues):
  buscado, nada encontrado. [queries do researcher: "Maestri macOS MCP git
  worktree floors remote SSH Docker runtime" etc.]
- Preco fora do Brasil/US e tier de time/empresa: nao descrito.
- Receita, numero de usuarios, roadmap publico, funding: **nao verificado**.
- Presenca oficial em YouTube/LinkedIn empresa/HN/Reddit: ausente nas buscas.

## 12. Fontes

| URL | Rendimento |
|---|---|
| https://www.themaestri.app/pt-br | Homepage completa: posicionamento, depoimentos, features, preco, stack |
| https://www.themaestri.app/pt-br/docs | Indice de docs + intro (o que e / nao e) |
| https://www.themaestri.app/pt-br/docs/maestro | Modo Maestro completo |
| https://www.themaestri.app/pt-br/docs/terminals | Responsibilities, role.json, atencao, aneis de uso, temas |
| https://www.themaestri.app/pt-br/docs/connections | Skill agente-agente, deteccao de turno, cross-workspace, agente-nota, agente-portal, cadeias |
| https://www.themaestri.app/pt-br/docs/routines | Prompts agendados + encadeamento && |
| https://www.themaestri.app/pt-br/docs/floors | Andares: CoW APFS, landing/merge, hooks + env vars |
| https://www.themaestri.app/pt-br/docs/partituras | Snapshots .maestripartitura, merge de responsabilidades, trust warning |
| https://www.themaestri.app/pt-br/docs/ombro | Companheiro on-device (Foundation Models) |
| https://www.themaestri.app/pt-br/docs/notes | Notas .md, lock, mermaid, cadeias |
| https://www.themaestri.app/pt-br/docs/ficharios | Binders/kanban de notas |
| https://www.themaestri.app/pt-br/docs/prompt-composer | Composer, @ mencoes, pills, drafts |
| https://www.themaestri.app/pt-br/docs/environments | Local/tmux/WSL/SSH/Docker/Sandbox/Custom, bridge :7433 |
| https://www.themaestri.app/pt-br/docs/chat | 7 threads/terminal, thread sobrevive restart, anexos |
| https://www.themaestri.app/pt-br/docs/workspaces | Workspace = projeto, CLAUDE.md/AGENTS.md sync, Spotlight |
| https://www.themaestri.app/pt-br/docs/wire | Protocolo Wire completo (pairing, roles, WS feed/stream) |
| https://www.themaestri.app/pt-br/remote | Maestri Remote iOS/iPad (TestFlight) |
| https://www.themaestri.app/pt-br/changelog | 0.45.x-0.48.x, cadencia, features novas |
| https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en | hands-on: prova do CLI maestri, roles, floors, Ombro |
| https://hunted.space/product/maestri/launches/maestri | lancamento PH: 2026-03-24, 177 upvotes, #8, quote do autor, $18 |
| https://www.producthunt.com/products/maestri | 403 no fetch direto; usado via mirror hunted.space |

Pesquisa complementar do subagente researcher transcrita em
`.devin/scratch/maestri-raw.md` (inclui lista completa de SOURCES e QUERIES).

---

# Parte B: nosso lado (leitura primaria)

Resumo exato do que cada arquivo de `skills/project-orchestrator/` faz hoje,
ancorado em paths e linhas. Leitura integral feita nesta sessao.

## B1. `skills/project-orchestrator/SKILL.md` (168 linhas)

- Identidade: orquestrador como Technical Program Manager que possui outcome,
  trilha documental e gates; subagentes especialistas possuem o trabalho
  (linhas 11-15). Barra de produto explicita: amazing/easy/convenient/
  beautiful/intuitive/fast/secure confirmada por gravacao de tela, nunca so
  testes verdes (14-15).
- "Compose the bundle; build no new runtime" - dispatch via `run_subagent`,
  estado inteiro em arquivos para sobreviver compaction (17-19).
- Iron rules (23-40): sem decisao de tecnologia antes do intake; prompt de
  delegacao e unico canal de input; handoffs so por artefatos em
  `.devin/handoffs/`; ledger append-only com Task Ledger + Progress Ledger;
  contexto fresco por delegacao + single-writer + lane por role; cap de 3
  subagentes com budget por fase; testes verdes nunca fecham fase (so gate de
  excelencia); orquestrador nunca escreve codigo de produto.
- Phase route (44-52): P0 analista condicional -> G0 visao -> G1 metodologia
  (RUP/Scrum/hibrido) -> G2 pesquisa+arquitetura (PRISMA-lite, ADRs, walking
  skeleton) -> G3 construcao (slices INVEST, MoSCoW+RICE, qa-ci por slice,
  excellence gate por RC) -> G4 transicao (testes, docs, semver, CI/CD, DORA,
  golden signals) -> G5 excelencia (gravacao do caminho real, frame a frame).
- Roles (57-68): role-matrix mapeia escopo -> papeis; roster seed = profiles do
  bundle (researcher, architect, implementer, reviewer, qa-ci, debugger,
  domain); papeis de produto sao contratos sobre `subagent_general`; cada role
  ativo ganha `workers/<role>/` com `role.md` charter + `.devin/` proprio
  (notes/ + adr/) para acumular conhecimento entre delegacoes; spawn so com
  gap real registrado.
- Delegation contract (70-86): arquivo preenchido em `.devin/handoffs/` antes
  de cada dispatch: objective, output, tools, boundaries (NOT-list),
  termination (turns/time/stop), verification VFs. Loop: contrato ->
  run_subagent -> handoff-doc -> verificacao contra VFs -> linha no Progress
  Ledger. Fix loops e breaker de 5 rounds vem de dispatching-parallel-agents.
- Research protocol (88-94): researcher por area; PRISMA-lite, queries
  logadas, lateral reading, verificacao de citacao (existencia + entailment),
  self-quiz de cobertura.
- Subconscious advisor (96-114): sessao `devin` peer via `computer-use`
  terminal.py; consulta antes de decisoes, apos ciclos, ao replanejar;
  contrato VERDICT/RATIONALE/RISKS/HYGIENE/MEMORY DELTA; estado em
  `.devin/advisor/`; higiene literal via `/clear` digitado; advisor pode pedir
  RESET_ORCHESTRATOR (chega como mensagem de usuario, quem confirma e o
  usuario); consultivo apenas (VERDICT nunca auto-executa; 1 consulta por
  decisao; debate cap 2; conta no fan-out budget). Fallbacks: resume-loop e
  `devin acp`.
- Isolation rules (116-123): lane branch/worktree por role em colisao de
  escrita; contexto fresco por delegacao; append-only ledgers; single-writer.
- Quality bar (125-130): Nielsen heuristics, budgets LCP/INP/CLS, convenience
  bar por feature (time-to-value, step count, required config).
- Excellence gate (132-141): gravacao de tela do caminho real via record.py,
  revisao frame a frame; falha volta para G3 como issues.
- Stop conditions (143-150): ambiguidade persistente, breaker em finding
  estrutural, excellence gate falha 2x, budget estourado, termination trip sem
  entrega, RESET_ORCHESTRATOR 2x numa fase.
- Cross-skills (159-168): grilling, dispatching-parallel-agents, afk-loop,
  executing-plans + gates + autonomous-gates, planning, spec-consistency.py,
  impeccable + a11y-audit, observability-quality + deploy, security,
  computer-use, finishing-a-development-branch.

## B2. `reference/` (4 arquivos)

- `methodology-selection.md` (48l): G1; decisao por Cynefin + regulacao +
  tamanho; regra tabular; saida `.devin/development-case.md`; sem SAFe/LeSS.
- `research-protocol.md` (54l): G2; PRISMA-lite (criteria/queries/coverage),
  claim mapping com existence+entailment, lateral reading para fontes
  criticas, self-quiz de cobertura antes de proposta de stack.
- `quality-gates.md` (62l): checklist Nielsen, budget de performance (LCP <=
  2.5s, INP <= 200ms, CLS <= 0.1), convenience bar por feature, procedimento
  do G5 (definir caminho -> gravar -> revisar frames -> julgar -> falhar vira
  issues), evidencia no Progress Ledger.
- `advisor-protocol.md` (125l): spawn via `terminal.py spawn` + TUI `devin`;
  consulta com marcador `CONSULT-<NN> END` e disciplina de TUI I/O; contrato de
  resposta; `.devin/advisor/` (charter, notes curadas, log, onboarding.md como
  payload de reset); observacao via `recv --tail` + meter de contexto do peer
  (~100k = gatilho); resets bidirecionais com regra de consentimento;
  fallbacks resume-loop (read-only, gratis) e `devin acp` (persistente, ~24k
  tokens baseline); limites e escalacao.

## B3. `templates/` (10 arquivos)

- `intake-vision.md` (53l): PR/FAQ, visao, stakeholders, JTBD, FRs/NFRs,
  convenience bar por feature, riscos iniciais, sucesso mensuravel, escopo.
  Zero tecnologia.
- `development-case.md` (34l): eixos Cynefin/regulacao/tamanho com evidencia;
  selecao justificada; tailoring de artefatos; regra de revisita.
- `role-matrix.md` (24l): escopo -> role -> profile existente? -> acao ->
  justificativa; checklist de spawn; anti-pattern "nao criar roles por
  variedade".
- `delegation-contract.md` (28l): ID, objective, profile, lane, inputs,
  output, tools, boundaries, termination, VFs; bloco Result com status
  DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED.
- `handoff-doc.md` (35l): inputs consumidos, outputs produzidos, decisoes,
  claims verificados, gaps, proxima acao.
- `ledger.md` (28l): Task Ledger (facts/plan/roster/advisor/deps/budget) +
  Progress Ledger (linha por gate/contrato com evidencia); append-only.
- `raid-register.md` (32l): riscos, premissas, issues, dependencias + mapa
  `Blocked by:` compativel com afk-loop.
- `adr.md` (30l): Nygard/MADR, sequencial por diretorio.
- `worker-role.md` (35l): charter com mandate, boundaries (owns/reads/never),
  base profile, DoD, standing context.
- `advisor-charter.md` (39l): mandato do subconsciente; may/may-not; formato de
  resposta.

## B4. Suporte e teste

- `USAGE.pt.md` (77l): guia PT; quando invocar; fases; artefatos; limites;
  secao advisor.
- `tests/validation/test_project_orchestrator.py` (151l): testes de contrato -
  frontmatter, existencia de templates/reference, vocabulario da phase route,
  mecanica de orquestracao, barra de qualidade, advisor codificado, sem
  em/en-dash.
- Design doc do advisor: `.devin/plans/2026-09-30-subconscious-orchestrator.
  design.md` (209l) - tabela de viabilidade verificada por tools, mapa
  pratica->mecanismo com fontes (lost-in-the-middle, context rot, evaluator,
  MemGPT, managed vs naive memory, Cognition multi-agents), protocolo de
  transporte TUI, higiene bidirecional, fallbacks.
- Ledger do advisor: `.devin/ledgers/subconscious-orchestrator.md` - gates G1-G7
  com evidencia.

## B5. Skills adjacentes (sistema de suporte)

| Skill | Papel no sistema | Path |
|---|---|---|
| dispatching-parallel-agents | fan-out, fix loops <=3 rounds resume, breaker 5, criterio de independencia, aviso 15x tokens | skills/dispatching-parallel-agents/SKILL.md (783l) |
| afk-loop | loop unattended sobre issues Markdown com DAG `Blocked by:` + worktrees + TDD | %APPDATA%/devin/skills/afk-loop/SKILL.md (95l) |
| autonomous-gates | tipos de gate (pre/step/integration/final/security), bounded output, no-change skip | %APPDATA%/devin/skills/autonomous-gates/SKILL.md (169l) |
| gates | iron law de verificacao, ledger de gates, VFs | %APPDATA%/devin/skills/gates/SKILL.md |
| executing-plans / execution | execucao atomica de plano, qa-ci anti-gaming independente | skills/execution/SKILL.md (94l) + %APPDATA%/.../executing-plans (76l) |
| context-hygiene | clear vs compact, folding RLM, cost guard, effort calibration | skills/context-hygiene/SKILL.md (116l) |
| memory-management | memoria cross-sessao gerenciada vs naiva, .devin/memory/ | skills/memory-management/SKILL.md (84l) |
| handoff | doc de continuacao para agente fresco | skills/handoff/SKILL.md (17l) |
| computer-use | terminal.py PTY spawn/send/recv/kill, record.py, bind --hwnd | skills/computer-use/SKILL.md (69l) -> extensions/computer-use/ |
| grilling | entrevista de analista (P0), perguntas assertivas + frontier rounds | skills/grilling/SKILL.md (230l) |

---

# Parte C: matriz de comparacao

Evidencia por celula: URL para Maestri; path:linha para o nosso lado.
"-n/a" = nao se aplica a natureza do produto.

| Dimensao | Maestri | project-orchestrator | Leitura |
|---|---|---|---|
| **Intake / especificacao** | Composer com @ mencoes; notas bloqueaveis como spec que agente le mas nao edita [docs/notes; docs/prompt-composer]. Sem metodologia de intake. | Entrevista de analista P0 (grilling) + intake-vision com JTBD/FR/NFR/convenience bar/sucesso mensuravel [SKILL.md:46-47; templates/intake-vision.md] + selecao de metodologia G1 [reference/methodology-selection.md] | Nosso: muito mais profundo (metodo formal). Maestri: "nota bloqueada" e um primitivo elegante que nao temos - spec imutavel para o worker (nos: fronteira e so convencao no contrato). |
| **Delegacao** | Peer-to-peer real: `maestri ask`, `ask --batch`, concurrent asks, ask-back chains, circular relays; qualquer agente pergunta a qualquer conectado [docs/connections; zenn.dev]. Maestro recruta/dispensa/reatribui dinamicamente [docs/maestro]. | Unico canal: orquestrador -> worker via contrato + `run_subagent` [SKILL.md:70-86; templates/delegation-contract.md]. Workers nao conversam entre si; advisor peer so existe para orquestrador [advisor-protocol.md]. | Gap real: Maestri tem mensageria worker<->worker e manager dinamico; nos roteamos tudo pelo orquestrador (decisao consciente: Cognition "dispersed decisions fragile" [design doc:39]). Adocao segura possivel: consulta peer bounded (ver plano). |
| **Isolamento** | Andares: clone CoW APFS instantaneo / branch no Windows; landing = git fetch + merge preview; hooks setup/run/teardown com env vars; ambientes por terminal (SSH/Docker/Sandbox/WSL/tmux) [docs/floors; docs/environments]. | Lane branch/worktree por role quando escrita colide [SKILL.md:34-35; git-workflows]; afk-loop usa worktree [afk-loop:26-31]. Sem hooks de ciclo de vida; sem ambientes remotos. | Gap: hooks de lane (setup/teardown automatico, ex.: instalar deps por lane) e merge-preview landing. Ambientes remotos provavelmente fora de escopo (YAGNI). |
| **Memoria / higiene de contexto** | Notas .md em disco lidas/escritas por agentes; cadeias de notas; ficharios; **thread record guardado pelo app e re-legivel pelo agente apos restart/compaction** [docs/chat]; partituras; CLAUDE.md/AGENTS.md por workspace. Sem curadoria de memoria documentada. | Ledgers append-only; handoffs; `.devin/advisor/` com MEMORY DELTA curatorial (add/update/archive) [advisor-protocol.md:48-56]; workers/<role>/.devin/notes; context-hygiene + memory-management com base empirica (naive -16-20pp). Resume-loop/ACP dao transcript persistence opt-in. | Convergencia forte (arquivos como memoria). Maestri na frente em: host-side transcript recall por default (nos: ACP opt-in, nao default) e templates compartilhaveis (partituras). Nos na frente em: semantica de curadoria e evidence-based hygiene. |
| **Gates de qualidade** | Nenhum formal documentado: aprovacao via permissao do harness (allowlist Bash(maestri:*)); attention dot + notificacao; Ombro sugere proximo passo [docs/terminals; docs/ombro; zenn.dev]. | G0-G5 phase route + quality-gates.md (Nielsen, CWV, convenience bar) + excellence gate por gravacao + qa-ci independente anti-gaming + VFs por contrato + stop conditions [SKILL.md:44-52,125-150; reference/quality-gates.md; execution/SKILL.md:53-62]. | Nosso diferencial maior. Maestri delega quality ao usuario/harness; nos temos verificacao contratual + verificador independente + gate de experiencia real. |
| **Papeis / team design** | Responsibilities: instrucoes nomeadas injetadas no start; role.json portatil + CLAUDE.md/AGENTS.md por subdir; discover/import; presets com aparencia; Maestro monta time sob demanda [docs/terminals; docs/maestro]. | Role matrix escopo->papel com justificativa de gap; worker-role charter (mandate/boundaries/DoD/standing context); workers/<role>/.devin/ acumula conhecimento; roster = profiles do bundle [SKILL.md:57-68; templates/role-matrix.md; templates/worker-role.md]. | Comparavel. Maestri na frente: portabilidade/descoberta de papeis (role.json viaja com o dir) e reatribuicao ao vivo preservando conexoes. Nos na frente: charter com boundaries explicitos + DoD + conhecimento acumulado por papel. |
| **Artefatos duraveis** | Notas .md, ficharios, partituras (.maestripartitura compartilhavel com revisao de import), .maestri workspaces, role.json, thread records [docs/notes; docs/partituras]. | vision.md, development-case, role-matrix, contracts, handoffs, ledgers, raid.md, ADRs, research files, advisor state, workers/.devin/ [SKILL.md + templates/]. | Nos: trilha documental de metodologia (RAID/ADR/PRISMA) mais rica. Gap: nada equivalente a Partitura - um pacote exportavel de time+layout reutilizavel entre projetos. |
| **UX / observabilidade** | O produto e a observabilidade: canvas espacial, attention dots, notificacoes, Ombro passivo proativo, aneis de uso de plano, Batuta search, app remoto iOS [docs/*]. | Ledger como superficie de verdade; advisor observa orquestrador via scrollback + context meter [advisor-protocol.md:69-72]; sem superficie de status para o usuario alem de ler arquivos. | Gap: nao temos renderizacao de estado para o usuario (somos CLI skill, nao app - n/a para canvas). Adaptavel: status compacto derivado de ledger + flags de atencao no handoff; gatilhos de consulta automatica ao advisor (Ombro e push, nosso advisor e pull-only). |
| **Escalacao ao humano** | Attention dot -> Ctrl+Shift+A -> notificacao; Maestro pode notificar; aprovacao remota via Remote/Wire; privilegio gated (so Maestro cria workspace/andar) [docs/terminals; docs/maestro; docs/wire]. | Stop conditions explicitos + ask_user_question no intake + consentimento de reset + breakers + budget approval [SKILL.md:143-150; advisor-protocol.md:88-95]. | Nos na frente em escalacao de decisao (condicoes explicitas). Maestri na frente em mecanica de atencao (sinal passivo, notificacao, aprovacao remota). |
| **Custo / budget** | Aneis de uso de plano por provider (mede quota, nao budget do enxame) [docs/terminals]. | Cap 3 subagentes + budget declarado por fase + termination por contrato + advisor conta no budget [SKILL.md:35-37; templates/ledger.md]. | Nos na frente: budget declarado e enforced como gate. Falta (ambos): registrar consumo real vs declarado por contrato. |
