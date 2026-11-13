# TikTok Official Platform APIs - Research Digest

## 1. API landscape

- Product families: Login Kit (OAuth 2.0), Share Kit, Content Posting API, Display API, Research API, Data Portability API: https://developers.tiktok.com/doc/overview
- Content Posting API: two modes, **Direct Post** (publish to profile) and **Upload** (send draft to creator inbox): https://developers.tiktok.com/products/content-posting-api
- Display API: read-only profile/video metadata: `/v2/user/info/`, `/v2/video/list/`, `/v2/video/query/`: https://developers.tiktok.com/docs/en/display-api-overview
- Research API: approved academic/non-profit access to public data via client credentials: https://developers.tiktok.com/products/research-api
- Login Kit = TikTok's OAuth 2.0 implementation; all user-delegated APIs flow through it: https://developers.tiktok.com/doc/login-kit-overview

## 2. Auth & access

- Authorize URL: `https://www.tiktok.com/v2/auth/authorize/` (`client_key`, `scope`, `redirect_uri`, `state`, `response_type=code`): https://developers.tiktok.com/docs/en/login-kit-overview
- Token exchange: `POST https://open.tiktokapis.com/v2/oauth/token/`, `grant_type=authorization_code`; web uses `client_secret`, mobile/desktop use `code_verifier` (PKCE): https://developers.tiktok.com/docs/en/oauth-user-access-token-management
- `access_token` valid **24h**; `refresh_token` valid **365 days**; refresh rotates, returned `refresh_token` may differ, must persist new one: https://developers.tiktok.com/doc/oauth-user-access-token-management
- Client access token (Research API): `grant_type=client_credentials`, 2h validity, `clt.` prefix: https://developers.tiktok.com/doc/client-access-token-management
- Key scopes: `user.info.basic` (avatar/display_name only), `user.info.profile` (bio/username), `user.info.stats` (follower/likes counts), `video.list`, `video.upload` (drafts), `video.publish` (direct post): https://developers.tiktok.com/doc/tiktok-api-scopes
- **No `photo.upload` scope exists**: photos use same `video.upload`/`video.publish` scopes with `media_type=PHOTO`: https://developers.tiktok.com/docs/en/content-posting-api-get-started
- Dual gate: app must be *approved* for a scope AND each user must authorize it; users can grant a subset: https://developers.tiktok.com/docs/en/scopes-overview
- Unaudited clients: `SELF_ONLY` posts only, <=5 users/24h, target accounts must be private: https://developers.tiktok.com/doc/content-sharing-guidelines
- Env vars: TikTok docs use `client_key`/`client_secret` params, not env names. `TIKTOK_CLIENT_KEY`/`TIKTOK_CLIENT_SECRET`/`TIKTOK_ACCESS_TOKEN`/`TIKTOK_REFRESH_TOKEN` are conventions, UNVERIFIED (not in official docs).

## 3. Publishing capabilities

- Direct Post video: `POST /v2/post/publish/video/init/` (scope `video.publish`): https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Upload-to-drafts video: `POST /v2/post/publish/inbox/video/init/` (scope `video.upload`); user must tap inbox notification and finish post in-app: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- Photos (both modes): `POST /v2/post/publish/content/init/` with `post_mode` (`DIRECT_POST`|`MEDIA_UPLOAD`) + `media_type=PHOTO`: https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
- Required pre-flight: `POST /v2/post/publish/creator_info/query/` returns `privacy_level_options`, `max_video_post_duration_sec`, interaction flags; must drive the export UI: https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info
- Status polling: `POST /v2/post/publish/status/fetch/` with `publish_id`: https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status
- `FILE_UPLOAD`: init returns `upload_url` (1h TTL), then chunked `PUT` with `Content-Range`: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- `PULL_FROM_URL`: TikTok downloads media; URL must be HTTPS, non-redirecting, under a domain/URL-prefix verified in app URL properties: https://developers.tiktok.com/docs/en/content-posting-api-media-transfer-guide
- `privacy_level` enum: `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, `SELF_ONLY`; must match `privacy_level_options`: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post

## 4. Formats & limits

- Video: MP4 (rec.)/WebM/MOV; H.264 (rec.)/H.265/VP8/VP9; 23-60 FPS; 360-4096px per side; <=4GB: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- Duration: API accepts up to 10 min; effective max is per-creator `max_video_post_duration_sec` (e.g., 300s) from creator_info: https://developers.tiktok.com/doc/content-sharing-guidelines
- Chunking: chunks 5-64MB (final <=128MB), 1-1000 chunks, sequential; <5MB uploads whole: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- Photos: JPEG/WebP, <=1080p, <=20MB each, up to 35 images, `PULL_FROM_URL` only, `photo_cover_index` required: https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
- Captions: video `title` <=2200 UTF-16 runes; photo `title` <=90, `description` <=4000 UTF-16 runes: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Hashtags/mentions: `#`/`@` in title parsed when delimited by spaces/newlines: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post

## 5. Scheduling & automation

- **No native scheduling endpoint** in official docs; posts publish on invocation; scheduling must live client-side (UNVERIFIED as explicit statement; inferred from absence in https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)
- Rate limits: init endpoints 6 req/min per user token; `creator_info/query` 20 req/min; 429 `rate_limit_exceeded`: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- Posting cap: ~15 posts/day per creator via Direct Post, shared across **all** API clients; error `spam_risk_too_many_posts`: https://developers.tiktok.com/doc/content-sharing-guidelines
- Inbox/draft cap: max 5 pending shares per 24h; error `spam_risk_too_many_pending_share`: https://developers.tiktok.com/docs/en/content-posting-api-reference-upload-video
- Per-client daily active-creator cap set at audit time: https://developers.tiktok.com/doc/content-sharing-guidelines
- Sandbox mode: <=5 sandboxes, <=10 target users, no app review; URL verification still required for Content Posting API: https://developers.tiktok.com/docs/en/add-a-sandbox
- ToS: no superimposed branding/watermarks/promo text in shared content: https://developers.tiktok.com/doc/content-sharing-guidelines

## 6. Analytics

- `/v2/user/info/` (GET): `follower_count`, `following_count`, `likes_count`, `video_count` need `user.info.stats`; `bio_description`, `username`, `is_verified` need `user.info.profile`: https://developers.tiktok.com/doc/tiktok-api-v2-get-user-info
- `/v2/video/list/` (POST, `video.list`): paginated recent videos, <=20/page: https://developers.tiktok.com/doc/tiktok-api-v2-video-list
- `/v2/video/query/` filters by video IDs: https://developers.tiktok.com/docs/en/display-api-overview
- Video object metrics: `like_count`, `comment_count`, `share_count`, `view_count`, `duration`: https://developers.tiktok.com/doc/tiktok-api-v2-video-object
- Research API adds `hashtag_names`, `music_id`, `favorites_count` etc. under `research.data.basic`: https://developers.tiktok.com/doc/research-api-specs-query-videos

## 7. Professional usage

- Commercial flags: `brand_content_toggle` (paid partnership), `brand_organic_toggle` (own business) on direct posts: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- `auto_add_music`, `is_aigc` (discloses machine-made content), `video_cover_timestamp_ms`, `disable_comment/duet/stitch`: https://developers.tiktok.com/docs/en/content-posting-api-get-started
- No official cadence/posting-frequency guidance found: UNVERIFIED.

## 8. Gotchas

- Unaudited client -> `SELF_ONLY` only + target account must be private; error `unaudited_client_can_only_post_to_private_accounts`: https://developers.tiktok.com/doc/content-sharing-guidelines
- 15/day cap is per-creator across ALL apps, not per-app: same URL
- Draft flow never auto-publishes; creator must open inbox notification and finish in TikTok: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- `upload_url` expires 1h after init; PULL_FROM_URL download task times out at 1h: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- Photo posts: `PULL_FROM_URL` only, no `FILE_UPLOAD`: https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
- Caption length counted in UTF-16 runes (emoji/surrogates = 2); video descriptions returned by API capped at 150 chars: https://developers.tiktok.com/doc/tiktok-api-v2-video-object
- `privacy_level` must be among `privacy_level_options` else `privacy_level_option_mismatch`: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Must re-query `creator_info` before each post (duration/options change per account): https://developers.tiktok.com/doc/content-sharing-guidelines
- Refresh-token rotation: storing the old `refresh_token` breaks subsequent refreshes: https://developers.tiktok.com/doc/oauth-user-access-token-management
- v1 OAuth endpoints EOL Feb 29, 2024; don't mix v1/v2: https://developers.tiktok.com/bulletin/migration-guidance-oauth-v1
- `cover_image_url` CDN links expire after 6h: https://developers.tiktok.com/doc/tiktok-api-v2-video-object
