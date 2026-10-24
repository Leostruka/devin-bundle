# MILESTONE 2 / ISSUE 01: `extensions/design-intelligence/` - BM25 engine + design corpus

Status: planned · Source: github.com/nextlevelbuilder/ui-ux-pro-max-skill (MIT, v2.15.0) + github.com/vercel-labs/agent-skills (MIT) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#2/B#3/C · Blocked-by: none · Blocks: M2_03, M2_04

## Contexto & Valor

- `creative-engineering` hoje carrega 16 arquivos `.md` inteiros por estilo; nao existe busca local: cada consulta de design paga o arquivo completo em contexto.
- Upstream prova o padrao: BM25 stdlib (~60 LOC, k1=1.5/b=0.75, sinonimos + difflib typo recovery), CSV corpus (79 estilos, 192 paletas, 74 tipografias, 22 stacks/1.260 regras), `search.py` emite top-3 com truncamento = resposta deterministica e barata.
- Valor: motor de recomendacao de design local, offline, sem LLM; base unica para os upgrades de cerebro (M2_03/04) e para o lint (M2_02 consome o mesmo diretorio).

## Brain (Skill)

- Nenhuma skill nova. Este issue e musculo puro; consumidores chegam em M2_03/04.
- Registrar o comando no header docstring: `python extensions/design-intelligence/search.py "<query>" --domain <d> [--top-k N]`.

## Muscle (Extension)

- `extensions/design-intelligence/`:
  - `core.py` - classe BM25 (fit/score, `_SYNONYMS`, stopwords) port stdlib.
  - `search.py` - CLI: `--domain`, `--top-k` (default 3), `TRUNCATE_AT`, `UNTRUNCATED_COLS`, cache de indice por mtime, auto-detect de dominio com runner-up reportado, sugestao de vocabulario em 0-result.
  - `design_system.py` - fan-out multi-dominio -> `design-system/MASTER.md` + `pages/{page}.md`; dials `--variance/--motion/--density`; `--persist`, skip-unless-`--force`.
  - `data/` - corpus CSV portado (styles, colors, typography, products, ux-guidelines, icons, motion, charts, landing, ui-reasoning) + `stacks/*.csv`.
  - `data/frontend-rules/` - regras vercel-labs vendorizadas como docs indexados (react-best-practices, composition-patterns, react-native-skills, view-transitions).
  - `data/aesthetics/` - alias/indice para `media-tools/knowledge_bases/aesthetics/` (fonte unica nao move; index.json vira documento do corpus).
  - `tests/` - relevancia (queries com top-1 esperado) + fixture CSV.

## Step-by-step

0. Port `core.py`/`search.py` -> stdlib Python; dry-run em 10 queries conhecidas.
1. Importar corpus CSV; `validate_csv.py` (schema check por dominio).
2. Vendorizar regras vercel como .md indexados; mapear `index.json` de aesthetics para documento de corpus.
3. `design_system.py --persist` smoke em 1 produto exemplo.
4. Gate: `pytest tests/` verde + `python audit.py` 0 errors + queries benchmark retornam top-3 esperado; self-check `python extensions/design-intelligence/search.py "saas dashboard dark" --top-k 3` nao-vazio.

## Non-goals

Sem embeddings/vetores, sem daemon, sem dependencias externas; nao reescrever `index.json` de aesthetics (camada de alias permanece).
