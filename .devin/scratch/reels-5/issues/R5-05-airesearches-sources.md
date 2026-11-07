# agent-reach/research: AI-news curation sources (airesearches)

status: ready-for-agent
priority: P3
source: reels batch-5 survey, airesearches/p/DfRqGa6DJgh

## Evidence

Carousel post ("Another huge week in AI and tech. Swipe through...", ~20 clips, caption summarizes Anthropic biotech acquisition, legal AI tools, etc.). Account @airesearches (~1.43M followers, verified) runs a broader operation:

- Newsletter/site: `airesearches.tech` (beehiiv, slug `ai_researches`); frequent AI-news posts.
- Archive: `github.com/airesearch-official/AI-Weekly-News`: every weekly "HUGE AI NEWS" episode with summaries + YouTube links.
- YouTube "AI Research" channel: weekly roundups matching the carousel format.
- X `@airesearch_ai`, Threads `@airesearches`. NOT affiliated with the unrelated "AI Search" (@theaisearch) entity.

beehiiv exposes `/feed` by default, `https://airesearches.tech/feed` likely works but unverified.

Bundle surface: `skills/agent-reach` (credential-free channels: YouTube transcripts/metadata, RSS/Atom) and `skills/research` source lists. Prior batch queued "PHP/Laravel sources listicle = agent-reach rss feed candidates" - same pattern.

## Task

1. Verify `https://airesearches.tech/feed` (or find the real RSS endpoint) returns valid RSS/Atom.
2. Add verified feed(s) + the GitHub weekly archive as curation sources in the appropriate surface: agent-reach SKILL.md source list and/or `.devin/research/social-midia/` notes; follow wherever prior RSS candidates were recorded (check `git log`/survey notes for the PHP/Laravel listicle precedent).
3. Record unverified items as "candidate (unverified)"; do not present guesses as fact.

## Acceptance

- [ ] Each listed source either verified-live (with check command/date) or marked candidate
- [ ] No fabricated URLs
- [ ] `python audit.py` green
