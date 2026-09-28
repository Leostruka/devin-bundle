# scrape-tools — web scraping/fetch/parse (Scrapling)

Fetch and parse HTML with a tiered footprint: offline parser, HTTP
(curl_cffi TLS impersonation), opt-in browser tiers. Use when a task needs
structured data out of web pages. All tools print JSON to stdout.

## Layout

| File | Purpose |
|---|---|
| `parse.py` | Offline HTML parsing: file/stdin + `--css`/`--xpath` + `--first`. Zero network. |
| `scrape.py` | HTTP fetch via `Fetcher` (curl_cffi): `--impersonate`, `--adaptive`, `--browser`. |
| `st_common.py` | Shared: JSON contract, node extraction, storage root, browser-tier check. |
| `requirements.txt` | `scrapling[fetchers]==0.4.15` (pinned: 0.x breaks across releases). |

## Interpreter

Run with the extension venv Python (created by `install.ps1`/`install.sh`,
or `python -m venv .venv && .venv/Scripts/pip install -r requirements.txt`):

```bash
.venv/Scripts/python parse.py page.html --css ".item"
.venv/Scripts/python scrape.py https://example.com --css "h1" --impersonate chrome
```

## Tiers

| Tier | Needs | Notes |
|---|---|---|
| Parse (parse.py) | core deps | no network, works on saved HTML |
| Fetch (scrape.py) | `[fetchers]` wheels | TLS impersonation, HTTP/3, `follow_redirects="safe"` (SSRF guard) |
| Browser (`--browser dynamic\|stealthy`) | user runs `python -m scrapling.cli.install` | ~300-600MB browser binaries; rejected with `feature_off:browser_tier_not_installed` until then |

## Adaptive

`scrape.py --adaptive [--identifier NAME]` fingerprints matches into local
SQLite (`$SCRAPE_STATE_ROOT` or `.devin/scrape-tools/storage/adaptive.db`)
and re-scores on the next call when markup changes. It is *tracking*, not
redesign recovery — a full page rewrite will not relocate elements.

## Honest limits

- No "undetectable" claims: enterprise Cloudflare has 403'd all fetcher
  tiers in field reports; basic CF may pass with `stealthy`.
- Stealth patches are JS-layer (detectable); IP reputation is not fixed.
- HTML only — no XML parsing.
- Forbidden uses: credential scraping, auth-bypass crawling, or any target
  whose ToS/robots you are not authorized to touch.

## Live gate (manual)

Real-network check, opt-in (not CI):

```bash
.venv/Scripts/python scrape.py https://httpbin.org/html --css "h1"
# expect: {"ok": true, "status": 200, "nodes": [{"tag":"h1", ...}]}
```
