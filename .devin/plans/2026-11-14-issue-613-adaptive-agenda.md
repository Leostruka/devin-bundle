# Plan: Issue #613 - Adaptive Agenda/Calendar/Routine Engine

Issue: https://github.com/Leostruka/devin-bundle/issues/613
Branch: `feat/613-adaptive-agenda-routine-engine` (from `main` @ d9206f5; note: PR #614 + montador branch unmerged - same-count conflicts will exist, disclose in PR)
Mode: SDD - implementer per task, task review each, fix loop, final review + QA-CI, controller does push/PR/comment.

## Global Constraints

- Same as issue-612 plan: no em/en dashes in new/edited files; UTF-8 pinned; Python 3.11; frontmatter `name`==dir + `description` "Use when" + `triggers: [user, model]`; progressive disclosure; no AI signatures; `git commit -F` density template with `Refs: #613`; `audit.py` Errors: 0; validate-skill-format all PASS; no test deletions; envelope v2 for new CLIs.
- Orchestrator+executors pattern (same as #612): new engine orchestrates; existing skills execute. Minimal cross-skill pointers only.
- gcal extension (`extensions/gcal/wrapper.py`) is the mechanical calendar backend - engine references it; do NOT modify it.

## Task 1: New skill `adaptive-agenda-calendar-routine-engine` + contract test + minimal inventory

- `skills/adaptive-agenda-calendar-routine-engine/SKILL.md` per issue spec: dual temporal architecture (macro calendar weeks/releases <-> micro agenda strict `HH:MM`-`HH:MM` time-blocking with inputs/profile/output-artifact + end-of-block handoff rite); 4 selectable combinable routine profiles (`foco-novidades`, `foco-qualidade-produto` [Steve Jobs UX-first reverse engineering], `foco-interno` [hardening/hardware/metrics], `foco-externo` [DX/ecosystem]) with block allocations; 5-stage flow (Radar&Hunt -> Triage/Jobs-conception+Hardening -> Workbench manifest -> >=32-cycle loop -> Close/Docs/Versioning/Open-Minded Scrum); delegation map to executor skills + gcal wrapper.
- `reference/`: `temporal-architecture.md` (macro/micro, handoff rite, gcal `wrapper.py plan`/`free-busy`/`add`/`apply` usage); `profiles.md` (4 profiles + combination rules); `five-stages.md` (stage protocols, workbench YAML manifest schema, 32-cycle batteries 1-8/9-16/17-24/25-32+, open-minded scrum self-eval questions).
- `tests/validation/test_adaptive_agenda_routine_engine.py`: frontmatter+"Use when"; tokens (HH:MM, handoff, workbench/objetivo_primario/objetivos_secundarios, 4 profile names, 32, Open-Minded Scrum/self-eval, Steve Jobs/experiencia, `extensions/gcal/wrapper.py`, radar, dossie); reference files exist; no em/en dashes.
- Minimal inventory for audit green (as 612 did): manifest.json skill entry + skill_count->185, README badge/prose, TOOLS-MAP, CHANGELOG can defer to Task 3 (audit warns only).
- Commit 1: `feat(skills): add adaptive-agenda-calendar-routine-engine (#613)`.

## Task 2: Wire temporal/loop executor skills

Add `adaptive-agenda-calendar-routine-engine` cross-skill pointer (one line, role-fitting) to: `afk-loop`, `scheduled-turns`, `continuous-improvement`, `self-improvement`, `retro`, `planning`, `executing-plans`, `gates`, `autonomous-gates`, `handoff`, `task-sizer`, `writing-plans`, `planning-pipeline`, `project-memory`. Extend contract test `WIRED_SKILLS` asserting all reference the engine.
- Commit 2: `refactor(skills): wire temporal/loop skills into agenda engine (#613)`.

## Task 3: Docs + ADR + remaining inventory

- `.devin/adr/010-adaptive-agenda-calendar-routine-engine.md` (001-009 format): dual temporal model, profiles, orchestrator+executors, gcal reuse.
- `.devin/docs/SKILL-TIERS.md` entry + count 185; `CHANGELOG.md` [Unreleased]; `README.md` skills-index row if applicable.
- Commit 3: `docs(agenda): ADR-010, skill-tiers, changelog (#613)`.

## FASE 3 (controller)

- Workbench manifest (bench doc) into SDD workspace + pasted in issue comment.
- Cycle log: track real verification iterations (each test run/review/gate = a cycle) grouped in the 4 batteries; require >=32 logged cycles before pushing.
- Push; `gh pr create --body-file` (Mermaid of agenda/routine/32-cycle flow, file map, `Closes #613`, labels type:feat/scope:skills/priority:high); issue comment with execution summary + Open-Minded Scrum self-evaluation + PR link.
