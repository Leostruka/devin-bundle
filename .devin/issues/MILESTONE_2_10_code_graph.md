# MILESTONE 2 / ISSUE 10: `extensions/code-graph/` - indice estrutural minimo + doc de roteamento

Status: resolved · Source: github.com/DeusData/codebase-memory-mcp (MIT, v0.12.1; padrao SQLite FTS5 + camel tokenizer; claim de economia NAO reproduzido - skillproof.dev +127%) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#7/D · Blocked-by: none · Blocks: none (gate de benchmark separado)

## Contexto & Valor

- Decisao aprovada: pattern-port + benchmark gate. NAO adotar o cbm como MCP: claim de -99% tokens nao reproduziu (bench independente mediu +127% MAIS tokens); 17 tools excedem o cap de 15 do mcp-governance; C binary + daemon e pesado.
- O padrao vale: indice estrutural local (path, simbolos, imports, mtime+hash) em SQLite FTS5 stdlib - consultas "onde X e definido/chamado", outline de arquivo, edges cross-file - sub-ms, zero LLM.
- Valor: fecha a perna estrutural do roteamento tripartite (sec D.1) sem custo de MCP nem dependencia nativa.

## Brain (Skill)

- Doc de roteamento (nao e skill nova): adicionar tabela de roteamento D.1 em `skills/skill-discovery` reference ou `research` deep-mode pointer - quando usar code-graph vs semble vs ask_laya_glob vs rg vs read. Update de `orchestrator_prompts_v2.md` linha "Codebase exploration" para citar code-graph como primeira parada estrutural quando presente, com fallback identico ao SEMBLE-DOWN (`[GRAPH-DOWN]`).

## Muscle (Extension)

- `extensions/code-graph/`:
  - `index.py` - build incremental: walk de exts conhecidas (.py/.ts/.tsx/.js/.md/.ps1/.sh...), extrai simbolos via regex por linguagem (def/class/function/export/import), grava SQLite FTS5 (`sqlite3` stdlib) com tokenizer camel/snake split; mtime+sha1 por arquivo -> purge+relink de nos mudados.
  - `query.py` - `symbols <q>`, `outline <file>`, `refs <symbol>` (tabela de edges import), `files <substr>`; saida bounded (`--limit`, `max_output_tokens` cap estilo cbm).
  - `detect_changes.py` - diff mtime+hash vs snapshot (para hooks/audit).
  - `selftest.py`; DB em `.devin/code-graph/index.db` (gitignored).
- Stdlib only (sqlite3 ja e stdlib); sem tree-sitter, sem daemon, sem embeddings na v1.

## Step-by-step

0. `index.py` no proprio bundle como primeiro corpus; medir tempo/tamanho.
1. `query.py` bounded; smoke: "onde esta install-ledger" retorna arquivo certo.
2. `detect_changes.py` + doc de roteamento nos dois pontos (skill-discovery ref + orchestrator prompts).
3. Gate: `pytest` (index/query/change-detection em fixture); benchmark mini: tokens-por-resposta vs rg em 10 queries estruturais; `audit.py` 0 errors.

## Non-goals

Sem MCP server, sem tree-sitter/grammars vendored, sem embeddings, sem watch daemon; cbm real so via issue de benchmark futura (lazy-enable em mcp_config.disabled.json se vencer >=30% mediana de economia).

## Answer

- `extensions/code-graph/` stdlib-only: `code_graph.py` core (FTS5 + camel/snake token split, mtime+sha1 incremental, purges vanished), `index.py`, `query.py` (symbols/outline/refs/files + `--limit`/`--json` + `[GRAPH-DOWN]` exit 2 sem indice), `detect_changes.py`, `selftest.py`. DB gitignored em `.devin/code-graph/index.db`.
- Corpus real: 1035 arquivos / 5964 simbolos / 1.06s index full. Smoke: `symbols reconcile` acha install-ledger; `files install-ledger` acha o arquivo.
- Routing doc: orchestrator_prompts_v2.md TOOLING RULES (code-graph antes do semble, `[GRAPH-DOWN]` fallback) + skill-discovery category shortcut.
- 5 testes: camel/snake tokens, outline/refs/files, detect clean/dirty/new, reindex incremental, GRAPH-DOWN sem indice.
- Bugs achados no loop: FTS nao faz substring (prefix `*` necessario); `-` em query quebra MATCH (sanitize `\w+`); `line` nao existe na tabela fts (join symbols).
- Non-goals respeitados: sem MCP, sem tree-sitter, sem daemon, sem embeddings.
