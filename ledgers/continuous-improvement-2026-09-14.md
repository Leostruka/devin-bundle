# LEDGER: continuous-improvement session 2026-09-14

## SESSION CONTRACT

- DELEGATION: authorized (user explicitly authorized subagents for independent verification, 2026-09-14 session). qa-ci may run `tests/held-out/`; implementer must not read/edit `tests/held-out/`.
- DELEGATION UPDATE (user, same session): "faca sem subagente o C1, C4 e D1" — C1/C4/D1 phase runs with DELEGATION: disabled; no run_subagent; verification = fresh tool-call re-execution by controller. Earlier C2/C3 subagent evidence remains valid.
- Ledger path decision: `.devin/ledgers/*` is gitignored (`.gitignore` lines `.devin/ledgers/*` + whitelist). Tracked convention = root `ledgers/` (existing CI ledgers present). Using `ledgers/continuous-improvement-2026-09-14.md`.
- NO PUSH / NO COMMIT. All changes stay local.

## INPUT_REGISTER

| ID | Origin | Content | State |
|----|--------|---------|-------|
| IN-01 | user, leo quick-start menu | "Improve skills / config" | routed: continuous-improvement |
| IN-02 | user, ask_user_question | Target = Full audit (FASE 0) | accepted |
| IN-03 | user, ask_user_question | DELEGATION = authorized | applied |

## SOURCE_REGISTER

Full table from researcher subagent (agent 1ed91db0) — S1..S16. Decisive rows:

- S1 accept: 8 hook events incl. PostCompaction — docs.devin.ai/cli/extensibility/hooks/overview (read: Hook Events table).
- S2 accept: only `.devin/hooks.v1.json` is a documented load path; root hooks.v1.json is install template (confirmed via install.ps1/sh).
- S3 accept: hook stdout JSON decision/reason/additionalContext/updatedInput; exit 2 blocks (lifecycle-hooks.md, read).
- S4 accept: `.devin/config.json` supports ONLY permissions/mcpServers/read_config_from/hooks; agent.model is user-config only (global-vs-local.md via researcher).
- S6 accept + decisive: `read_config_from` defaults all true; `agents_standard` gates "standard project rules" = AGENTS.md, AGENTS.local.md, AGENT.md, .windsurfrules (read-config-from.md, read directly, Options table).
- S7 accept: custom subagents `.devin/agents/<name>.md` or `agents/<name>/AGENT.md`; frontmatter name/description/model/allowed-tools/max-nesting (subagents.md, read full).
- S8 accept: subagent_explore→default subagent model (SWE-1.6); subagent_general→parent model; `model:` pin is the only way to pin non-parent model.
- S9/S10 accept: SWE-2 effort levels trained w/ cost penalty; medium cheaper/faster (cognition.com/blog/swe-2 via researcher).
- S11 RESOLVED by live tool: `devin models list` (CLI 3000.10.21) shows swe-2-high/-medium/-max, 262K ctx, Free; alias swe→swe-2. bundle-models.json VERIFIED CORRECT.
- S12 accept: Cognition multi-agent guidance — parallel readers OK, writes single-threaded (covered by dispatching-parallel-agents SKILL.md lines 45-62).
- S13 accept: Anthropic ~15x token fan-out cost (already cited in skill).
- S14 accept: lost-in-the-middle (arXiv:2307.03172) — justifies constraint-pinning hook.
- S15 accept: context engineering = smallest high-signal set (context-window-hygiene aligned).
- S16 accept w/ caveat: prompt caching prefix order (Anthropic doc; applies by analogy).

## SCOPE

- Authorized: `AGENTS.md`, `config.json`, `hooks.v1.json`, `mcp_config.json`,
  `scripts/*`, `skills/*/SKILL.md`, `docs/*`, `data/*`, `agents/*`, `ledgers/*`,
  `.devin/global_rules.md`, `.devin/rules/*`, `README.md`, `devin-*.ps1`, `install.*`
- Forbidden: `tests/held-out/` (read/write by implementer), `credentials.toml`
  values, anti-cheat principles, AI signatures in deliverables.
- Any file outside this list requires a new INPUT_REGISTER entry + own gate.

## VFS (FASE 0 gates)

- [x] G0.1: Devin CLI capabilities confirmed from docs
  CHECK: webfetch docs.devin.ai (hooks overview+lifecycle, subagents, models, rules, creating-skills, changelog, llms.txt, read-config-from)
  EXPECT: capability table with URLs + read excerpts
  EVIDENCE: pages read; excerpts in session. Changelog: live CLI 3000.10.21 > validated 3000.6.14; new keys disabled_tools, agent.compaction_threshold_tokens, tool_provenance, web_search permissionable, /code /smart /bypass.

- [x] G0.2: doc claims verified against installed bundle
  CHECK: read hooks.v1.json, config.json, .gitignore; ls scripts/agents/.devin; diff .devin/hooks.v1.json hooks.v1.json; devin --version; devin doctor; devin models list; grep model: frontmatter
  EXPECT: match/mismatch per claim
  EVIDENCE: MATCH=8 events both files, all 15 hook scripts exist, all model pins swe-2-*, .devin/hooks.v1.json==root copy, swe-2 IDs real+Free. MISMATCH=devin doctor loads reviewer TWICE (agents/reviewer.md vs .devin/agents/reviewer.md diverge); validated 3000.6.14 vs live 3000.10.21; agents_standard:false vs AGENTS.md-centric design.

- [x] G0.3: trusted sources read directly
  CHECK: researcher subagent 1ed91db0 (web_search extracts; webfetch unavailable in its env) + own webfetch on docs pages
  EXPECT: SOURCE_REGISTER decisions
  EVIDENCE: SOURCE_REGISTER above; S11 resolved via devin models list.

- [x] G0.4: best-practice matrix for bundle models
  CHECK: researcher S9-S16 + rules.md "keep rules small, prefer skills"
  EXPECT: practice→source→decision→metric
  EVIDENCE: effort routing confirmed (S9/S10); rules-minimal guidance → C4 candidate; fan-out guidance already in dispatching skill (S12/S13).

- [x] G0.5: past errors mined from git history
  CHECK: git log --oneline -30; --diff-filter=D -20; --grep fix -25; -S agents_standard -p config.json
  EXPECT: failures + lessons
  EVIDENCE: dafb9ab hook contract fix (tool_name/exit2/anchored matchers); a03c7e7 subagent frontmatter boolean; c984271 full revert; dbea22c SWE-2 migration; f13a7f7 introduced read_config_from as live-config export with NO documented rationale. Lesson: config semantics changes need intent notes; frontmatter schema drifted before (validator added).

- [x] G0.6: reproducible baseline snapshot
  CHECK: git status --short (clean); python audit.py; python -m pytest tests/validation -q; wc AGENTS.md
  EXPECT: exit codes + counts
  EVIDENCE: audit 0 errors / 1 warning (__pycache__ dirs); pytest tests/validation 150 passed in 129s; held-out NOT run (qa-ci only); AGENTS.md 25,560 bytes; tree clean at 72dfc93.

- [x] G0.7: synthesis — prioritized candidate list + coverage matrix
  CHECK: every IN/source/candidate has disposition
  EXPECT: matrix below
  EVIDENCE: CANDIDATE MATRIX

## CANDIDATE MATRIX (FASE 0.7)

| ID | Failure (repro) | Source | Files | Risk | VF |
|----|------------------|--------|-------|------|----|
| C1 | agents_standard:false disables project AGENTS.md in every repo using installed config; bundle is AGENTS.md-centric. Repro: docs read-config-from Options table + config.json:12 | S6, f13a7f7 (no rationale) | config.json, docs | med | pytest validation green; audit green |
| C2 | validated_cli_version 3000.6.14 stale vs live 3000.10.21; new keys undocumented | devin --version; changelog | data/bundle-identity.json, docs/DEVIN-CLI-COMPATIBILITY.md | low | devin --version; audit; pytest |
| C3 | reviewer profile loads twice, divergent (global+project) | devin doctor: "reviewer, reviewer"; diff showed divergence | .devin/agents/reviewer.md | low-med | devin doctor unique names |
| C4 | AGENTS.md 25.5KB always-on vs "keep rules small" (rules.md) + Rule 18 | wc -c=25560; rules.md | AGENTS.md | high | defer — restructure needs owner decision |
| C5 | empty PermissionRequest block | hooks.v1.json:166-171 | — | — | REJECTED: audit expects 8 events |
| C6 | __pycache__ audit warning | audit output | — | — | REJECTED: regenerable noise; warning by design |
| C7 | cost_tier "free" doubt | S11 | data/bundle-models.json | — | REJECTED: devin models list confirms Free |

IN-01 routed; IN-02 applied (FASE 0 executed); IN-03 applied (researcher + planned qa-ci).

## LOOP GATES (per candidate, appended below)

Deferred by user decision: C1, C3, C4. Rejected in synthesis: C5, C6, C7.
Selected: C2 (bump validated CLI + document 3000.10.x keys).

### C2 — Passo 1 OBSERVE
- OUTCOME: bundle claims validation at 3000.6.14; live CLI is newer.
- CHECK: `devin --version` vs `data/bundle-identity.json` field.
- EXPECT: mismatch shown.
- EVIDENCE: `devin 3000.10.21 (611c1cba)` vs `"validated_cli_version": "3000.6.14"` (bundle-identity.json:8). README.md:40 hardcodes 3000.6.14. CHANGE_CLASS: doc-only/metadata (no runtime behavior).

### C2 — Passo 2 CRITICAR
- Rule link: Rule 15/17 (reproducible evidence; verify with tools) — a "validated" pin must match observed reality.
- Regra violada: none hard; staleness undermines the pin's evidentiary value.
- Comportamento atual: pin lags installed CLI by two releases (3000.6.14 → 3000.10.21).
- Intenção positiva: pin records last-verified CLI so installs are deterministic and untested drift is visible.
- Por que falha apesar da intenção: the intent is sound; the pin was simply never advanced after the CLI updated. Fix = re-validate and advance, not remove.

### C2 — Passo 3 ALTERNATIVAS
| Alt | Descrição | Arquivos | Risco | Métrica/VF | Prob. real |
|-----|-----------|----------|-------|------------|------------|
| 1 | Bump pin to 3000.10.21 + doc section on new keys | bundle-identity.json, README.md, DEVIN-CLI-COMPATIBILITY.md | baixo | audit+pytest green; devin --version match | alta |
| 2 | Keep 3000.6.14, add "also verified under 3000.10.21" note | compat doc only | baixo | audit green | média (pin stays stale) |
| 3 | Bump + adopt new config keys (disabled_tools etc.) | config.json too | médio | new gates needed | fora de escopo — defer |
- Selected: Alt 1. Alt 3 splits into deferred candidate D1 (adopt new keys needs own gates).

### C2 — Passo 4 REVISAR
- EVIDENCE: `git diff --stat` → README.md +1/-1, data/bundle-identity.json +1/-1, docs/DEVIN-CLI-COMPATIBILITY.md +11. All inside SCOPE. No AI signature, no secrets, no test removal. `git diff --check` clean.

### C2 — Passo 5 VALIDAR
- CHECK: `python audit.py`; `python -m pytest tests/validation -q`
- EVIDENCE: audit 0 errors / 1 warning (unchanged __pycache__ — pre-existing); 150 passed in 60.44s. held-out pending qa-ci.

### C2 — Passo 6 FUTURE PACE
| Cenário | Comportamento esperado | Resultado |
|---------|------------------------|-----------|
| Fresh install on CLI 3000.10.21 | pin == devin --version → parity confirmed | beneficiado |
| User on older 3000.6.x | doc section clearly labeled "3000.10.x" — no false claim | neutro |
| Maintainer evaluating config | new keys documented w/ adoption status | beneficiado |
- 2/3 beneficiado, 0 prejudicado → PASS.

### C2 — Passo 7 ECOLOGICAL CHECK
- diff limited to 3 files; no hook/script/config behavior change; placeholders {{VALIDATED_CLI_VERSION}} now resolve to 3000.10.21 consistently (TOOLS-MAP, leo SKILL); historical docs untouched by design; tests untouched. Sem impacto negativo.

### C2 — Passo 8 SIMULAR
- Doc-only change: live configuration untouched; no install needed. audit + 150 tests re-run post-change → green. `devin doctor` passed earlier (1 check). Impacto observado: none expected — metadata/doc only.

### C2 — Passo 9 CLASSIFICAR
- Baseline: pin 3000.6.14 vs live 3000.10.21 (mismatch). Post: pin == live (parity). Delta: version parity restored; +11 doc lines covering 6 new capabilities.
- Independent verification (reviewer subagent edb203aa, qa-ci profile unavailable in runtime — deviation recorded): git scope PASS, `devin --version`=3000.10.21 PASS, audit 0 errors PASS, FULL pytest incl. held-out **289 passed** PASS, diff/changelog cross-check PASS (all 6 claims verbatim), JSON validity PASS. Overfitting: none. **Verdict: PASS**.
- CLASSIFICAÇÃO: **MELHOROU** (métrica real: parity 0→1; held-out 139/139 dentro dos 289; sem efeitos colaterais).

### C2 — Passo 10 CONVERGIR
- C2 applied+MELHOROU. C1/C4 deferred by user; C3 later selected by user (below); C5/C6/C7 rejected with evidence; D1 deferred.
- Todos os inputs/candidatos com estado final e evidência. Sem falha reproduzível pendente.

---

### C3 — Passo 1 OBSERVE (user re-entered loop: selected C3)
- CHECK: `devin doctor`; `head` both reviewer.md files; grep .devin for reviewer refs.
- EVIDENCE: doctor → "10 profile(s) loaded: … reviewer, reviewer …"; both files declare `name: reviewer`; content diverges (global=full two-axis, project=repo-local). No live refs require project name `reviewer` (.devin grep: only historical docs).
- CHANGE_CLASS: config (agent profile identity).

### C3 — Passo 2 CRITICAR
- Comportamento atual: two profiles share identifier `reviewer` → ambiguous resolution.
- Intenção positiva: project-local reviewer tailored to this repo (CONTEXT.md scope) — deliberate per AUDIT_REPORT 2.3.4.
- Falha: identifier collision, not the local profile itself.
- Regra: Rule 17 (ambiguous dispatch target can't be verified deterministically).

### C3 — Passo 3 ALTERNATIVAS
| Alt | Descrição | Risco | VF |
|-----|-----------|-------|-----|
| 1 | rename → `repo-reviewer` (file + name) | baixo | doctor unique names; audit+pytest |
| 2 | delete project profile | perde tailoring | — |
| 3 | `name:` override only | file≠id, confuso | — |
- Selected: Alt 1. audit.py checks only root agents/ (expected list of 6) — .devin/agents names free.

### C3 — Passo 4 REVISAR
- `mv .devin/agents/reviewer.md .devin/agents/repo-reviewer.md`; `name:` → `repo-reviewer`; description clarified. Diff: rename + 2 lines.

### C3 — Passo 5 VALIDAR
- EVIDENCE: `devin doctor` → 10 profiles, all unique: "…qa-ci, repo-reviewer, researcher, reviewer…". audit 0 errors. pytest tests/validation 150 passed in 82.22s.

### C3 — Passo 6 FUTURE PACE
| Cenário | Resultado |
|---------|-----------|
| dispatch `reviewer` in this repo | resolves unambiguously to global; `repo-reviewer` available → beneficiado |
| install elsewhere without .devin/agents | only global reviewer → neutro |
| repo-local review by name | `repo-reviewer` unambiguous → beneficiado |
- 2/3 beneficiado → PASS.

### C3 — Passo 7 ECOLOGICAL CHECK
- .devin/agents names not audited; no skill/doc live references to project `reviewer`; run_subagent list gains `repo-reviewer`. Sem efeito colateral.

### C3 — Passo 8 SIMULAR
- Observed live: doctor re-run post-change shows unique names. No install impact (`.devin/` is project-local, not exported).

### C3 — Passo 9 CLASSIFICAR
- Baseline: `reviewer` loaded ×2 (ambiguous). Post: 10 unique names; `repo-reviewer` resolvable by name. Delta: duplicate identifier count 1→0.
- Independent verification (reviewer e46c0724): git scope PASS, doctor unique names PASS, audit 0 errors PASS, FULL pytest incl. held-out **289 passed in 72.21s** PASS, frontmatter valid + no write/edit PASS, overfitting none (self-extend SKILL.md:58 is a generic example — still accurate). **Verdict: PASS**.
- CLASSIFICAÇÃO: **MELHOROU**.

### C3 — Passo 10 CONVERGIR
- C3 applied+MELHOROU. Remaining at that point: C1/C4 deferred, C5/C6/C7 rejected, D1 deferred.

---

## PHASE 2 — user: "faca sem subagente o C1, C4 e D1 em sequencia" (DELEGATION disabled)

### C1 — Passos 1-4 (agents_standard)
- OBSERVE: `config.json:12` had `"agents_standard": false`; doc (read-config-from Options) gates project `AGENTS.md`/`AGENTS.local.md`/`AGENT.md`/`.windsurfrules`. Introduced by f13a7f7 live-export, no rationale.
- CRITICAR: intenção positiva = isolar bundle de imports de outras ferramentas; over-broad porque `agents_standard` é o mecanismo NATIVO de regras do Devin (mesmo usado pelo AGENTS.md global do bundle).
- ALTERNATIVAS: (1) `true` + demais imports `false` + doc da decisão [escolhida]; (2) manter `false` e documentar isolamento; (3) remover a key (default true, implícito — menos claro).
- REVISAR: `config.json` → `"agents_standard": true`; nova seção "read_config_from policy" em docs/DEVIN-CLI-COMPATIBILITY.md explicando por quê.
- EVIDENCE Passo 5: `agents_standard = True` via json.load; audit 0 errors; pytest tests/validation 150 passed (combined run w/ C4).
- Passo 6 future-pace: repo de usuário com AGENTS.md próprio → regras carregam (beneficiado); repo malicioso com AGENTS.md → mesmo risco de qualquer instalação Devin padrão (neutro, comportamento default); manutenção → decisão documentada (beneficiado). 2/3 → PASS.
- Passo 7 ecology: config template only; live config NOT reinstalled (drift warning is the intended signal). Side-finding: audit [15] compares config.json HOOKS only — `read_config_from` and other non-hook keys are not drift-checked (audit coverage gap, noted, not fixed — out of scope).
- Passo 9: CLASSIFICAÇÃO = **INCONCLUSIVO** (formal: held-out não executada — DELEGATION disabled nesta fase e implementer não pode rodá-la; gates visíveis todos verdes, semântica verificada na doc primária). Estado: não_validada_por_heldout.

### C4 — Passos 1-8 (AGENTS.md 25.5KB → 16.9KB)
- OBSERVE: `wc -c AGENTS.md` = 25560; audit ~6390 tokens; docs.devin.ai rules.md: "keep rules as small as possible; prefer skills". Redundância real: regra aparece 2-3x (summary + seção).
- CRITICAR: intenção positiva = regras always-on aplicam-se sempre; falha = summary carregava detalhe completo duplicando as seções; Rule 20 tinha PT solto e detalhe já coberto por docs/MODEL-GUIDE.md.
- ALTERNATIVAS: (1) index compacto + dedup rule20/rule3 [escolhida]; (2) split para `~/.devin/rules/` — exige mudanças em install.ps1/sh + export + audit (fora do passo); (3) comprimir prosa das pinned — rejeitada (pinned = enforcement sobrevivente de compaction).
- REVISAR: summary → "Rule index" (26 linhas `N. **Name**`, padrão audit preservado); rule 3 checklist → 1 parágrafo + ponteiro `writing-skills`; rule 20 → essência EN + ponteiro MODEL-GUIDE. Pinned intactas.
- EVIDENCE Passo 5: audit — Rules found [1..27 exceto 6] = 26 = manifest.rule_count OK; "AGENTS.md within budget" (~4220 tok); 0 errors; `git diff --check` limpo; pytest 150 passed.
- Passo 6: sessão longa (beneficiado: −2170 tokens always-on); regra buscada por número (neutro: index + seções preservam); compaction (beneficiado: pinned intactas, pinning hook cobre resto). 2/3 → PASS.
- Passo 7: audit detection pattern `\nN. **` preservado; nenhum teste grep conteúdo de AGENTS.md; install compara por hash → drift warning correta até próximo install.
- Passo 8: efeito observado — audit token readout 6390→4220 (−34%).
- Passo 9: CLASSIFICAÇÃO = **INCONCLUSIVO** (formal, mesmo motivo do C1); métrica real 25560→16935 chars. Estado: não_validada_por_heldout.

### D1 — Passos 1-9 (adopt 3000.10.x keys)
- OBSERVE/CRITICAR: C2 documentou 6+ capabilities; D1 = decidir adoção com gates.
- ANÁLISE (tool-verified): `disabled_tools` — todos os 14 tools candidatos têm refs no bundle (grep counts registrados); `compaction_threshold_tokens` — sem base em fonte primária para valor não-default e compactar mais cedo só aumenta eventos de drop; `web_search` permissions — allow vazio, ask fricção, deny quebra research; `codex_tools`/`exec_shell`/`DEVIN_REFUSAL_FALLBACK` — fora do modelo/config escopo.
- REVISAR: docs/DEVIN-CLI-COMPATIBILITY.md tabela de decisões por key (adopted/not adopted + rationale). Nenhuma key adotada em config.json — adoção arbitrária violaria métrica-real (A5).
- Passo 9: CLASSIFICAÇÃO = **NEUTRO** para config (nada mudou); melhoria documental real (decisões explícitas). Estado: validada como doc-only (gates verdes).

### C8 — install.ps1 Get-FileHash bug (found during authorized install)
- FALHA_REPRODUZIDA: `install.ps1 -Force -Backup` → `Get-FileHash não é reconhecido` — host PowerShell 5.1 sem module autoload ($PSModulePath vazio) → Microsoft.PowerShell.Utility não carrega → cmdlet ausente.
- ALTERNATIVA_APLICADA: `Get-FileHash256` reescrito com `[Security.Cryptography.SHA256]` .NET (funciona em qualquer host, mesmo formato hex uppercase); `Get-FolderHash` reuso da função.
- EVIDENCE: install completou (4 overwritten, 188 skipped, backup criado); audit [15] todo `live=bundle` — drift AGENTS.md zerado; `devin doctor` 10 perfis únicos PASS.
- NOTA: `devin.org_id` = MASKED no live E no backup pré-install → Force-overwrite não perdeu nada (org real não mora em config.json).
- CLASSIFICAÇÃO: MELHOROU (bug bloqueante removido; install agora roda em host sem autoload). Held-out não executada nesta fase.
