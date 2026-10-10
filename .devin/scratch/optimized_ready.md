# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Principal Security Architect & Red Team Automation Lead

# Goal
Arquitetar e integrar uma "Red Team Capability" completa e estruturada dentro do `devin-bundle`. A missão possui duas frentes:
1. Analisar e adaptar a arquitetura do MCP de engenharia reversa `morluto/rea` (binários nativos, JS/Electron, .NET) para o ecossistema do bundle.
2. Realizar uma pesquisa profunda e documentada sobre o espectro de segurança ofensiva (Reverse Engineering, Pen-test, Injeção, Vulnerability Scanning em Redes/Web/Firmware/Wireless) e consolidar as ferramentas open-source correspondentes em extensões seguras e habilidades cognitivas.

# Context
O bundle opera no paradigma "Brain vs Muscle" (`skills/` vs `extensions/`). As skills de segurança atuais (`skills/security`, `secure-defaults-check`) são puramente defensivas (SAST, secret leak). Esta nova suíte deve integrar capacidades ofensivas de simulação de adversários (Red Team).
**Regras do Ambiente (Bundle AGENTS.md):**
- Preferência estrita por tooling free/open-source e wrappers locais em Python.
- Nenhuma assinatura de IA permitida (Rule 2).
- Verificação determinística com ferramentas, nunca dedução LLM (Rule 12).
- As skills desenvolvidas assumirão autorização de contexto local (Rule 13), porém devem delegar a execução de ações destrutivas irreversíveis à confirmação do usuário.

# The "Iron-Clad Academic" Mandate (Regra de Pesquisa)
Para a frente de pesquisa (Frente 2), alucinações ou sugestões de ferramentas deprecadas são inaceitáveis. Para CADA domínio de segurança ofensiva (RE, Web, Infra/Redes, Wireless/RF, Firmware):
- Você deve extrair, ler e documentar no mínimo **20 fontes primárias validadas**.
- Fontes aceitas: Papers acadêmicos (IEEE/ACM/USENIX/S&P), frameworks globais (OWASP, MITRE ATT&CK, NVD/CVE), documentações oficiais de ferramentas ou RFCs.
- Todo claim crítico sobre o uso de uma ferramenta deve ser cross-validado por >= 2 fontes destas listas.

# Acceptance Criteria
1. **Relatório de Análise REA:** Gerar `.devin/research/rea-analysis.md` detalhando a arquitetura do `morluto/rea`, o catálogo de ferramentas, o modelo de investigação/evidência e o plano exato do que será portado via MCP vs reimplementado via extensões locais.
2. **Matriz de Cobertura de Domínios:** Gerar `.devin/research/red-team-domains.md`. Deve conter a matriz cruzando [Domínio] x [Ferramentas Open-Source recomendadas] x [Status de Integração]. Inclua as 20 fontes com URLs e tipos de citação para cada domínio.
3. **The Brain (Skills):** Criar as skills necessárias em `skills/` seguindo a convenção do bundle (<= 10KB, frontmatter de roteamento claro). O roteamento deve distinguir perfeitamente quando usar as novas skills ofensivas vs as antigas defensivas.
4. **The Muscle (Extensions):** Criar as extensões correspondentes em `extensions/` usando o padrão `wrapper.py` (com dependências *lazy* e isoladas).
5. **Contract Tests & Governance:** Criar testes em `tests/validation/test_*.py` para cada nova skill e documentar os gates no ledger `.devin/ledgers/red-team-skill.md`. Atualizar o `install.ps1` de forma não-destrutiva.

# Scope & Non-Goals
- **IN SCOPE:** Pesquisa acadêmica exaustiva, análise de código read-only do repositório alvo, criação de documentação técnica, arquitetura de skills e wrappers Python.
- **OUT OF SCOPE:** NÃO execute ataques, injeções ou scans reais contra nenhum alvo externo ou interno durante esta tarefa. Seu objetivo é construir a *Capability* (as ferramentas e os prompts) e não realizar o *Exercício*.
- **OUT OF SCOPE:** NÃO crie, codifique ou sugira payloads maliciosos inéditos (malware, zero-days). A capability deve focar na automação e orquestração de ferramentas open-source de auditoria reconhecidas pela indústria.
- **OUT OF SCOPE:** NÃO instale dependências globais ou MCP servers cegamente antes do review.

# Execution Hints & Checkpoints
1. **Fase 1 (Recon & Research):** Realize a clonagem/leitura do `morluto/rea` e inicie a pesquisa agressiva dos domínios exigindo as 20 fontes. **PARE. Gere o `rea-analysis.md` e o `red-team-domains.md`. Apresente no terminal a arquitetura proposta (Quais skills e extensões serão criadas). Aguarde minha aprovação.**
2. **Fase 2 (Brain & Muscle):** Após aprovação, implemente os arquivos `.md` das skills, os scripts `wrapper.py` nas extensões e defina o escopo de ROE (Rules of Engagement) dentro das documentações das skills.
3. **Fase 3 (Validation Gates):** Rode o `pytest tests/validation -q` e valide a integridade do `install.ps1` usando a flag `-DryRun`.
4. **Fase 4 (Ledger):** Escreva a evidência no `.devin/ledgers/red-team-skill.md` e conclua a tarefa.