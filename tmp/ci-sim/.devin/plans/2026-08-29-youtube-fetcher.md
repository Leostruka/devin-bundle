# Plano: integrar YouTube Fetcher to Markdown

**Bloqueado por:** extração estruturada inspirada no Hyper-Extract.

**Objetivo:** aceitar uma URL do YouTube e produzir uma nota Markdown verificável, pronta para análise e ingestão em `.devin`.

## Fonte primária verificada

- README: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/README.md
- Skill: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/SKILL.md
- Script: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/scripts/fetch_transcript.py
- Dependências: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/requirements.txt
- Licença MIT: https://github.com/JimmySadek/youtube-fetcher-to-markdown/blob/main/LICENSE

O projeto usa `youtube-transcript-api>=1.2,<1.3` e `requests>=2.32,<3`; `yt-dlp` é opcional. Captura captions, metadados e capítulos, protege duplicatas e não executa Whisper.

## Ciclos sequenciais

### Ciclo 1 — auditoria e fixtures

- [ ] Revisar integralmente o script sem executá-lo no host.
- [ ] Mapear rede, subprocessos, filesystem, validação de host e overwrite.
- [ ] Executar testes upstream somente em ambiente isolado.

### Ciclo 2 — adaptação Devin-native

- [ ] Comparar wrapper, fork mínimo e integração como plugin.
- [ ] Criar skill com caminhos `.devin/` e ferramentas Devin-native.
- [ ] Não instalar dependências automaticamente.
- [ ] Salvar transcript e metadados com proveniência e idioma real.

### Ciclo 3 — segurança e falhas

- [ ] Rejeitar hosts semelhantes, IDs inválidos e redirecionamentos inesperados.
- [ ] Preservar arquivos existentes sem confirmação específica.
- [ ] Tratar captions ausentes, privadas ou bloqueadas sem inventar conteúdo.
- [ ] Limitar tamanho e normalizar Markdown/YAML.

### Ciclo 4 — conexão com conhecimento

- [ ] Alimentar a camada de extração estruturada após captura íntegra.
- [ ] Manter transcript bruto separado de resumo e inferências.
- [ ] Registrar timestamps quando disponíveis.

## Aceitação

- [ ] URLs suportadas geram Markdown determinístico.
- [ ] URL inválida não produz arquivo parcial.
- [ ] Duplicata permanece intacta sem confirmação.
- [ ] Idioma e tipo de caption são registrados corretamente.
- [ ] Ausência de caption encerra sem análise fabricada.
- [ ] Testes específicos, audit e held-out passam.
