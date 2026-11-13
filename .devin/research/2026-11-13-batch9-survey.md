# Batch-9 link survey - 2026-11-13

3 links, fetched + validated against bundle. Verdicts: ADOPT/ADAPT/COVERED/BACKLOG/skip.

## L1 - caleb.is-a.dev/blog/amazing-github-repos
16 curated GitHub repos: awesome lists, TheAlgorithms, build-your-own-x,
free-for-dev, free-programming-books, roadmap.sh, OSSU CS, engineering-blogs,
system-design-primer, public-apis, open-source-alternatives, papers-we-love,
best-websites (ARCHIVED Nov 2025), LLMs-from-scratch, ML-from-scratch, devops-daily.

Signal for bundle: resource-index layer. Highest-value for agent work:
papers-we-love (topic-organized CS papers), system-design-primer,
public-apis, awesome (meta-index), LLMs-from-scratch/ML-from-scratch
(implementation pedagogy, pairs with ai-tools local training).
Verdict: ADAPT -> lean resource index doc + pointers in researcher/ai-tools.
Skip: best-websites (archived), devops-daily (low signal vs bundle depth).

## L2 - meshy.ai/features/image-to-3d
Hosted SaaS: Meshy 7.1 image->3D, browser-based, multi-view (up to 4 imgs),
res Standard/Ultra2K/Ultra4K, PBR maps, exports FBX/OBJ/GLB/USDZ/STL/BLEND/
3MF/DXF, API + MCP + CLI integrations, free tier (Ultra = paid).

Signal: ai3d-gen is local-first (comfyui/trellis/direct). Meshy = hosted
path w/ MCP server - could be optional adapter IF free API tier suffices;
paid Ultra conflicts w/ "no paid SaaS" default. Verdict: BACKLOG ->
evaluate Meshy API/MCP as opt-in hosted adapter behind existing
local-first pipeline; no default dependency.

## L3 - yisusvii.github.io astryx article (meta/astryx)
Meta open-sourced design system (GitHub trending): React 19+, 150+
components, StyleX-invisible, CSS-var theming, 7 themes, CLI contract:
`init` writes component index into AGENTS.md/CLAUDE.md; `manifest --json`;
`docs`/`component`/`search`; `swizzle` ejects source; `upgrade --apply`
codemods. Security: MIT, SECURITY.md->Meta Bug Bounty, latest-only
security updates, Beta, vega/charts canary-only, no postinstall hooks.

Signal: HIGH pattern-match - the "agent-readable component index +
self-documenting CLI" is exactly the bundle's own TOOLS-MAP/skills model.
Areas: (a) self-extend/devin-config could adopt `init`-writes-index UX;
(b) `manifest --json` machine-readable contract = same shape as
bundle-identity/manifest; (c) design-intelligence skill could reference
astryx theming model (CSS custom properties) for future web surfaces.
Verdict: ADAPT -> spike/eval astryx CLI contract as reference impl for
agent-facing tooling; pointer in relevant skill. NOT adopting the lib
(bundle is not a React app).

## Issues filed
- (see gh issue list; numbered below in agenda)

## L3 deep-dive (astryx CLI contract) - evidence

Fetched meta/astryx README + packages/cli/README (primary sources).
Agent-facing innovations vs bundle grep (apiVersion/answeredBy/--detail/
outsideProject: ZERO matches repo-wide):

| Astryx pattern | Bundle equivalent | Verdict |
|---|---|---|
| `manifest --json` full machine contract | manifest.json + bundle-identity.json | COVERED (static, not per-command) |
| Typed envelope `{apiVersion,type,data,meta.answeredBy}` | flat `{"ok":...}` envelopes | GAP: no version provenance - stale live copies indistinguishable (relates to #582 drift bug) |
| `--detail brief|compact|full`, `--dense`, `--lang` | none | GAP: no token-efficient output levels on high-traffic CLIs |
| `outsideProject: same|own|refuse` per command | implicit | GAP (minor): capability honesty not declared |
| `search` cross-domain ranked + follow-up cmd | graph-query.py, check-tools.py, TOOLS-MAP | PARTIAL: no unified ranked search w/ next-command hints |
| `init` writes component index -> AGENTS.md | TOOLS-MAP.md + auto-discovered skills | COVERED (different mechanism, same outcome) |
| `swizzle` eject component source | skill copy/export mechanism | COVERED conceptually |
| global vs project install precedence | install-ledger + live sync | COVERED |

Adopted now: comparison documented here + follow-up issue for envelope v2.
Not adopted: the React library itself (bundle is not a React app).

## L2 deep-dive (Meshy) - evidence

Fetched docs.meshy.ai/en/api/image-to-3d (primary source).
API real: POST /openapi/v1/image-to-3d, Bearer key, async task lifecycle
(create -> poll/stream -> result), accepts base64 data URI (no public URL
needed), target_formats incl glb/fbx/obj/usdz/stl/blend, models
meshy-7.1/meshy-t2/t2.5, texture models meshy-7/n1/6-lite, credit-based
pricing w/ refunds, deprecations tracked (meshy-7 retires 2026-12-31).
MCP integration exists per feature page.

Verdict: BACKLOG. ai3d-gen stays local-first/open-weights. Hosted path
only if user explicitly opts in (image upload to third party = privacy
decision; Ultra tiers paid). No default dependency. Revisit if local
pipeline can't cover a case or user requests hosted gen.
