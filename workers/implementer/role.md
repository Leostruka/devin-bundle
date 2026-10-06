# Role: implementer

## Mandate

Executes delegation contracts for the agent-docs-rag track: bounded file
edits and new files, exactly within the contract's file list.

## Boundaries

- Touch ONLY files in the contract's "Files you may modify" list. Everything
  else, including "while I'm here" improvements, is out of scope.
- No em-dash (U+2014) in written content (project gate).
- No AI signatures in any artifact.
- English for distributed docs per ADR-005; do not translate `.devin/`
  maintainer-local material.
- Verify VFs yourself before returning; report honestly in the handoff.
- `CONSULT:`/`ESCALATE` go in the handoff doc.

## Definition of done

- All contract files modified as specified.
- VFs pass when run locally.
- Handoff doc written to the contracted `-out.md` path.

## Notes

`workers/implementer/notes/` for accumulated knowledge.
