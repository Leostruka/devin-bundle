---
name: social-midia-reddit
description: Use when the user wants to draft, post, comment, or analyze Reddit content (subreddit posts, self-posts, links, crossposts, flair), or asks about the Reddit API (OAuth2 app types, /api/submit, rate limits, scopes, PRAW).
triggers: [user, model]
---

# Reddit

Data API (`oauth.reddit.com`, OAuth2) for organic posting; Devvit is a
separate hosted platform for in-subreddit apps; Ads API is separate.
Docs: https://www.reddit.com/dev/api + the Data API wiki.

## Capabilities (official)

- `POST /api/submit` (scope `submit`): kinds `link`, `self` (markdown
  text), `image`, `video`, `videogif`, `crosspost`; params `sr`, `title`,
  `text`, `url`, `flair_id`, `flair_text`, `nsfw`, `spoiler`,
  `sendreplies`, `resubmit`.
- `POST /api/comment`: `thing_id` (parent `t3_`/`t1_`), markdown `text`.
- Errors come back **inside HTTP 200** (`json.errors[]`): check the body.
- Media posts use undocumented `POST /api/media/asset.json` (S3 lease +
  websocket confirm); unstable, PRAW wraps it.
- Karma check: `GET /api/v1/me/karma` (`mysubreddits`).

Detail: `api.md`.

## Auth & access

- App types: **web** (server+secret), **installed** (no secret),
  **script** (single user, `grant_type=password`, only accounts listed
  as app developers).
- Grants: `authorization_code`, `refresh_token`, `password` (script
  only), `client_credentials` (app-only).
- Access tokens live 3600s. Token endpoint `www.reddit.com`; API calls
  `oauth.reddit.com`.
- User-Agent required and unique: `<platform>:<app ID>:<version> (by /u/<user>)`.
- Scopes: `submit`, `read`, `identity`, `mysubreddits`, `flair`, `edit`,
  `history`, `privatemessages`, mod scopes.
- Approval: Responsible Builder Policy request for API access;
  commercial use needs a written agreement.
- Env vars (convention): `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`,
  `REDDIT_USERNAME`, `REDDIT_PASSWORD`, `REDDIT_USER_AGENT`.

## Formats & limits

- Title <=300 chars. Self-text is markdown.
- Flair: `flair_id` (template) + optional `flair_text` only when the
  template is editable; `flair_text` alone is rejected.
- Per-sub gates (account age, karma, verified email, approved submitter)
  enforced by AutoMod; thresholds undisclosed; failures surface only at
  submit time.
- Crosspost requires being subscribed to the target sub.

## Scheduling & automation

- No API scheduling: native scheduled posts are mod-only UI. Devvit apps
  get a real scheduler (`context.scheduler.runJob`, cron/runAt).
- Rate limit: 100 QPM per OAuth client id (10 QPM unauthenticated,
  mostly blocked); averaged over 10min; headers
  `X-Ratelimit-Used/Remaining/Reset`.
- Bot etiquette: no unsolicited replies, no vote manipulation, respect
  per-sub bot rules, offer opt-out. Self-promo ~10% guideline is
  per-community.

## Analytics

- Post fields: `score`, `upvote_ratio`, `num_comments`, `created_utc`,
  `poll_data`, comment tree.
- No documented impressions/views endpoint; in-app "insights" are UI
  only. Ads metrics live in the separate Ads API.

## Professional routines

- Brands: Reddit Pro (free UI suite) + organic posting; community
  self-promo rules apply per sub.
- Profile posts go to the `u_<name>` profile subreddit.
- AMA format exists; treat subreddit rules and karma gates as the real
  distribution constraint, not the API.

## Reference

- `api.md`: app types, submit params, media flow, error-in-200 trap.
- Provenance: `.devin/research/social-midia/reddit.md`.
