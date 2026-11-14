# R7-05: python -c blocks interpolate paths into source code

**Severity:** P3 (injection/mangling)
**Files:** export.sh:283-294 (config mask), 377-405 (mcp mask)

**Defect:** `'$config_src'`/`'$mcp_src'`/`'$mcp_dst'` are interpolated
inside `python3 -c "..."` source. A path containing a quote or
backslash (Windows DEVIN_HOME) mangles or breaks the embedded code --
and it is code injection via environment path. The same file already
uses the correct pattern at line 87 (path via stdin + env var).

**Fix:** pass paths via sys.argv instead of interpolation.

## Answer

Fixed + regression test in `tests/validation/test_install_export_scripts.py`.
