# TikTok - API reference

Doc home: https://developers.tiktok.com/doc/overview

## API landscape
- Families: Login Kit (OAuth2), Share Kit, Content Posting API, Display API, Research API, Data Portability API: https://developers.tiktok.com/doc/overview
- Content Posting API: **Direct Post** vs **Upload** (drafts inbox): https://developers.tiktok.com/products/content-posting-api
- Display API read-only: `/v2/user/info/`, `/v2/video/list/`, `/v2/video/query/`: https://developers.tiktok.com/docs/en/display-api-overview
- Research API: approved academic/non-profit, client credentials: https://developers.tiktok.com/products/research-api

## Auth & access
- Authorize: `https://www.tiktok.com/v2/auth/authorize/` (`client_key`, `scope`, `redirect_uri`, `state`, `response_type=code`): https://developers.tiktok.com/docs/en/login-kit-overview
- Token: `POST https://open.tiktokapis.com/v2/oauth/token/`; `grant_type=authorization_code`; web `client_secret`, mobile PKCE `code_verifier`: https://developers.tiktok.com/docs/en/oauth-user-access-token-management
- `access_token` 24h; `refresh_token` 365d, rotates on refresh; persist the new value: https://developers.tiktok.com/doc/oauth-user-access-token-management
- Client access token (Research): `client_credentials`, 2h, `clt.` prefix: https://developers.tiktok.com/doc/client-access-token-management
- Scopes: `user.info.basic`, `user.info.profile`, `user.info.stats`, `video.list`, `video.upload`, `video.publish`: https://developers.tiktok.com/doc/tiktok-api-scopes
- No `photo.upload` scope; photos use `video.upload`/`video.publish` + `media_type=PHOTO`: https://developers.tiktok.com/docs/en/content-posting-api-get-started
- Dual gate: app approved for scope AND user authorizes; users may grant subsets: https://developers.tiktok.com/docs/en/scopes-overview
- Unaudited: `SELF_ONLY` only, <=5 users/24h, private accounts: https://developers.tiktok.com/doc/content-sharing-guidelines
- Sandbox: <=5 sandboxes, <=10 target users, no review; URL verification still required: https://developers.tiktok.com/docs/en/add-a-sandbox
- v1 OAuth EOL Feb 29 2024; do not mix v1/v2: https://developers.tiktok.com/bulletin/migration-guidance-oauth-v1

## Publishing
- Direct video: `POST /v2/post/publish/video/init/` (`video.publish`): https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Draft video: `POST /v2/post/publish/inbox/video/init/` (`video.upload`); creator finishes in-app: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- Photos: `POST /v2/post/publish/content/init/` + `post_mode` (`DIRECT_POST`|`MEDIA_UPLOAD`) + `media_type=PHOTO`: https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
- Pre-flight `POST /v2/post/publish/creator_info/query/` -> `privacy_level_options`, `max_video_post_duration_sec`, interaction flags: https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info
- Status: `POST /v2/post/publish/status/fetch/` w/ `publish_id`: https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status
- `FILE_UPLOAD`: init -> `upload_url` (1h TTL) -> chunked `PUT` `Content-Range`; chunks 5-64MB (final <=128MB), 1-1000 chunks; <5MB whole: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- `PULL_FROM_URL`: HTTPS, non-redirecting, URL-prefix verified in app URL properties.
- `privacy_level`: `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, `SELF_ONLY`; must be in `privacy_level_options` else `privacy_level_option_mismatch`.

## Formats & limits
- Video: MP4/WebM/MOV; H.264/H.265/VP8/VP9; 23-60fps; 360-4096px; <=4GB; API <=10min but `max_video_post_duration_sec` governs.
- Photos: JPEG/WebP <=1080p <=20MB, up to 35, `PULL_FROM_URL` only, `photo_cover_index` required.
- Captions in UTF-16 runes: video `title` <=2200; photo `title` <=90, `description` <=4000.
- `#`/`@` parsed in title when space/newline delimited.

## Scheduling & limits
- No scheduling endpoint; Direct immediate, Upload to drafts.
- ~15 posts/day/creator via Direct, shared across all clients (`spam_risk_too_many_posts`); 5 pending shares/24h (`spam_risk_too_many_pending_share`): https://developers.tiktok.com/doc/content-sharing-guidelines
- Init endpoints 6 req/min/user; `creator_info` 20 req/min; 429 `rate_limit_exceeded`.
- Per-client daily active-creator cap set at audit.
- ToS: no superimposed branding/watermarks/promo text.

## Analytics
- `GET /v2/user/info/`: counts under `user.info.stats`; bio/username/verified under `user.info.profile`: https://developers.tiktok.com/doc/tiktok-api-v2-get-user-info
- `POST /v2/video/list/` <=20/page; `/v2/video/query/` by ID: https://developers.tiktok.com/doc/tiktok-api-v2-video-list
- Video metrics: `like_count`, `comment_count`, `share_count`, `view_count`, `duration`; `cover_image_url` expires 6h: https://developers.tiktok.com/doc/tiktok-api-v2-video-object
- Research API extras under `research.data.basic`: `hashtag_names`, `music_id`, `favorites_count`.

## Gotchas
- Unaudited -> `SELF_ONLY` + private target; error `unaudited_client_can_only_post_to_private_accounts`.
- 15/day cap is per-creator across ALL apps.
- Drafts never auto-publish.
- `upload_url` TTL 1h; PULL_FROM_URL download times out at 1h.
- Photos: `PULL_FROM_URL` only.
- Captions counted in UTF-16 runes (emoji = 2); API returns descriptions truncated at 150 chars.
- Re-query `creator_info` before each post.
- Old `refresh_token` stored = refresh breaks.

Provenance: `.devin/research/social-midia/tiktok.md`
