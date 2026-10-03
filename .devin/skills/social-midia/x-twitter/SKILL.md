---
name: social-midia-x-twitter
description: Use when the user wants to draft, post, or analyze X (Twitter) content (posts, threads, polls, replies, long-form articles), or asks about the X API v2 (OAuth 2.0/OAuth 1.0a, scopes, rate limits, media upload, metrics).
triggers: [user, model]
---

# X / Twitter

API v2 is the current surface; canonical docs at https://docs.x.com/.

## Capabilities (official)

- `POST /2/tweets`: text, media refs, polls (4 options + duration),
  quote, reply, `community_id`, `paid_partnership`, `made_with_ai` flag,
  `reply_settings`, `edit_options`. https://docs.x.com/x-api/posts/create-post
- `media` is mutually exclusive with `quote_tweet_id`, `poll`, `card_uri`.
- Threads: sequential replies chaining `in_reply_to_tweet_id`.
- Long-form Articles: `POST /2/articles/draft` then
  `POST /2/articles/{id}/publish`.
- Delete: `DELETE /2/tweets/:id`.
- Media upload is v2 now: `POST /2/media/upload/initialize|append|finalize`;
  the old `upload.twitter.com/1.1` command-style flow is legacy.

## Auth & access

- OAuth2 Authorization Code + PKCE (user context, recommended), OAuth
  1.0a user context, or app-only Bearer (read-only public data).
- OAuth2 access tokens die in **2 hours**: `offline.access` scope gives a
  refresh token; required for anything unattended.
- `POST /2/tweets` needs `tweet.read`, `tweet.write`, `users.read`.
- Pricing moved to pay-per-use credits (Feb 2026); legacy Free/Basic/Pro
  tiers closed to new signups (UNVERIFIED in official docs).
- Env vars (convention): `X_BEARER_TOKEN`, `X_API_KEY`, `X_API_SECRET`,
  `X_CLIENT_ID`, `X_CLIENT_SECRET`, `X_ACCESS_TOKEN`,
  `X_ACCESS_TOKEN_SECRET`.

## Formats & limits

- 280 weighted chars; emoji/CJK count 2; every URL costs 23 (t.co).
- Long posts: read via `note_tweet` field (`text` truncates ~280);
  creating >280 via REST is UNVERIFIED (Articles are the official path).
- Media per post: 4 photos OR 1 GIF OR 1 video. Image <=5MB; GIF <=15MB.
- Video: 0.5s-20min, 8GB (Premium: 125min, 16GB); limits follow the
  posting user's Premium status.
- `media_category` must match intent (`tweet_image`, `tweet_video`, ...);
  wrong category uploads fine but fails at post-create.

## Scheduling & automation

- No native scheduling endpoint in v2 (Ads API has `scheduled_tweets`,
  separate product). Scheduling = external queue.
- `POST /2/tweets`: 100 req/15min per user; 10,000/24h per app. Undocumented
  100/24h per-user cap reported via response headers (UNVERIFIED).
- Automation rules: "Automated" label required, bot disclosure in bio,
  honor opt-outs, no identical content across accounts, no unsolicited
  mentions. https://docs.x.com/developer-guidelines
- Self-serve replies only when the author @mentioned or quoted you first:
  no cold-reply bots. https://docs.x.com/x-api/posts/manage-tweets/introduction

## Analytics

- `public_metrics` (any auth): retweet/reply/like/quote/impression/bookmark
  counts.
- `non_public_metrics` (own posts, user context): impression_count,
  url_link_clicks, user_profile_clicks, engagements.
- `organic_metrics`/`promoted_metrics`: user context.

## Professional routines

- Confirmed formats: threads, polls, community posts, Articles.
- No official cadence guidance; policy only bans spam/duplication.
- Draft threads as numbered blocks the user can post or queue; never
  promise API scheduling.

## Reference

- `api.md`: upload protocol, scopes list, error traps.
- Provenance: `.devin/research/social-midia/x-twitter.md`.
