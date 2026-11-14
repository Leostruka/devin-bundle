# ADR 010: Adaptive agenda, calendar, and routine engine

## Status

Accepted

## Context

Issue #613 asked for a skill that turns the calendar into a strict
execution machine: long-horizon planning, disciplined daily
execution, switchable routine profiles, and a verification loop with
an evidence floor. The bundle already had the mechanical pieces:
`extensions/gcal/wrapper.py` (free/busy, plan, add, apply behind a
`--confirm` gate), `roteiro` (day packing), `afk-loop`,
`scheduled-turns`, `retro`, `continuous-improvement`,
`self-improvement`, `handoff`, `gates`, and friends. What was missing
was the layer that decides what runs, in which order, under which
cognitive posture, across hours, days, weeks, and sprints.

## Decision

Ship `skills/adaptive-agenda-calendar-routine-engine` as an
orchestrator over the existing executors, structured as:

1. **Dual temporal model.** A macro layer (weeks, sprints, releases)
   persists milestones and deadlines as calendar events; a micro
   layer cuts each day into strict `HH:MM`-`HH:MM` blocks. Each block
   declares its dominant routine profile, expected inputs, and the
   handoff output artifact it must leave behind; the last ~15 minutes
   of every block run the mandatory handoff rite (index, decide,
   verify next inputs, append handoff note) so boundaries are real,
   not aspirational.
2. **Four routine profiles** (`foco-novidades`,
   `foco-qualidade-produto`, `foco-interno`, `foco-externo`) act as
   switchable cognitive postures: they change what the radar hunts,
   how triage scores benefit, and which batteries of the verification
   loop get emphasis. Max two profiles per block, one dominant;
   profiles switch only at block boundaries.
3. **Five-stage flow.** Radar and Hunt -> Triage plus Steve Jobs
   experience-first conception -> workbench YAML manifest
   (`objetivo_primario` armored against `objetivos_secundarios`) ->
   >=32-cycle loop in four batteries of eight -> Close with living
   docs, versioned commits, Open-Minded Scrum self-evaluation, and
   calendar re-plan.
4. **Orchestrator plus executors.** The engine decides what runs and
   when; existing skills execute (delegation map in SKILL.md). Task 2
   wired 15 temporal/loop skills with one-line cross-skill pointers;
   no executor bodies were rewritten.
5. **gcal reused, not modified.** `extensions/gcal/wrapper.py` remains
   the mechanical calendar backend (`free-busy`, `plan`, `add`,
   `apply`, `--confirm` gate, dedicated `AGdevin` calendar, envelope
   v2). The engine references it; writes are preview-first and
   destructive operations keep explicit per-action confirmation.
6. **Re-plan, never hand-patch.** Drift between macro and micro is
   the main failure mode; the fix is re-running `plan` with updated
   inputs. Three artifacts are the source of truth over memory:
   calendar events, the workbench manifest, and the cycle/dossie log.

## Consequences

- Long-horizon work gains a single entry point: invoke the engine,
  it unfolds macro milestones into micro blocks and delegates.
- The >=32-cycle loop makes "done" evidence-bearing: `gates` requires
  a logged verdict per cycle; padded repeats do not count.
- Calendar writes stay safe by construction: preview without
  `--confirm`, dedupe via `apply`, honest `partial` reporting.
- Maintenance surface stays small: the engine owns orchestration
  only; executor contract changes land in the executor skills.
