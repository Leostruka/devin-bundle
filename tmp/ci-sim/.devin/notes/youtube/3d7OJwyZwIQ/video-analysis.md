# Analise: 3d7OJwyZwIQ -- LFM3 Audio (Liquid AI)

## Conteudo

Review pt-BR (~18 min) da familia `LFM3` da Liquid AI (open weights):

- Modelos: `LFM3 1.7B` (texto), `LFMVL 2B` (visao), `LFM3 Audio 2B`
  (ouve + transcreve + fala), `LFM Omni 2B`, `D1 Omni 2B` (decisao).
- Formatos de pesos: FP8, NVFP4, MLX, ONNX.
- Licenca: LFM Open License -- comercial permitido ate US$10M/ano de
  receita (nao e MIT/Apache).

## Observacoes do autor (demo, nao medidas aqui)

- TTS: geracao rapida, pt-BR entendido ("voz feminina/masculina").
- STT: transcreve conversa em ingles mesmo com fala em portugues.
- Modo streaming: latencia baixa, mas resposta pt sai com sotaque EN;
  modo sequencial: resposta pt correta + escolha de voz/idioma, com
  latencia maior.
- 2B se confunde em consultas complexas (LLM -> "lentes/molduras"),
  as vezes repete a pergunta. Autor nao confiaria em tool-calling
  sensivel (ex.: comprar passagem).

## Veredito: avaliado, nao adotado

- **Candidato real** para voz local: substituiria ou complementaria
  `extensions/asr/` (whisper.cpp) e `extensions/voicebox/` (wrapper
  HTTP backend-swappable) num unico modelo bidirecional.
- **Nao adotado**: maturidade 0-day, 2B confuso, licenca com
  threshold comercial, falta runner local (llama.cpp/MLX/ONNX).
- Documentado como candidato avaliado no
  `.devin/docs/MODEL-GUIDE.md` (secao inferencia local) --
  mesma postura do BitNet: registrado, aguardando medicao.

## Itens implementados

- Entrada "Local audio: LFM3 family" no MODEL-GUIDE com capacidades,
  licenca, limitacoes observadas e criterio de adocao
  (latencia + WER pt-BR em held-out).
