# Handoff doc

Structured artifact moving work between roles. Written by the producing
role; read by the consuming role. Replaces free chat between roles.

## Header

- **Handoff**: <contract ID>
- **From role**: <role>
- **To role**: <role>
- **Date**: <YYYY-MM-DD>
- **ESCALATE**: <reason, or "none"> - when set, the orchestrator stops the
  loop and presents it to the user before dispatching further work
- **CONSULT**: <role>: <question>, or "none" - a bounded question to a peer
  role, relayed by the orchestrator per the contract's Peer consults cap

## Inputs consumed

- <artifact paths with one-line relevance>

## Outputs produced

- <artifact paths created/modified; commits if any>

## Decisions taken

- <decision + rationale + alternatives rejected>

## Verified claims

- <claim -> evidence (command output, source, test)>

## Open items / gaps

- <what the next role must resolve or know>

## Requested next action

- <what the receiver should do with this>
