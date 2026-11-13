# 03 - Isolar falhas de leitura por nota em memory-retrieval

Status: resolved
Priority: P2
Type: reliability
Blocked by: none

## Contexto

`scripts/memory-retrieval.py:load_note()` le cada `*.md` de
`.devin/memory/` sem tratamento de erro (linha 98). Um arquivo com
encoding invalido, permissao negada ou leitura truncada levanta
`OSError`/`UnicodeDecodeError` -- sob `_hookrun` isso mata so o script
(fail-open), fazendo a recuperacao inteira ficar muda: nenhuma nota e
injetada e nenhum aviso chega ao stderr do CLI. Sob spawn direto, o
processo morre com traceback (exit 1).

## Impacto

Uma unica nota corrompida desativa silenciosamente todo o recurso de
memoria -- degradacao invisivel, oposta ao comportamento esperado de
"pular a nota ruim e continuar".

## Reproducao

Fixture: `.devin/memory/` com um .md valido e um arquivo binario
corrompido. `main()` lanca antes de emitir qualquer contexto.

## Aceite

- [ ] Erro por arquivo e contido: nota ilegivel e pulada com aviso em
  stderr; notas validas continuam pontuando.
- [ ] `main()` continua saindo 0 sem stdout quando nada casa.
- [ ] Aviso de nota pulada nao injeta conteudo em additionalContext.
- [ ] Gate: `python -m pytest tests/ -k memory -q`.

## Answer

main() envolve load_note em try/except (OSError, ValueError): nota ilegivel e pulada com aviso em stderr, notas validas continuam. Regressao test_memory_retrieval_skips_unreadable_note: nota boa injetada + aviso emitido + exit 0.
