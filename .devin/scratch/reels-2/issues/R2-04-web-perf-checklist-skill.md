# web-perf-checklist: 30-item frontend performance fix-list

status: open
priority: P2
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 04 (breakingbreach): a single prompt/checklist covering skeleton loading, WebP/AVIF, debounced inputs, pagination, CDN, background queues, n+1 queries, brotli/gzip, redis caching, dep pruning, timeouts, token streaming, optimistic UI, lazy-load, parallel requests, db indexes, OTEL tracing, SSR/SSG, deferred scripts, code splitting, list virtualization, select-columns, connection pooling, re-render prevention, browser cache, load balancing, self-hosted fonts, RUM, slow-device testing. Transcript: `transcripts/04-breakingbreach.json`.

## Recommendation
New skill `skills/web-perf-checklist/SKILL.md`: the 30 items grouped by layer (render, network, server, data, infra), each with the symptom it fixes and the check command. Pairs with `benchmark-checklist` (that one vets the number; this one lists the fixes). Frontend/backend agnostic items marked.

## Verification
`ls skills/web-perf-checklist/SKILL.md`; manifest + count bump; audit clean.
