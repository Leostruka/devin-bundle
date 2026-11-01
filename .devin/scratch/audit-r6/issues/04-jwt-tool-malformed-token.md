# 04 -- jwt_tool: malformed token raises traceback instead of die()

- **Status**: resolved
- **Severity**: P3
- **File**: `skills/dma/tools/jwt_tool.py:42-45`

## Evidence

`json.loads(b64d(parts[0]))` and the sibling payload/sig decodes run
unguarded. Malformed input is the COMMON case for a JWT analysis tool:
`jwt_tool.py "aaa.bbb.ccc"` reproduces `UnicodeDecodeError`; non-JSON
segments raise `JSONDecodeError`, invalid b64 `binascii.Error`, and a
JSON scalar/list header hits `header.get` -> `AttributeError`. All are
raw tracebacks while the tool's own error convention is `die(msg)`.

## Fix

Wrap the three decodes in try/except (ValueError, binascii.Error)
-> `die("segmento nao e base64/JSON valido")`, and verify `header`/
`payload` are dicts before `.get`.

## Verification

`jwt_tool.py "aaa.bbb.ccc"` and `"e30.e30.e30"` (JSON scalar header)
exit with a `die` message, not a traceback.

## Answer

Fixed. The three segment decodes are wrapped in try/except
(ValueError, UnicodeDecodeError) -> die("segmento nao e base64/JSON
valido"), and header/payload must decode to dicts or die() fires.
"aaa.bbb.ccc" now exits via die(); tests cover malformed segments,
scalar header, and a valid HS256 token.
