# Journalistic OSINT & Competitive Intelligence Protocol

## Purpose

Investigate the problem space and competing products like an investigative tech journalist combined with a Staff Reverse-Engineering & Product Analyst. Never accept a competitor's landing page at face value. When a competitor is closed-source or private, reconstruct its architecture, bottlenecks, and blind spots from public and semi-public fragments.

## Rules of Engagement (Ethical OSINT & Primary-Source Discipline)

- Operate strictly on public, semi-public, or user-provided/authorized artifacts (Rule 13 & Safety rules: never harvest private credentials, cookies, or unauthorized endpoints).
- Apply **PRISMA-lite** and **lateral reading**: log every search query, cross-check vendor claims against independent sources, and verify both existence and entailment of every cited source.
- Never deduce what a competitor does when a tool (`web_search`, `webfetch`, `agent-reach`, `scrape-tools`, `binary-triage`) can observe it directly.

## The 7 Investigative Channels (Fragment Triangulation)

| Channel | What to Hunt ("Furos & Fragmentos") | Tools | Strategic Signal Extracted |
|---|---|---|---|
| **1. Issue Trackers, PRs & Changelogs** | Most-upvoted open issues, recurring regressions, "wontfix" architectural limits, breaking-change release notes and changelogs. | `gh`, `web_search`, `webfetch` | Structural ceilings the incumbent cannot fix without rewriting their core. |
| **2. Engineering Job Postings & Tech Blogs** | Required skills in Senior/Staff roles (e.g., "experience migrating from X to Y", "fixing memory leaks in Electron/Python"), conference talks, postmortems, and verbatim signals from job postings. | `web_search`, `scrape-tools` | Unannounced stack debt, scaling pain points, and internal roadmap direction of private companies. |
| **3. User Pain & Migration Forensics** | 1-3 star reviews (G2, Capterra, App Store, Play Store, Chrome Web Store), Reddit/HN/X threads ("switching from X", "X is slow/broken when..."). | `agent-reach`, `scrape-tools`, `web_search` | Exact verbatim pain vocabulary, broken workflows, pricing resentment, and unmet edge cases. |
| **4. Historical Diffs & Pricing/Docs Drift** | Wayback Machine snapshots of docs, pricing pages, terms of service, and deprecated API pages; removed features or silent enterprise paywalls. | `webfetch`, `web_search` | Features users lost, dark patterns introduced, and commoditized vs. gated capabilities. |
| **5. Public Artifacts, Packages & Schemas** | Published npm/PyPI/Cargo manifests, OpenAPI/GraphQL schemas, public bundle size (Bundlephobia), source maps, public telemetry/benchmarks. | `web_search`, `webfetch`, `exec` | Dependency bloat, real runtime footprint, API contract rigidity, and attack surface. |
| **6. Patents, Papers & Standards** | ArXiv papers cited by founders, patent filings, RFCs, and regulatory filings. | `web_search`, `webfetch` | Core algorithmic assumptions and theoretical limits of their approach. |
| **7. Authorized Local Binary/App Triage** | When a local binary/installer/package is legitimately present in the workspace: symbol tables, exported functions, embedded strings, engine versions. | `binary-triage` | Exact native dependencies, runtime engine, and architectural seams without guesswork. |

## Competitor Teardown Synthesis Table

Every `montador-de-ideias` dossier MUST include a filled table with at least 3 incumbents or adjacent workarounds:

| Incumbent / Workaround | Core Architecture (Observed via OSINT) | Verified Structural Flaw / Bottleneck (Cited Source) | User Pain Caused | How Our Design Eliminates This at the Root |
|---|---|---|---|---|
| `<Competitor A>` | `<Observed stack/model>` | `<Issue/Job post/Benchmark link + quote>` | `<Pain metric>` | `<First-principles counter-architecture>` |

## Coverage Self-Quiz (Gate Before Leaving Phase 1)

1. Did I name at least 3 real competitors or existing user workarounds?
2. Does every critical claim about a competitor cite a verifiable primary or OSINT source (not vendor marketing)?
3. Can I state in one sentence the single structural reason why incumbents fail to heal the user's acute pain?
