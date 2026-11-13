# Plano: integrar extração estruturada inspirada no Hyper-Extract

**Bloqueado por:** gerenciador `.devin` baseado no DeepPaperNote.

**Objetivo:** extrair conhecimento verificável de documentos para estruturas tipadas e notas relacionáveis dentro de `.devin`.

## Fonte primária verificada

- README: https://github.com/yifanfeng97/Hyper-Extract/blob/main/README.md
- Pacote: https://github.com/yifanfeng97/Hyper-Extract/blob/main/pyproject.toml
- Licença Apache-2.0: https://github.com/yifanfeng97/Hyper-Extract/blob/main/LICENSE

O projeto oferece CLI `he`, estruturas tipadas, evolução incremental, busca semântica, exportação Obsidian e MCP opcional. Requer Python 3.11+ e inclui dependências como FAISS, LangChain, Pydantic-based providers e `python-dotenv`.

## Decisão a validar

Preferir um adaptador mínimo e provider-neutral. Não incorporar o framework completo antes de medir benefício, custo de contexto, dependências e necessidade real de embeddings.

## Ciclos sequenciais

### Ciclo 1 — extração determinística

- [ ] Definir fixtures e falhas atuais de extração.
- [ ] Comparar schema simples, Pydantic e integração Hyper-Extract.
- [ ] Extrair entidades, relações, evidências e proveniência para JSON/Markdown.

### Ciclo 2 — evolução incremental

- [ ] Mesclar nova extração sem apagar evidência anterior.
- [ ] Detectar conflitos e exigir resolução explícita.
- [ ] Garantir idempotência e versionamento do schema.

### Ciclo 3 — busca

- [ ] Medir baseline lexical antes de adicionar embeddings.
- [ ] Comparar busca lexical, embeddings locais e provider remoto.
- [ ] Manter funcionamento sem API key.

### Ciclo 4 — integração opcional

- [ ] Avaliar CLI externo, biblioteca e MCP em ambiente isolado.
- [ ] Auditar ferramentas MCP e custo de contexto antes de habilitar.
- [ ] Guardar credenciais somente em configuração local ignorada.
- [ ] Cumprir atribuições Apache-2.0 se houver derivação de código.

## Aceitação

- [ ] Extração aponta cada fato à fonte original.
- [ ] Reprocessamento não duplica entidades.
- [ ] Conflitos não são resolvidos silenciosamente.
- [ ] Caminho sem LLM e sem API key permanece funcional.
- [ ] Dependências opcionais não oneram instalação básica.
- [ ] Testes específicos, audit e held-out passam.
