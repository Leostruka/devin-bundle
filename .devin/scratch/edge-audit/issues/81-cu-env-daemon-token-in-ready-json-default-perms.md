# 81 -- cu_env_daemon TCP auth token written to ready.json with default file perms
- **Status**: open
- **Category**: security
- **Severity**: P3
- **File**: extensions/computer-use/cu_env_daemon.py:198-204, 236-240
## Evidence
On platforms without AF_UNIX (Windows; or deep tmp paths where sun_path overflows), `_bind_listener` mints a 128-bit `token` and returns it inside the `ready` dict; `serve` then writes the whole dict via `(env_dir / "ready.json").write_text(...)` (line 239-240). `write_text` uses default umask permissions (0644 typical), so the only secret gating the QMP-forwarding listener (checked at line 297 `obj.get("token") != token`) is readable by any local account. The docstring claims the token lives "only in the private env dir" (line 188) but nothing makes the dir or file private.
## Recommendation
`os.chmod(env_dir, 0o700)` at creation and write `ready.json` via `os.open(..., O_WRONLY|O_CREAT, 0o600)`; or keep the token out of the file and return it over the unix socket / a separate channel.
## Verification
`stat -c %a <env_dir>/ready.json` on POSIX after daemon start; confirm it contains `"token"` and is group/other-readable.
