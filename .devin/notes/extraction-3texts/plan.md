# Plano de implementação — pontos extraídos de `improvements.md`

## Objetivo

Transformar as propostas do `.devin/notes/extraction-3texts/improvements.md` em alterações concretas no bundle, começando pela correção do processo de melhoria contínua e depois aplicando as melhorias em `leo`, `AGENTS.md`, skills existentes e novas.

## Escopo

- Revisar e endurecer `skills/continuous-improvement/SKILL.md` para que siga o workflow exigente (evidência, fontes, `qa-ci`, `unlazy`, held-out).
- Atualizar `skills/leo/SKILL.md` para refletir os novos gates (segurança, intenção, tamanho, TDD, MCP, dev container, validação ontológica).
- Atualizar `AGENTS.md` / `global_rules.md` e o template `agents.md` de projeto.
- Fortalecer skills existentes (`security-audit`, `tdd`, `setup-pre-commit`, `planning-pipeline`, `grilling`, `api-design`, `cost-optimization`, `context-window-hygiene`, `docker`, `mcp-context-audit`, `verification-before-completion`, `using-skills`, `implement`, `code-review`, `project-memory`, `effort-calibration`, `model-interface-preflight`).
- Criar novas skills/gates (`ontology-validator`, `task-sizer`, `secure-defaults-check`, `agent-cost-guard`, `intention-capture`, `api-context-spec`).
- Melhorar `structured-knowledge-extraction` com camada semântica/ontológica mínima.

## Fora de escopo (por enquanto)

- Push/commit sem autorização explícita.
- Quebra forçada de tarefas em PRs menores que 300 linhas quando a mudança for naturalmente pequena.
- Integração real com Code Rabbit ou GitHub Marketplace (a skill pode apenas documentar o hook esperado).

---

## Fase 0 — Corrigir o processo de melhoria contínua

**Por que primeiro:** a Fase 0 é o meta-processo. Se a skill que governa as demais melhorias estiver frouxa, as outras fases vão sair sem evidência e sem fontes.

### Tarefa 0.1 — Revisar `skills/continuous-improvement/SKILL.md`

**O que fazer:**
1. Ler `skills/continuous-improvement/SKILL.md`, `AGENTS.md` regras 15-17, `skills/leo/SKILL.md` (QA/CI), `skills/unlazy/SKILL.md` e `skills/verification-before-completion/SKILL.md`.
2. Comparar cada passo do loop de 10 passos contra as regras exigentes.
3. Levantar lacunas concretas e reproduzíveis.

**Lacunas conhecidas / suspeitas:**
- A skill pede `unlazy` "no início", mas não exige que **cada** Passo 1-10 tenha um gate ledger com `EVIDENCE: pending` antes de avançar.
- A skill não exige explicitamente um subagente `qa-ci` independente por passo; embora tenha `subagent: true`, o agente é `implementer`, não `qa-ci`.
- A FASE 0 exige fontes, mas não diz como verificar se uma fonte é confiável além de "verificar domínio, autores, data".
- O formato de saída é extenso; em contextos longos, o meio pode ser perdido (lost-in-the-middle).
- Não há referência explícita a `verification-before-completion` como gate final.

**Entregável:**
- Documento `.devin/notes/extraction-3texts/continuous-improvement-review.md` com lacunas e propostas de correção.

**Gate:**
- `python audit.py` passa sem erros após as mudanças na skill.
- `python -m pytest -q` 260/260.

### Tarefa 0.2 — Endurecer `skills/continuous-improvement/SKILL.md`

**O que fazer:**
1. Adicionar a cada passo do loop a exigência de gate `unlazy` (`gate:` / `expect:` / `evidence:`).
2. Trocar/expandir o subagente para `qa-ci` em passos não-triviais (verificação independente, sem ferramentas de escrita).
3. Exigir `verification-before-completion` antes de declarar a melhoria pronta.
4. Exigir que toda fonte citada tenha URL, autor, data e citação verificada; rejeitar blogs sem fonte primária.
5. Resumir o formato de saída e apontar para `.devin/ledgers/<melhoria>.md` para detalhes, evitando bloat no chat.

**Arquivos:**
- `skills/continuous-improvement/SKILL.md`
- `.devin/ledgers/continuous-improvement-fix.md` (ledger `unlazy`)

**Gate:**
- `python -m pytest tests/validation/test_skill_format_passes.py tests/validation/test_audit_passes.py -v` passa.
- Revisar diff com `git diff` e confirmar que não há AI signatures.

---

## Fase 1 — Regras e setup de projeto

### Tarefa 1.1 — Atualizar `AGENTS.md` / `global_rules.md`

**O que fazer:**
Adicionar regras não-pinned ou fortalecer existentes com base nas fontes:
1. Menor código possível; rejeitar token maxing/overengineering.
2. Sanitizar inputs de usuário; nunca logar/outputar secrets.
3. Não comitar secrets; se detectado, rotacionar.
4. Não deletar testes sem aprovação explícita.
5. Ações destrutivas precisam de confirmação.
6. Endpoints e S3 públicos precisam de justificativa documentada.
7. Sempre declarar intenção e impacto no usuário antes de codar.

**Arquivos:**
- `AGENTS.md`
- `global_rules.md` (se necessário)

**Gate:**
- `python scripts/validate-skill-format.py`? (não é skill; teste com `python audit.py`)
- `python -m pytest tests/held-out/behavioral/test_rule7_opinion_silent.py tests/held-out/behavioral/test_rule17_verify_with_tools.py -v` passa.

### Tarefa 1.2 — Criar template `agents.md` de projeto

**O que fazer:**
1. Criar/expandir `skills/project-setup` ou `skills/writing-for-agents` para gerar um `agents.md` de projeto com:
   - Pense antes de codar.
   - Declare presunções; pergunte em vez de adivinhar.
   - Menor código possível.
   - Testes verificam intenção.
   - Regras de stack (ex.: TypeScript sem `any`, rodar linters).
   - Não deletar testes sem aprovação.
   - Tamanho de tarefa (PR ~300 linhas, quebrar se >500).

**Arquivos:**
- `skills/project-setup/SKILL.md`
- `skills/writing-for-agents/SKILL.md` (ou novo template)
- `tests/...` se aplicável

**Gate:**
- Rodar `project-setup` em um projeto teste e verificar que `agents.md` é gerado.

---

## Fase 2 — `leo` / fluxos principais

### Tarefa 2.1 — Atualizar o situation router de `leo`

**O que fazer:**
1. Inserir `security-audit` como gate obrigatório no fluxo Build/Change quando tocar API, DB, secrets, endpoints, infra.
2. Roteamento padrão: issue/task -> `grilling` (intenção) -> `planning-pipeline` (PRD + tickets) -> `implement` + `tdd` -> `code-review` -> `verification-before-completion`.
3. `grilling` deve capturar objetivo final, onde a feature vai e impacto no usuário.
4. `planning-pipeline` deve estimar tamanho de PR e quebrar >500 linhas.
5. `tdd` passa a ser passo padrão, não opcional.
6. `setup-pre-commit` como passo de `project-setup` e build flow.
7. `docker`/`dev container` recomendado para tarefas destrutivas.
8. Paralelismo limitado a 1-3 agentes; alertar se >3.

**Arquivos:**
- `skills/leo/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_leo_orchestrator.py -v` passa.
- `python audit.py` sem erros.

### Tarefa 2.2 — Adicionar gate ontológico/Pydantic no loop de ferramentas

**O que fazer:**
1. Em `leo`, após execução de ferramentas críticas, exigir validação:
   - Pydantic para tipos.
   - Ontologia/razoabilidade para resultado.
   - Side effects só após validação.
2. Se resultado não for razoável, voltar ao LLM ou humano.

**Arquivos:**
- `skills/leo/SKILL.md`
- (depende da nova skill `ontology-validator` da Fase 5)

**Gate:**
- Teste de orquestração simulado passa.

---

## Fase 3 — Fortalecer skills existentes

### Tarefa 3.1 — `security-audit`

**O que fazer:**
Adicionar checklist dos 5 princípios do `sec-needs.md`:
1. Superfície: código, inputs, outputs, endpoints, logs, tempo de resposta.
2. Menor privilégio: permissões de serviços, usuários, acesso ao banco/VPC.
3. Defaults seguros: senha oculta, confirmação em destruição, 2FA.
4. Criptografia: dados sensíveis, hash padrão, nada caseiro.
5. Updates: Dependabot, SAST (SonarQube), WAF.

**Arquivos:**
- `skills/security-audit/SKILL.md`
- `scripts/scan_secrets.py` (já existe em `skills/obsidian-workflow/scripts`; avaliar reuso)

**Gate:**
- `python audit.py` passa.
- Teste de busca por secrets simulado passa.

### Tarefa 3.2 — `tdd` + `setup-pre-commit`

**O que fazer:**
1. `tdd`: incluir handler/script de teste, exigir testes antes de commit, regra de não deletar testes.
2. `setup-pre-commit`: configurar Husky + lint-staged + testes; forçar teste antes de commit.
3. Integrar ambos ao `leo` build flow.

**Arquivos:**
- `skills/tdd/SKILL.md`
- `skills/setup-pre-commit/SKILL.md`
- `skills/leo/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_skill_format_passes.py -v` passa.

### Tarefa 3.3 — `planning-pipeline`

**O que fazer:**
1. Adicionar campo obrigatório "Intenção" em specs e tickets.
2. Adicionar campo "Tamanho estimado (linhas)" e lógica de quebra.
3. Adicionar campo "Input/Output" (boundaries) para APIs e serviços.
4. PRD como gate antes de `implement`.

**Arquivos:**
- `skills/planning-pipeline/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_grilling_frontier_rounds.py -v` passa.

### Tarefa 3.4 — `api-design`

**O que fazer:**
Exigir especificação de input/output/comportamento; gerar/consumir OpenAPI spec como contexto.

**Arquivos:**
- `skills/api-design/SKILL.md`

**Gate:**
- `python audit.py` sem erros.

### Tarefa 3.5 — `cost-optimization` e `context-window-hygiene`

**O que fazer:**
1. `cost-optimization`: detectar token maxing, sugerir Codex, limitar loops.
2. `context-window-hygiene`: alertar sobre prompts/skills >1000 linhas, monitorar diluição.

**Arquivos:**
- `skills/cost-optimization/SKILL.md`
- `skills/context-window-hygiene/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_prompt_bloat_gate.py -v` passa.

### Tarefa 3.6 — `docker` e `mcp-context-audit`/`mcp-lazy-enablement`

**O que fazer:**
1. `docker`: fornecer template de dev container para sessões destrutivas.
2. `mcp-context-audit`/`mcp-lazy-enablement`: tornar gate antes de habilitar MCP no `leo`; priorizar GitHub + task manager.

**Arquivos:**
- `skills/docker/SKILL.md`
- `skills/mcp-context-audit/SKILL.md`
- `skills/mcp-lazy-enablement/SKILL.md`

**Gate:**
- `python audit.py` sem erros.

### Tarefa 3.7 — `verification-before-completion`

**O que fazer:**
Incluir checks: SAST, WAF/Dependabot, secret scan, lint, testes de intenção, validação ontológica.

**Arquivos:**
- `skills/verification-before-completion/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_audit_passes.py -v` passa.

### Tarefa 3.8 — `using-skills` e `implement`

**O que fazer:**
1. `using-skills`: alertar sobre mito do one-shot, incentivar `grilling`/`planning-pipeline`.
2. `implement`: rejeitar tarefas sem testes, spec clara ou intenção.

**Arquivos:**
- `skills/using-skills/SKILL.md`
- `skills/implement/SKILL.md`

**Gate:**
- `python -m pytest tests/held-out/trajectory/test_invokes_skill_before_action.py -v` passa.

### Tarefa 3.9 — `grilling` (intenção e PRD)

**O que fazer:**
1. Reforçar `grilling` para capturar intenção e gerar PRD antes de implementação.
2. Usar o padrão "entreviste-me incansavelmente até entendimento mútuo".
3. Garantir que `leo` acione `grilling` para tarefas não-triviais.

**Arquivos:**
- `skills/grilling/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_grilling_frontier_rounds.py -v` passa.

### Tarefa 3.10 — `code-review` (Code Rabbit)

**O que fazer:**
1. Documentar integração com Code Rabbit para revisão automática.
2. Automatizar o loop: Code Rabbit sugere -> implementador aplica -> retorna ao código.
3. Revisão humana somente após o loop automático estabilizar.

**Arquivos:**
- `skills/code-review/SKILL.md`

**Gate:**
- `python audit.py` sem erros.

### Tarefa 3.11 — `project-memory`

**O que fazer:**
1. Capturar referências, regras de projeto e convenções aprovadas.
2. Integrar `project-memory` com `agents.md` para manter regras vivas.

**Arquivos:**
- `skills/project-memory/SKILL.md`

**Gate:**
- `python audit.py` sem erros.

### Tarefa 3.12 — `effort-calibration` e `model-interface-preflight`

**O que fazer:**
1. `effort-calibration`: alertar sobre mito do one-shot, over-prompting e overengineering; ajustar esforço à dificuldade real.
2. `model-interface-preflight`: sugerir Codex para tarefas baratas de código e Cloud Code quando interação IDE justifica; considerar custo no roteamento `leo`.

**Arquivos:**
- `skills/effort-calibration/SKILL.md`
- `skills/model-interface-preflight/SKILL.md`
- `skills/leo/SKILL.md`

**Gate:**
- `python -m pytest tests/validation/test_model_interface_preflight.py -v` passa.

---

## Fase 4 — Novas skills / gates

### Tarefa 4.1 — `ontology-validator`

**O que fazer:**
Criar skill que valide outputs de ferramentas contra `.devin/notes/structured-knowledge-extraction/knowledge.json` e regras OWL/RDFS mínimas.

**Arquivos:**
- `skills/ontology-validator/SKILL.md`
- `.devin/skills/ontology-validator/` (se seguir o padrão)
- Atualizar `manifest.json` se necessário

**Gate:**
- `python audit.py` sem erros.
- Teste de validação ontológica passa.

### Tarefa 4.2 — `task-sizer`

**O que fazer:**
Criar gate que estima tamanho de PR e sugere quebra quando >500 linhas ou fronteiras ausentes.

**Arquivos:**
- `skills/task-sizer/SKILL.md` (ou integrar em `planning-pipeline`)

**Gate:**
- Teste com exemplos de >500 e <300 linhas passa.

### Tarefa 4.3 — `secure-defaults-check`

**O que fazer:**
Criar checklist automatizado: `.env.example`, `.env` no `.gitignore`, S3/URLs públicos, endpoints sem auth, confirmação em ações destrutivas.

**Arquivos:**
- `skills/secure-defaults-check/SKILL.md` (ou integrar em `security-audit`)

**Gate:**
- `python audit.py` sem erros.

### Tarefa 4.4 — `agent-cost-guard`

**O que fazer:**
Monitorar tokens por loop, alertar token maxing, limitar subagentes.

**Arquivos:**
- `skills/agent-cost-guard/SKILL.md` (ou integrar em `cost-optimization`)

**Gate:**
- `python -m pytest tests/validation/test_prompt_bloat_gate.py -v` (ou novo teste) passa.

### Tarefa 4.5 — `intention-capture`

**O que fazer:**
Skill dedicada a capturar e validar campo "intenção" em tickets/specs.

**Arquivos:**
- `skills/intention-capture/SKILL.md` (ou integrar em `grilling`/`planning-pipeline`)

**Gate:**
- `python audit.py` sem erros.

### Tarefa 4.6 — `api-context-spec`

**O que fazer:**
Gerar/manter OpenAPI specs como contexto para IA.

**Arquivos:**
- `skills/api-context-spec/SKILL.md` (ou integrar em `api-design`)

**Gate:**
- `python audit.py` sem erros.

---

## Fase 5 — Melhorar `structured-knowledge-extraction`

### Tarefa 5.1 — Adicionar camada semântica/ontológica

**O que fazer:**
1. Avaliar se é viável enriquecer `extract.py` para extrair conceitos, não só headings/URLs.
2. Alternativa: criar `ontology-validator` que use `knowledge.json` como ledger.
3. Documentar limitação atual no `SKILL.md`.

**Arquivos:**
- `skills/structured-knowledge-extraction/SKILL.md`
- `skills/structured-knowledge-extraction/scripts/extract.py`

**Gate:**
- `python -m pytest tests/validation/test_structured_knowledge_extraction.py -v` passa.

---

## Fase 6 — Verificação e estabilização

### Tarefa 6.1 — Rodar todos os checks

**O que fazer:**
1. `python audit.py`.
2. `python -m pytest -q`.
3. Verificar `git status` para arquivos não rastreados ou temp.
4. Confirmar que nenhum secret foi exposto.

**Gate:**
- `audit.py` 0 erros, 0 warnings.
- `pytest` 260/260.
- `git status` limpo (só mudanças intencionais).

### Tarefa 6.2 — Revisão final

**O que fazer:**
1. Revisar diff com `git diff`.
2. Confirmar que nenhuma skill foi comitada com AI signature.
3. Confirmar que `AGENTS.md` e `global_rules.md` estão consistentes.
4. Atualizar `CHANGELOG.md` se necessário.

**Gate:**
- Revisão manual aprovada (ou `qa-ci` subagent se fase exigir).

---

## Ordem de execução recomendada

1. Fase 0 (Tarefas 0.1 e 0.2) — corrigir `continuous-improvement`.
2. Fase 1 (Tarefas 1.1 e 1.2) — regras e setup.
3. Fase 2 (Tarefas 2.1 e 2.2) — `leo`.
4. Fase 3.1, 3.2, 3.3, 3.4 — segurança, TDD, planning, API.
5. Fase 3.5, 3.6, 3.7, 3.8 — custo/janela, docker/MCP, verificação, implement.
6. Fase 4 — novas skills (priorizar `ontology-validator`, `task-sizer`, `secure-defaults-check`).
7. Fase 5 — extrator.
8. Fase 6 — checks finais.

---

## Rastreamento

- Cada tarefa deve ser trabalhada com `todo_write` e `unlazy` quando apropriado.
- Cada fase termina com `python audit.py` e `python -m pytest -q` verdes.
- Nenhuma fase inicia sem a anterior estar `completed` e verificada.
