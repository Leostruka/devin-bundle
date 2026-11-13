# 82 -- scrape.py fetches arbitrary URLs with no scheme/host allowlist
- **Status**: resolved
- **Category**: security
- **Severity**: P3
- **File**: extensions/scrape-tools/scrape.py:56-57
## Evidence
The positional `url` argument is passed straight to `fetcher.get(args.url, ...)` with `follow_redirects="safe"`. The docstring (line 3) claims "SSRF-safe redirects on", but nothing validates the initial URL: no scheme check (`file://`, `gopher://` reach curl_cffi depending on backend), no host allowlist, no private/loopback/link-local rejection. An agent call can hit `http://169.254.169.254/latest/meta-data`, `http://127.0.0.1:PORT/` on internal daemons (e.g. the cu_env QMP gate from issue 81, blender_server :19693), or `file:///etc/passwd`. Whether scrapling's `"safe"` redirect mode actually blocks redirect-to-private is unverified in-repo; the initial request is unchecked regardless.
## Recommendation
Parse with `urllib.parse.urlparse`; require scheme in {http, https}; resolve the host and reject loopback/link-local/RFC1918 (or gate private IPs behind an explicit `--allow-private` flag). Verify what `follow_redirects="safe"` does in the pinned scrapling version and add a regression test for redirect-to-127.0.0.1.
## Tradeoffs
This is a local agent tool, so full SSRF hardening may be disproportionate; a private-range opt-out flag preserves legitimate intranet scraping.
## Verification
`python scrape.py http://127.0.0.1:<any-listener>/ --css body` succeeds today; add a test asserting it is rejected after the fix.

## Answer
`check_url_allowed` gates the initial request: scheme must be http/https; IP literals are checked directly; hostnames are resolved and rejected when any answer is loopback/private/link-local/multicast/reserved/unspecified. `--allow-private` is the explicit opt-out. Failure exits code 2 with `ssrf_blocked:...`. Tests cover file/gopher/ftp schemes, 127.0.0.1/169.254.169.254/10.x/::1, DNS-to-private, the opt-out flag, and unresolvable hosts.

Status: resolved
