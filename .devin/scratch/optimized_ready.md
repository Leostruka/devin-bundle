# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Principal Engineer (Agent Orchestration & RTS UX)

# Goal
Analisar as duas referências 'AgentCraft' (o mod Minecraft de blendi-remade e o orquestrador com interface RTS de getagentcraft.com, do idosal) e produzir análise comparativa + plano arquitetural para construir um orquestrador de agentes com UX de jogo RTS sobre o Devin CLI. O usuário prefere explicitamente a abordagem RTS. O resultado deve ser diretamente consumível pelo orchestrator deste bundle (skills leo / project-orchestrator), mapeando como uma camada RTS de visualização e comando se conecta ao runtime efêmero de subagentes, ledgers e issues locais já existentes.

# Context
Repositório devin-bundle: bundle de configuração do Devin CLI com skills (~/.config/devin/skills e .devin/skills), perfis de subagentes (run_subagent: leo, project-orchestrator, implementer, researcher, qa-ci etc.), extensions/ (wrappers headless: operate-godot, operate-spline, blender-operator, system-control), issue tracker local em .devin/scratch/ (Markdown), ledgers de gates em .devin/ledgers/, e roteamento de modelos via data/bundle-models.json. Runtime de subagentes é efêmero (sem A2A nativo; ver skill primeagent-reference). Não existe UI gráfica hoje: orquestração é via prompts/skills CLI. Referências externas: github.com/blendi-remade/agentcraft (Fabric mod Minecraft; Claude Agent SDK; foreman/sandbox/tools; task wall, decision podium, merge gate) e getagentcraft.com (npx @idosal/agentcraft; UI RTS single-pane; suporta Claude Code/Codex/OpenCode/Cursor; Docker/Apple Containers com isolamento; PWA remota + Telegram/Discord; Alliance Hall multiplayer). Verificar com tools (webfetch/web_search); não deduzir features.

# Acceptance Criteria
1. Feature matrix comparando as duas referências lado a lado (lifecycle de agentes, task board, fluxo de aprovação/decisão, isolamento, controle remoto, persistência) com fontes citadas.
2. Comparação explícita RTS vs Minecraft e justificativa da escolha RTS para este bundle.
3. Documento de arquitetura: componentes (UI RTS, camada de controle de agentes, transporte/eventos, persistência), integração com run_subagent, .devin/scratch, .devin/ledgers e bundle-models.json, e recomendação de stack (Godot headless? web/canvas? Electron?) com alternativas rejeitadas.
4. Gap analysis: o que o bundle já tem (dispatch, ledgers, triage labels, issue DAG) vs o que falta para uma UX RTS (event streaming, estado observável, comandos remotos).
5. Roadmap faseado MVP -> v1 com tickets/decisões rastreáveis e pontos de reuso para leo/project-orchestrator.
6. Artefatos salvos sob .devin/ (ex.: .devin/scratch/agentcraft-rts/); nada fora de .devin/ sem manifest.

# Scope & Non-Goals
- **IN SCOPE:** Análise das duas referências AgentCraft (repo, docs, site) com verificação via tools.
- **IN SCOPE:** Inventário dos pontos de extensão do Devin CLI/bundle relevantes (subagent dispatch, hooks, ledgers, scratch issues, extensions headless).
- **IN SCOPE:** Arquitetura proposta, trade-offs de stack, e roadmap faseado.
- **IN SCOPE:** Mapeamento de como o orchestrator existente consumiria a camada RTS.
- **OUT OF SCOPE:** Implementar código ou scaffolding de produto; somente análise e plano.
- **OUT OF SCOPE:** Commits, pushes, ou instalação de dependências.
- **OUT OF SCOPE:** Clonar a versão Minecraft; a referência principal é a RTS (getagentcraft.com).
- **OUT OF SCOPE:** Redesenhar skills existentes (leo, project-orchestrator); a camada RTS consome, não substitui.
- **OUT OF SCOPE:** Decisões de monetização/branding.

# Execution Hints & Checkpoints
1. **Fase 1:** Pesquisa: deep-dive nas duas referências (estrutura do repo, docs de integração do idosal, features reais vs marketing) + inventário dos hooks de lifecycle de subagentes, ledgers e scratch issues do bundle. **PARE e aguarde aprovação.**
2. **Fase 2:** Análise comparativa + gap analysis vs capacidades atuais do bundle.
3. **Fase 3:** Proposta de arquitetura (UI RTS, agent-control layer, transporte de eventos, persistência) + recomendação de stack com alternativas rejeitadas.
4. **Fase 4:** Roadmap MVP -> v1 em tickets + plano de integração com o orchestrator. **PARE e aguarde aprovação final.**
