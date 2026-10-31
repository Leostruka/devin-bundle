# Auditoria geral - indice de issues e evidencias

Snapshot: working tree `feature/egm-runtime-rollout`, com alteracoes locais
preexistentes. Nao e uma auditoria exclusiva de um commit ou PR.

## Backlog

| ID | Prioridade | Status | Achado | Reproducao |
|---|---|---|---|---|
| [01](issues/01-bound-input-reads.md) | P2 | resolved | Leitura integral antes dos limites DOM e manifests | `reproduce.py reads` + fonte do loader |
| [02](issues/02-tpu-batch-completeness.md) | P2 | resolved | Batch TPU declara sucesso com respostas faltantes | `reproduce.py tpu`, backend simulado |
| [03](issues/03-heldout-output-clobber.md) | P2 | resolved | --out pode sobrescrever o corpus/manifesto | `reproduce.py clobber`, somente temporarios |
| [04](issues/04-compact-tool-response.md) | P2 | resolved | Digest ignora erros em tool_response | `reproduce.py response` |
| [05](issues/05-hook-extension-boundary.md) | P2 | resolved | Hook contradiz fronteira scripts/extensions | `reproduce.py boundary`, AST |
| [06](issues/06-blender-json-schema.md) | P2 | resolved | JSON valido nao-objeto escapa do servidor Blender | `reproduce.py protocol`, bpy simulado |
| [07](issues/07-bash-hash-whitespace.md) | P2 | resolved | Hash Bash falha com nomes contendo espacos | `reproduce.py hashes`, funcoes reais |
| [08](issues/08-ci-whitespace-fail-open.md) | P3 | resolved | Push CI mascara falhas de git diff --check | `reproduce.py ci-mask`, fonte + shell |
| [09](issues/09-rust-test-gate-empty.md) | P3 | resolved | Cargo test executa zero casos | Cargo local + fonte Rust |

Total: 9 issues; 7 P2 e 2 P3 -- **todas resolvidas na mesma rodada**, sob a
diretriz "se nao ha, implemente" (a auditoria original nao alterava codigo;
as correcoes vieram da ordem posterior de resolucao sistematica).
Os epicos de `../egm-laya-bitnet-upgrade/` continuam referencias de escopo;
os tickets acima tratam falhas especificas ou lacunas de evidencia.
Busca de duplicatas: issues existentes em `.devin/scratch/*/issues/` e
`.devin/issues/`, pelos simbolos e causas documentados. Nao houve publicacao
ou deduplicacao remota no GitHub.

## Como reproduzir

A partir da raiz do repositorio:

```sh
python .devin/scratch/general-audit/reproduce.py all
```

O script retorna exit0 quando os oito comportamentos auditados continuam
confirmados. Isso NAO significa que foram corrigidos. Nao usa credenciais,
rede ou inferencia real. Fixtures de clobber sao criadas e removidas em
TemporaryDirectory; somente arquivos do proprio reprodutor sao afetados.
Casos individuais e assercoes de aceite constam de cada issue.

## Verificacoes atuais

| Check | Resultado observado | Evidencia |
|---|---|---|
| `python audit.py` | exit0; 0 erros, 2 avisos live!=bundle | `.devin/ledgers/general-audit-final.log:1612-1618` |
| `python -m pytest -q -o addopts=` | 2029 passaram, 5 skips | `.devin/ledgers/general-audit-pytest.log:30` |
| `python -m pytest tests/held-out/ -q -o addopts=` | 212 passaram | `.devin/ledgers/general-audit-heldout.log:4` |
| `cargo test --manifest-path extensions/rust-core/Cargo.toml --offline --locked` | exit0; compilacao, 0 testes | `.devin/ledgers/general-audit-cargo.log:15-20` |
| `bash -n install.sh` e `bash -n export.sh` | exit0 | comando encadeado de verificacao |
| `node --check scripts/mermaid-parse-check.js` | exit0 | comando encadeado de verificacao |
| ParseFile de install.ps1/export.ps1 | 0 erros em cada arquivo | PowerShell Parser, sem executar instaladores |
| Reproducoes direcionadas | 8 confirmadas | `.devin/ledgers/general-audit-reproductions.json` |
| Metadados e links das issues | 9 arquivos/9 links; 7 ready-for-agent, 2 needs-triage | assertions stdlib + leitura dos metadados |
| Hooks consolidados apos os artefatos | 8 passaram | `.devin/ledgers/general-audit-artifacts.log:2` |
| `git diff --check` | exit0; apenas avisos LF/CRLF preexistentes | verificacao final do working tree |

Os avisos do audit sao user-prompt.py e compact-gate.py diferentes da live.
Nenhuma reinstalacao foi feita para ocultar essa divergencia esperada.
Testes verdes nao demonstram ausencia de bugs: as reproducoes expuseram
caminhos que os testes atuais nao impedem.

## Cobertura e limites

- Inspecionados: contratos do bundle, governanca de hooks, CI, helpers de
  distribuicao, fronteiras de entrada/saida DOM e inferencia, envelope Blender,
  markup nativo OpenUI e gate Rust. Nao houve leitura exaustiva de cada linha
  de todas as extensoes ou skills.
- Inputs de probes sao sinteticos. vLLM e bpy foram substituidos onde marcado;
  nao se afirma falha observada em TPU fisica ou Blender real nesta auditoria.
- A suite local nao substitui a matriz CI em Linux/macOS/Windows/Python3.11.
  Nao houve novo push, instalacao live ou execucao remota de CI.
- Os cinco skips continuam skips; nao foram removidos ou desativados testes.
  Nao se reutilizam smoke tests historicos como prova atual de Chrome/inferencia.
- pip_audit, bandit, semgrep e shellcheck nao estao disponiveis no ambiente
  inspecionado. Nao foram instalados. Houve inventario de manifests, mas nao
  uma varredura CVE transitiva, SAST automatizada completa ou auditoria de licencas.
- Nao houve crawling de credenciais pessoais, exploracao de servicos externos,
  benchmark de qualidade de modelos, auditoria manual por leitor de tela,
  nem validacao de hardware TPU/GPU.
- A grafia de flags vLLM dependentes de versao nao foi registrada como bug
  confirmado sem validar a versao real do backend.

## Sequenciamento

01 e 03 compartilham heldout_batch.py: evitar edicao concorrente desse arquivo.
04 e 05 compartilham compact-gate.py: reconciliar a triagem arquitetural antes
de refatorar seu transporte. Nao ha dependencia funcional artificial entre
os demais tickets.
