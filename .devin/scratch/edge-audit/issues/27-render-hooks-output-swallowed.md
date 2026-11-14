# 27 -- install.ps1 swallows render-user-hooks.py output, leaving a reason-free warning
- **Status**: resolved
- **Category**: user-experience
- **Severity**: P3
- **File**: install.ps1:527-539

## Evidence
The hook-render step runs `& python $renderHooks $devinHome --merge $configDst | Out-Null` (line 531). Piping to `Out-Null` discards the renderer's stdout, which is where the script reports which hooks were written or why it skipped entries. On failure (non-zero `$LASTEXITCODE`) the installer prints only `render-user-hooks.py failed - hooks not updated` (line 535) with no stderr capture and no hint about the cause (bad JSON? missing devinHome? permission?). stderr from python does still reach the console, but any structured diagnostics the script prints to stdout are lost.

Silent-success path has the inverse problem: a renderer that exits 0 while writing partial hooks reports `config.json hooks rendered from hooks.v1.json` unconditionally.

## Recommendation
Capture output (`$out = & python ... 2>&1`), echo it at DarkGray on success, and include the tail of it in the warning on failure. Alternatively have render-user-hooks.py emit a one-line summary the installer can print.

## Tradeoffs
Merits: actionable failure messages; verifiable success. Demerits: slightly noisier install output.

## Verification
Force a failure (e.g. temporarily corrupt hooks.v1.json) and run install.ps1: the only diagnostic is the generic warning line.

## Answer
install.ps1 render step now captures `$renderOut = & python ... 2>&1`. On success it echoes renderer output at DarkGray; on failure the warning includes the exit code and prints the last 5 output lines. Covered by tests/test_install_ps1_edge_audit.py.
