# Temporal architecture: macro calendar -> micro agenda

Two synced layers. The macro layer holds intent (weeks, sprints,
releases); the micro layer holds execution (the day, in strict
`HH:MM`-`HH:MM` blocks). Drift between them is the main failure mode;
re-planning, never hand-patching, is the fix.

## Layer split

```
MACRO (weeks / sprints / releases)
  milestone: "v2.0 release"      deadline: "sprint review Fri"
        |
        v   unfold: Stage 3 workbench decides block shape + profile
MICRO (one day)
  08:00-10:00  foco-novidades    in: last dossie   out: radar dossie v2
    (09:45-10:00 handoff rite inside the block)
  10:00-12:00  foco-qualidade-produto  in: dossie v2  out: triage ranking
    (11:45-12:00 handoff rite)
  12:00-13:00  break / admin
  13:00-17:00  foco-interno      in: workbench manifest  out: 32-cycle log
    (16:45-17:00 handoff rite)
  17:00-17:30  foco-externo      in: cycle log  out: release notes draft
    (17:15-17:30 handoff rite)
```

## Block contract

Every micro block declares five fields before it starts:

| Field | Content |
|---|---|
| `HH:MM`-`HH:MM` | Strict start/end; the last ~15 min are the handoff rite |
| `perfil_ativo` | One dominant routine profile (max 2 combined) |
| `inputs` | Artifacts the block consumes (dossie, manifest, prior log) |
| `output` | The handoff artifact the block must leave behind |
| `rite` | What "clean" means for this block's output |

A block that ends without its declared output is an incomplete block:
log it, do not silently carry debt into the next block.

## Handoff rite protocol

Runs inside the final ~15 minutes of every block (or early if the
block ends ahead of schedule):

1. **Index**: every finding lands in the block's output artifact in
   structured form (dossie entries, triage rows, cycle log lines).
2. **Decide**: mark what was decided, what was rejected, and why.
3. **Verify inputs**: confirm the next block's declared `inputs`
   actually exist; create stubs for anything missing.
4. **Hand off**: append a one-line handoff note (block id, artifact
   path, open question) to the shared ledger or `.devin/handoffs/`.

The rite is mandatory, not optional polish: it is the mechanism that
makes `HH:MM` boundaries real instead of aspirational.

## Mechanical backend: extensions/gcal/wrapper.py

The engine references this wrapper; it never modifies it. All commands
emit JSON envelopes (`api_version: 2`) and exit 0 on `ok`.

### Read availability

```sh
python extensions/gcal/wrapper.py free-busy \
  --from 2026-11-16T08:00:00Z --to 2026-11-16T20:00:00Z
```

Returns `{status, source, busy, free_slots, all_day?}`. Backends:
default Google Calendar, `--caldav` for CalDAV servers, `--ics FILE` /
`--ics-url URL` for offline iCal feeds. `status: missing` means no
credentials on any backend: report it, offer the `--ics` path, never
invent free time.

### Pack tasks into slots

```sh
python extensions/gcal/wrapper.py plan --tasks tasks.json --ics cal.ics
```

`tasks.json`: `[{"name": "...", "minutes": N, "priority": 1..5}]`
(priority 1 = first). Output `roteiro`: `{schedule: [{task, start,
end}], unscheduled, slack_min, overcommit}`. `overcommit` is a finding
to report, not a failure to hide; atomic blocks only, never hand-split
tasks to make the plan look fuller.

### Write events (preview first, always)

```sh
python extensions/gcal/wrapper.py add \
  --summary "foco-interno: 32-cycle loop" \
  --start 2026-11-16T13:00:00Z --end 2026-11-16T17:00:00Z \
  --tz America/Sao_Paulo --confirm
```

Without `--confirm` the CLI prints the payload and exits
`confirm-required`; nothing is sent. Re-run with `--confirm` only on
explicit approval. Writes default to the dedicated `AGdevin` calendar
(find-or-create, isolated from personal calendars); `--calendar
primary` or a raw id overrides. `apply` batch-writes a roteiro:

```sh
python extensions/gcal/wrapper.py apply --roteiro file.json --prefix "agenda: " --confirm
```

`apply` dedupes by content key (`skipped_existing` in output) and
reports `created`/`failed` per block; `partial` means some blocks
failed and must be reported honestly.

## Unfolding macro into micro

1. Run `free-busy` for the planning window; feed `plan` the macro
   milestones as tasks (one task per milestone/block, priority ordered).
2. Take the `roteiro.schedule` and expand each packed task into
   micro blocks: assign `HH:MM`-`HH:MM` bounds inside the packed slot,
   pick the dominant profile, declare inputs and the handoff artifact.
3. Reserve the last ~15 min of each block for the handoff rite inside
   the block bounds; do not schedule the rite as a separate block.
4. Persist the unfolded agenda (workbench manifest + block list) under
   the target project's `.devin/` so it survives compaction.
5. Re-plan triggers: meeting moved/added, block finished early,
   priority change, profile switch. Re-run `plan` with updated inputs;
   never patch the old roteiro by hand.

## Long-range persistence

Macro calendars span weeks to releases. Keep three artifacts per
horizon:

- **Calendar events** (via `apply`/`add`): what the human sees.
- **Workbench manifest** (Stage 3 YAML): what the agent executes.
- **Cycle log / dossie trail**: what actually happened, feeding Stage 5
  re-planning.

When the three disagree, the artifacts win over memory: re-read them,
re-run `plan`, and record the correction in `regras_e_decisoes`.
