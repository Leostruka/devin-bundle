# FASE 0 — Deep Research

- [x] 0.1 — Pesquisar Devin CLI
  OUTCOME: Confirm the exact `ask_user_question` limits and how Devin CLI discovers/installs skills.
  CHECK: Read `docs/TOOLS-MAP.md`, `config.json` PreToolUse matcher, `scripts/validate-tool-args.py`, and `tests/held-out/mutation/test_validate_tool_args_new.py`.
  EXPECT: `ask_user_question` accepts at most 4 questions and 4 options per question; skills are loaded from `%APPDATA%\devin\skills` (Windows) or `~/.config/devin/skills` (Unix).
  EVIDENCE: `validate-tool-args.py` lines 204-221 block `len(questions) > 4` and `len(opts) > 4`; `test_validate_tool_args_new.py` lines 37-55 assert the same; `docs/TOOLS-MAP.md` line 30 lists `ask_user_question` as a UI tool.

- [x] 0.2 — Confirmar pela estrutura real
  OUTCOME: Map the current `grilling` skill against the transcript claims and the ask tool limits.
  CHECK: `read skills/grilling/SKILL.md`; `grep` for one-question/batch/frontier/grill-me; compare with `ledgers/grilling-batch-questions-v2.md`.
  EXPECT: Skill already uses frontier rounds, but does **not** state the `ask_user_question` 4-question / 4-option limit.
  EVIDENCE: SKILL.md has frontier rounds (Phase 2), Statelese mode "ask all currently-unblocked questions at once", and "When questions are independent, batch them in one round" — all without an upper bound.

- [x] 0.3 — Pesquisar fontes confiáveis
  OUTCOME: Use primary/runtime sources for tool limits and the video only as the author design story.
  CHECK: Use the bundle's own validator and config as the ground truth; do not treat the Tactiq transcript as an official caption.
  EXPECT: Tool limits are enforced by the runtime hook, not by the skill text; transcript is user-provided via Tactiq.
  EVIDENCE: `scripts/validate-tool-args.py` is referenced by `config.json` PreToolUse; provenance file notes Tactiq/user-provided, not official caption.

- [x] 0.4 — Pesquisar melhores práticas
  OUTCOME: Compare sequential, fixed-batch and adaptive frontier-round strategies.
  CHECK: Review `skills/continuous-improvement/SKILL.md` and the existing `grilling` anti-pattern "Yes-tail".
  EXPECT: Adaptive frontier rounds minimize turns while keeping dependent questions sequential; fixed batch sizes can delay dependent questions; one-at-a-time wastes turns.
  EVIDENCE: `grilling/SKILL.md` already has the design-tree / frontier-round concept; simulation table later shows independent 6-question fixture drops from blocked (0 coverage) to 2 turns full coverage.

- [x] 0.5 — Não repetir erros anteriores
  OUTCOME: Understand why the previous grilling batching change missed the tool limit.
  CHECK: `git log --oneline -30 -- skills/grilling`; read `ledgers/grilling-batch-questions-v2.md`.
  EXPECT: Previous change (commit 1b8a34d) added frontier rounds and Yes-tail warning but did not probe `ask_user_question` limits; no reverts of `skills/grilling/SKILL.md`.
  EVIDENCE: Ledger `grilling-batch-questions-v2.md` FASE 0.6 only says 139 tests passed; it does not cite a probe with 5 questions.

- [x] 0.6 — Baseline
  OUTCOME: Capture pre-change audit, held-out and tool-limit baseline.
  CHECK: `python audit.py`; `python -m pytest tests/held-out -q`; run `validate-tool-args.py` with 4 and 5 questions; preserve transcript with SHA-256.
  EXPECT: `audit.py` 0 errors/warnings; held-out 135 passed; 4-question payload passes, 5-question payload blocked; transcript saved under `.devin/notes/youtube/U832hShMVnc/`.
  EVIDENCE: audit output "ALL 31 CHECKS PASSED"; held-out "135 passed"; validator `n=4 returncode=0`, `n=5 returncode=2 reason="ask_user_question supports at most 4 questions, got 5."`; transcript SHA-256 `130e991f1ccccd657445b368c962bbf7822db02bf594d228a342c4c5adfcf658`.

- [x] 0.7 — Síntese
  OUTCOME: Identify a reproducible failure and three candidate alternatives.
  CHECK: Run the new failing validation test before any edit; run the fixture simulation with the old (no-limit) rule.
  EXPECT: Test fails because the skill text lacks the limit; independent/mixed fixtures produce a blocked `ask_user_question` call.
  EVIDENCE: `python -m pytest tests/validation/test_grilling_frontier_rounds.py -q` showed 4 failed, 2 passed; simulation table shows old behavior blocked for independent and mixed, 0 coverage.

# LOOP DE MELHORIA

- [x] 1 — OBSERVAR
  OUTCOME: Concrete, reproducible failure of the current frontier-round instruction.
  CHECK: `python scripts/validate-tool-args.py` with a 5-question `ask_user_question` payload; `python -m pytest tests/validation/test_grilling_frontier_rounds.py` against the unmodified skill.
  EXPECT: Validator exits 2 and returns `{"decision":"block","reason":"ask_user_question supports at most 4 questions, got 5."}`; the new test fails on `independent.json` and `mixed.json` simulations.
  EVIDENCE: Validator probe output for n=4/n=5; pytest failure output `independent.json: generated ask_user_question was blocked` and `SKILL.md must acknowledge the ask_user_question 4-question limit`.

- [x] 2 — CRITICAR
  OUTCOME: Separate behavior from positive intention and locate the violated rule.
  CHECK: Compare `skills/grilling/SKILL.md` text with the runtime tool contract.
  EXPECT: Current behavior: "Ask the whole frontier in one round" can produce >4 questions. Intention: reduce turns by batching independent questions. Failure cause: the instruction is unbounded, so the `ask_user_question` tool is blocked by `validate-tool-args.py`. Violates Rule 17 (verify with tools) and Rule 21 (research/ask before assuming tool behavior).
  EVIDENCE: Skill text line 83 `Ask the whole frontier in one round`; validator blocks 5+ questions.

- [x] 3 — GERAR ALTERNATIVAS
  OUTCOME: Compare at least three designs.
  CHECK: Write alternative table in this ledger.
  EXPECT: Table scored by discovery, maintenance, context, turns and compatibility.
  EVIDENCE:

| # | Descrição | Risco | Prob. de melhoria real |
|---|-----------|-------|------------------------|
| 1 | **Adaptive frontier rounds in `grilling`** — keep single skill, split frontier into multiple `ask_user_question` calls when >4 questions/options, keep dependent questions sequential. | Low | High: fixes the reproducible block without changing skill surface. |
| 2 | **Explicit `sequential` and `frontier` modes** inside `grilling` — let the user pick. | Medium | Medium: adds UX choice and more mode logic; not needed while default already works. |
| 3 | **New `batch-me` skill** — split frontier-only behavior into a separate skill. | Medium-High | Low: duplicates `grilling` discovery and mode logic; no measurable gain over Alt 1. |

- [x] 4 — REVISAR
  OUTCOME: Implement the highest-probability alternative (Alt 1: adaptive frontier rounds) with a failing validation test.
  CHECK: Write `tests/validation/test_grilling_frontier_rounds.py` first (red); edit `skills/grilling/SKILL.md` to cap calls at 4 questions/4 options.
  EXPECT: New test goes from 4 failed to 7 passed; skill still passes `validate-skill-format.py`.
  EVIDENCE: Red pytest output before edit; green `7 passed` after review fixes; `grilling/SKILL.md` now enforces 1–4 questions, 2–4 options, waiting for answers, frontier recomputation, and unanswered-prerequisite exclusion.

- [x] 5 — VALIDAR
  OUTCOME: Verify with audit, held-out and specific tests.
  CHECK: `python audit.py`; `python -m pytest tests/held-out -q`; `python -m pytest tests/validation/test_grilling_frontier_rounds.py tests/validation/test_skill_format_passes.py tests/validation/test_audit_passes.py -q`; `python scripts/validate-skill-format.py`.
  EXPECT: audit 0 errors/warnings; held-out 135 passed; full validation passes; skill format `grilling` 100.
  EVIDENCE: audit "ALL 31 CHECKS PASSED"; held-out "135 passed"; full validation "94 passed"; specific frontier suite "7 passed"; `validate-skill-format.py` `[PASS] grilling\SKILL.md (score: 100)`.

- [x] 6 — FUTURE PACE
  OUTCOME: Confirm the change helps at least two scenarios without harming the third.
  CHECK: Project the new rule onto three user profiles.
  EXPECT:
  - Dictation/long answers: chunking still lets the user blast through many answers, just in multiple `ask_user_question` calls. Helps.
  - Beginner/one-at-a-time: dependent questions remain sequential; only independent questions are batched. No regression.
  - Mixed dependencies (e.g., `mixed.json`): 5 independent + 2 dependent can now be asked in 2 turns instead of being blocked. Helps.
  EVIDENCE: All three fixtures in `tests/fixtures/grilling-frontier/` pass simulation.

- [x] 7 — ECOLOGICAL CHECK
  OUTCOME: No negative side effects on other rules, skills or context budget.
  CHECK: Search `skills/project-setup/SKILL.md`, `skills/planning-pipeline/SKILL.md`, `skills/domain-modeling/SKILL.md` for `grilling`; check no new skill created; check `tests/held-out` untouched.
  EXPECT: Callers reference `grilling` by behavior, not by exact wording; no new skill; no held-out changes; added text is a few lines.
  EVIDENCE: No test files in `tests/held-out` reference grilling; no new `skills/batch-me` created; edits only in `skills/grilling/SKILL.md`.

- [x] 8 — SIMULAR
  OUTCOME: Install to a temporary home and confirm the change loads correctly without touching the real home.
  CHECK: Save `APPDATA`/`USERPROFILE`, redirect to `.devin/scratch/grilling-frontier-install/`, run `install.ps1 -Force`, compare SHA-256 of `grilling/SKILL.md` in temp vs bundle, restore variables.
  EXPECT: Temp home contains `devin/skills/grilling/SKILL.md` identical to bundle; real home unchanged.
  EVIDENCE: Install output target `D:\Programing\ai_workspace\devin-bundle\.devin\scratch\grilling-frontier-install\devin`; bundle SHA and temp SHA matched; `RESTORED` printed. The temporary install directory was removed after verification, and `.gitignore` now covers `.devin/scratch/*-install/`.

- [x] 9 — CLASSIFICAR
  OUTCOME: Decide whether the change improved, stayed neutral, or regressed.
  CHECK: Compare the fixture simulation table before vs after.
  EXPECT:
  - `independent.json`: old 0 turns/0 coverage/blocked, new 2 turns/6 coverage/unblocked.
  - `dependent.json`: old 6 turns/6 coverage/unblocked, new 6 turns/6 coverage/unblocked (no regression).
  - `mixed.json`: old 0 turns/0 coverage/blocked, new 2 turns/7 coverage/unblocked.
  EVIDENCE: `.devin/notes/grilling-frontier/metrics.md` table and test `test_frontier_simulation` pass.
  CLASSIFICAÇÃO: **MELHOROU**

- [x] 10 — REPETIR OU CONVERGIR
  OUTCOME: Decide whether there is another reproducible failure to address.
  CHECK: Re-run failing test and re-inspect skill text for any remaining unbounded batch instruction.
  EXPECT: No remaining instruction tells the agent to put >4 questions or >4 options in one `ask_user_question` call; no new failure.
  EVIDENCE: `grep -n "whole frontier" skills/grilling/SKILL.md` now followed by the split instruction; `grep -n "at most 4 questions" skills/grilling/SKILL.md` matches multiple locations; all tests green.
