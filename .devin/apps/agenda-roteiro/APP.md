# Agenda Roteiro (agenda-roteiro)

intent: build each day's roteiro from real calendar free/busy + open tasks
kind: agentic-app
schedule: daily morning (scheduled-turns) + on-demand re-plan when meetings move
inputs: Google Calendar via extensions/gcal (free/busy) or --ics dev file; task list from .devin/scratch open issues or user prompt
outputs: roteiro JSON {schedule, unscheduled, slack_min, overcommit} + a short plan message; on user approval, calendar events via `apply --confirm` (writes to dedicated AGdevin calendar, isolated from the rest of the account)
done-when: every task is scheduled with concrete start/end or named unscheduled, slack reported, overcommit flagged to the user

## Prompt

Fetch free/busy: `python extensions/gcal/wrapper.py free-busy [--calendars ids] --from <day-start> --to <day-end>` (fallback: `--ics <file>` or ask the user for constraints; never fabricate). Collect today's candidate tasks (open scratch issues + user's list) with minutes and priority. Run `python extensions/gcal/wrapper.py plan --tasks <file> --ics <file>` and emit the roteiro: scheduled blocks in order, then "does not fit" list with total slack. Re-plan on calendar changes instead of editing the roteiro by hand. When the user approves the roteiro, write it: `python extensions/gcal/wrapper.py apply --roteiro <file> [--prefix "[roteiro] "] --confirm` - preview without `--confirm` first, confirm once. Single ad-hoc events: `add --summary X --start ISO --end ISO --confirm`. See skills/roteiro for the full contract.

## Run log

- 2026-11-08 first REAL run: Google OAuth (oauth_setup.py -> credentials.toml [gcal], 3 scopes incl. calendar.calendars) -> Calendar API enabled -> `free-busy` source=api (all-day "Mensalidade united" reported informational, timed busy=[]) -> `plan` over slots.json -> `apply --confirm` created AGdevin calendar + 4 events, all confirmed, 0 failed. Roteiro: .devin/scratch/dev-org-ladder/roteiro.json. Found+fixed: freeBusy endpoint counted all-day events as full-day busy -> switched to events.list; apply crashed on plan envelope -> unwrap fix.
- (first real run pending credentials; --ics dev mode verified 2026-11-06)
