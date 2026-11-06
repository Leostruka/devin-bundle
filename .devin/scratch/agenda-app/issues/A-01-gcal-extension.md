# extensions/gcal: free/busy + ics dev input

status: resolved
priority: P2
source: github issue #345/#346 (app backlog)

## Evidence
GitHub #345 (ISSUE_08): agent-planned daily roteiro needs real free/busy data. OAuth refresh-token flow via urllib (no deps); --ics flag parses local iCal VEVENTs for dev/test without credentials.

## Task
CLI wrapper.py: free-busy --ics FILE | --calendars ids --from --to -> JSON busy+free_slots. credentials from env BUNDLE_GCAL_* or credentials.toml; graceful error when absent. ics parser: VEVENT DTSTART/DTEND, UTC + floating local.

## Answer

Shipped: extensions/gcal/gcal.py + wrapper.py - urllib refresh-token flow (no deps), --ics dev mode (VEVENT DTSTART/DTEND, folded lines, TZID, all-day), BUNDLE_GCAL_* env + credentials.toml [gcal], missing-creds graceful envelope. 10 tests green.
