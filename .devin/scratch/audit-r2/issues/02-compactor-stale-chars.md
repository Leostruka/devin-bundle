# 02 - Atualizar chars apos truncate para medir reducao real

Status: claimed
Priority: P2
Type: measurement-bug
Blocked by: none

## Contexto

`extensions/laya-compactor/compact.py`: `_apply_pair_action` encurta
`it["text"]` mas nao atualiza `it["chars"]`. `compact()` calcula
`new_chars`/`reduction` sobre contagens pre-truncacao.

## Impacto

A reducao medida e sempre MENOR que a real: textos truncados a
TRUNCATE_HEAD contam pelo tamanho original. Casos com bastante truncate
podem cair abaixo de REDUCTION_FLOOR e devolver o transcript original
em vez da versao compactada -- decisao correta descartada por metrica
errada.

## Reproducao

Transcript com um par grande decidido como "truncate": `stats.reduction`
e calculado com chars antigos; o texto efetivamente escrito e ~300
chars + snip.

## Aceite

- [ ] it["chars"] reflete o texto pos-truncate antes de new_chars.
- [ ] stats.reduction corresponde ao tamanho real do output.
- [ ] REDUCTION_FLOOR passa a ser avaliado com dados corretos.
- [ ] Gate: regressao medindo reduction esperado em fixture controlada.

## Answer

Resolved. Regression coverage in tests/test_laya_compactor.py
(audit-r2 section). Suite: 16 passed.
