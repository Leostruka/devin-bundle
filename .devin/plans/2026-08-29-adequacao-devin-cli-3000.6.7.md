# Plano: adequar o bundle ao Devin CLI v3000.6.7

**Bloqueado por:** ajuste de declarações.

**Objetivo:** alinhar configuração, documentação e empacotamento ao CLI instalado e às notas oficiais.

## Estado observado

- `devin --version`: `3000.6.7`.
- A versão 3000.6.7 altera MCP com proxy/TLS e desempenho de renderização.
- A versão 3000.5.20 adiciona plugins Agent Plugins 1.0.0, `devin doctor`, `/recap`, Plan mode em arquivo e correções em hooks, skills e sessões.
- `config.json` usa `adaptive`; `devin models list` informa custo de `$0.5/$0.1/$2` por milhão de tokens.
- O bundle ainda declara GLM-5.2 High como parent gratuito.
- A documentação oficial classifica plugins como closed beta.

## Fontes primárias

- https://docs.devin.ai/cli/changelog/stable
- https://docs.devin.ai/cli/extensibility/plugins
- https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks

## Ciclos sequenciais

### Ciclo 1 — modelo configurado

- [ ] Reproduzir a divergência `adaptive` × política GLM-5.2.
- [ ] Comparar três alternativas e escolher por custo/comportamento verificável.
- [ ] Alinhar `config.json`, AGENTS e documentação.

### Ciclo 2 — hooks e instaladores

- [ ] Comparar os oito eventos e payloads com a documentação oficial.
- [ ] Testar `install.ps1` e `install.sh` em homes temporários.
- [ ] Resolver o papel global/projeto de `hooks.v1.json`.
- [ ] Cobrir `Stop.last_assistant_message`, `SessionEnd.reason` e bloqueio `pre_tool`.

### Ciclo 3 — skills e subagents

- [ ] Executar `devin doctor` e diagnosticar todos os erros.
- [ ] Verificar descoberta das 71 skills após instalação temporária.
- [ ] Atualizar validadores para ferramentas efetivamente expostas pelo CLI.
- [ ] Verificar aliases `allowed-tools`/`tools` sem duplicar configuração.

### Ciclo 4 — plugins

- [ ] Criar protótipo isolado de `.devin-plugin/plugin.json`.
- [ ] Comparar plugin nativo, Agent Plugins 1.0.0 e instaladores atuais.
- [ ] Manter instaladores enquanto plugins estiverem em closed beta.
- [ ] Não instalar MCP externo durante o teste.

## Aceitação

- [ ] Nenhuma declaração de modelo contradiz `devin models list`.
- [ ] `devin doctor` não aponta frontmatter inválido.
- [ ] Instalação temporária encontra todas as skills esperadas.
- [ ] Hooks correspondem aos payloads documentados.
- [ ] Estratégia de plugin explicita o status closed beta.
- [ ] Audit e held-out passam sem regressões.
