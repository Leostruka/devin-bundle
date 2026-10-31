# 01 - Aplicar limites antes de ler e decodificar entradas

Status: resolved
Priority: P2
Type: reliability
Blocked by: none

## Achado

Os limites declarados nao limitam a alocacao da leitura inicial:

- `extensions/computer-use/cu_dom_picker.py:273-282`: read/read_text sem
  tamanho; json.loads antes de comparar len(raw) com MAX_SNAPSHOT_BYTES.
- `extensions/scrape-tools/dom_elements.py:37-46`: mesmo padrao.
- `extensions/ai-tools/heldout_batch.py:77-83,125-132`: read_bytes integral
  do manifesto e de cada entrada, seguido de verificacao de tamanho.

Nos dois CLIs DOM, len(str) conta caracteres, nao bytes UTF-8.
Entradas grandes podem consumir memoria e CPU antes de serem rejeitadas.
O nome MAX_*_BYTES nao corresponde ao limite efetivamente aplicado.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py reads
```

Resultado observado: ambos os CLIs chamam stdin.read com size=-1.
Uma sentinela intercepta a leitura; nenhum arquivo grande e criado.
O comportamento de read_bytes no loader foi confirmado estaticamente.

## Correcao solicitada

Ler no maximo limite+1 bytes, rejeitar excesso antes do JSON e somente
entao decodificar. Preservar erros JSON tipados, codificacao explicita e
binding dos bytes verificados no loader. Um stat previo isolado nao basta
para limitar leituras sujeitas a alteracao concorrente.

## Aceite

- [ ] Stdin e arquivo sao limitados antes da decodificacao/parse.
- [ ] Manifesto e entradas do batch usam leitura limitada.
- [ ] Fixtures multibyte respeitam limites em bytes, nao caracteres.
- [ ] A sentinela de teste rejeita read/read_bytes sem limite.
- [ ] Excesso retorna erro tipado e nao inicia daemon ou inferencia.
- [ ] Regressao: `python -m pytest tests/test_jev_review_dom.py tests/test_local_inference.py -q`.

## Answer

`read_bounded(source, limit)` adicionado a `cu_dom_picker.py` (le limit+1
bytes antes de decodificar; `None` = excedeu). `dom_elements.py` reusa o
helper; `heldout_batch.py` usa leitura limitada no manifesto e em cada
entrada. 7 testes novos cobrem sentinelas de read, contagem em bytes
(multibyte) e bounds de manifesto. `pytest tests/test_jev_review_dom.py
tests/test_local_inference.py -q`: 118 passed.

## Comments

Auditoria apenas; nenhuma implementacao alterada.
