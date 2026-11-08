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
`{status, source, busy, free_slots, all_day?}` - Google Calendar by
default, `--caldav` for CalDAV servers (iCloud, Fastmail, Nextcloud,
Radicale), or `--ics FILE` / `--ics-url URL` for iCal feeds when
credentials are absent (Google Calendar "secret address in iCal
format" works read-only). `all_day` lists informational all-day events
(reminders/holidays) that do NOT block slots - only `busy` (timed,
non-transparent) does. ics sources may under-report recurring events:
RRULE is counted (`recurring_events` + `hint` in output) but not
expanded - each recurring VEVENT contributes only its first instance.
TZID parameters are honored via zoneinfo (needs system tzdata or
`pip install tzdata`; unresolved TZIDs warn and assume UTC).

## Run

```sh
python extensions/gcal/wrapper.py free-busy --ics cal.ics \
  --from 2026-11-06T08:00:00Z --to 2026-11-06T20:00:00Z
python extensions/gcal/wrapper.py free-busy --caldav \
  --from 2026-11-08T12:00:00Z --to 2026-11-08T21:00:00Z
python extensions/gcal/wrapper.py plan --tasks tasks.json --ics cal.ics
```

`--caldav` reads all calendars via calendar-query REPORT (busy =
non-TRANSPARENT VEVENTs); `--calendars name[,name]` filters by
display-name. CalDAV credentials: `BUNDLE_CALDAV_URL/USER/PASSWORD` env
or `[caldav]` in credentials.toml - app passwords, no OAuth.

`plan` prints `roteiro`: `{schedule:[{task,start,end}], unscheduled,
slack_min, overcommit}`.

## Rules

- **Never fabricate availability.** If `free-busy` returns `missing`
  (no credentials on any backend), say so and offer the `--ics` path
  or ask the user for the day's constraints manually.
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
  ISO [--calendar NAME-or-id] [--tz Zone] --confirm` - same
  preview-first gate.
- Writes default to the dedicated `AGdevin` calendar: find-or-create
  on first write, reused after - agent events stay isolated from the
  account's other calendars. `--calendar primary` or a raw id
  overrides (Google); on CalDAV, `--calendar` matches a display-name
  or creates the collection.
- Backend flag: `--caldav` routes free-busy/add/apply to the CalDAV
  client (same `--confirm` gate, same AGdevin default).
- Google writes need the refresh token to carry `calendar.events`
  scope; CalDAV writes use the app password. Auth/scope/HTTP failures
  surface as `status: error`, never fake success.

## Done when

Every input task is either in `schedule` with a concrete start/end or
named in `unscheduled`, and slack is reported.
