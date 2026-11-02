# Analise: 0F63pTS8Gt0 -- Avalon vs Strata (AMD MoE inference)

## Conteudo

Deep-dive EN (~28 min) de benchmark-literacy sobre `Avalon`, fork MIT
de llama.cpp tuned para Qwen3-80B flash-next em RX 7900XT.

- Modelo: MoE ~125B ativos + 51B lookup; 48x512 experts, 480
  ativos/token, ~1GB de pesos de experts por token.
- Hardware do benchmark: 7900XT (20GB), R7 3800XT, B450 (PCIe3),
  64GB DDR4 (~34GB/s real).
- Bandwidth math: RAM sozinha teto ~34 t/s; PCIe3 ~14 t/s. Avalon
  62.4 t/s sem drafting = >metade dos experts vindos do VRAM.
- Expert cache: todo byte livre de VRAM vira cache (buffers de
  compute emprestados, KV nao usado, reserva 400MB); GPU computa hits
  enquanto CPU resolve misses em paralelo (+27%).
- Draft head MoE-ciente: 1.5GB (vs 3.4GB strata), vocab 65k,
  compartilha o cache; 80.7% agreement, 2 guesses -> +15%.
- Qualidade: arquivo 88GB (13% maior), perplexity menor (1.443 vs
  1.469 EN). Caveat: engine+arquivo misturados na comparacao; strata
  0.1.43 vs 0.2.8 atual; RDNA4/Nvidia empata; sem Windows; 1 dev.
- Licoes do video: "toda tabela de speed e foto de uma maquina";
  checklist de 4 perguntas para ler benchmark.

## Veredito: avaliado, nao adotado

- Candidato real apenas para quem roda 7900XT/XTX em Linux com o
  modelo unico suportado. Nao aplicavel ao bundle (Windows, modelos
  variados).
- Documentado no MODEL-GUIDE (`### AMD MoE: Avalon`) como referencia
  de mecanismo para uma futura evolucao MoE do `offload_plan`.
- Checklist de leitura de benchmark adicionado ao mesmo arquivo
  (alinhado a Rule 12/15).

## Itens implementados

- Entrada `AMD MoE: Avalon` no `.devin/docs/MODEL-GUIDE.md` com
  mecanismo, claims, caveats e o checklist de benchmark.
