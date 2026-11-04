# 76 -- blender_server nonce check is optional and nonce is leaked in every response
- **Status**: open
- **Category**: security
- **Severity**: P1
- **File**: extensions/blender-operator/blender_server.py:71-74, 116
## Evidence
`_handle` enforces the nonce only when the caller supplies one:

    n = req.get("nonce")
    if n is not None and n != NONCE:
        return {"ok": False, "error": "nonce mismatch"}

A request with no `nonce` field passes the check (line 73 `is not None` short-circuits). Worse, every response embeds the nonce verbatim (`resp["nonce"] = NONCE`, line 116), including responses to malformed JSON ("bad json") and unknown ops, so any local process can read the nonce first and then send `exec` anyway. Net effect: the 127.0.0.1:19693 listener (line 95) gives arbitrary `eval`/`exec` inside Blender (lines 48-50) to any local process, nonce or not.
## Recommendation
Require `req.get("nonce") == NONCE` via `hmac.compare_digest` for `exec` and `shutdown`, and stop echoing `nonce` in responses. Keep `ping` unauthenticated but strip the nonce field there too.
## Tradeoffs
Pinning the nonce into a handshake (first message must carry it, server writes it to a file next to the wrapper) is stronger but requires wrapper changes; compare_digest + no echo is a two-line fix that closes the bypass.
## Verification
Connect to 127.0.0.1:PORT, send `{"op":"ping"}` and observe `nonce` in the reply; send `{"op":"exec","code":"1+1"}` with no nonce and observe it executes.

## Answer
Server now requires the nonce on `exec`/`shutdown` via `hmac.compare_digest`; missing or wrong nonce is rejected. The nonce is never echoed in responses. Instead it is written owner-only (0o600) to `%TEMP%/blender-operator-<port>.nonce` (`--nonce-file` arg, default derived from port) before the listener binds; `wrapper.py` and `camera_blocking.py` pass the path, read it (`wrapper._load_nonce`), and attach it to requests. Stale nonce files are removed at launch and at kill. Ping stays unauthenticated and nonce-free. New socket-level test proves unauthenticated exec is rejected, responses carry no `nonce`, and valid-nonce exec works.

Status: resolved
