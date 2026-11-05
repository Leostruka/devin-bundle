---
name: web-perf-checklist
description: Use when a web app feels slow, when a PR touches frontend/backend performance, or when asked for the concrete fix-list behind a performance complaint.
disable-model-invocation: true
---

# Web performance checklist

The fix-list behind "make my app fast". Grouped by layer; each item names the symptom it fixes and the fastest check. Vet any number you produce with `benchmark-checklist` before claiming it.

Pick the layer that matches the complaint first; do not blast all 30 at once.

## Render (user sees delay/jank)

- **Skeleton loading screens** for content that streams in - symptom: layout shift, perceived slowness. Check: does the page paint a stable frame before data lands?
- **Token-by-token streaming** for AI responses - symptom: long silent spinner. Check: is the UI painted as chunks arrive?
- **Optimistic UI** - update before the server responds on reversible actions. Symptom: clicks feel dead.
- **Prevent unnecessary re-renders** - symptom: input lag under React/Vue. Check: profiler shows renders outside the edited subtree.
- **Virtualize long lists** - symptom: scrolling thousands of rows stutters. Check: DOM node count vs visible rows.
- **Lazy-load below-fold images** - symptom: heavy first paint. Check: `loading="lazy"` or equivalent on non-hero media.
- **Self-host fonts, limit weights** - symptom: FOUT/blocked first paint. Check: third-party font requests in the network tab.
- **Defer third-party scripts** - symptom: TTI delayed by tag managers/widgets. Check: `async`/`defer` on non-critical tags.
- **Code-split by route** - symptom: multi-MB initial bundle. Check: does every page need what it downloads?
- **RUM monitoring** - symptom: "fast for me" claims. Check: real-user p75 instrumentation exists (not lab-only).
- **Test on slow devices/networks** - symptom: regressions invisible on dev machines. Check: throttled profile run before ship.

## Network (bytes and round trips)

- **Serve images as WebP/AVIF** - symptom: oversized media payload. Check: response content-type on image requests.
- **Debounce search/autocomplete** - symptom: request-per-keystroke. Check: requests fired per typed character.
- **Prevent duplicate API calls** - symptom: identical requests in flight (mounts, retried effects). Check: dedup window in the network tab.
- **Paginate API results** - symptom: 10k-row responses. Check: unbounded `?limit=` or missing cursor.
- **CDN for static files** - symptom: assets served from origin across regions. Check: static host and cache headers.
- **Brotli/gzip compression** - symptom: uncompressed text bodies. Check: `content-encoding` on HTML/JS/JSON.
- **Browser caching for static files** - symptom: every visit re-downloads. Check: `cache-control` max-age on hashed assets.
- **Parallel independent requests** - symptom: waterfall of serial fetches. Check: requests that could fire together.
- **Timeouts on external calls** - symptom: one slow dependency stalls all. Check: every outbound call has a deadline.

## Server (time before first byte)

- **Background job queue for slow tasks** - symptom: requests do email/report/resize work inline. Check: work that outlives the request moved out of band.
- **SSR or build-time rendering** - symptom: blank page until JS hydrates. Check: meaningful HTML in the first response.
- **Load balancing across instances** - symptom: one saturated node. Check: single-instance deploy.
- **Keep servers near the database** - symptom: RTT-per-query amplification. Check: app and DB region/AZ.
- **OTEL tracing on slow backend requests** - symptom: "somewhere slow" with no map. Check: spans exist for hot paths.

## Data (queries and caching)

- **Fix n+1 queries** - symptom: query count scales with row count. Check: query log on a list endpoint.
- **Indexes on common queries** - symptom: seq scans on filtered columns. Check: `EXPLAIN` on the slowest query.
- **Cache hot data (redis/local)** - symptom: identical expensive recomputation per request. Check: cache hit metrics for top queries.
- **Select only needed columns** - symptom: `SELECT *` hauling blobs. Check: column list vs fields used.
- **Connection pooling** - symptom: connect latency per request, DB connection churn. Check: pool config and connection count over time.

## Hygiene

- **Remove unused dependencies** - symptom: bundle/install bloat. Check: dep-graph vs imports.

## Report

- Name the layer and the evidence for each confirmed fix; do not hand back the raw 30-item list as "the answer".
- Rank fixes by (user-visible impact) x (effort); lead with the top 3.
- Numbers go through `benchmark-checklist` first - a fix without a before/after is a hypothesis.
