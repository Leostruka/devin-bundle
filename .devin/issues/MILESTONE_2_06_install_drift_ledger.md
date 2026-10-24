# MILESTONE 2 / ISSUE 06: install/export drift ledger - installs.json + reconcile 5-state + backup

Status: planned · Source: github.com/msitarzewski/agency-agents-app (MIT; `src-tauri/src/install/mod.rs`, `memory-bank/systemPatterns.md`) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#6/E · Blocked-by: none · Blocks: M2_07

## Contexto & Valor

- `install.ps1`/`export.sh` copiam e mesclam mas nao tem ledger: nao sabemos se um arquivo instalado ainda bate com o bundle, se foi modificado localmente, ou se e estranho (foreign). `manifest.json` tem `export_hash` por skill mas nenhuma reconciliação contra o live config.
- Upstream resolve deterministicamente: `installs.json` (slug, tool, scope, dest, source_hash, rendered_hash=sha256 dos bytes escritos, installed_at, corpus_version) + `corpus-index.json` -> reconcile em 5 estados [Current/Outdated/Modified/Removed/Foreign]; `backup_if_differs` copia bytes anteriores fora dos dirs de destino, aborta o write se backup falhar, pula quando byte-identical.
- Valor: install idempotente auditavel + backup garantido antes de sobrescrever; deteccao de drift entre bundle e live config.

## Brain (Skill)

- Nenhuma; doc curto dentro de `devin-config` apontando `python scripts/install-ledger.py status`.

## Muscle (Extension/Scripts/Installers)

- `scripts/install-ledger.py` (stdlib): comandos `record`, `reconcile`, `status`; ledger `.devin/install-ledger/installs.json` + `corpus-index.json` (ordem estavel de chaves); renderers devem ser deterministicos (sem timestamps/randomness nos bytes renderizados - render timestamp vai no record, nao no conteudo).
- `install.ps1`/`install.sh`/`export.*`: chamar `record` apos cada write bem-sucedido; `backup_if_differs` antes de overwrite (`%APPDATA%/devin/.backups/<name>.<fs-safe-ts>`; falha de backup aborta o write; byte-identical pula).
- `audit.py`: novo check - reconcile reporta estados; Modified/Foreign listados como warning (nao erro).

## Step-by-step

0. `install-ledger.py` com schema + reconcile 5-state + testes de tabela-verdade.
1. Wire em install.ps1 (record+backup) e install.sh (mesmo contrato); manter flags existentes.
2. `audit.py` ganha check `Ledger:`.
3. Gate: `pytest` novos testes (reconcile cobre os 5 estados; backup aborta write em falha simulada); `install.ps1 -DryRun` sem regressao; `audit.py` 0 errors.

## Non-goals

Sem renderizacao multi-CLI ainda (M2_07); sem assinar/hash de conteudo fora dos arquivos geridos; sem migrar manifest.json (continua metadata, ledger e runtime).
