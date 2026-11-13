# Scrapling – Deep Research Report

*Read-only investigation. Facts verified against primary docs/repo where noted; marketing claims flagged. Snapshot: Aug-Sep 2026. Page-level claims rely on search-indexed excerpts of primary sources - flagged UNVERIFIED where thin.*

## 1. ARCHITECTURE

Scrapling is a Python **adaptive web-scraping framework** (not just a parser or just a fetcher) covering three layers, all returning one unified `Response` object [1][5]:

- **Parser** - `Selector` wrapping `lxml.html.HtmlElement` (composition, not inheritance - lxml elements aren't picklable [33]). Core install.
- **Fetchers** - `Fetcher` (HTTP via `curl_cffi`), `DynamicFetcher` (Playwright/Chromium), `StealthyFetcher` (Chromium via `patchright`). Require `scrapling[fetchers]` [5][10].
- **Spiders** (v0.4+) - Scrapy-inspired async crawling on `anyio`: `Spider` ABC with `start_urls`/`parse`, Scheduler (priority queue + request fingerprints), Crawler Engine (concurrency limits, per-domain throttling, `robots_txt_obey`, retry x3), Session Manager by `sid`, checkpoint pause/resume via `crawldir`, `stream()` mode, AutoThrottle, uvloop option [25][26][27].

**Flow:** `Fetcher.get()/fetch()` -> engine -> `Response` (subclasses `Selector`; adds `status`, `reason`, `headers`, `cookies`, `history`, `body` bytes (v0.4), `meta`, `captured_xhr`) [5][46]. Sync `Fetcher`/`AsyncFetcher`; sessions: `FetcherSession`, `DynamicSession`/`AsyncDynamicSession`, `StealthySession`/`AsyncStealthySession` [6].

## 2. FETCHERS

| Fetcher | Engine | Browser | Notes |
|---|---|---|---|
| `Fetcher`/`AsyncFetcher` | `curl_cffi` | none | TLS impersonation, HTTP/3, stealthy headers [7][10] |
| `DynamicFetcher` | `playwright` | Chromium/real Chrome | JS render, `page_action`/`page_setup` hooks; formerly PlayWrightFetcher [9][12] |
| `StealthyFetcher` | `patchright` | Chromium/real Chrome; `cdp_url` attach | stealth + Cloudflare solver [4][8] |

- Persistent sessions; browser sessions use **tab pool** (`max_pages`); tabs reused since v0.4.15 [6][15].
- **Camoufox dropped at v0.3.13** for Patchright/Chromium (faster, less RAM/disk, ~400 LOC shorter) [13][14]; fully removed by 0.4.10 [16].

## 3. STEALTH / ANTI-BOT

**Verified:** TLS/JA3 impersonation via curl_cffi (`impersonate=` chrome/edge/safari/firefox/tor + versions) [7]; matched real browser headers (`stealthy_headers`, incl. Google referer) [7][17]; StealthyFetcher args: `solve_cloudflare` (Turnstile/Interstitial incl. interactive), CDP runtime-leak bypass, `block_webrtc`, canvas noise (`hide_canvas`), headless-detection patches, `dns_over_https`, `real_chrome`, `cdp_url` attach, ad blocking (~3,500 domains) [4][8][18]; `follow_redirects="safe"` SSRF guard on `Fetcher` [7]; MCP strips prompt-injection content (README claim) [19].

**Removed (Camoufox era):** `humanize`, `geoip`, `os_randomize`, `addons`, `disable_ads`, `block_images` [13]. Third-party matrix: human-mouse sim NO, fingerprint rotation NO [20].

**Limits:** Patchright = JS-layer patches (detectable via toString enumeration + CDP attach) [22]; enterprise Cloudflare 403'd all fetchers in a user test (basic CF passed) [23]; Tencent WAF intermittency [24]; does not fix IP reputation.

## 4. PARSING API

CSS3 via cssselect + XPath via lxml; **HTML only, no XML** [28]. `css`, `xpath`, `find`/`find_all`, `find_by_text`, `find_by_regex`, `.get()`/`.getall()` (extract_first/extract), `.first`/`.last`; `Selectors` is a List subclass [29][30]. v0.4 wraps text nodes as `Selector(tag="#text")` [29][31].

**Adaptive/auto-match:** `auto_save=True` fingerprints an element into pluggable storage (**SQLite default**, thread-safe; `StorageSystemMixin` for custom backends) keyed by (domain, identifier); `adaptive=True` re-scores every page element by similarity, returns best above `percentage` (default 40); `relocate()` runs matching (`__calculate_similarity_score`, parser.py); `adaptive_domain` for domain moves. Pure heuristics, no AI [32][33][34][35]. Independent test: works after class rename; "tracking, not redesign recovery" [36].

## 5. SESSION / TOOLING

- `ProxyRotator` (v0.4): thread-safe cyclic/custom strategies; per-proxy browser contexts; `response.meta["proxy"]` [38][39].
- **CLI** (Click): `install`/`--force`, `shell` (IPython, `uncurl`/`curl2fetcher`), `extract get|post|put|delete|fetch|stealthy-fetch` -> .md/.txt/.html with `--css-selector`/`--impersonate`/`--solve-cloudflare`, `mcp` [40][41][42][43].
- **MCP** (`scrapling[ai]`): `scrapling mcp` or `ScraplingMCPServer`; stdio + streamable-http (`SCRAPLING_MCP_AUTH_TOKEN`); v0.4.15 = **13 tools** (make_request, fetch/stealthy_fetch + bulk, session open/fetch/close, screenshot->ImageContent) [44][45][15].
- **agent-skill/** ships SKILL.md + references; on Clawhub since v0.4.2 [46][47].

## 6. DEPENDENCIES + SIZE

BSD-3-Clause; Python >=3.10; Beta classifier [48]. Core: `lxml,cssselect,orjson,tld,w3lib,typing_extensions` - parser only [49][1]. `[fetchers]`: `click,curl_cffi,playwright,patchright,browserforge,apify-fingerprint-datapoints,msgspec,anyio,protego` (was hard-pinned playwright==1.61.0/patchright==1.61.2; later unpinned) [49][50]. `[ai]` mcp+markdownify; `[shell]` IPython; `[rag]`; `[all]` [48][51]. `scrapling install` downloads Playwright Chromium AND Patchright's own browser dir (~/.local-browsers) - ~300MB each, second download [52][24]. Docker: `pyd4vinci/scrapling`, `ghcr.io/d4vinci/scrapling` [1].

## 7. MATURITY

Created 2024-10-13; v0.2 Nov 2024, v0.3 Sep 2025 (rewrite+sessions+MCP+CLI), v0.4 Feb 2026 (spiders), v0.4.15 Aug 23 2026; ~fortnightly cadence [53-56][15]. ~76-83k stars / ~8k forks (trackers disagree); ~228k PyPI dl/week (~397k/mo); #45 Python on GitTrend [57-60]. **Bus factor = 1** (D4Vinci ~1,537 commits vs next 15; ~32 contributors; ~2d median issue close) [58][61]. "92% coverage" = badge claim, UNVERIFIED [62][63]. Known: enterprise CF fails [23]; headless Turnstile loop (fix on dev) [64]; Windows papercuts filed+fixed [65][50]; browserforge version-lag crashes #394/#396/#400 [50]; **breaking changes across 0.x** (v0.4 removed css_first, changed get()/body semantics) [66]; adaptive = extra DOM pass + SQLite write per element [33][34].

## 8. COMPARISON

| Alternative | Real edge | Marketing-only |
|---|---|---|
| requests+bs4 | TLS impersonation, matched headers, ~parsel speed, adaptive | "785x faster" = vendor bench; real = lxml parity [52][53] |
| curl_cffi alone | unified Response+Selector, header/fingerprint orchestration, sessions, CLI/MCP | value-add wrapper [7][10] |
| playwright+bs4 | patchright stealth, CF solver, tab pool, page hooks | stealth delegated to patchright [16][22] |
| parsel/Scrapy | same lxml + adaptive storage + integrated stealth | spider is Scrapy-inspired, no middleware/pipeline ecosystem [25][26] |
| nodriver | breadth (HTTP+browser+parser+spider+MCP) | nodriver raw-CDP > JS shims [20][69] |
| botasaurus | ProxyRotator, CLI, MCP, adaptive | botasaurus > on human-mouse [18][20] |

Real differentiators: **adaptive relocation** (unique, works [36]) + all-in-one packaging. "Undetectable"/"bypasses all Cloudflare" = marketing, disproven at enterprise tier [23][48].

## 9. INTEGRATION MODEL -> devin-bundle

- Tiered footprint fits stdlib-first: core parser = 6 deps; HTTP tier adds curl_cffi+fingerprint pkgs (pip only); browser tiers need `scrapling install` = ~300-600MB first-run binary download [49][52].
- Offline: parser+Fetcher need no browser download; browser fetchers require online first-run install (UNVERIFIED whether Fetcher needs zero post-install) [51][70].
- Agent integration is first-class: bundled MCP server (stdio/http+bearer) could register as bundle's scraping MCP; `agent-skill/` SKILL.md ready-made [44][47].
- `scrapling extract`/`shell` are ready CLI commands; `scrapling.cli.install` callable from Python for a managed first-run inside `extensions/scrape-tools/` [48].
- Risks for a pinned bundle: 0.x churn (breaking every few months) [66]; pin-vs-unpin dep friction [49][50]; bus factor 1 [58]. **Recommended scoping: adopt parser+Fetcher first; gate browser tiers behind opt-in extra/Docker
**Recommended scoping: adopt parser+Fetcher first; gate browser tiers behind opt-in extra/Docker** [1].

## PROPOSTA DE ENCAIXE (bundle)

`extensions/scrape-tools/` - thin wrappers, no vendor fork:

1. `scrape.py url --selector css --adaptive` - Fetcher+curl_cffi path, JSON out (Response fields + extracted nodes).
2. `parse.py file --css/--xpath` - offline parser-only path (stdlib-shaped contract, no network).
3. Optional `browser` tier (`scrapling install` behind `--install` consent flag; Docker fallback per repo docs).
4. Laya shadow optional later (selector suggestion profile) - NOT in v1 (assist still gated by E-evals).
5. Invariants kept: stdlib hooks untouched; new dep behind extension requirements.txt; no secret/session state in repo; offline parse path works with zero install.

## SOURCES (67)

1. scrapling.readthedocs.io/en/latest/index.html - official-docs - architecture, extras, parser-only base, Docker.
2. .../fetching/choosing.html - official-docs - 3 fetchers+sessions matrix, "not wrappers".
3. .../api-reference/fetchers.html - official-docs - class list, fetch/async_fetch.
4. .../fetching/stealthy.html - official-docs - Stealthy=Chromium+Playwright API, stealth args.
5. .../fetching/static.html - official-docs - curl_cffi engine, impersonate list, http3, SSRF-safe redirects.
6. .../fetching/dynamic.html - official-docs - DynamicFetcher; stealth moved 0.3.13.
7. pypi.org/project/scrapling/0.4.10 - PyPI - BSD-3, py>=3.10, author.
8. .../v0.3.10/fetching/choosing - official-docs - Response attrs.
9. d4vinci-scrapling.mintlify.app/concepts/fetchers - docs mirror - stealth header contents.
10. d4vinci-scrapling.mintlify.app/installation - docs mirror - browsers ~300MB.
11. .../v0.3.7 api-reference/fetchers - official-docs - Camoufox-era Stealthy.
12. .../v0.3.3 stealthy - official-docs - humanize/geoip/os_randomize args.
13. newreleases.io .../release/v0.3.13 - repo - Camoufox->Patchright, removed args.
14. github.com/pim97/anti-detect.../scrapling.md - repo - camoufox grep-verified gone; patchright imports.
15. github releases v0.4.15 - repo - MCP 13 tools, tab reuse.
16. stealthy.html current - official-docs - dns_over_https, real_chrome, cdp_url, block_webrtc.
17. github docs/fetching/static.md - repo - impersonate incl. tor; default latest Chrome.
18. korben.info/en/scrapling-python-self-healing-scraper.html - article - ProxyRotator vs Botasaurus; ~3,500 ad domains.
19. github README.md - repo - MCP prompt-injection stripping; extras.
20. pim97 comparison index - repo - matrix: fingerprint-rotation NO, human-mouse NO, CF auto-solve 5*.
21. aicoolies.com/reviews/scrapling-review - article - stale marketing example.
22. github discussions/341 - repo - patchright JS-layer limits; CF pain refs.
23. github discussions/266 - forum - enterprise CF 403 on all fetchers; basic CF ok.
24. github issues/265 - issue - Tencent WAF probabilistic; .local-browsers second download.
25. .../spiders/architecture.html - official-docs - scheduler/engine/session mgr, checkpoints.
26. .../spiders/advanced.html - official-docs - concurrency, AutoThrottle, robots.txt.
27. releases v0.4 - repo - spiders on anyio, breaking changes.
28. github scrapling/spiders/spider.py - repo - Spider ABC attrs (concurrent_requests=4, robots_txt_obey).
29. .../parsing/main_classes.html - official-docs - Selector/Selectors/TextHandler; #text wrapping.
30. .../api-reference/response.html - official-docs - captured_xhr, meta.
31. .../parsing/selection.html - official-docs - cssselect+lxml, HTML-only, find_by_text/regex, has_class.
32. .../parsing/adaptive.html - official-docs - save/match phases, SQLite default, domain+identifier keys.
33. .../api-reference/selector.html - official-docs - SQLiteStorageSystem; pickle rationale; percentage=40.
34. github scrapling/parser.py - repo - relocate()+similarity score impl.
35. .../development/adaptive_storage_system.html - official-docs - StorageSystemMixin, Redis example.
36. thunderbit.com/blog/scrapling-review - article - independent adaptive test; "tracking not recovery".
37. releases v0.3 - repo - session classes; CF solver; first MCP.
38. .../api-reference/proxy-rotation.html - official-docs - ProxyRotator signature.
39. .../spiders/proxy-blocking.html - official-docs - per-proxy contexts; meta["proxy"].
40. .../cli/overview.html - official-docs - shell/extract/install; [shell] extra.
41. .../cli/extract-commands.html - official-docs - extract verbs+outputs.
42. .../cli/interactive-shell.html - official-docs - uncurl/curl2fetcher.
43. .../ai/mcp-server.html - official-docs - scrapling mcp; Claude setup.
44. .../api-reference/mcp-server.html - official-docs - ScraplingMCPServer params, streamable-http, env vars.
45. agent-skill references/mcp-server.md - repo - 10-tool list, screenshot ImageContent.
46. agent-skill SKILL.md - repo - pip "scrapling[all]>=0.4.14"; extract opts.
47. releases v0.4.2 - repo - Agent Skill + Clawhub; py<3.12 crash fix.
48. github pyproject.toml - repo - core+fetchers deps; exact pins snapshot.
49. pypi.org/project/scrapling/0.4 - PyPI - per-extra dep table.
50. github CHANGELOG.md - repo - unpinning; Windows fixes #123/#344; browserforge #394/#396/#400.
51. deepwiki .../installation-and-setup - article - install mandatory only for browser fetchers.
52. .../benchmarks.html - official-docs - vendor bench: 1.99ms vs parsel 2.06, BS4 ~785x.
53. github benchmarks.py - repo - methodology.
54. issues/422 - issue - headless interactive Turnstile loop; dev fix.
55. issues/191 - issue - Quora CF managed challenge fails.
56. issues/47 - issue - early Turnstile limitation.
57. issues/57 - issue - Windows install path bug (playwright install chromium).
58. github.com/d4vinci/scrapling - repo - stars/forks range; created 2024-10-13; BSD-3; contributor list.
59. gittrend.io/repo/D4Vinci/Scrapling - article - 83.0k stars, +7.0k/30d, #45 Python.
60. repositoryradar.dev/repo/d4vinci/scrapling - article - ~228k dl/week, ~2d issue close, bus factor 1, 32 contributors.
61. webscraping.fyi compare botasaurus-vs-scrapling - article - ~397.4k dl/mo; "92% coverage" echo.
62. substack.thewebscraping.club scrapling-hands-on-guide - article - hands-on; headless Turnstile cleared.
63. publish.obsidian.md twsc-public scrapling - article - fetch/parse split; Camoufox line stale.
64. dev.to Lazada test May 2026 - article - timings Fetcher .77s/Dynamic 3.66/Stealthy ~4s.
65. newreleases.io v0.1.2 - repo - first tagged release Oct 2024.
66. xf-secops anti-detect matrix - repo - taxonomy: delegates to Patchright+curl_cffi.
67. docs.rs scrapling (Rust port) - official-docs - Rust port mirrors SQLiteStorageSystem - relevant to ADR-003.

**UNVERIFIED:** exact star/download counts (trackers disagree); "92% coverage" badge; zero-post-install claim for Fetcher; stealth durability on hardened targets (issues #191/#265/#266 mixed).
