# maestri-raw.md - dump bruto do subagente researcher (df2e6bed)

Gerado por researcher background agent em 2026-09-30. O subagente nao tinha
ferramenta de escrita; conteudo transcrito do retorno. Claims-chave foram
re-verificados pelo orquestrador antes de entrar no dossier
(.devin/research/maestri.md): mecanismo `maestri ask` verificado em
zenn.dev; dados de lancamento PH verificados em hunted.space; itens nao
re-verificados permanecem marcados NAO VERIFICADO.

```markdown
# Dossier: Maestri (themaestri.app)

Pesquisa de fontes publicas. Metodo: web_search (nao havia webfetch disponivel neste ambiente; os snippets de busca retornaram trechos longos das paginas, citados abaixo). Tudo sem citacao direta esta marcado como NAO VERIFICADO.

## Status legenda
- CONFIRMADO: trecho de fonte publica citado
- NAO VERIFICADO: afirmacao plausivel sem fonte primaria lida
- AUSENTE: buscado, nada encontrado

## 1. O que e / posicionamento / usuario alvo

CONFIRMADO:
- "Meet Maestri, the first infinite canvas made for orchestrating agents. Every agent gets a role, they talk to each other directly, and the whole operation stays in front of you." [fonte: https://www.themaestri.app/en]
- "Maestri is not an AI agent itself. It's the canvas and orchestration layer that sits around your agents. It expects you to have coding agents like Claude Code, Codex, or OpenCode already installed." [fonte: https://themaestri.app/en/docs/intro]
- App nativo macOS (Swift/SwiftUI/Metal, sem Electron/web views); versao Windows existe hoje: homepage tem link "Go to Maestri for Windows" e docs dizem "Maestri runs on macOS and Windows". [fonte: https://themaestri.app/ , https://themaestri.app/en/docs/intro]
- Requisito Mac: "Free. macOS 15.4+ required."; Apple Silicon mencionado em listagens. [fonte: https://themaestri.app/ , https://www.macaiapps.com/apps/maestri/]
- Usuario alvo: devs rodando varios coding agents em paralelo ("developers juggling multiple projects"). [fonte: https://themaestri.app/]
- Posicionamento explicito do autor: "It's not about replacing IDEs, it's about having a workspace layer on top where you orchestrate the work." [fonte: https://www.producthunt.com/products/maestri]

## 2. Paradigma de orquestracao

CONFIRMADO:
- Modelo espacial: canvas infinito onde cada terminal e um no; agentes sao CLIs reais (Claude Code, Codex, OpenCode, Gemini, shell puro) rodando em PTYs. "they talk to each other through PTY. No API glue, no middleware. Just one agent typing into another's terminal." [fonte: https://www.themaestri.app/en]
- Coordenacao e hibrida: (a) usuario conecta terminais com linhas no canvas; (b) agentes conversam via CLI `maestri` injetada como skill ("Maestri Agent Skill" instalada automaticamente ao conectar dois terminais; `maestri list`, `maestri ask "Nome" "prompt"`, resposta volta ao contexto do agente que perguntou). [fonte: https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en]
- Hierarquia opcional via Maestro Mode: um terminal promovido a "manager" ganha a skill `/maestri-manager` e pode recrutar, conectar, mudar roles e dispensar recrutas. [fonte: https://themaestri.app/en/docs/maestro]
- Padroes de mensageria suportados: "Concurrent asks, ask-back chains, and circular relays between agents"; `maestri ask --batch` para requests paralelos. [fonte: https://www.themaestri.app/en/changelog]
- Conexoes cross-workspace: "Wire an agent to one that lives in another workspace... address it as 'Name @ Workspace'." [fonte: https://www.themaestri.app/en/changelog]
- Nao e pipeline declarativo: topologia e espacial/visual + delegacao em runtime via prompts entre agentes.

## 3. Roles / personas nomeadas

CONFIRMADO:
- Roles embutidos citados nos docs: Lead ("coordinator that delegates"), Coder, Reviewer, Tester. [fonte: https://themaestri.app/en/docs/terminals]
- Roles sao customizaveis: "name, a color badge, and a set of instructions", gerenciados em Settings -> Agents, atribuidos na criacao do terminal ou via right-click. [fonte: https://themaestri.app/en/docs/terminals]
- Implementacao: agente inicia em subdiretorio do projeto com `CLAUDE.md`/`AGENTS.md` proprios + sidecar `role.json` (nome, cor, prompt) que viaja com o diretorio; botao "Discover Roles" importa `role.json` de pastas `.maestri`. [fonte: https://themaestri.app/en/docs/terminals]
- Maestro e um modo por terminal (checkbox), nao um role comum: "Maestro Mode promotes a terminal from a regular agent into a manager". [fonte: https://themaestri.app/en/docs/maestro]
- Ombro: companion on-device (Apple Foundation Models) que vigia agentes, resume o que aconteceu e sugere proximos passos; requer macOS 26+. [fonte: https://themaestri.app/ , https://www.themaestri.app/en/privacy]
- Exemplo de uso real: departamento de vendas com 8 agentes (CRO, VP, RevOps, BDR, SDR, Sales Engineer, Closer, Partner) - depoimento de usuario no site. [fonte: https://www.themaestri.app/en]

## 4. Memoria e contexto

CONFIRMADO:
- Notes = arquivos markdown reais em disco, pinados no canvas; agentes conectados leem e escrevem neles ("shared source of truth"); multiplos agentes na mesma nota = memoria compartilhada persistente entre sessoes e harnesses. [fonte: https://themaestri.app/en/docs/maestro , https://www.producthunt.com/products/maestri , https://somi.ai/products/maestri]
- Workspace lembra layout, posicoes de terminais, agentes e settings. [fonte: https://themaestri.app/en/docs/workspaces]
- `CLAUDE.md`/`AGENTS.md` por workspace com opcao de sync automatico entre os dois. [fonte: https://themaestri.app/en/docs/workspaces]
- Chat face por terminal: "every conversation survives a relaunch and travels with the terminal", 7 threads coloridos por terminal. [fonte: https://www.themaestri.app/en/changelog]
- Partitura: snapshot/template de um canto do canvas (agentes+roles+notas+portais+conexoes) reinstanciavel em qualquer floor/workspace. [fonte: https://themaestri.app/]
- Persistencia local: "Configuration is plain JSON, notes are Markdown files. Nothing is uploaded." [fonte: https://themaestri.app/]
- Handoff de contexto: notas conectadas + mentions com @ no composer apontando para terminal/nota/portal; screenshots colados direto. [fonte: https://www.themaestri.app/en]

## 5. Mecanicas de delegacao

CONFIRMADO:
- Humano -> agente: Prompt Composer (Cmd+Shift+P) com @-mentions de agentes, notas, portais e floors. [fonte: https://www.themaestri.app/en/changelog , https://www.themaestri.app/en]
- Agente -> agente: CLI `maestri` (skill instalada ao conectar). Comandos vistos: `maestri list`, `maestri ask`, `maestri ask --batch`, `maestri routine` (agendar comandos/lembretes por workspace), `maestri floor land`, `maestri floor delete`, `maestri portal resize`. [fonte: https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en , https://www.themaestri.app/en/changelog]
- Maestro -> time: Recruit (spawn de terminal conectado, flag `--floor`), Connect (ligar recruta a notas), reassign de roles/prompts (processo reinicia, posicao e conexoes preservadas), Dismiss, flag `--replace`. Recrutar em outro workspace tambem e possivel. [fonte: https://themaestri.app/en/docs/maestro , https://www.themaestri.app/en/changelog]
- Delegacao funciona entre harnesses heterogeneos: "works across all CLIs because it operates at a terminal level" (resposta do autor no PH). [fonte: https://www.producthunt.com/products/maestri]

## 6. UX / superficie

CONFIRMADO:
- App desktop nativo (macOS 15.4+ Apple Silicon; versao Windows existe). Canvas infinito com engine propria "MaestriCanvas" em Metal; terminal emulator proprio em Swift. [fonte: https://themaestri.app/ , https://www.macaiapps.com/apps/maestri/ , https://hunted.space/product/maestri/launches/maestri]
- Elementos do canvas: Terminal, Connection (cabos com fisica animada), Note (markdown), File Tree, sketches/desenho a mao livre, Portals (browser, iOS Simulator, Android emulator, telefone fisico via USB; agente clica/digita lendo a element tree real). [fonte: https://themaestri.app/en/docs/intro , https://www.themaestri.app/en]
- Floors: copia isolada do workspace inteiro ("New branch, new terminals, zero interference"), com git-isolated working tree, land/delete via agente ou UI, hooks configuraveis. [fonte: https://www.themaestri.app/en , https://www.themaestri.app/en/changelog]
- Chat face por terminal com threads; Batuta Search (Cmd+P) busca em chats/terminais/notas/portais entre workspaces e floors. [fonte: https://www.themaestri.app/en/changelog , https://www.themaestri.app/pt-br/changelog]
- Maestri Remote: app iPhone/iPad (TestFlight em review) sobre protocolo "Wire" (beta): parear via QR/senha, read-only ou controle total, revogavel; expoe git menu, file tree, floors, chat ao vivo. [fonte: https://www.themaestri.app/en/changelog]
- Runtimes remotos: SSH, Docker, Sandbox, Custom Runtime, Local (tmux) para sessoes persistentes. [fonte: https://www.themaestri.app/en/changelog]
- Navegacao estilo tmux: Ctrl+setas entre workspaces, Ctrl+<n> foca terminal, badges numericos. [fonte: https://themaestri.app/en/docs/terminals , https://themaestri.app/en/docs/workspaces]
- Anéis de uso de plano (quota restante) para Claude, Codex e Antigravity com reset times. [fonte: https://www.themaestri.app/en/changelog]

## 7. Quality gates / aprovacoes / escalacao humana

CONFIRMADO:
- Attention dot vermelho quando terminal para de produzir output (agente esperando decisao ou fim de turno); Ctrl+Shift+A cicla entre terminais que pedem atencao; banner de sistema via Settings -> Notifications. [fonte: https://themaestri.app/en/docs/terminals]
- Maestro pode mandar notificacao de sistema para chamar o humano. [fonte: https://themaestri.app/en/docs/maestro]
- Gating de privilegio: "a regular agent can't create workspaces or floors on its own - only a Maestro (or you) can." [fonte: https://themaestri.app/en/docs/maestro]
- Wire permite parear dispositivo read-only vs full control, revogavel. [fonte: https://www.themaestri.app/en/changelog]
- Permissao de execucao do CLI `maestri` e feita pelo harness do agente (ex.: allowlist `Bash(maestri:*)` no Claude Code), nao por camada propria de aprovacao. [fonte: https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en]
- NAO VERIFICADO: existencia de gates formais de aprovacao de diffs/PRs dentro do Maestri. Floors tem "hooks" configuraveis (tipo de hook nao detalhado nas fontes). [fonte: https://www.themaestri.app/en/changelog]

## 8. Integracoes

CONFIRMADO:
- Agentes/harnesses: Claude Code, Codex, OpenCode, shell puro; Gemini e Antigravity citados (PH: "Gemini delegates to OpenCode"; changelog: aneis de plano para "Claude, Codex and Antigravity"); Grok usado por usuario em blog. [fonte: https://www.producthunt.com/products/maestri , https://www.themaestri.app/en/changelog , https://ranimontagna.com/en/blog/do-terminal-ao-cockpit-orca-superset-maestri]
- Editores: abre diretorio do workspace em VS Code, Zed, Xcode. [fonte: https://www.macaiapps.com/apps/maestri/ , https://themaestri.app/en/docs/workspaces]
- Git: floors = copias git-isoladas com branch picker, land, hooks; file tree com git menu (changes, diffs, commit, push, branches, stash) via Maestri Remote. [fonte: https://www.themaestri.app/en/changelog]
- Sistema: Spotlight indexing (macOS), notificacoes nativas, Apple Intelligence/Foundation Models (Ombro). [fonte: https://themaestri.app/en/docs/workspaces , https://www.themaestri.app/en/privacy]
- Dispositivos: iOS Simulator, Android emulator, telefone fisico via USB como Portals. [fonte: https://www.themaestri.app/en]
- Rede: `maestri` CLI exposto a agentes via skill; `$MAESTRI_CLI` aponta para binario em path temporario. [fonte: https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en]
- AUSENTE: nenhuma evidencia de suporte MCP first-party, nem integracao nativa com issue trackers (Linear/Jira/GitHub Issues). Queries: "Maestri macOS MCP git worktree floors remote SSH Docker runtime", "themaestri.app docs connections maestri ask". (O protocolo Wire cobre controle remoto, nao MCP.)

## 9. Precos

CONFIRMADO:
- Free: $0 forever: 1 workspace, unlimited agents, infinite canvas, sketching, sticky notes, agent connections, connected notes, Ombro, "All features included". [fonte: https://themaestri.app/]
- Pro: $18 one-time payment: unlimited workspaces, workspace navigation shortcuts, uso em ate 2 Macs; "7 days free, then pay once". [fonte: https://themaestri.app/]
- Autor no PH: "1 workspace free. $18 lifetime for Pro." [fonte: https://www.producthunt.com/products/maestri]
- Agentes sao BYO: pagos separadamente via subscriptions/API dos providers. [fonte: https://somi.ai/products/maestri]
- Sem conta nem telemetria: "Download it and start working. Maestri never asks who you are."; rede apenas para ativacao de licenca e update checks. [fonte: https://themaestri.app/ , https://www.themaestri.app/en/privacy]

## 10. Sinais da empresa

CONFIRMADO:
- Empresa: Evercraft Labs (privacy policy: "Maestri, by Evercraft Labs", hello@themaestri.app, bugs@themaestri.app; "developed in Brazil"). Atencao: existe outra "Evercraft Labs" australiana (evercraftlabs.com) sem relacao. [fonte: https://www.themaestri.app/en/privacy , https://www.linkedin.com/in/shannon-bartjes-15799214a]
- Fundador: Evert Junior, solo dev, Brasilia DF; X @evertjr ("Senior Front-end Developer | Generative AI expert - Building Maestri"); GitHub evertjr (14 repos publicos). [fonte: https://tweetlook.com/evertjr , https://github.com/evertjr]
- Lancamento PH: 24/03/2026, 177 upvotes, 18 comentarios, #8 do dia; tags Mac, Developer Tools, AI. [fonte: https://hunted.space/product/maestri/launches/maestri , https://hunted.space/dashboard/maestri/launches/maestri]
- Docs em /en/docs (intro, workspaces, terminals, maestro) e changelog versionado em /en/changelog (ultima versao vista: 0.47.0); site em en e pt-br. [fonte: https://themaestri.app/en/docs/intro , https://www.themaestri.app/en/changelog , https://www.themaestri.app/pt-br/changelog]
- Comunidade: Discord oficial citado nos docs e changelog. [fonte: https://themaestri.app/en/docs/intro , https://www.themaestri.app/en/changelog]
- Reviews/mentions: Product Hunt (reviews positivos), somi.ai, macaiapps.com, makerstack.co (7.9/10), coding4food.com, zenn.dev (hands-on tecnico), fyve.co.jp, flowtune-media.com, clauday.com, LinkedIn posts em pt-br de usuarios. [fontes: URLs na secao SOURCES]
- Versao atual aproximada: 0.47.x (changelog top = 0.47.0; listagem 3rd party mostra 0.47.1). [fonte: https://www.themaestri.app/en/changelog , https://cmacked.com/app/maestri/]
- AUSENTE: canal YouTube oficial, pagina LinkedIn da empresa brasileira, presenca em HN/Reddit (buscas retornaram so produtos homonimos: Mastra, "Maestro App Factory", "Maestro" Electron app). Queries na secao QUERIES.
- NAO VERIFICADO: data de lancamento pre-PH (privacy policy ja existia em 26/02/2026), receita, numero de usuarios, roadmap publico.

## Comparativo rapido vs skill interna de orquestracao
- Maestri = camada de workspace/orquestracao visual para CLIs existentes; nao define workflows declarativos nem gates de qualidade proprios; delegacao e feita pelos proprios agentes via `maestri ask` + notas markdown compartilhadas. Equivalente conceitual: "tmux espacial + skill de mensageria injetada + roles como CLAUDE.md por subdir + manager agent opcional".

## SOURCES
- https://themaestri.app/ : homepage; features, pricing, Windows link, requisitos macOS 15.4+.
- https://www.themaestri.app/en : homepage EN; PTY orchestration, roles, portals, composer, partitura, floors, Ombro, depoimentos X de usuarios.
- https://themaestri.app/en/docs/intro : posicionamento ("not an AI agent"), conceitos core, "runs on macOS and Windows", Discord.
- https://themaestri.app/en/docs/terminals : criacao de terminais, roles (Lead/Coder/Reviewer/Tester), role.json, Discover Roles, attention dot, notificacoes, atalhos.
- https://themaestri.app/en/docs/maestro : Maestro Mode (manager skill, Recruit/Connect/Reassign/Dismiss, --floor, --replace, workspaces/floors gated), notificacao ao humano.
- https://themaestri.app/en/docs/workspaces : persistencia de workspace, CLAUDE.md/AGENTS.md sync, import .maestri, Folders/Groups, Spotlight, atalhos.
- https://www.themaestri.app/en/changelog : chat face + threads, cross-workspace connections, Wire/Remote, runtimes SSH/Docker/Sandbox/tmux, routines, ask --batch, floor land/delete, portal resize, plan rings, Batuta Search, versao 0.47.0.
- https://www.themaestri.app/pt-br/changelog : confirmacao do changelog em pt-br.
- https://www.themaestri.app/en/privacy : Evercraft Labs, dados 100% locais, Ombro on-device, contatos.
- https://www.producthunt.com/products/maestri : tagline, blurb, comentarios do autor e usuarios.
- https://hunted.space/product/maestri/launches/maestri : data lancamento PH (24/03/2026), quote completo do maker.
- https://hunted.space/dashboard/maestri/launches/maestri : 177 upvotes, #8 daily.
- https://hunted.space/hunter/evertjr : perfil PH do fundador.
- https://somi.ai/products/maestri : FAQ independente (precos, macOS-only na epoca, PTY, Ombro).
- https://www.macaiapps.com/apps/maestri/ : stack (Swift/SwiftUI/AppKit/Metal), integracoes VS Code/Zed/Xcode.
- https://makerstack.co/reviews/maestri-review/ : review 7.9/10, preco, stack, privacidade.
- https://coding4food.com/en/post/maestri-mac-app-ai-terminal-canvas-english : review independente.
- https://zenn.dev/youjinfox/articles/bb3facc650adb1?locale=en : hands-on com prova do CLI (`Skill(maestri)`, `maestri list/ask`, $MAESTRI_CLI, permissoes Bash(maestri:*)).
- https://ranimontagna.com/en/blog/do-terminal-ao-cockpit-orca-superset-maestri : uso real com Codex orchestrator + Grok executor via `maestri ask`.
- https://tweetlook.com/evertjr : perfil X do fundador.
- https://github.com/evertjr : GitHub do fundador.
- https://pt.linkedin.com/posts/thiagogriao_... : post LinkedIn de usuario (pt-br).
- https://pt.linkedin.com/posts/deivcst_... : post LinkedIn de usuario (pt-br).
- https://fyve.co.jp/claude-code/articles/maestri-ai-agent-canvas-guide : guia japones, instalacao .dmg.
- https://clauday.com/article/1267c13c-8e58-4259-b7f3-cc316570f3a6 : resumo editorial.
- https://www.productcool.com/product/maestri : perfil do produto.
- https://super-launch.app/product/maestri : perfil do produto.
- https://cmacked.com/app/maestri/ : versao 0.47.1 (site de pirataria; usado so como sinal de versao).
- https://www.producthunt.com/products/maestri/alternatives : lista de alternativas (Claude Code, agent-manager, Warp, cmux, ClawTab).
- https://ai-explorer.io/en/tools/maestri : listagem (diz macOS 26.2+; conflita com 15.4+ do site - site oficial prevalece).

## QUERIES
- "themaestri.app Maestri AI agents orchestration"
- "\"Maestri\" agent orchestration AI product"
- "themaestri.app docs connections agents PTY orchestration"
- "themaestri.app docs floors notes portals Ombro"
- "Maestri app macOS pricing Pro lifetime Evert founder"
- "Maestri infinite canvas Product Hunt launch"
- "themaestri.app docs connections notes \"floors\" OR \"portals\" OR \"remote\""
- "\"evertjr\" OR \"Evert Junior\" Maestri Evercraft Labs Twitter LinkedIn"
- "Maestri app YouTube demo video canvas agents"
- "Maestri macOS MCP git worktree floors remote SSH Docker runtime"
- "Maestri themaestri Windows version download"
- "themaestri.app/en/docs connections OR notes OR floors OR portals"
- "Maestri canvas agents reddit OR \"hacker news\" review"
- "themaestri.app \"docs\" quickstart connections notes chat routines shortcuts"
- "\"themaestri.app\" pt-br Maestri canvas orquestrar agentes"
- "themaestri.app docs \"connections\" \"maestri ask\" agent skill CLI"
- "\"Evercraft Labs\" OR \"themaestri\" discord linkedin changelog first release"
```
