# Plano: adaptar DeepPaperNote para gerenciar `.devin`

**Bloqueado por:** adequação ao Devin CLI v3000.6.7.

**Objetivo:** transformar o padrão evidence-first do DeepPaperNote em um gerenciador auditável de conhecimento e configuração `.devin` por projeto.

## Fonte primária verificada

- README: https://github.com/917Dhj/DeepPaperNote/blob/main/README.md
- Skill principal: https://github.com/917Dhj/DeepPaperNote/blob/main/skills/deeppapernote/SKILL.md
- Dependências: https://github.com/917Dhj/DeepPaperNote/blob/main/pyproject.toml
- Licença MIT: https://github.com/917Dhj/DeepPaperNote/blob/main/LICENSE

O projeto processa uma fonte por vez, preserva evidências e gera notas duráveis. Requer Python 3.10+, `PyMuPDF>=1.24` e `certifi>=2024.0.0` para seu fluxo de PDFs.

## Escopo proposto

- Inventário de regras, skills, hooks, agentes, MCP e memória do projeto.
- Notas Markdown com proveniência, estado, relações e diagnóstico.
- Operações `scan`, `explain`, `diff`, `doctor` e `plan`; nenhuma correção silenciosa.
- Persistência somente dentro de `.devin/`, salvo destino explícito.
- Reuso de `project-setup`, `project-memory` e validadores existentes.

## Ciclos sequenciais

### Ciclo 1 — diagnóstico somente leitura

- [ ] Reproduzir a dificuldade atual de responder “o que existe em `.devin`?”.
- [ ] Comparar adaptação conceitual, incorporação parcial e integração externa.
- [ ] Implementar inventário determinístico com proveniência.

### Ciclo 2 — nota durável do projeto

- [ ] Definir schema Markdown estável e links entre artefatos.
- [ ] Preservar evidência textual e comandos de verificação.
- [ ] Detectar referências quebradas, duplicações e divergências.

### Ciclo 3 — propostas de mudança

- [ ] Produzir plano/diff sem aplicar alterações.
- [ ] Exigir aprovação antes de persistir memória ou editar configuração.
- [ ] Integrar gates do `continuous-improvement` em cada proposta.

### Ciclo 4 — fontes documentais opcionais

- [ ] Avaliar suporte a PDF sem tornar PyMuPDF obrigatório ao núcleo.
- [ ] Isolar parsing externo e validar tipos/tamanhos de entrada.
- [ ] Preservar avisos e licença quando código for incorporado.

## Aceitação

- [ ] Um projeto de fixture gera inventário reproduzível.
- [ ] Nenhum arquivo fora de `.devin/` é alterado no modo padrão.
- [ ] Conflitos e referências quebradas são relatados com origem.
- [ ] Execução repetida é idempotente.
- [ ] Testes específicos, audit e held-out passam.
