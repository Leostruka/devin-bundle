# Issue: comfyui cmd_download writes server-controlled filenames (traversal)

- **Severity**: P2
- **Status**: resolved
- **File**: `extensions/comfyui-operator/wrapper.py` (`cmd_download`)

## Evidence

```python
name = f["subfolder"] + f["filename"] if f["subfolder"] \
    else f["filename"]
dest = os.path.join(outdir, name.replace("/", "_"))
```

`filename`/`subfolder`/`type` come from the server's `/history`
response -- attacker-controlled when the base URL is non-local
(see issue 01), or crafted via a hostile workflow on a local server.

- `subfolder="..\\.."` -> `name="..\\..\\x.png"`;
  `replace("/","_")` does NOT strip backslashes ->
  `os.path.join(outdir, "..\\..\\x.png")` writes OUTSIDE outdir
  on Windows (verified: `os.path.normpath` resolves `..\`).
- `filename="C:\\evil.png"` -> `os.path.join(outdir, "C:\\evil.png")`
  returns `C:\evil.png` on Windows (absolute second arg wins) ->
  arbitrary write.

## Reproduce

```python
# with a stubbed _collect_outputs returning
# {"filename":"..\\evil.png","subfolder":"","type":"output"}
# cmd_download writes to <parent-of-outdir>/evil.png on Windows
```

## Acceptance

- Dest name reduced to `os.path.basename` of the combined name AND
  normalized: reject or strip `..` segments, both `/` and `\\`,
  drive-letters/absolute names (e.g. `ntpath.basename` + whitelist of
  `[A-Za-z0-9._-]` or explicit escape check: resolved dest must be
  inside resolved outdir)
- Traversal filename -> skipped file + reported in output (or typed
  fail), never written outside outdir
- Regression tests on Windows semantics: `..\`, absolute drive path,
  mixed separators

## Answer

Fixed. `cmd_download` writes through new `_safe_dest(outdir,
subfolder, filename)`: normalizes `\` to `/`, reduces to basename
(neutralizing `..\`, `../`, drive-absolute and UNC paths to a plain
filename inside outdir), rejects empty/`.`/`..` results, and verifies
`os.path.commonpath([realpath(outdir), realpath(dest)]) == outdir`
with a `ValueError` guard for cross-drive paths. A name that still
fails produces typed `_fail("unsafe output name...")`. Tests cover
`..\`/`../` traversal, traversal embedded in filename, absolute drive
path, `..` rejection, and an end-to-end download that lands inside
outdir with nothing written outside.
