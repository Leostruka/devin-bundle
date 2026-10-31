# 02 - Incluir nomes de arquivo no hash de pasta do install.ps1

Status: resolved
Priority: P2
Type: distribution-bug
Blocked by: none

## Contexto

`install.ps1:Get-FolderHash` (linhas 103-110) junta apenas os hashes de
conteudo de cada arquivo ordenado por nome. Um arquivo renomeado com o
mesmo conteudo produz hash identico -> o instalador pula a copia e o
destino fica com o nome velho sem ganhar o novo (drift silencioso).

O equivalente Bash (`dir_hash` em install.sh/export.sh) inclui o nome no
hash: `sha256sum` imprime `hash  ./caminho` por linha antes do digest
agregado -- renomear muda o digest. Os dois instaladores divergem.

## Impacto

Rename de SKILL.md/arquivo de skill/script entre versoes nao e detectado
no Windows: o update e pulado e a instalacao fica com layout velho.

## Reproducao

Duas pastas com mesmo conteudo e nomes diferentes produzem a mesma
string em `Get-FolderHash`; em Bash o `dir_hash` difere.

## Aceite

- [ ] Linhas do hash agregado carregam hash + caminho relativo (mesma
  semantica do `sha256sum` Bash).
- [ ] Rename com conteudo identico altera o resultado.
- [ ] Diretorio vazio continua "" e exclusao por regex continua
  equivalente.
- [ ] Gate: ParseFile limpo + comparacao funcional em pastas temporarias.

## Answer

Get-FolderHash agora emite "hash  ./relpath" por arquivo (mesma forma do sha256sum do dir_hash Bash). Verificado via pwsh: rename com mesmo conteudo altera o hash (RENAME-DETECTED), edicao de conteudo altera (CONTENT-DIFF), ParseFile limpo.
