# GATES: bitter-lesson

> Improvement: apply "The Bitter Lesson" (Rich Sutton, 2019) to devin-bundle — test whether model-specific optimizations are already causing reproducible failures, and replace only reproducible failures with general, scalable, verifiable mechanisms.
> Branch: `feat/bitter-lesson-improvement`
> Ledger created per `skills/unlazy/SKILL.md` and `skills/continuous-improvement/SKILL.md`.
> Rule: no bundle behavior change without a reproduced failure.

---

## FASE 0 — Deep Research

- [x] **0.1 — Pesquisar Devin CLI**
  - **OUTCOME:** Confirm Devin CLI version, model registry, lifecycle hooks, and official source URLs.
  - **CHECK:** `devin --version` ; `devin models list` ; `devin doctor`
  - **EXPECT:** CLI 3000.6.7; `glm-5-2` and `swe-1-7` present and Free; `devin doctor` passes.
  - **EVIDENCE:**
    - `devin 3000.6.7 (260a97c8)`
    - `devin models list`: `glm-5-2` = GLM-5.2 High, 200K, Free; `swe-1-7` = SWE-1.7 Max, 262K, Free; `swe-1-7-lightning` = paid ($2.5/$12.5), 202752 context; `swe-1-6` = paid ($0.5/$2.5), 200K; 40 families available.
    - `devin doctor`: 1 check passed, 0 warnings, 0 failures.
    - Local docs match official sources: `docs/DEVIN-CLI-COMPATIBILITY.md` (CLI 3000.6.7, 8 lifecycle events, plugins, installer contract); `docs/MODEL-GUIDE.md` (model specs, routing, context budgets, conditional paid-model policy).
    - Official source URLs recorded: `https://docs.devin.ai/cli/changelog/stable`, `https://docs.devin.ai/cli/extensibility/plugins`, `https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks`.

- [x] **0.2 — Confirmar pela estrutura real**
  - **OUTCOME:** Disk matches documented bundle structure.
  - **CHECK:** `find_file_by_name`, `python audit.py`, `git ls-files`, manual counts.
  - **EXPECT:** 74 skills, 20 rules, 5 agents, 17 scripts, 8 hook events, all files valid.
  - **EVIDENCE:**
    | Documented | Disk | Match |
    |---|---|---|
    | 74 skills | 74 | yes |
    | 20 rules (1-5,7-21) | 20 | yes |
    | 5 agents | 5 | yes |
    | 17 scripts | 17 | yes |
    | 8 Devin CLI hook events | 8 | yes |
    | Devin CLI 3000.6.7 | 3000.6.7 | yes |
    | `glm-5-2` free primary | present, Free | yes |
    | `swe-1-7` free subagent | present, Free | yes |
    - `python audit.py`: ALL 31 CHECKS PASSED — NO ERRORS, NO WARNINGS.
    - `devin models list`: 8 custom subagent profiles loaded (`architect`, `debugger`, `domain`, `implementer`, `issue-tracker`, `researcher`, `reviewer`, `triage-labels`).

- [x] **0.3 — Pesquisar fontes confiáveis (Rich Sutton primary article)**
  - **OUTCOME:** Read the primary source and verify the video's claims against it.
  - **CHECK:** Download `http://www.incompleteideas.net/IncIdeas/BitterLesson.html`, compare selected transcript timestamps.
  - **EXPECT:** Article author = Rich Sutton, date = March 13, 2019; video opening matches article; video paraphrase 00:00:57.920–00:01:07.280 is more absolute than article.
  - **EVIDENCE:**
    - Downloaded to `.devin/notes/youtube/HtsFKx9mAu8/sutton-bitter-lesson.html`.
    - SHA-256: `f1baabbabfde3e2a368104fe91cb7efcf3566e8a9dd2c5fe50ccd1d96ec1acb6` (7297 bytes).
    - Primary source: Rich Sutton, "The Bitter Lesson", March 13, 2019, http://www.incompleteideas.net/IncIdeas/BitterLesson.html.
    - Video `00:00:00.080–00:00:21.120` matches article opening: "The biggest lesson that can be read from 70 years of AI research is that general methods that leverage computation are ultimately the most effective, and by a large margin."
    - Sutton's nuance: human-knowledge improvements help in the short term and are satisfying, but only leveraging computation matters in the long run; the two need not run counter, but in practice they compete for time; the scalable methods are **search** and **learning**.
    - Video paraphrase `00:00:57.920–00:01:07.280` ("nothing really matters in AI research apart from just improving the power of these machines") is a stronger, more absolute gloss. Recorded as the presenter's interpretation, not the primary source's claim.
    - See `.devin/notes/youtube/HtsFKx9mAu8/sutton-article-provenance.md`.

- [x] **0.4 — Pesquisar melhores práticas**
  - **OUTCOME:** Identify bundle practices that are general, scalable, and verifiable.
  - **CHECK:** Read `AGENTS.md`, `docs/MODEL-GUIDE.md`, `skills/continuous-improvement/SKILL.md`.
  - **EXPECT:** Find deterministic gates, held-out tests, context-window management, cache stability, subagent fan-out, native tool-use, model-aware but not over-specified rules.
  - **EVIDENCE:**
    - Rule 14 (`constraint-pinning.py`): deterministic re-injection of pinned constraints after compaction.
    - Rule 15 (`validate-refinement-evidence.py`): evidence must be reproducible; run returned `Total: 50  Valid: 50  Phantom suspects: 0`.
    - Rule 16: self-improvement gains are 47–74% illusory; validate with `tests/held-out/`; `check-push-green.py` blocks push if validation passes but held-out fails.
    - Rule 17: verify with tools; do not deduce.
    - Rule 18: keep context window lean; pinned rules at top; `context-budget.py` reports 24,173 characters, approximately 6,043 tokens, or 3.02% of the 200K GLM-5.2 window.
    - Rule 20: model-aware operation, but `GLM-5.2` decides tool-use natively — no over-specified tool-use rules.
    - `docs/MODEL-GUIDE.md`: prompt cache ($0.26/M read), lost-in-the-middle mitigation, SWE-1.7 fan-out (262K, 1000 TPS), conditional paid-model policy, explicit pin to `swe-1-7` to avoid paid `swe` alias.
    - `skills/continuous-improvement/SKILL.md`: FASE 0 + 10-step loop, unlazy ledger, anti-trapace A1–A5, held-out validation, no push/commit.

- [x] **0.5 — Não repetir erros anteriores**
  - **OUTCOME:** Learn from prior prune/fix/revert commits.
  - **CHECK:** `git log --oneline -30` ; `git log --diff-filter=D --oneline -30`
  - **EXPECT:** Relevant commits with hash, failure pattern, and applicable lesson.
  - **EVIDENCE:**
    | Hash | Commit | Lesson applied |
    |---|---|---|
    | `2451629` | fix: conditional paid-model policy + `subagent_explore` PAGO bug | Pin `swe-1-7` and avoid `subagent_explore` when parent is free. |
    | `034683c` | Revert "feat(skills): add pr-review skill (dour-firefly inline review workflow)" | Avoid narrow workflow-specific skills. |
    | `b3ef46f` | prune: remove graphify skill (9659 tok, unused) | Remove large, unused, domain-specific skills. |
    | `b437fd3` | prune: remove framework-specific skills (laravel, gsap, hig, apple-hig, tailwind, animation, ui-motion) | Prefer general skills over vendor/framework-specific ones. |
    | `0c33fac` | remove animation-physics skill | Prune domain-specific, not generalist, skills. |
    | `3f32fa9` | Complete Devin CLI compatibility: remove platform artifacts | Keep bundle Devin-native and cross-platform. |

- [x] **0.6 — Baseline**
  - **OUTCOME:** Capture bundle state before any change.
  - **CHECK:** `python audit.py` ; `python -m pytest tests/held-out -q` ; count model-specific content.
  - **EXPECT:** 0 audit errors/warnings; 135 held-out tests passed; size and model-term counts recorded.
  - **EVIDENCE:**
    - `python audit.py`: ALL 31 CHECKS PASSED — NO ERRORS, NO WARNINGS.
    - `python -m pytest tests/held-out -q`: 135 passed in 5.00s.
    - `python scripts/validate-refinement-evidence.py`: 50 valid, 0 phantom.
    - AGENTS.md: 24,316 bytes, 221 lines.
    - docs/MODEL-GUIDE.md: 19,688 bytes, 365 lines.
    - Skills/rules/agents/scripts: 74 / 20 / 5 / 17.
    - Model-term occurrences (case-sensitive variants, can overlap with different casing):
      - AGENTS.md: `glm-5-2` 1, `GLM-5.2` 7, `swe-1-7` 7, `SWE-1.7` 7, `SWE-1.6` 3, `subagent_explore` 4 (total 29).
      - MODEL-GUIDE.md: `glm-5-2` 18, `GLM-5.2` 40, `swe-1-7` 32, `SWE-1.7` 43, `SWE-1.6` 2, `swe-1-6` 9, `subagent_explore` 7, `swe-1-8` 1 (total 152).
      - config.json: `glm-5-2` 1.
      - Total across all `.md` files: 403 occurrences.

- [x] **0.7 — Síntese**
  - **OUTCOME:** Prioritize candidates and determine whether any has a reproduced failure.
  - **CHECK:** Cross 0.1–0.6 for model-specific optimizations with a failing command.
  - **EXPECT:** At least one candidate tied to a reproducible failure.
  - **EVIDENCE:**
    | Candidate | Claimed risk | Reproduced failure? | Command / output |
    |---|---|---|---|
    | 1. `config.json` pins `glm-5-2` as primary; agent profiles pin `swe-1-7`. | Becomes obsolete when new free models appear. | No. | `devin models list` shows both still Free and available. |
    | 2. Rule 20 + `MODEL-GUIDE.md` are large model-specific blocks in `AGENTS.md`. | May stale as model families evolve; lost-in-the-middle. | No. | Audit passes; content is accurate as of CLI 3000.6.7; no test fails. |
    | 3. `MODEL-GUIDE.md` references future `swe-1-8` (line 230). | Prediction may become wrong or stale. | No. | It is a conditional future note, not a runtime rule; no executable failure. |
    | 4. Framework/domain-specific skills. | Already pruned in prior commits. | No. | `audit.py` skill count = 74; no obsolete framework skills on disk. |
    - **Conclusion:** No concrete, reproducible failure found. No bundle behavior change warranted.

---

## LOOP DE MELHORIA

- [x] **1 — OBSERVAR**
  - **OUTCOME:** Find a concrete, reproducible failure in the bundle caused by a model-specific optimization.
  - **CHECK:** `python audit.py` ; `python -m pytest tests/held-out -q` ; `devin doctor` ; `devin models list` ; targeted probes of model-specific rules.
  - **EXPECT:** At least one failing command/output tied to a model-specific rule or skill.
  - **EVIDENCE:**
    - `python audit.py`: ALL 31 CHECKS PASSED — NO ERRORS, NO WARNINGS.
    - `python -m pytest tests/held-out -q`: 135 passed in 5.00s.
    - `devin doctor`: 1 check passed, 0 warnings, 0 failures.
    - `devin models list`: `glm-5-2` and `swe-1-7` are available and Free; `swe` alias resolves to paid `swe-1-7-lightning`.
    - `python scripts/validate-refinement-evidence.py`: 50 valid, 0 phantom suspects.
    - **No reproducible failure observed.** Stop and classify **INCONCLUSIVE**.

- [x] **2 — CRITICAR**
  - **OUTCOME:** N/A — Step 1 produced no failure.
  - **CHECK:** —
  - **EXPECT:** —
  - **EVIDENCE:** No failure to criticize.

- [x] **3 — GERAR ALTERNATIVAS**
  - **OUTCOME:** Generate at least 3 alternatives only for a reproduced failure.
  - **CHECK:** Review candidates from 0.7.
  - **EXPECT:** 3 scored alternatives.
  - **EVIDENCE:** No failure reproduced. Alternatives were not generated, per the plan/skill instruction to generate alternatives only for a reproduced failure.

- [x] **4 — REVISAR**
  - **OUTCOME:** Apply chosen alternative only after a reproducible failure and alternatives.
  - **CHECK:** —
  - **EXPECT:** —
  - **EVIDENCE:** No bundle behavior change applied.

- [x] **5 — VALIDAR**
  - **OUTCOME:** Confirm bundle passes audit and held-out after (non-)change.
  - **CHECK:** `python audit.py` ; `python -m pytest tests/held-out -q`
  - **EXPECT:** 0 audit errors; 135 held-out tests passed.
  - **EVIDENCE:**
    - `python audit.py`: ALL 31 CHECKS PASSED — NO ERRORS, NO WARNINGS.
    - `python -m pytest tests/held-out -q`: 135 passed in 5.00s.

- [x] **6 — FUTURE PACE**
  - **OUTCOME:** N/A — no change applied.
  - **CHECK:** —
  - **EXPECT:** —
  - **EVIDENCE:** No change to project.

- [x] **7 — ECOLOGICAL CHECK**
  - **OUTCOME:** N/A — no change applied.
  - **CHECK:** —
  - **EXPECT:** —
  - **EVIDENCE:** No change to evaluate.

- [x] **8 — SIMULAR**
  - **OUTCOME:** N/A — no change applied.
  - **CHECK:** —
  - **EXPECT:** —
  - **EVIDENCE:** No install run was required because no bundle behavior change was made; the "temporary installer homes only" restriction is recorded and applies to any future install simulation.

- [x] **9 — CLASSIFICAR**
  - **OUTCOME:** Assign final classification.
  - **CHECK:** Compare real metric to baseline and verify no failure.
  - **EXPECT:** `INCONCLUSIVO`.
  - **EVIDENCE:**
    - Baseline: audit 0 errors, held-out 135/135.
    - After session: audit 0 errors, held-out 135/135.
    - No reproducible failure found.
    - Classification: **INCONCLUSIVO**.

- [x] **10 — REPETIR OU CONVERGIR**
  - **OUTCOME:** Conclude the improvement session.
  - **CHECK:** Confirm no new reproducible failure remains and no further candidate is actionable.
  - **EXPECT:** Stop; do not commit or push.
  - **EVIDENCE:** Session stopped at INCONCLUSIVE. No git commit or push performed; `git status` shows only the new ledger/notes files and the pre-existing `.gitignore` modification.

---

## Saída final (per `skills/continuous-improvement/SKILL.md`)

```
MELHORIA: Aplicar "The Bitter Lesson" ao devin-bundle
FASE0_RESEARCH: Devin CLI 3000.6.7; `glm-5-2`/`swe-1-7` Free; Rich Sutton primary article verified; bundle passes all audits.
FALHA_REPRODUZIDA: Nenhuma — `python audit.py`, `python -m pytest tests/held-out -q`, `devin doctor`, and `devin models list` all pass/confirm.
REGRA_VIOLADA: N/A
INTENÇÃO_POSITIVA: N/A
ALTERNATIVA_APLICADA: N/A
HELD_OUT: passou (135/135)
SIMULAÇÃO: N/A — nenhuma mudança de comportamento aplicada.
MÉTRICA_REAL: baseline audit 0 erros / held-out 135/135; sem mudança, métrica inalterada.
CLASSIFICAÇÃO: INCONCLUSIVO
ESTADO: não_validada (nenhuma mudança; nenhuma falha reproduzível)
ARQUIVOS_ALTERADOS:
  - `.gitignore` (allow this evidence ledger to be reviewed and versioned)
  - `.devin/ledgers/bitter-lesson.md` (this ledger)
  - `.devin/notes/youtube/HtsFKx9mAu8/raw-transcript.md` (verbatim transcript)
  - `.devin/notes/youtube/HtsFKx9mAu8/transcript-provenance.md` (SHA-256 + Tactiq/user provenance)
  - `.devin/notes/youtube/HtsFKx9mAu8/sutton-bitter-lesson.html` (primary article)
  - `.devin/notes/youtube/HtsFKx9mAu8/sutton-article-provenance.md` (source verification)
PUSH_COMMIT: não feito
```

**ABANDON:** No bundle behavior change was made because no reproducible failure was found. The video's most absolute paraphrase (00:00:57.920–00:01:07.280) was verified against Sutton's primary article and classified as the presenter's interpretation, not a fact requiring a code change.
