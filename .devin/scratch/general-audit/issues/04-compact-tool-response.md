# 04 - Capturar erros do campo PostToolUse realmente utilizado

Status: resolved
Priority: P2
Type: bug
Blocked by: none

## Achado

`scripts/compact-gate.py:173-180` consulta somente tool_output.
O contrato descrito em `scripts/silent-error-review.py:4-8` e consumido em
`scripts/memory-post-exec.py:85-93` utiliza tool_response, incluindo objetos
com output/stdout. Erros desses eventos nao chegam a recent_errors no digest.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py response
```

Mesmo texto sintetico, mesmo evento PostToolUse e mesmo DEFAULTS:

```json
{"tool_response": 0, "tool_output": 1}
```

Os numeros sao contagens de erros capturados. Nao ha daemon, gravacao de
estado real ou modelo envolvido na reproducao.

## Correcao solicitada

Normalizar tool_response de acordo com os contratos do repositorio;
manter tool_output como compatibilidade se necessario. Extrair campos de
saida de objetos sem registrar credenciais e preservar truncamento.

## Aceite

- [ ] tool_response string e objeto capturam o erro sintetico uma vez.
- [ ] Campos output/stdout/error suportados seguem contrato documentado.
- [ ] Payload legado continua funcionando, sem duplicar erros.
- [ ] Valores inesperados falham abertos sem traceback.
- [ ] Gate: `python -m pytest tests/test_jev_routing.py -q`.

## Answer

`_update_digest` agora normaliza `tool_response` (contrato documentado em
`silent-error-review.py`) com fallback para `tool_output` legado; objetos
extraem `output`/`stdout`/`error`. 3 testes cobrem dict, string e legado.
`pytest tests/test_hook_laya_gate.py tests/test_jev_routing.py -q`:
44 passed.

## Comments

A auditoria constata divergencia entre os consumidores locais do evento.
