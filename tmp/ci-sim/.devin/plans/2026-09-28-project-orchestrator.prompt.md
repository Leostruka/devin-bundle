# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Technical Program Manager / Staff Engineer

# Goal
Criar a skill `project-orchestrator` no bundle Devin: um orquestrador nível PO/Gerente de Projeto que conduz um projeto de pasta vazia até entrega e ciclo CI/CD, coordenando subagentes especialistas (uma pasta por papel, cada qual com .devin/ próprio acumulando conhecimento da área), produzindo a documentação completa da metodologia adequada ao escopo (RUP / Scrum / híbrido) e o MVP, com pesquisa profunda validada em cada área antes de qualquer decisão de tecnologia. Barra de qualidade explícita: o produto deve ser incrível, fácil, conveniente, belo, intuitivo, rápido e seguro para o usuário: excelência de ponta a ponta confirmada pelos olhos do usuário, não por testes passando. O gate de excelência grava a tela com a skill computer-use e revisa os frames (não apenas screenshots isolados) para capturar estados transitórios que ocorrem entre ações. Fundamento: pesquisa de 213 fontes primárias/renomadas (RUP IBM/Kruchten, Scrum Guide 2020, Anthropic multi-agent, Magentic-One, MetaGPT, IEEE 830/1016/42010, DORA, Lean/JTBD, Wineburg lateral reading, FEVER/SAFE).

# Context
Bundle Devin CLI em D:\Programing\ai_workspace\devin-bundle. Primitivas existentes a REUSAR (não recriar): run_subagent + profiles (researcher, implementer, qa-ci, reviewer, domain, architect, debugger), dispatching-parallel-agents (fan-out), afk-loop (DAG de issues locais), autonomous-gates/executing-plans (checkpoints), spec-consistency.py (SDD), .devin/ledgers/ (gates com evidência), .devin/adr/, skills/planning/modes/plan-doc.md, install.ps1 (exporta skills/ para %APPDATA%\devin\skills). Convenções duras: skills/<nome>/SKILL.md com front-matter válido; testes de contrato em tests/; pytest tests -q e audit.py 0 erros antes de commit; hooks são stdlib-only; sem em-dashes; sem assinaturas AI; Rules do AGENTS.md aplicam (verificar com tools, evidência reproduzível, held-out). Achados de pesquisa que o design DEVE incorporar: (1) contexto fresco por subagente: delegation prompt é o único canal de entrada (objetivo+formato de saída+tools+fronteiras, Anthropic); (2) ledgers duplos Task/Progress Ledger (Magentic-One); (3) handoff por artefatos estruturados > chat livre (MetaGPT SOPs); (4) isolation em 3 tiers: filesystem (branch/worktree lane), context (janela fresca), state (ledger append-only + transcripts); parallel reads ok, single-writer em arquivos compartilhados; (5) fan-out tem custo ~15x chat -> budget explícito por complexidade; diversidade de papéis > contagem de agentes; terminação explícita (max msgs/tokens/timeout); (6) falha dominante em MAS é coordenação, não modelo (MAST 14 modos); (7) pesquisa: protocolo PRISMA-lite (critérios declarados, queries logadas, mapeamento claim->fonte), leitura lateral (nunca avaliar fonte pelas próprias alegações), verificação de citações em 2 níveis (existência + entailment), self-quiz como auditoria de cobertura; (8) metodologia por complexidade: Cynefin/Stacey: domínio complexo -> agile, complicado -> expertise/boas práticas, estável/regulado -> preditivo; >50% dos projetos reais são híbridos (PMI); (9) RUP: Inception(LCO: Vision, business case, riscos, UC 10-20%) -> Elaboration(LCA: UC >=80%, SAD, protótipo executável, riscos maiores aposentados) -> Construction(IOC: feature-complete) -> Transition(PR: release); tailoring via Development Case (artefato que justifica inclusão/exclusão); (10) Scrum 2020: 3 accountabilities, Sprint<=1mês, eventos com timeboxes, artefatos com commitments (Product Goal/Sprint Goal/DoD); (11) discovery: PR/FAQ working-backwards primeiro, JTBD/job stories, VPC fit, MoSCoW+RICE, walking skeleton -> fatias verticais INVEST; (12) quality bars: Nielsen 10 heurísticas como critérios de aceite, CWV budgets (LCP<=2.5s, INP<=200ms, CLS<=0.1 @p75); (13) lifecycle: CI>=diário, trunk-based branches <48h, semver+changelog, DORA 4 keys, SRE golden signals pós-release; (14) TPM artifacts: dependency map, RAID register, decision log, RAG status por audiência; (15) persistência: notas de memória por papel -> destilação em SKILL.md (progressive disclosure).

# Acceptance Criteria
1. skills/project-orchestrator/SKILL.md válido (validate-skill-format passa) + templates: intake RUP-lite, matriz de papéis, delegation-contract, handoff-doc, ledger, risk register
2. Fase 0 (Inception): intake obrigatório antes de tecnologia: PR/FAQ ou Vision doc, stakeholders, JTBD/job stories, requisitos funcionais+não-funcionais, riscos iniciais, sucesso mensurável
3. Regra de seleção de metodologia explícita: complexidade Cynefin/Stacey + regulação + tamanho -> RUP completo / Scrum / híbrido, com Development-Case listando artefatos incluídos/excluídos e justificativa
4. Matriz de papéis: escopo -> papéis necessários -> workers/<role>/ com .devin/ por papel (notas de conhecimento + ADRs locais); papel novo só se gap real (diversidade > contagem)
5. Delegation contract obrigatório por subagente: objetivo, formato de saída, tools permitidas, fronteiras (o que NÃO fazer), critérios de parada explícitos
6. Protocolo de pesquisa: PRISMA-lite (fontes declaradas + exclusões justificadas), leitura lateral obrigatória para claims críticos, citações verificadas existência+entailment, self-quiz de cobertura antes de propor stack
7. Decisões arquiteturais em ADRs (Nygard/MADR) em .devin/adr/; handoffs entre papéis por artefatos estruturados, não chat livre
8. Ledgers: .devin/ledgers/<projeto>.md com Task Ledger (fatos/plano) + Progress Ledger (status por gate com evidência); RAID register e dependency map mantidos
9. Rota de ciclo de vida com gates: requisitos -> arquitetura/ADR -> walking skeleton -> fatias verticais (INVEST, priorizadas MoSCoW+RICE) -> testes -> docs -> release semver -> CI/CD + DORA + golden signals
10. Quality gates de produto: heurísticas Nielsen como checklist de aceite UX; performance budget (LCP<=2.5s, INP<=200ms, CLS<=0.1) quando aplicável
11. Gate de excelência pelos olhos do usuário: antes de fechar cada fase/release, o orquestrador percorre o caminho real do usuário GRAVANDO A TELA com a skill computer-use e revisando os frames capturados (não só screenshots entre ações: estados transitórios, glitches, feedbacks intermediários só aparecem em vídeo); avalia se a experiência é incrível, fácil, conveniente, bela, intuitiva, rápida e segura; testes verdes não bastam
12. Conveniência como requisito explícito: onboarding e uso medidos em esforço do usuário (tempo-para-valor, nº de passos, configuração necessária) com barra declarada por feature
13. Regras de isolamento codificadas: branch/worktree por papel quando writes colidem, contexto fresco por delegação, single-writer em arquivos compartilhados, fan-out budget por complexidade, terminação explícita
14. Testes de contrato novos em tests/ verdes + pytest tests -q 0 falhas + audit.py 0 erros

# Scope & Non-Goals
- **IN SCOPE:** skills/project-orchestrator/SKILL.md denso e completo (o prompt compilado é o spec)
- **IN SCOPE:** Templates de suporte: intake/vision, development-case (tailoring), matriz de papéis, delegation contract, handoff doc, RAID/dependency-map, ADR skeleton
- **IN SCOPE:** Mapeamento explícito para primitivas do bundle (profiles, gates, ledgers, afk-loop)
- **IN SCOPE:** Testes de contrato + validação de SKILL.md
- **IN SCOPE:** Docs de uso em PT
- **OUT OF SCOPE:** Novos mecanismos de subagente no runtime (usar run_subagent existente)
- **OUT OF SCOPE:** Sessões Devin CLI ou processos externos reais
- **OUT OF SCOPE:** Executar o orquestrador num projeto real nesta tarefa
- **OUT OF SCOPE:** Portar skills de terceiros verbatim
- **OUT OF SCOPE:** Mudar hooks/MCP/protocolos existentes
- **OUT OF SCOPE:** SAFe/LeSS ou scaling frameworks corporativos pesados

# Execution Hints & Checkpoints
1. **Fase 1:** Ler skills relacionadas do bundle (dispatching-parallel-agents, afk-loop, gates, executing-plans, researcher) e propor o design completo: estrutura do SKILL.md, matriz de papéis, fluxo de fases, contratos. PARE e aguarde aprovação.
2. **Fase 2:** Escrever SKILL.md + templates + testes de contrato.
3. **Fase 3:** pytest + audit.py verdes, contagens manifest/README se mudarem, commit e reportar com evidências.
