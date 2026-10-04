# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Staff Engineer - Agent Runtime / LLM Systems

# Goal
Melhoria geral do agente Devin CLI, inicialmente focada no Computer Use (CU): entender exatamente como o devin-cli recebe informacao, processa, pensa e age, e encontrar a forma mais viavel de o agente processar, pensar e agir de forma continua - o mais proximo possivel de tempo real. Para cada hipotese levantada, pesquisar validacao tecnica e evidencias (codigo do bundle, docs locais, fontes primarias externas). Testar na pratica, uma a uma, as hipoteses tecnicamente validas, com parametrizacao e metricas. Se nenhuma atingir o limiar satisfatorio, voltar ao levantamento de hipoteses.

# Context
Repo: bundle Devin CLI em D:\Programing\ai_workspace\devin-bundle. Branch nova feat/cu-realtime; commits = checkpoints por fase/hipotese. 'Tempo real' no contexto CU = latencia do ciclo perceber->decidir->agir->reperceber. Mecanismos candidatos existentes a verificar com ferramentas (nao deduzir): skills/computer-use (screenshot, screen recording com video + contact sheet, mouse/teclado, leitura de terminais), extensions/ (blender-operator = TCP exec loop persistente com bpy; spline-operator = bridge MCP ws://127.0.0.1:19692; system-control = sessoes persistentes + event streams + inventario de processos), hooks PreToolUse/UserPromptSubmit/SessionStart (constraint-pinning.py, architecture-gate.py), run_subagent is_background + <subagent_completion_notification>, get_output polling de shells. O binario devin-cli e fechado - 'vasculhar o proprio codigo' = bundle, extensions, skills, .devin/docs e %APPDATA%\devin\docs. Skills relevantes: primeagent-reference (harness design, A2A, Refine loop), computer-use, system-control, context-hygiene, gates. Anti reward-hacking: metrica e limiar de 'satisfatorio' definidos ANTES dos testes.

# Acceptance Criteria
1. Mapa verificado por ferramentas do ciclo do devin-cli (entrada do prompt -> tools/hooks -> raciocinio -> acao -> saida), citando arquivos/skills concretos; inclui o ciclo CU atual com baseline de latencia medido por iteracao
2. Tabela de hipoteses de tempo real: cada uma com evidencia tecnica (arquivo do bundle ou fonte primaria) e veredicto viavel/inviavel com motivo
3. Cada hipotese viavel testada na pratica, uma a uma, com parametrizacao e metricas registradas (latencia por ciclo, custo de tokens, taxa de acerto); resultados em doc/ledger rastreavel
4. Veredicto final: abordagem mais proxima de tempo real + parametros recomendados; OU retorno documentado a fase de hipoteses com aprendizados, se nenhuma atingir o limiar pre-definido
5. Branch feat/cu-realtime com um commit por checkpoint; nenhum checkpoint com estado quebrado; gates verdes ao final (validate-skill-format se SKILL.md mudar, pytest/audit se existirem)

# Scope & Non-Goals
- **IN SCOPE:** Pesquisa com evidencias: bundle, extensions, skills, docs locais, fontes primarias externas
- **IN SCOPE:** Prototipos/testes de hipoteses dentro do bundle (extensions, hooks, skills, scripts em .devin/)
- **IN SCOPE:** Medicao e parametrizacao do ciclo CU (screenshot->acao->screenshot e alternativas)
- **IN SCOPE:** Commits checkpoint na branch feat/cu-realtime
- **OUT OF SCOPE:** Modificar o binario devin-cli ou exigir features inexistentes do runtime fechado
- **OUT OF SCOPE:** Modelos pagos (parent free: apenas swe-2-medium/max)
- **OUT OF SCOPE:** Deploy em producao ou mudancas irreversiveis no ambiente do usuario
- **OUT OF SCOPE:** Reescrever skills/extensions existentes sem design aprovado

# Execution Hints & Checkpoints
1. **Fase 1:** Mapear com ferramentas o ciclo devin-cli (prompt -> tools/hooks -> acao) e o ciclo CU atual, medindo baseline de latencia por iteracao; levantar hipoteses de tempo real, cada uma com evidencia tecnica e veredicto de viabilidade; definir metrica e limiar de 'satisfatorio' ANTES dos testes. Commit checkpoint. PARE e aguarde aprovacao.
2. **Fase 2:** Testar as hipoteses viaveis uma a uma, com parametrizacao; registrar metricas por hipotese; um commit checkpoint por hipotese testada.
3. **Fase 3:** Avaliar resultados contra o limiar: se nenhuma satisfatoria, voltar a Fase 1 incorporando os aprendizados; senao, documentar veredicto + parametros + recomendacao. Gates verdes, commit final e reporte com evidencias.
