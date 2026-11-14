# 65 -- architecture-gate exec escape is a comment-level bypass

- **Status**: resolved
- **Category**: applied-rules
- **Severity**: P2
- **File**: scripts/architecture-gate.py:106-107

## Evidence

`check_exec` returns early whenever the literal string `ARCHITECTURE_MANIFEST`
appears anywhere in the command. `echo x > src/a.py  # ARCHITECTURE_MANIFEST`
or `touch src/a.py && echo ARCHITECTURE_MANIFEST` mutates the source tree and
passes the gate. The escape exists so the manifest can be created via shell,
but it is not scoped to commands that actually write the manifest file.

## Recommendation

Narrow the hatch: allow only commands whose redirect/target path ends with
`.devin/ARCHITECTURE_MANIFEST.md`, or require the manifest be created via the
write tool (already exempted at line 85) and remove the exec hatch entirely.

## Tradeoffs

Removing the exec hatch forces manifest creation through write/edit, which is
already exempt, so no legitimate path is lost.

## Verification

In a .devin project without the manifest, run an exec payload for
`echo hi > x.py # ARCHITECTURE_MANIFEST`; the hook exits 0.

## Answer
Removed the exec escape hatch entirely. The manifest is created via the
write/edit tools, which are already exempt, so no legitimate path is lost;
`echo x > src/a.py  # ARCHITECTURE_MANIFEST` now correctly blocks. Docstring
updated to document the removal.
