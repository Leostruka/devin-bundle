# 07 - Suportar nomes com espacos no hash de diretorios Bash

Status: resolved
Priority: P2
Type: distribution-bug
Blocked by: none

## Achado

- `install.sh:54-61`: dir_hash e dir_hash_ext usam find/sort/xargs sem
  delimitadores seguros para nomes de arquivo.
- `export.sh:52-54`: mesmo pipeline em dir_hash.
- `install.sh:264-267,503-506,592-595` e `export.sh:254-257` consomem os hashes.

Um arquivo permitido como asset name.txt e dividido em dois argumentos
pelo xargs. sha256sum falha, com stderr ocultado. Com set -euo pipefail,
o helper retorna erro e pode interromper instalacao/exportacao incremental.
Nao se trata de arquivo corrompido: somente o nome contem um espaco.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py hashes
```

O reprodutor extrai as funcoes da fonte, preserva set -euo pipefail e usa
somente dois diretorios temporarios. Para os tres helpers:

- asset.txt: exit0.
- asset name.txt: exit123.

No Windows, o harness resolve Bash por caminho absoluto e fornece stdin
em bytes LF, evitando confundir Git Bash/WSL e conversao CRLF com o defeito.
Nao executa o instalador inteiro nem escreve na configuracao live.

## Correcao solicitada

Calcular hashes com transporte seguro de nomes, preservando a ordem e
as exclusoes de runtimes/artefatos. Verificar compatibilidade Linux/macOS,
sem introduzir dependencia obrigatoria ausente dos sistemas suportados.

## Aceite

- [ ] Espacos, tabs e nomes Unicode nao interrompem o hash.
- [ ] Alterar o conteudo altera o hash, inclusive nos nomes especiais.
- [ ] Funciona para skills, extensoes e docs nos dois scripts.
- [ ] Exclusoes de .venv/target/binarios continuam equivalentes.
- [ ] Teste de regressao usa funcao real, nao copia divergente.
- [ ] Gates: `bash -n install.sh` e `bash -n export.sh`, mais regressao dos helpers.

## Answer

`dir_hash`/`dir_hash_ext` em `install.sh` e `export.sh` agora usam
`find -print0 | xargs -0 sha256sum | sort | sha256sum`: delimitacao por
NUL tolera espacos/tabs/unicode, e ordenar as linhas de hash preserva
determinismo sem `sort -z` (ausente no BSD/macOS, plataforma suportada).
Verificado em Bash real: nomes com espaco/tab/unicode exit 0; alteracao
de conteudo altera o hash; arquivos em .venv/target/*.so continuam
excluidos do dir_hash_ext. `bash -n` limpo; reprodutor `hashes` nao
confirma mais o defeito.

## Comments

Reproducao do helper; nao se afirma instalacao real em Linux/macOS nesta auditoria.
