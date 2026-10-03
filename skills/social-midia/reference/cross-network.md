# Cross-network reference

Shared facts that apply to more than one network. Per-network detail lives
in `<net>/api.md`; provenance in `.devin/research/social-midia/`.

## Native scheduling matrix

| Network | API scheduling | Mechanism |
|---|---|---|
| Facebook (Pages) | Yes | `published=false` + `scheduled_publish_time` on `/{page}/feed`; docs conflict on window (10min-30d / 10min-75d / 10min-6mo) |
| YouTube | Yes | `status.publishAt` (ISO 8601) + `privacyStatus=private`, never-published videos only |
| LinkedIn | No | UI-only scheduler (10min-3mo); Posts API is PUBLISHED-only |
| X/Twitter | No | Ads API has scheduled_tweets (separate product) |
| Instagram | No | app-side queue against publish quota (50-100/24h) |
| TikTok | No | Direct Post publishes immediately; Upload goes to drafts inbox |
| Threads | No | app-side queue against 250 posts/24h quota |
| Reddit | No | mod-only UI feature; Devvit scheduler for Devvit apps |

Anything without native scheduling needs an external queue (cron + stored
draft + explicit publish call). Never promise "scheduled" on a network
marked No.

## Auth and access gates

| Network | What unlocks real publishing | Self-serve? |
|---|---|---|
| LinkedIn | `w_member_social` scope (person) | Yes (Share on LinkedIn product); org scopes need app approval |
| X/Twitter | OAuth2 user context, `tweet.write` | Yes, but pay-per-use pricing since Feb 2026 |
| Instagram | professional account + `instagram_business_content_publish` or `instagram_content_publish` | Standard Access: own accounts; Advanced needs App Review |
| Facebook | Page token + `pages_manage_posts` + `CREATE_CONTENT` task | Dev mode: own roles; production: App Review + screencast |
| TikTok | audited app + `video.publish` | Unaudited app: SELF_ONLY/private-account drafts only |
| YouTube | OAuth2 `youtube.upload` | Unverified project (post-2020-07-28): uploads locked private until compliance audit |
| Threads | `threads_content_publish` | App Review only for users without a role on your app |
| Reddit | OAuth2 app + `submit` scope + Responsible Builder approval | script apps: only accounts listed as app developers |

## Automation / ToS constraints

- LinkedIn API Terms 3.1 item 26 prohibits using the APIs to automate
  posting. https://www.linkedin.com/legal/l/api-terms-of-use
- X: automated accounts need the "Automated" label, bot disclosure in bio,
  opt-out honored; no identical content across accounts. https://docs.x.com/developer-guidelines
- Meta (FB/IG/Threads): get consent before publishing on someone's behalf;
  no prefilled share text; automation outside Platform APIs prohibited.
  https://developers.facebook.com/devpolicy/
- TikTok: no superimposed branding/watermarks/promo text in shared content;
  ~15 posts/day/creator shared across all API clients. https://developers.tiktok.com/doc/content-sharing-guidelines
- Reddit: bots must follow subreddit rules, offer opt-out, no unsolicited
  replies; ~10% self-promo guideline is per-community. https://support.reddithelp.com/hc/en-us/articles/28012014962580

## Media upload models

- **Public-URL fetch** (no binary upload): Instagram, Threads. Media must
  be publicly reachable; local files need hosting first.
- **Initialize -> upload -> reference URN**: LinkedIn (Images/Videos/
  Documents APIs).
- **Chunked upload**: TikTok (`FILE_UPLOAD`, 5-64MB chunks, upload_url TTL
  1h), X (`/2/media/upload/initialize|append|finalize`), Facebook video
  (`graph-video.facebook.com`), YouTube (resumable session URI + 308
  resume).
- **Undocumented/unstable**: Reddit `POST /api/media/asset.json` + S3
  lease + websocket confirm.

## Env var conventions (names only, not official)

No platform documents env var names; these are community conventions.
Never print values.

- LinkedIn: `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`
- X: `X_BEARER_TOKEN`, `X_API_KEY`, `X_API_SECRET`, `X_CLIENT_ID`, `X_CLIENT_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` (docs examples use `BEARER_TOKEN`, `USER_ACCESS_TOKEN`)
- Instagram/Meta: `META_APP_ID`, `META_APP_SECRET`, `INSTAGRAM_ACCESS_TOKEN`, `IG_USER_ID`, `INSTAGRAM_REDIRECT_URI`
- Facebook: `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `META_APP_ID`, `META_APP_SECRET`
- TikTok: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN`, `TIKTOK_REFRESH_TOKEN`
- YouTube: `YOUTUBE_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `YOUTUBE_OAUTH_TOKEN`
- Threads: `THREADS_APP_ID`, `THREADS_APP_SECRET`, `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`
- Reddit: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD`, `REDDIT_USER_AGENT`

## Drafts and two-step models worth remembering

- Async containers that expire: Instagram and Threads containers die 24h
  after creation if unpublished; poll status (1/min, <=5min).
- TikTok drafts never auto-publish: the creator must finish in-app from
  the inbox notification.
- Reddit returns errors inside HTTP 200 bodies (`json.errors`); check the
  body, not the status code.
- X OAuth2 tokens live 2h; `offline.access` (refresh token) is required
  for anything unattended.
