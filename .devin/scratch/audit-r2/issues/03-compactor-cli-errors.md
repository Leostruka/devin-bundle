# 03 - Converter falhas de entrada do compactor em erro tipado

Status: claimed
Priority: P3
Type: cli-ux
Blocked by: none

## Contexto

`extensions/laya-compactor/compact.py:main()` faz
`Path(args.transcript).read_text` + `json.loads` sem tratamento:
arquivo ausente, permissao negada ou JSON invalido saem como traceback,
nao como erro tipado. Mesma classe do R1-01 (ffprobe timeout).

## Impacto

Uso erroneo do CLI (caminho errado, JSON quebrado) produz crash ilegivel
em vez de `{"ok": false, "error": ...}` + exit != 0.

## Reproducao

`python compact.py nao-existe.json -o out.json` -> FileNotFoundError
com traceback.

## Aceite

- [ ] Transcript ausente/invalido vira erro JSON + exit 2.
- [ ] Escrita de out/report com falha de IO tambem e tipada.
- [ ] Sucesso continua imprimindo stats em JSON na stdout.
- [ ] Gate: regressao CLI com arquivo inexistente e JSON invalido.

## Answer

Resolved. Regression coverage in tests/test_laya_compactor.py
(audit-r2 section). Suite: 16 passed.
