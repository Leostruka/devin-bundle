---
name: adaptive-agenda-calendar-routine-engine
description: Use when planning or executing work across hours, days, weeks, or sprints. Turns the calendar into a strict time-blocked agenda (HH:MM-HH:MM blocks carrying a routine profile, expected inputs, and a handoff output artifact), runs the 5-stage cognitive flow (Radar and Hunt -> Triage plus Steve Jobs conception -> workbench manifest -> >=32-cycle loop -> Close plus Open-Minded Scrum), and unfolds macro calendar milestones into micro agenda blocks through extensions/gcal/wrapper.py.
triggers: [user, model]
---

# Adaptive Agenda Calendar Routine Engine

## Overview

Orchestrating engine that turns the calendar into a strict execution
machine. It owns two synced temporal layers and the cognitive pipeline
that feeds them; executor skills do the actual work.

- **Macro calendar**: weeks, sprints, releases. Milestones, deadlines,
  and review points persisted through `extensions/gcal/wrapper.py`.
- **Micro agenda**: the day, cut into strict `HH:MM`-`HH:MM`
  time-blocks. Each block declares its start/end, the active routine
  profile, the expected inputs, and the handoff output artifact it must
  leave behind.

Every block ends with the **handoff rite**: the final ~15 minutes index
and clean all findings so the next block starts without friction. No
block closes on raw output; it closes on a clean, indexed artifact.

## Five-stage flow (summary)

Full protocols live in `reference/five-stages.md`; this is the routing
map.

| Stage | Name | Output artifact |
|---|---|---|
| 1 | Radar and Hunt | Indexed raw dossier (dossie) feeding the next block |
| 2 | Triage, benefit calc, Jobs conception | Ranked opportunities + experience-first design direction |
| 3 | Workbench manifest | YAML manifest: janela_horario, perfil_ativo, objetivo_primario, objetivos_secundarios, ferramentas_na_bancada, regras_e_decisoes |
| 4 | 32-cycle loop | >=32 logged cycles across 4 batteries of 8 |
| 5 | Close | Living docs, versioned commits, self-evaluation, re-planned calendar |

## Routine profiles

Four switchable, combinable profiles set the cognitive posture per
block, day, or sprint. Full rules in `reference/profiles.md`.

| Profile | Posture | Hunt focus |
|---|---|---|
| `foco-novidades` | P&D radar | Direct + surrounding news, tools, papers, adjacent tech |
| `foco-qualidade-produto` | Steve Jobs UX-first | Human experience first, then reverse to tech: exists / reusable / invent |
| `foco-interno` | Hardening | Deep refactor, zero-trust security, hardware-level optimization, telemetry |
| `foco-externo` | Ecosystem | DX, integrations, public docs, benchmarks, external demand |

Combination rules: max 2 profiles active per block, one dominant;
profiles switch at block boundaries, never mid-block.

## Temporal flow

1. **Macro planning**: `wrapper.py free-busy` + `plan` pack macro
   milestones into real free slots; `apply`/`add` write the approved
   roteiro (always preview `confirm-required` first; `--confirm` to
   write). Commands in `reference/temporal-architecture.md`.
2. **Micro unfolding**: each macro milestone expands into
   `HH:MM`-`HH:MM` blocks; each block carries profile + inputs +
   handoff artifact.
3. **Execution**: blocks run the five-stage flow; the handoff rite
   closes each block.
4. **Re-plan**: drift triggers a `plan` re-run with updated inputs,
   never hand-patching the old roteiro.

## Delegation map

The engine orchestrates; these skills execute:

| Need | Executor |
|---|---|
| Unattended multi-issue implementation | `afk-loop` |
| Recurring/always-on turns (morning radar, daily triage) | `scheduled-turns` |
| Day packing against real free/busy | `roteiro` |
| Session/period retrospective | `retro` |
| Kaizen self-improvement loop | `continuous-improvement`, `self-improvement` |
| Block-to-block context transfer | `handoff` |
| Completion-claim discipline, >=32-cycle evidence | `gates` |
| Versioned delivery in Stage 5 (commits, PRs, issue wiring) | `gh`, `git-workflows`, `pr`, `finishing-a-development-branch` |

## Boundaries

- `extensions/gcal/wrapper.py` is the mechanical calendar backend:
  referenced here, never modified by this skill. Writes need
  `--confirm`; always run the preview first.
- Destructive calendar operations need explicit per-action
  confirmation.
- The engine decides what runs and in which order; it does not bypass
  executor skills' own contracts.
- The engine schedules and sequences work; git/GitHub delivery mechanics
  (commits, PRs, issues, releases) belong to the git/GitHub skills and
  are never re-implemented here.
