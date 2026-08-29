# Plano de planos: evolução do bundle e ingestão de conhecimento

**Objetivo:** executar seis planos sequenciais, cada um em PR próprio de implementação, usando a diretiva `continuous-improvement` sem alterar os testes held-out.

## Ordem obrigatória

1. [Corrigir declarações e contagens](2026-08-29-ajuste-declaracoes.md)
2. [Adequar o bundle ao Devin CLI v3000.6.7](2026-08-29-adequacao-devin-cli-3000.6.7.md)
3. [Adaptar DeepPaperNote para gestão de `.devin`](2026-08-29-deeppapernote-devin-manager.md)
4. [Integrar extração estruturada inspirada no Hyper-Extract](2026-08-29-hyper-extract.md)
5. [Integrar YouTube Fetcher to Markdown](2026-08-29-youtube-fetcher.md)
6. [Analisar o vídeo `HtsFKx9mAu8`](2026-08-29-analise-video-HtsFKx9mAu8.md)

Cada plano bloqueia o seguinte. Não executar dois ciclos de melhoria em paralelo.

## Contrato comum de execução

Para cada plano:

- [ ] Criar `.devin/ledgers/<topico>.md` com gates 0.1–0.7 e 1–10.
- [ ] Executar toda a FASE 0 da skill `continuous-improvement`.
- [ ] Registrar falha reproduzível; sem reprodução, encerrar como inconclusivo.
- [ ] Gerar pelo menos três alternativas antes de editar.
- [ ] Implementar somente a alternativa selecionada.
- [ ] Executar teste específico, `python audit.py` e `python -m pytest tests/held-out -q`.
- [ ] Executar future pace em três cenários e ecological check.
- [ ] Simular instalação em diretório temporário, sem sobrescrever configuração real.
- [ ] Classificar o ciclo como MELHOROU, PIOROU, NEUTRO ou INCONCLUSIVO.
- [ ] Reverter ciclos PIOROU; não declarar ganho para resultados inconclusivos.
- [ ] Revisar licença, dependências, rede, subprocessos e gravações antes de incorporar código externo.
- [ ] Manter segredos fora do repositório e não executar código externo sem isolamento.
- [ ] Criar PR independente, com checks verdes, antes do próximo plano.

## Critério global de conclusão

- [ ] Os seis planos foram executados na ordem definida.
- [ ] Cada implementação possui ledger e evidência reproduzível.
- [ ] Nenhum teste held-out foi alterado.
- [ ] O vídeo foi analisado somente após validar a captura de transcript.
- [ ] O audit final apresenta zero erros.
- [ ] A suíte held-out final apresenta zero falhas.

## Fontes primárias

- Devin CLI stable changelog: https://docs.devin.ai/cli/changelog/stable
- Devin CLI plugins: https://docs.devin.ai/cli/extensibility/plugins
- Devin CLI lifecycle hooks: https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks
- DeepPaperNote: https://github.com/917Dhj/DeepPaperNote
- Hyper-Extract: https://github.com/yifanfeng97/Hyper-Extract
- YouTube Fetcher to Markdown: https://github.com/JimmySadek/youtube-fetcher-to-markdown
- Vídeo-alvo: https://youtu.be/HtsFKx9mAu8?si=tJXCXVETxMVwBrdO
