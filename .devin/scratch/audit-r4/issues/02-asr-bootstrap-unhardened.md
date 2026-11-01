# Issue: asr/bootstrap.py -- no error handling, unvalidated extractall, --model traversal

- **Severity**: P2
- **Status**: resolved
- **File**: `extensions/asr/bootstrap.py`

## Evidence

Three independent defects (file has zero `try` blocks):

**a) Network/zip errors escape as tracebacks**
`_fetch` uses `urllib.request.urlopen` -- URLError/HTTPError/timeout ->
traceback, not the `{"ok": false, ...}` contract. `zipfile.ZipFile` on a
corrupt/truncated download -> `BadZipFile` traceback.

**b) `ZipFile.extractall` without member validation (zip-slip)**
`z.extractall(CACHE)` extracts a downloaded archive with no check on
member names. A malicious or corrupted zip containing `../evil` members
writes outside `_cache`. Pinned release URL reduces likelihood, not the
class of bug.

**c) `--model` path traversal**
`fname = f"ggml-{args.model}.bin"`; `CACHE / fname` -- a `--model`
argument containing `../` produces segments that escape `_cache`:
`--model "a/../../evil"` -> `CACHE/ggml-a/../../evil.bin` resolves
outside `_cache` (e.g. `extensions/asr/evil.bin`).

## Acceptance

- `_fetch` errors -> `{"ok": false, "error": "fetch_error:..."}` exit non-zero
- Bad zip -> typed `{"ok": false, "error": "bad_archive"}`
- All zip member names validated: reject absolute paths and `..`
  segments before extraction
- `--model` validated against `[a-z0-9.-]+` (no separators/traversal)
- Regression tests covering traversal arg + zip-slip member + fetch error

## Answer

Fixed. `_fetch` wraps `urlopen` errors into `_FetchError` ->
`{"ok": false, "error": "fetch_error:..."}` exit 2; `BadZipFile` ->
`bad_archive:`. `extractall` now runs through `_safe_members` which
rejects absolute paths, drive-letter (`:`) and `..` segments before any
byte is written -> `bad_archive:unsafe_member:<name>`. `--model`
validated against `^[a-z0-9.-]+$` before any fetch -> `bad_model:`.
`OSError` on mkdir/write -> `write_error:`. 6 regression tests in
`tests/test_asr_bootstrap.py` (traversal arg, slash arg, fetch error,
corrupt zip, zip-slip member blocked + not written, safe zip roundtrip).
