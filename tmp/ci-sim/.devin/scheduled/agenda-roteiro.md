# Scheduled turn: agenda-roteiro (daily morning)

Fire: once daily ~09:00 local (registered by user via Register-ScheduledTask;
this file is the prompt only - the agent never registers the task itself).

## Do

1. Read `.devin/ledgers/scheduled-agenda-roteiro.md` first (inter-turn
   memory). If missing, create it.
2. Fetch real availability:
   `python extensions/gcal/wrapper.py free-busy --from <today>T00:00:00-03:00 --to <tomorrow>T00:00:00-03:00`
   If `status: missing`, STOP and write `ABANDON: no calendar credentials`
   to the ledger.
3. Build today's slots from `free_slots` intersected with work windows
   09:00-12:00 and 14:00-18:00 local (drop slots outside; all-day events
   are informational only). Write `.devin/scratch/dev-org-ladder/slots-<date>.json`.
4. Collect candidate tasks: open items from `.devin/scratch/*/issues/` and
   `.devin/issues/` plus the week's roteiro
   (`.devin/plans/2026-11-09-week-roteiro.md`) - pick today's blocks,
   estimate minutes, assign priority 1..5.
5. Run `python extensions/gcal/wrapper.py plan --tasks <file> --slots <file>`.
   Write roteiro to `.devin/scratch/dev-org-ladder/roteiro-<date>.json`.
6. Report: scheduled blocks, unscheduled list, slack_min, overcommit.
   Never fabricate availability; never write to the calendar without
   explicit user approval in-session (`apply --confirm` gate stays).

## Ledger entry (append each run)

`## <date>` - outcome (ok/abandon), blocks scheduled, unscheduled count,
slack, overcommit, next check.

## Hard stop

Max ~10 minutes wall clock. If free-busy errors twice or plan output is
malformed, write `ABANDON: <reason>` and exit. No retries beyond 2.
