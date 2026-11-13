# X (Twitter) - API reference

Canonical docs: https://docs.x.com/ (developer.x.com redirects).

## API landscape
- X API v2 is primary; v1.1 and enterprise legacy slated for deprecation: https://docs.x.com/x-api/getting-started/about-x-api
- v2 covers Posts, Users, DMs, Spaces, Lists, Communities, Community Notes, Media, Trends, Articles, streaming, webhooks: https://docs.x.com/x-api/overview
- Media upload now v2 (`/2/media/upload*`); v1.1 command-style is the "previous upload protocol": https://docs.x.com/x-api/media/quickstart/media-upload-chunked
- Enterprise-only: volume streams, likes streams, Powerstream, Account Activity, engagement at scale: https://docs.x.com/x-api/overview

## Auth & access
- Three methods: OAuth2 + PKCE (recommended user context), OAuth 1.0a user context, OAuth2 app-only Bearer (read-only): https://docs.x.com/fundamentals/authentication/overview
- OAuth2 access token: 2h; `offline.access` issues refresh token: https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code
- Scopes: `tweet.read`, `tweet.write`, `tweet.moderate.write`, `users.read`, `users.email`, `follows.*`, `like.*`, `list.*`, `block.*`, `mute.*`, `bookmark.*`, `dm.*`, `space.read`, `media.write`, `offline.access`: same URL
- `POST /2/tweets` requires `tweet.read` + `tweet.write` + `users.read`: https://docs.x.com/x-api/posts/create-post
- Credentials per app: API Key & Secret (OAuth1.0a), Access Token & Secret, Client ID & Secret (OAuth2), Bearer Token: https://docs.x.com/x-api/getting-started/getting-access
- Pay-per-use credits default since Feb 2026; capped 3M Post reads/cycle; higher volume = Enterprise: https://docs.x.com/x-api/getting-started/pricing
- Doc examples use `$BEARER_TOKEN`, `$USER_ACCESS_TOKEN`: https://docs.x.com/x-api/posts/manage-tweets/quickstart

## Publishing
- `POST /2/tweets` params: `text`, `media`, `reply.in_reply_to_tweet_id`, `quote_tweet_id`, `poll` (4 options, `duration_minutes`), `community_id`, `card_uri`, `direct_message_deep_link`, `paid_partnership`, `made_with_ai`, `edit_options`, `reply_settings`: https://docs.x.com/x-api/posts/create-post
- `media` mutually exclusive with `quote_tweet_id`, `poll`, `card_uri`.
- Threads: sequential `in_reply_to_tweet_id` chains: https://docs.x.com/x-api/posts/manage-tweets/introduction
- `DELETE /2/tweets/:id`.
- Media v2 flow: `POST /2/media/upload/initialize` -> `POST /2/media/upload/{id}/append` (<=5MB chunks, index from 0) -> `POST /2/media/upload/{id}/finalize` -> `GET /2/media/upload?command=STATUS&media_id=`: https://docs.x.com/x-api/media/quickstart/media-upload-chunked
- Simple `POST /2/media/upload` for images/small files; chunked required for all video: https://docs.x.com/x-api/media/introduction
- Articles: `POST /2/articles/draft` -> `POST /2/articles/{article_id}/publish` (`tweet.write`): https://docs.x.com/x-api/articles/create-draft-article
- Reply gate: self-serve replies only when the original author summoned you (@mention or quote): https://docs.x.com/x-api/posts/manage-tweets/introduction

## Formats & limits
- 280 weighted chars; emoji/CJK = 2; URLs = 23 via t.co; twitter-text lib for counting: https://docs.x.com/fundamentals/counting-characters
- Reads: `note_tweet` field for >280 bodies; `text` truncates ~280: https://docs.x.com/x-api/fundamentals/data-dictionary
- Media per post: 4 photos OR 1 GIF OR 1 video; image <=5MB (JPG/PNG/GIF/WEBP); GIF <=15MB: https://docs.x.com/x-api/media/quickstart/best-practices
- Video `tweet_video`/`amplify_video`: 0.5s-20min/8GB; Premium 125min/16GB; `dm_video` 0.5-140s/512MB: https://docs.x.com/x-api/media/introduction
- `media_category` values: `tweet_image`, `tweet_video`, `tweet_gif`, `amplify_video`, `dm_*`, `subtitles`.

## Scheduling & rate limits
- No v2 scheduled-posts endpoint (verified by absence; only `/2/broadcasts/scheduled` for live): https://docs.x.com/x-api/overview
- Ads API `POST accounts/:id/scheduled_tweets` is a separate product.
- `POST /2/tweets`: 100 req/15min per user; 10,000/24h per app. `DELETE`: 50/15min per user: https://docs.x.com/x-api/fundamentals/rate-limits
- Undocumented `x-user-limit-24hour-limit: 100` header reported, UNVERIFIED.
- Automation rules: Automated label, bio disclosure, opt-outs, no cross-account duplicates: https://docs.x.com/developer-guidelines ; consent required for automated replies/DMs: https://docs.x.com/developer-terms/restricted-use-cases

## Analytics
- `public_metrics` (any auth): retweet_count, reply_count, like_count, quote_count, impression_count, bookmark_count: https://docs.x.com/x-api/fundamentals/metrics
- `non_public_metrics` (user context, own posts): impression_count, url_link_clicks, user_profile_clicks, engagements.
- `organic_metrics`, `promoted_metrics`: user context; media objects: `playback_*_count`, `view_count`: https://docs.x.com/x-api/fundamentals/data-dictionary
- Private metrics unavailable on full-archive search (app-only auth).

## Gotchas
- Cold replies blocked for self-serve apps (summon gate above).
- Upload success != attachable: post-create re-checks duration/size -> 403.
- OAuth 1.0a app permission levels are separate from OAuth2 scopes; configure both: https://docs.x.com/fundamentals/developer-apps
- Bearer token cannot write or read private metrics.
- `text` alone hides long-post bodies: always request `note_tweet`.
- Docs' rate table omits the 100/24h per-user cap: read `x-*-limit-*` headers.
- 2h token lifetime without `offline.access` breaks unattended agents.

Provenance: `.devin/research/social-midia/x-twitter.md`
