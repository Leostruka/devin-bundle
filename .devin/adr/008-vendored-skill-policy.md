# ADR 008: Vendored and external skill adoption policy

## Status

Accepted

## Context

The bundle regularly adopts skills authored elsewhere: cursor/plugins
vendors (e.g. `thermos`), ports (e.g. Ponytail `lean-code`), and renames
to avoid collisions (e.g. Cloudflare `security-audit`). Without a
written policy each adoption re-decides license, attribution, naming,
and audit questions.

## Decision

Policy for adopting an external skill into `skills/`:

1. **License**: permissive licenses only; MIT is the observed baseline.
   Copyleft or unclear licensing requires explicit maintainer sign-off
   recorded in the adoption commit.
2. **Attribution**: upstream source is recorded in `manifest.json`
   (`source` field) and, where required by the license, in `NOTICE.md`
   or the skill header (e.g. "Vendored from cursor/plugins `thermos`
   (MIT license, (c) Cursor)").
3. **Rename on collision**: if the upstream name collides with an
   existing bundle skill or a likely built-in, adopt under a distinct
   name and record the upstream name in `source`.
4. **Adaptation note**: skills adapted to Devin mechanics (e.g.
   `run_subagent` instead of the origin platform's dispatch) state the
   adaptation in the header so future upstream syncs know what diverged.
5. **Audit before vendoring**: the adopting change must scan the vendored
   content for secrets, telemetry, unexpected network calls, and
   non-Devin platform leakage; skill files are executable agent
   instructions and get the same scrutiny as code.
6. **Sync metadata**: no upstream-sync automation is promised; `source`
   records the origin and rough version taken.

Scope: skills only. Extensions have their own distribution and build
constraints (ADR 003) and are out of scope.

## Consequences

- Adoption friction is explicit but bounded: one `source` field, one
  attribution line, one audit pass.
- `skill-coverage`/`skill-discovery` flows that evaluate external skills
  reference this ADR for the accept/reject criteria.
- Policy changes land by amending this ADR, not by editing individual
  skills.
