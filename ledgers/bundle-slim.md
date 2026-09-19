# GATES: bundle-slim (BRUTAL_AUDIT execution)

Plan: `.devin/notes/BRUTAL_AUDIT_3000_10_31.md` — EXECUTION PLAN, Fases 0-6.
Branch: `chore/bundle-slim` (from `feat/hybrid-rust-extensions`).

- [x] G0: baseline reproduzível salvo; audit+pytest verde pré-mudança
  CHECK: test -f .devin/notes/hook-bench-baseline.json && python audit.py && python -m pytest tests/ -q
  EXPECT: baseline json existe; audit 0 errors; pytest sem failures
  EVIDENCE: hook-bench-baseline.json N=10 (exec ~486ms, write ~271ms, prompt ~178ms); audit 0 errors/4 warn pré-existentes; pytest 432 passed/1 skipped. Sentinel: `.devin/hooks.v1.json` não dispara mid-session + nudge aparece 1×/prompt → project file não carregado ou deduplicado; docs confirmam user-level só lê config.json.hooks.

- [x] G1: superfícies duplicadas eliminadas (sentinel decide fonte única de hooks)
  CHECK: test ! -f .devin/hooks.v1.json && python audit.py && python -m pytest tests/ -q
  EXPECT: cópia stale removida; hooks com fonte única documentada; verde
  EVIDENCE: `.devin/hooks.v1.json` removido; `config.json.hooks={}` + `render-user-hooks.py` (install injeta, export stripa); audit 0 errors (4 warn pré-existentes); pytest 433 passed. `global_rules.md` mantido (consumidores existem); agents/ divisão documentada em `.devin/agents/README.md`.

- [x] G2: hooks consolidados; latência exec-hook medida cai
  CHECK: python .devin/notes/hook-bench-post.py 2>/dev/null || true; python audit.py && python -m pytest tests/ -q
  EXPECT: bindings ~10; exec total <= ~200ms medido (alvo ~155); verde
  EVIDENCE: 22→9 bindings (6 guards consolidados via _hookrun in-process). N=10: exec 486→193ms (−60%), write 271→145ms, prompt 178→102ms, Stop 158→87ms (hook-bench-post.json). Desvio documentado: nudge ficou command-hook (type:prompt = eval LLM/evento — pior); signature mantida em pre-write+stop (custo ~0 in-process). audit 0 errors; pytest 439+8 passed.

- [ ] G3: skills ~50; monstros split (SKILL.md <=10KB + REFERENCE.md); triggers nas raras
  CHECK: ls skills | wc -l; python audit.py && python -m pytest tests/ -q
  EXPECT: count ~50 (+/-5); SKILL-TIERS/manifest/ask-bundle atualizados; verde
  EVIDENCE: pending

- [ ] G4: AGENTS.md <= 11KB; regras fundidas; constraint-pinning/audit/manifest sincronizados
  CHECK: wc -c AGENTS.md; python audit.py && python -m pytest tests/ -q
  EXPECT: <= 11264 bytes; verde
  EVIDENCE: pending

- [ ] G5: adoção nativa decidida item a item (plugin, permissions, sandbox, tool-args hit-rate, doctor)
  CHECK: grep -n "Fase 5" .devin/notes/hook-bench-baseline.json 2>/dev/null; ls docs/DEVIN-CLI-COMPATIBILITY.md
  EXPECT: decisões registradas em commit(s); itens não adotados documentados com motivo
  EVIDENCE: pending

- [ ] G6: verificação final — audit 0 errors, pytest verde, bash -n install.sh, diff report
  CHECK: python audit.py && python -m pytest tests/ -q && bash -n install.sh
  EXPECT: tudo verde; gates do plano (AGENTS<=11KB, ~50 skills, exec-hook <=200ms) cumpridos
  EVIDENCE: pending

## G3 — Consolidação de skills 83→48 (2026-10-31)

OUTCOME: 22 merges executados; 83→48 skills (gate ≤~50 ✓). SKILL.md viraram routers
(~500-1600 tok); conteúdo pesado em modes//reference/ (progressive disclosure).
CHECK: `python audit.py` + `python scripts/validate-skill-format.py` + `python -m pytest tests/ -q`
EXPECT: 0 errors; 131/131 skills pass; suite verde
EVIDENCE: audit Errors=0 (warnings = drift live-vs-bundle pré-install + pycache);
validate 131/131; pytest 442 passed, 1 skipped (baseline 432 — +10 testes novos).
Refs antigas→canônicas varridas em AGENTS/README/docs/agents/scripts/skills/tests;
fixtures renomeadas (devin-config, knowledge-modeling); NOTE_SUBDIR alinhados;
audit.py new_skills → nomes merged; leo-detail.md → orchestration-detail.md.

## G4 — AGENTS.md minificado 18.3KB→10.9KB (2026-10-31)

OUTCOME: merges do audit executados — 12+17+21→12, 15+16→15, 19+23+24+26→19,
18+22→18, 3+4→3; regras-pointer (9, 27) e corpos terse comprimidos; aliases de
número preservados no índice (refs externas intactas).
CHECK: `wc -c AGENTS.md` + `python audit.py` + `python -m pytest tests/ -q`
EXPECT: ≤11264 bytes; rule_count=28; 0 errors; suite verde
EVIDENCE: 11199 bytes (10.9KB, −39%); audit Errors=0; 442 passed, 1 skipped.
PINNED_CONSTRAINTS alinhado aos números canônicos; README "20 regras"→"28
entradas (20 corpos + 8 aliases)"; manifest hash de constraint-pinning resync.
