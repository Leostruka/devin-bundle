# Nível de Esforço Obrigatório: HIGH
# Perfil Operacional: Staff Engineer / Skill Curator

# Goal
Evoluir o bundle Devin com o que há de útil em github.com/akitaonrails/my-skills, preferindo gap-fill nas skills existentes alinhadas: extrair apenas os mecanismos/checklists que faltam e fundi-los na skill correspondente (ex.: pr-audit -> code-review ganha verificação de claims do contributor, resistência a prompt-injection e revisão de supply-chain). Skill nova só quando não existir casa alinhada. Candidatas pré-selecionadas: fact-check, pr-audit, pr-bump, pr-post-audit, worktrees, humanizer, deepwork.

# Context
Bundle Devin CLI em D:\Programing\ai_workspace\devin-bundle. Mapa de alinhamento inicial a validar contra o código: pr-audit -> code-review; iss-audit -> issue-tracker/debugging; pr-post-audit -> finishing-a-development-branch ou code-review; pr-bump -> fast-path dentro de code-review; worktrees -> dispatching-parallel-agents; fact-check -> possivelmente skill nova ou merge em continuous-improvement; humanizer -> possivelmente skill nova (writing/docs); deepwork -> padrões para afk-loop/dispatching; improve-codebase-architecture/simplify/post-refactor -> architecture/code-review; verification-planning -> autonomous-gates; reflect -> continuous-improvement; security-audit -> security. my-skills é Claude-Code-flavored (allowed-tools, Bash(...), CLIs externos zcode/claude/codex): adaptar ao formato Devin (front-matter, run_subagent profiles), nunca copiar verbatim. Convenções duras: skills/<nome>/SKILL.md front-matter válido; testes de contrato em tests/; pytest tests -q + audit.py 0 erros; sem em-dashes; sem assinaturas AI; diffs mínimos, preservando conteúdo existente que já funciona.

# Acceptance Criteria
1. Por candidata: leitura do SKILL.md fonte + veredito em 3 vias: fundir-em-<skill> / nova-skill / descartar, com gap concreto citado
2. Gap-fill cirúrgico: apenas o delta que falta entra na skill existente; nada de reescrever seções que já cobrem o tema
3. Skill nova obrigatória quando a candidata é útil E nenhuma casa alinhada existe (listar skills avaliadas no veredito); descarte só se inútil ou duplicada
4. Adaptação real: referências a CLIs externos -> run_subagent/profiles; allowed-tools removidos (não existe no runtime Devin)
5. Front-matter válido em todo arquivo tocado (validate-skill-format passa)
6. pytest tests -q verde + audit.py 0 erros; manifest/README contagens só se skill nova for criada
7. Cada mudança registrada com origem: qual trecho veio de qual skill do akita

# Scope & Non-Goals
- **IN SCOPE:** Avaliação das 7 candidatas: ler fonte, diff mental contra a skill alinhada
- **IN SCOPE:** Gap-fill nas skills existentes ou skills novas onde justificado
- **IN SCOPE:** Testes de contrato para o que mudar
- **IN SCOPE:** Tabela de decisões (veredito + gap + destino) reportada ao usuário
- **OUT OF SCOPE:** Copiar SKILL.md verbatim ou criar skill nova quando já existe casa alinhada
- **OUT OF SCOPE:** Deps de CLI externa inexistentes no runtime Devin
- **OUT OF SCOPE:** As demais 16 skills do repo não listadas
- **OUT OF SCOPE:** Reescrever/reformatar skills existentes além do delta necessário
- **OUT OF SCOPE:** Mudar hooks/MCP/protocolos

# Execution Hints & Checkpoints
1. **Fase 1:** Ler o SKILL.md fonte das 7 candidatas + as skills alinhadas do bundle; produzir tabela de vereditos (fundir-em / nova / descartar) com gap citado por item. PARE e aguarde aprovação.
2. **Fase 2:** Aplicar os gap-fills aprovados + skills novas justificadas + testes de contrato.
3. **Fase 3:** pytest + audit.py verdes, contagens manifest/README se skill nova, commit e reportar com a tabela final.
