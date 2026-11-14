# 03 - Impedir que resultados sobrescrevam o manifesto ou corpus

Status: resolved
Priority: P2
Type: data-integrity
Blocked by: none

## Achado

`extensions/ai-tools/heldout_batch.py:207-213` grava --out com write_text,
sem exclusividade, confirmacao ou verificacao de colisao com entradas.
--out pode ser o proprio --manifest ou um arquivo do corpus congelado.
O dataset e alterado depois de ter sido validado, prejudicando reexecucoes.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py clobber
```

O reprodutor cria somente arquivos temporarios sinteticos e simula o runner.
Passa --out igual a --manifest. O CLI termina com exit=0; o JSON original
perde a chave entries e passa a conter manifest_entries/ok/results.
Nenhum arquivo existente do usuario ou modelo real e executado/alterado.

## Correcao solicitada

Validar o destino antes de iniciar jobs; rejeitar alias com manifesto,
entradas, binario e modelo. Nao sobrescrever artefatos existentes por padrao.
Caso seja necessario --force para resultados anteriores, documentar o opt-in
sem permitir corromper os arquivos de entrada. Tratar erros de IO em JSON.

## Aceite

- [ ] Destino igual ao manifesto ou corpus e rejeitado antes do runner.
- [ ] Colisoes por caminhos relativos/resolvidos tambem sao detectadas.
- [ ] Destino preexistente permanece intacto sem opt-in especifico.
- [ ] Falha de escrita retorna erro tipado e status nao zero.
- [ ] Gate: `python -m pytest tests/test_local_inference.py -q`.

## Answer

`--out` agora e validado antes de rodar jobs: resolve e rejeita colisao
com manifesto, entradas, binario e modelo; destino preexistente e
recusado sem opt-in; falha de escrita retorna erro tipado + exit 2.
4 testes cobrem colisao com manifesto/entrada, destino existente e
escrita em caminho novo. `pytest tests/test_local_inference.py -q`:
61 passed.

## Comments

A reproducao altera apenas arquivos criados no seu TemporaryDirectory.
