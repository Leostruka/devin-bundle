---
name: roteiro
description: Use when planning a day against a real calendar: pack tasks into actual free slots, re-plan when meetings move, and flag what fits vs. what slips. Composes with extensions/gcal for free/busy data and scheduled-turns for the recurring morning run.
disable-model-invocation: true
---

# roteiro: day planning against real free/busy

Given a task list and today's calendar availability, produce an ordered
roteiro (schedule) with explicit overcommit flags. The packing is
deterministic (`extensions/gcal/plan.py`); the agent's job is assembling
inputs and interpreting the output; never invent free time.

## Input contract

Tasks JSON: `[{"name": "...", "minutes": N, "priority": 1..5}]`
(priority 1 = first). Sources: `.devin/scratch/*/issues/` open items,
`.devin/apps/*/APP.md` prompts, or the user's explicit list.

Calendar: `python extensions/gcal/wrapper.py free-busy` returns
`{busy, free_slots}` from Google Calendar (read-only), or `--ics FILE`
for local iCal files when credentials are absent.

## Run

```sh
python extensions/gcal/wrapper.py free-busy --ics cal.ics \
  --from 2026-11-06T08:00:00Z --to 2026-11-06T20:00:00Z
python extensions/gcal/wrapper.py plan --tasks tasks.json --ics cal.ics
```

`plan` prints `roteiro`: `{schedule:[{task,start,end}], unscheduled,
slack_min, overcommit}`.

## Rules

- **Never fabricate availability.** If `free-busy` returns `missing`
  (no credentials), say so and offer the `--ics` path or ask the user
  for the day's constraints manually.
- **Atomic blocks.** A task fits whole or goes to `unscheduled`; do not
  hand-split tasks to make the plan look fuller.
- **Overcommit is a finding, not a failure.** Report what slips and by
  how much; the human decides what drops.
- **Re-plan triggers**: meeting moved/added, task finished early,
  priority change: re-run `plan` with the updated inputs, don't patch
  the old roteiro by hand.

## Write to the calendar

The agent can write, never silently:

- Preview first: `wrapper.py apply --roteiro <file>` prints the event
  payloads with `status: confirm-required`, nothing is sent.
- On explicit user approval, re-run with `--confirm`. Batch result is
  `created`/`failed` per block; report `partial` honestly.
- Single ad-hoc event: `wrapper.py add --summary X --start ISO --end
  ISO [--calendar id] [--tz Zone] --confirm` - same preview-first gate.
- Writes need the refresh token to carry `calendar.events` scope; a
  scope/HTTP failure surfaces as `status: error`, never fake success.

## Done when

Every input task is either in `schedule` with a concrete start/end or
named in `unscheduled`, and slack is reported.
