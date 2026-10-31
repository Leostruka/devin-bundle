# 02 - Validar completude antes de declarar sucesso no batch TPU

Status: resolved
Priority: P2
Type: validation-gap
Blocked by: none

## Achado

`extensions/ai-tools/vllm_tpu_runner.py:79-94` usa zip(ordered, outs)
e retorna ok=true sem conferir a cardinalidade das respostas.
Se o backend retornar menos resultados, os jobs faltantes desaparecem
silenciosamente; manifest_entries continua refletindo todas as entradas.
Isso enfraquece a evidencia de execucao de um conjunto congelado.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py tpu
```

Duas entradas passam por heldout_batch.load_manifest com SHA-256 validado.
Um backend simulado retorna zero respostas. Resultado observado:

```json
{"ok": true, "manifest_entries": 2, "results": []}
```

O check de disponibilidade e a API vLLM sao substituidos somente no
reprodutor. Nenhuma TPU foi usada; nao se afirma que vLLM real normalmente
retorne listas incompletas. O defeito confirmado e a ausencia do gate.

## Correcao solicitada

Conferir completude e formato antes de agregar sucesso. Nao truncar por zip.
Reportar jobs ausentes/duplicados/excedentes como falha do batch, preservando
ids, hashes de entrada e a distincao entre erro e backend indisponivel.

## Aceite

- [ ] Zero, menos e mais respostas que entradas nunca produzem ok=true.
- [ ] Uma resposta valida por entrada produz exatamente N registros.
- [ ] Jobs ausentes aparecem explicitamente ou invalidam todo o batch.
- [ ] Testes usam stubs declarados; nao simulam prova de TPU real.
- [ ] Gate: `python -m pytest tests/test_local_inference.py -q`.

## Answer

`run_tpu_batch` agora valida cardinalidade antes de agregar: respostas em
numero diferente das entradas retornam `ok=False` com erro
`incomplete_results` e contagens. Outputs malformados viram registros
`ok=False` por entrada em vez de excecao; `ok` final e a conjuncao dos
registros. Testes cobrem 0/1/3 respostas para 2 entradas e o caminho
completo. `pytest tests/test_local_inference.py -q`: 57 passed.

## Comments

Auditoria apenas. A pendencia de hardware real permanece separada.
