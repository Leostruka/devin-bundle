# 09 -- export.sh validation py_compile writes __pycache__ into bundle scripts/
- **Status**: resolved
- **Category**: optimization
- **Severity**: P3
- **File**: export.sh:529-540

## Evidence
Pre-push validation runs `python3 -m py_compile "$py_file"` on every file in
`$BUNDLE_DIR/scripts`. py_compile writes `__pycache__/*.pyc` next to each
script unconditionally. export.ps1's equivalent (Test-PythonSyntax,
export.ps1:210-220) deliberately uses `ast.parse` "to validate syntax without
writing .pyc files". Effect: every `--push` litters scripts/ with a
__pycache__ dir; it is gitignored, so it does not commit, but it then gets
copied by `install.sh`'s `for script_file in "$scripts_src"/*` glob? -- no,
that loop skips dirs (`-f` check), so impact is a dirty working tree and
extra files on disk. Still a behavior the ps1 explicitly avoids.

## Recommendation
Replace with `python3 -c 'import ast,sys; ast.parse(open(sys.argv[1],encoding="utf-8").read())' "$py_file"` (same as ps1), or
`PYTHONDONTWRITEBYTECODE` does NOT help (py_compile ignores it); use
`python3 -m py_compile` with `-` stdin alternative or set `sys.dont_write_bytecode`
via a `-c` wrapper: `python3 -c 'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=os.devnull, doraise=True)'`.

## Tradeoffs
None.

## Verification
`find scripts -name __pycache__` empty after a `--push` validation run.

## Answer

Pre-push script validation now runs `python -c 'ast.parse(...)'` instead of py_compile, so no __pycache__/.pyc is written into bundle scripts/ (same approach as export.ps1 Test-PythonSyntax).
