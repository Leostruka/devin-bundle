# MILESTONE 2 / ISSUE 09: `extensions/harness-tree/` - component-tree diff/validate engine (SurfaceSpec)

Status: resolved · Source: github.com/google-research/harness2 (Apache-2.0; `core/tree.py`, `SurfaceSpec`, `ns()` em `schedule.py`) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#1/E · Blocked-by: M2_08 (spec de componentes) · Blocks: none

## Contexto & Valor

- PPC (M2_08) precisa de uma representacao formal do harness para propor/validar/compor: upstream modela o harness como arvore `c1..c8` = `dict[path->content]` com `SurfaceSpec` parametrizando paths/caps/frontmatter/hooks por ferramenta; edicao segue "omitted-is-inherited" (propostas emitem so diffs).
- Valor: engine deterministico e stdlib que trata AGENTS.md/rules/hooks/skills/agents/scripts/mcp como uma arvore difeavel e validavel - permite probe/compose mecanicos e snapshots reproduziveis de runs.

## Brain (Skill)

- Nenhuma; usado por self-improvement (M2_08) via CLI: `python extensions/harness-tree/tree.py {snapshot,diff,validate,apply,ns}`.

## Muscle (Extension)

- `extensions/harness-tree/`:
  - `tree.py` - `ComponentTree` = dict ordenado path->content; `read(root, spec)`/`validate(spec)`/`diff(a,b)`/`write(base,diff)`; omitted-is-inherited; `RESERVED` lista de scripts protegidos.
  - `specs.py` - `SurfaceSpec` dataclass: mapeamento c1..c8 -> paths do bundle (system prompt=AGENTS.md+global_rules.md, guardrails=rules+hooks, memory=.devin/memory+memory-*, tool guidance=skill-discovery/ask-bundle docs, subagents=agents/*.md, skills=skills/, scripts=scripts/, plugins=mcp_config+extensions manifest).
  - `ns.py` - namespacing de runs: `.devin/runs/<ts>-<seed>/` com tree snapshot + evidence log, rerun resume.
  - `selftest.py` + `tests/` - round-trip read->diff->apply==identidade; validate detecta path fora do spec.
- Stdlib only; sem deps; sem escrita fora de `.devin/runs/` em modo snapshot.

## Step-by-step

0. `specs.py` SurfaceSpec devin (unico alvo; outras rows chegam com M2_07/platform branch).
1. `tree.py` ops + RESERVED (check-ai-signature.py, install-ledger.py protegidos de mutate).
2. `ns.py` snapshot dir + rerun-resume.
3. Gate: `pytest` round-trip verde; `audit.py` 0 errors; dry-run `validate` no bundle atual reporta arvore completa sem erros.

## Non-goals

Sem mutacao automatica de skills/rules (engine e ferramenta, decisao fica no PPC humano/agente); sem CLI de sweep; sem execucao de rollouts.

## Answer

Shipped `extensions/harness-tree/` (stdlib only):

- `specs.py` - SurfaceSpec devin: c1 system-prompt (AGENTS.md + global_rules.md), c2 guardrails (.devin/rules + hooks.v1.json), c3 memory (.devin/memory), c4 tool-guidance (skill-discovery/ask-bundle/SKILL-TIERS), c5 subagents (.devin/agents), c6 skills/, c7 scripts/, c8 plugins (mcp_config+manifest); `component_of`/`skipped` helpers; noise-dir excludes.
- `tree.py` - `ComponentTree` = ordered path->content; `read`/`validate`/`diff`/`apply` + `tree_hash`; omitted-is-inherited (diff lists only changes, None=delete); RESERVED set (check-ai-signature, install-ledger, check-push-green, stop-guard) refused in `apply`; CLI snapshot/validate/diff/apply; stdout reconfigured utf-8 (Windows cp1252).
- `ns.py` - `.devin/runs/<ts>-<seed>/` snapshot (tree.json + meta.json + evidence.log), `create`/`resume`, writes only inside runs dir; `.devin/runs/` gitignored.
- `selftest.py` + `tests/test_harness_tree.py` - 9 tests: round-trip diff/apply identity, reserved + outside-spec refusal, delete propagation, validate clean/missing, ns create/resume, real-bundle validate.

Real bugs found while building: (a) c4 paths also under c6 `skills/` yielded duplicate entries - `_iter_files` now first-wins dedupe; (b) console cp1252 crashed on `→` in payload - stdout reconfigured utf-8. Real bundle `validate`: 0 problems, 566 in-spec files. README/TOOLS-MAP extension rows added (also filled pre-existing code-graph gap).
