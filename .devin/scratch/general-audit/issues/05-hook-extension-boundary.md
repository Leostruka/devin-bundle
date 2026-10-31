# 05 - Reconciliar imports do compact-gate com a fronteira arquitetural

Status: resolved
Priority: P2
Type: architecture-drift
Blocked by: none

## Achado

`.devin/ARCHITECTURE_MANIFEST.md:23-24,59-61` exige stdlib-only em scripts
e proibe imports de extensions pelos hooks.
`scripts/compact-gate.py:216-223` injeta laya_dir no sys.path e importa
decision_contract e laya_client. `_laya_ext_dir` resolve extensions/laya-tools.
Existe contradicao direta entre a declaracao vigente e a implementacao.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py boundary
```

Analise AST da fonte atual identifica decision_contract na linha221 e
laya_client na linha222. E evidencia estatica; nao implica que terceiros
sejam necessariamente carregados ou que um guard critico tenha falhado.

## Encaminhamento

Triar a colocacao de um contrato/transporte hook-safe compartilhado,
preservando uma fonte canonica e stdlib-only. Nao enfraquecer o manifesto
ou introduzir excecao silenciosa para aprovar o check. Qualquer excecao
arquitetural requer decisao explicita e documentada do mantenedor.

## Aceite

- [ ] Decisao de arquitetura registrada antes de mover modulos.
- [ ] Hooks nao importam extensions segundo o contrato aprovado.
- [ ] Testes cobrem imports diretos e caminhos adicionados dinamicamente.
- [ ] Indisponibilidade de Laya preserva fallback deterministico.
- [ ] Guards criticos permanecem fail_closed=true e sem rede sincronica nova.
- [ ] Gate funcional: `python -m pytest tests/test_jev_routing.py -q`.
- [ ] Gate estrutural adicional valida a fronteira, nao apenas o nome do import.

## Answer

Direcao escolhida: honrar o manifesto, nao cria excecao. `compact-gate.py`
agora e stdlib-only (AST confirma: hashlib/json/os/socket/subprocess/sys/
time). O import de `decision_contract`/`laya_client` virou um espelho
documentado de ~230 linhas: `_load_config`, `_effective_mode` +
`_activation_errors` (mesmas regras de calibracao), `_ensure_daemon`
(lockfile, digest de config, spawn via `laya_cli.py` como subprocesso --
exec, nao import) e `_recommend` (protocolo hello/auth + request line,
com verificacao de request_id e candidato no conjunto). `deadline` agora
usa `deadline_ms` do profile. Fixtures de teste migradas para o novo
seam `_laya_cli_path`. `pytest tests/test_hook_laya_gate.py
tests/test_jev_routing.py -q`: 44 passed; reprodutor `boundary` ja nao
confirma o defeito.

## Comments

Drift constatado no working tree; a auditoria nao atribui origem temporal
nem altera regras para acomodar a divergencia.
