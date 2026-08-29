# Plano: analisar o vídeo HtsFKx9mAu8

**Bloqueado por:** integração validada do YouTube Fetcher to Markdown.

**Fonte:** https://youtu.be/HtsFKx9mAu8?si=tJXCXVETxMVwBrdO

**Objetivo:** capturar, compreender e analisar o conteúdo do vídeo usando evidência rastreável.

## Pré-condições

- [ ] A skill YouTube Fetcher está instalada e validada.
- [ ] A captura possui transcript, idioma, metadados e proveniência.
- [ ] O transcript bruto está preservado separadamente.
- [ ] Captions estão disponíveis; caso contrário, interromper e registrar bloqueio.

## Ciclo 1 — captura

- [ ] Executar sem `--force` e salvar em diretório `.devin/` dedicado.
- [ ] Verificar ID, título, canal, duração, idioma e tipo de caption.
- [ ] Validar completude por timestamps e início/fim do transcript.
- [ ] Registrar hash do artefato bruto.

## Ciclo 2 — estruturação

- [ ] Dividir por capítulos ou blocos temporais sem perder timestamps.
- [ ] Extrair afirmações, conceitos, exemplos, recomendações e ressalvas.
- [ ] Associar cada item ao trecho e timestamp correspondente.
- [ ] Separar fala explícita de inferência analítica.

## Ciclo 3 — análise crítica

- [ ] Resumir tese e linha argumentativa.
- [ ] Identificar práticas aplicáveis ao `devin-bundle`.
- [ ] Verificar externamente afirmações factuais relevantes em fontes primárias.
- [ ] Marcar afirmações não verificáveis como opinião ou pendência.
- [ ] Gerar alternativas de aplicação antes de propor mudanças.

## Ciclo 4 — saída

- [ ] Produzir nota Markdown com metadados e sumário executivo.
- [ ] Incluir mapa temporal, conceitos, evidências e implicações.
- [ ] Criar backlog separado; não alterar o bundle durante a análise.
- [ ] Executar ecological check sobre contexto, custo e manutenção.

## Aceitação

- [ ] Toda citação possui timestamp verificável.
- [ ] Inferências estão rotuladas.
- [ ] Fatos externos relevantes possuem fonte primária.
- [ ] Nenhuma conclusão depende de trecho ausente.
- [ ] O transcript bruto permanece inalterado.
- [ ] O backlog final é rastreável às evidências do vídeo.
