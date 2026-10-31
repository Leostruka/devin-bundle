# 01 - Nao parear tool_result orfao com tool_use sem id

Status: claimed
Priority: P2
Type: data-integrity
Blocked by: none

## Contexto

`extensions/laya-compactor/transcript.py:collect_items` registra
`pending[b.get("id")] = pair` mesmo quando `b["id"]` e None. Todos os
tool_use sem id colidem na chave None; um `tool_result` sem
`tool_use_id` faz `pending.get(None)` e pareia com o ULTIMO tool_use sem
id -- um par arbitrario e incorreto.

## Impacto

`orphan_check` aprova um pareamento espurio e `pair_actions` trata os
dois como um par: uma decisao "drop" no tool_use remove tambem o
tool_result de um chamado diferente -- perda de conteudo errada na
compactacao.

## Reproducao

Transcript com tool_use sem id e um tool_result sem tool_use_id:
`pairs()` os junta em `p:m?b?` compartilhado em vez de manter o resultado
sem par.

## Aceite

- [ ] pending so e populado quando o id do tool_use nao e None.
- [ ] tool_result sem tool_use_id fica com pair=None (orfao visivel,
  nao mascarado).
- [ ] orphan_check reporta orfao real nesses casos.
- [ ] Gate: testes de compactacao existentes + regressao de pareamento.

## Answer

Resolved. Regression coverage in tests/test_laya_compactor.py
(audit-r2 section). Suite: 16 passed.
