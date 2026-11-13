# Analise: SMYzc9FMXj0 -- NCM (Next Concept Modeling)

## Conteudo

Explainer EN (~14 min) do paper NCM da equipe Hazy Research (Stanford).
Geracao de texto coarse-to-fine como alternativa ao auto-regressivo:

- **Tokenizer**: multi-scale residual VQ-VAE -- texto vira pilha de
  codigos discretos (nivel 1 curto/grosseiro, niveis seguintes adicionam
  detalhe ate o comprimento total).
- **Gerador**: transformer que prediz todos os codigos de um nivel em
  paralelo, condicionado nos niveis anteriores; decoder reconstroi texto.
- **vs difusao**: difusao refina a sequencia inteira por passadas; NCM
  prediz niveis crescentes -- passadas iniciais mais baratas.

## Resultados reportados (claims do paper, nao medidos aqui)

| Benchmark | Resultado |
|---|---|
| XSum (summarization) | Rouge L comparavel a AuroraLM (difusao), 31x mais rapido (H100, batch 16, 1024 seqs) |
| LM1B | Melhor generative perplexity que baseline de difusao, 21x |
| OpenWebText | Competitivo, 10x |
| Sudoku | Supera AR + difusao em todos os niveis, menos NFEs |
| WMT14 DE-EN | MBR decoding melhora saida (custo extra) |

Escala testada: ate 725M params. Checkpoints no HF para XSum, WMT14,
Sudoku, TinyStories, LM1B (OpenWebText pendente). NCM ainda usa
transformer -- "matou o LLM" e clickbait; e um procedimento de geracao
alternativo dentro de LMs.

## Veredito: sem capacidade implementavel

- Explainer de arquitetura de pesquisa; nao ha tool, workflow ou API
  adotavel.
- **Nao entra no MODEL-GUIDE** (diferente do LFM3): checkpoints sao
  task-specific, <=725M, sem modelo de chat/assistant -- nao e backend
  candidato para `asr`/`voicebox`/`ai-tools` hoje.
- Licoes uteis apenas como heuristica de avaliacao: conferir baseline,
  batch/hardware do claim, e orcamento de inferencia (MBR) antes de
  confiar em speedup -- consistente com a regra de verificacao de
  fontes do bundle.

## Itens implementados

Nenhum (veredito honesto): nada no video muda routing, hooks,
inferencia local ou skills. Artefato = transcript + provenance +
esta analise.
