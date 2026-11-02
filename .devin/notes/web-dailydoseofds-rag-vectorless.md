# Analise: dailydoseofds "RAG vs. Vectorless RAG, clearly explained"

| Field | Value |
|---|---|
| URL | https://blog.dailydoseofds.com/p/rag-vs-vectorless-rag-clearly-explained |
| Author | Avi Chawla (Daily Dose of DS) |
| Published | 2026-10-30 |
| Captured | 2026-11-02 via webfetch |

## Conteudo extraido

### Parte 1 -- Weaver + DFlash speculative decoding (MacBook)

- Qwen3.5 9B num M5 MacBook: 22.0 t/s plain, 34.7 t/s spec decoding
  comum, 92.1 t/s com DFlash + Weaver (engine Uzu, open source,
  `brew install mirai`).
- Weaver = adapter de 1 camada (56.7M) sobre drafters paralelos:
  escolhe entre top-candidates da esquerda p/ direita (cada pick
  depende do anterior), cresce arvore de continuacoes, modelo
  principal verifica a arvore inteira numa passada. ~7.5
  tokens/pass. Paper reporta 4.08x no B200.

### Parte 2 -- Vectorless RAG (PageIndex)

Duas falhas estruturais do similarity search:

- **Template-identical chunks**: relatorios anuais seguem o mesmo
  template; "divida FY2022" fica tao proximo de chunk FY2025 quanto
  do alvo. O LLM responde do ano errado e nada sinaliza (o chunk e
  on-topic).
- **Cross-references**: "ver Apendice G" e recuperado, mas a tabela
  no apendice nao parece a query -- nunca entra no top-k.

Correcoes no lado vetorial ajudam (contextual retrieval da Anthropic
+ reranker: falhas 5.7% -> 1.9% top-20) mas continuam ranqueando por
semelhanca. Comentario leitor: o mixup de ano tambem se resolve com
metadata filtering no vector side -- caveat honesto.

**Mecanismo vectorless** (PageIndex, impl. open-source mais usada):

1. Preprocessamento: layout do doc -> arvore ToC. Cada no: titulo de
   secao + page range + resumo curto (modelo basico escreve resumos).
   Nada e chunkeado -- tabelas nunca sao cortadas.
2. Query: LLM le a arvore + query, escolhe secoes por raciocinio
   (pode SEGUIR cross-references -- como um analista le um 10-K).
3. Puxa secoes completas, avalia suficiencia da evidencia; insuf.
   -> volta a arvore e abre mais nos. Chat history tambem entra.

**Custos** (numeros do proprio PageIndex -- vendor data):

- 63/63 corretas a ~$110/1k queries vs melhor vector 92.1% @ top-100
  (~$134); vector top-10 fica <=76.2% a ~$15.
- Latencia: cada hop na arvore = chamada LLM (sem numeros publicos).
- Index: 2-5 min de LLM calls por doc (benchmark independente pulou
  arvores por isso). Versionar a arvore com o doc -- resumo velho =
  resposta errada silenciosa se o doc for emendado.
- So funciona com estrutura real: pilha de tickets nao tem ToC.

**Selector do artigo**: arvore para docs longos estruturados
(filings, contratos, manuais); vector DB para muito texto curto e
desrelacionado.

## Veredito e aplicacao ao bundle

- **Adotado em docs**: skill `agentic-rag` e a mesma fonte (Daily
  Dose of DS) e seu "Architecture selector" nao cobria o caso
  vetorless. Adicionada linha para docs longos estruturados + nota
  com os dois failure modes e tradeoffs.
- **Weaver/DFlash**: nao adotado -- engine Uzu e Apple Silicon
  (bundle e Windows); anotado como referencia de tree-verification
  no espaco de spec decoding (cf. entrada Avalon no MODEL-GUIDE).
- Nada em runtime: o padrao e relevante para projetos que usarem a
  skill agentic-rag, nao para o proprio bundle.
