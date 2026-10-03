# X (Twitter) Official APIs - Research Digest

## 1. API landscape
- X API v2 is the primary, recommended API; v1.1 and enterprise legacy are slated for eventual deprecation. https://docs.x.com/x-api/getting-started/about-x-api
- v2 covers Posts, Users, DMs, Spaces, Lists, Communities, Community Notes, Media, Trends, Articles, streaming, webhooks. https://docs.x.com/x-api/overview
- Media upload is now a v2 surface (`/2/media/upload*`); the v1.1 command-style (`command=INIT/APPEND/FINALIZE` to one endpoint) is the "previous upload protocol"; docs say don't send command params to `POST /2/media/upload`. https://docs.x.com/x-api/media/quickstart/media-upload-chunked
- Enterprise-only: volume streams, likes streams, Powerstream, Account Activity, engagement metrics at scale. https://docs.x.com/x-api/overview
- Docs home: https://docs.x.com/ (canonical); legacy redirects live under developer.x.com.

## 2. Auth & access
- Three methods: OAuth 2.0 Authorization Code + PKCE (user context, recommended), OAuth 1.0a User Context, OAuth 2.0 App-Only Bearer (read-only public data). https://docs.x.com/fundamentals/authentication/overview
- OAuth 2.0 access tokens expire after 2 hours; `offline.access` scope issues a refresh token. https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code
- Scopes include `tweet.read`, `tweet.write`, `tweet.moderate.write`, `users.read`, `users.email`, `follows.*`, `like.*`, `list.*`, `block.*`, `mute.*`, `bookmark.*`, `dm.*`, `space.read`, `media.write`, `offline.access`. https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code
- `POST /2/tweets` requires user-context auth with `tweet.read`, `tweet.write`, `users.read`. https://docs.x.com/x-api/posts/create-post
- Credentials issued per app: API Key & Secret (OAuth 1.0a), Access Token & Secret (own account), Client ID & Secret (OAuth 2.0), Bearer Token (app-only). https://docs.x.com/x-api/getting-started/getting-access
- Pricing model changed Feb 2026: pay-per-use credits is the default; no subscriptions; pay-per-use capped at 3M Post reads per billing cycle; higher volume requires Enterprise. https://docs.x.com/x-api/getting-started/pricing
- Legacy tiers (Free/Basic/Pro) closed to new signups: UNVERIFIED in official docs (confirmed only by third-party reporting: https://api.sorsa.io/blog/twitter-api-pricing-2026).
- Doc examples use env names `$BEARER_TOKEN`, `$USER_ACCESS_TOKEN`. https://docs.x.com/x-api/posts/manage-tweets/quickstart
- Env var conventions (UNVERIFIED as official): `X_BEARER_TOKEN`, `X_API_KEY`, `X_API_SECRET`, `X_CLIENT_ID`, `X_CLIENT_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.

## 3. Publishing capabilities
- `POST /2/tweets`: body needs at least `text` or `media`; supports `reply.in_reply_to_tweet_id`, `quote_tweet_id`, `poll` (4 options, `duration_minutes`), `community_id`, `card_uri`, `direct_message_deep_link`, `paid_partnership`, `made_with_ai`, `edit_options`, `reply_settings`. https://docs.x.com/x-api/posts/create-post
- `media` is mutually exclusive with `quote_tweet_id`, `poll`, `card_uri`. https://docs.x.com/x-api/posts/create-post
- Threads = sequential replies chaining `in_reply_to_tweet_id` (docs: "create threads"). https://docs.x.com/x-api/posts/manage-tweets/introduction
- DELETE via `DELETE /2/tweets/:id`. https://docs.x.com/x-api/posts/manage-tweets/introduction
- v2 media flow: `POST /2/media/upload/initialize` -> `POST /2/media/upload/{id}/append` (<=5 MB chunks, server max 8 MB, index from 0) -> `POST /2/media/upload/{id}/finalize` -> `GET /2/media/upload?command=STATUS&media_id=` for `processing_info`. https://docs.x.com/x-api/media/quickstart/media-upload-chunked
- Simple upload `POST /2/media/upload` for images/small files only; chunked required for all video. https://docs.x.com/x-api/media/introduction
- Long-form Articles are official v2 endpoints: `POST /2/articles/draft`, `POST /2/articles/{article_id}/publish` (scope `tweet.write`). https://docs.x.com/x-api/articles/create-draft-article
- Restriction: "Self-serve customers: Replies are only permitted if the original post's author has explicitly summoned the replying account by @mentioning them or quoting one of their posts." https://docs.x.com/x-api/posts/manage-tweets/introduction
- Editing posts exists via `edit_options` on `POST /2/tweets`. https://docs.x.com/x-api/posts/create-post

## 4. Formats & limits
- 280 weighted chars; emoji/CJK count 2; every URL costs 23 chars via t.co; use twitter-text library. https://docs.x.com/fundamentals/counting-characters
- Reading >280-char posts: request `note_tweet` field; `text` truncates ~280. https://docs.x.com/x-api/fundamentals/data-dictionary
- Creating >280 posts via REST `POST /2/tweets`: UNVERIFIED (no documented request field; long-form creation officially surfaces as Articles).
- Media per post: up to 4 photos OR 1 GIF OR 1 video. https://docs.x.com/x-api/media/quickstart/best-practices
- Image <=5 MB (JPG/PNG/GIF/WEBP); GIF <=15 MB. https://docs.x.com/x-api/media/quickstart/best-practices
- Video (`tweet_video`/`amplify_video`): 0.5 s-20 min, 8 GB default; Premium/verified 125 min, 16 GB; `dm_video` 0.5-140 s, 512 MB (Premium: 10 min, 1 GB). Limits follow posting user's Premium status, not API plan. https://docs.x.com/x-api/media/introduction
- `media_category` values: `tweet_image`, `tweet_video`, `tweet_gif`, `amplify_video`, `dm_*`, `subtitles`; wrong category = upload succeeds, post-create fails. https://docs.x.com/x-api/media/quickstart/best-practices

## 5. Scheduling & automation
- No scheduled-posts endpoint in v2 public docs, verified by absence; only `/2/broadcasts/scheduled` (live broadcasts) exists. https://docs.x.com/x-api/overview : UNVERIFIED as a definitive "unsupported" claim; Ads API has `POST accounts/:id/scheduled_tweets` (ads-api.twitter.com, separate product). https://github.com/twitterdev/twitter-python-ads-sdk
- Official rate limits, `POST /2/tweets`: 100 req/15 min per user; 10,000/24 h per app. `DELETE /2/tweets/:id`: 50/15 min per user. https://docs.x.com/x-api/fundamentals/rate-limits
- Undocumented `x-user-limit-24hour-limit: 100` rolling cap reported via response headers, UNVERIFIED (third-party). https://nabbilkhan.com/nabster/posts/the-x-api-rate-limit-that-doesnt-exist-in-the-docs
- Automation rules: "Automated" profile label required, bot disclosure in bio, link to human-managed account, honor opt-outs, official API only; no identical content across accounts, no unsolicited mentions. https://docs.x.com/developer-guidelines
- Developer Policy: explicit consent before automated replies/DMs; no bulk/aggressive actions. https://docs.x.com/developer-terms/restricted-use-cases

## 6. Analytics
- `public_metrics` (any auth incl. Bearer): `retweet_count`, `reply_count`, `like_count`, `quote_count`, `impression_count`, `bookmark_count`. https://docs.x.com/x-api/fundamentals/metrics
- `non_public_metrics` (user context, own posts): `impression_count`, `url_link_clicks`, `user_profile_clicks`, `engagements`. https://docs.x.com/x-api/fundamentals/metrics
- `organic_metrics`, `promoted_metrics`: user context; media objects have playback metrics (`playback_*_count`, `view_count`). https://docs.x.com/x-api/fundamentals/data-dictionary
- Private metrics unavailable on full-archive search (app-only auth). https://docs.x.com/x-api/posts/search/integrate/overview

## 7. Professional usage
- Confirmed API formats: text, media posts, polls, quotes, replies, threads, community posts (`community_id`), Articles (draft/publish). https://docs.x.com/x-api/posts/create-post ; https://docs.x.com/x-api/articles/create-draft-article
- No official cadence guidance found in docs, UNVERIFIED; policy only prohibits spam/duplication. https://docs.x.com/developer-guidelines

## 8. Gotchas
- Reply gating: self-serve replies only when the author summoned you via @mention/quote; bots can't cold-reply. https://docs.x.com/x-api/posts/manage-tweets/introduction
- Media upload is v2 now; old `upload.twitter.com/1.1` + `command=` params are legacy; agents citing "v1.1 required for media" are outdated. https://docs.x.com/x-api/media/quickstart/media-upload-chunked
- Upload success does not mean attachable; `POST /2/tweets` re-checks duration/size -> 403 "not allowed to post a video longer than N minutes". https://docs.x.com/x-api/media/introduction
- App permission levels (OAuth 1.0a read/write/DM) are separate from OAuth 2.0 scopes; both must be configured. https://docs.x.com/fundamentals/developer-apps
- Bearer/app-only token cannot write or read private metrics. https://docs.x.com/x-api/fundamentals/metrics
- `text` alone hides long-post bodies; always request `note_tweet` on reads. https://docs.x.com/x-api/fundamentals/data-dictionary
- Docs' published POST limits omit the 100/24 h per-user cap; read `x-*-limit-*` headers, not just the table. https://docs.x.com/x-api/fundamentals/rate-limits (header detail UNVERIFIED)
- OAuth 2.0 tokens die in 2 h; missing `offline.access` breaks unattended agents. https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code
- Poll/media/quote are mutually exclusive; `media_ids` required inside `media`. https://docs.x.com/x-api/posts/create-post
