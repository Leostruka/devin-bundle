# Meta Threads API - Official Docs Digest

## 1. API landscape
- GA since 2024-06-18 for all developers; self-serve docs, no waitlist. (https://developers.facebook.com/blog/post/2024/06/18/the-threads-api-is-finally-here/)
- Doc home: https://developers.facebook.com/docs/threads (mirror: /documentation/threads/). Reference: https://developers.facebook.com/documentation/threads/reference/publishing
- Accessed via a Meta app using the "Threads API" use case in App Dashboard; two app IDs exist; use **Threads App ID** + Threads App Secret. (https://developers.facebook.com/docs/threads/get-started/)
- Graph hosts: `graph.threads.com` **or** `graph.threads.net`, versioned `v1.0`. (https://developers.facebook.com/documentation/threads/overview)
- Instagram: API now works for Threads profiles **without** a linked IG account, except `followers_count`/`follower_demographics` metrics. (https://developers.facebook.com/documentation/threads/changelog)
- Capabilities: publish posts, fetch own media/profile, moderate replies, insights, keyword/tag search, mentions, location tagging, embeds, webhooks. (https://developers.facebook.com/docs/threads)

## 2. Auth & access
- OAuth 2.0, app-scoped user access tokens. Scopes: `threads_basic` (all endpoints), `threads_content_publish`, `threads_read_replies` (GET), `threads_manage_replies` (POST), `threads_manage_insights`. (https://developers.facebook.com/docs/threads/get-started/)
- Additional scopes: `threads_keyword_search`, `threads_manage_mentions`, `threads_delete`, `threads_location_tagging`, `threads_profile_discovery`. (https://developers.facebook.com/docs/threads/keyword-search/, /overview)
- Flow: Authorization Window `https://threads.com/oauth/authorize` -> code -> `POST https://graph.threads.com/oauth/access_token` (short-lived, 1h). (https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions/)
- Long-lived: `GET /access_token?grant_type=th_exchange_token` -> 60 days; refresh via `GET /refresh_access_token` (>=24h old, unexpired; unrefreshed 60d = dead). Server-side only; contains app secret. (https://developers.facebook.com/docs/threads/get-started/long-lived-tokens/)
- App Review: required only for users **without** a role on your app; testers/own account need none. Webhooks need published app + Advanced Access for all fields. (https://developers.facebook.com/docs/threads/get-started/, /docs/threads/webhooks/)
- "Threads Tester" generates tokens for own-account testing. (https://developers.facebook.com/documentation/threads/changelog)
- Env var names: **UNVERIFIED**: docs use placeholders `<THREADS_APP_ID>`, `<THREADS_APP_SECRET>`, `<ACCESS_TOKEN>`, `<THREADS_USER_ID>`; `THREADS_ACCESS_TOKEN` etc. is convention, not official.

## 3. Publishing capabilities
- Two-step: `POST /{threads-user-id}/threads` (container) -> `POST /{threads-user-id}/threads_publish` (`creation_id`). Carousel = 3 steps (child containers -> CAROUSEL container -> publish). (https://developers.facebook.com/docs/threads/posts/)
- `media_type`: `TEXT`, `IMAGE`, `VIDEO`, `CAROUSEL`; media must be a **public URL** (`image_url`/`video_url`), Threads fetches it server-side. No direct binary upload. (https://developers.facebook.com/documentation/threads/posts)
- Attachments on container: `link_attachment`, `poll_attachment`, `gif_attachment` (`gif_id`+`provider`), `text_attachment`, `alt_text`, `is_spoiler_media`, `text_entities` (text spoilers), `topic_tag`, `location_id`. (https://developers.facebook.com/documentation/threads/reference/publishing)
- Replies: `reply_to_id`; audience via `reply_control` (`everyone`, `accounts_you_follow`, `mentioned_only`, `parent_post_author_only`, `followers_only`); `enable_reply_approvals`. Quotes: `quote_post_id`. (same URL)
- Reply moderation: `POST /{reply-id}/manage_reply` (`hide`), `/manage_pending_reply` (approve/ignore); `GET /{media-id}/replies` (top-level), `/conversation` (flattened all depths). (https://developers.facebook.com/documentation/threads/reply-management)
- Repost: `POST /{threads-media-id}/repost`. Delete: `DELETE /{threads-media-id}` (`threads_delete` scope). (https://developers.facebook.com/documentation/threads/reference/publishing, /overview)

## 4. Formats & limits
- Text <=500 chars; **emoji count as UTF-8 bytes** (4-byte emoji = 4 chars). (https://developers.facebook.com/docs/threads/posts/)
- Images: JPEG/PNG only, 8 MB, aspect <=10:1, width 320-1440 (auto-scaled), sRGB. Video: MOV/MP4 (moov atom front, no edit lists), H.264/HEVC, AAC <=48kHz mono/stereo, 23-60 FPS, <=1920px wide, AR 0.01:1-10:1 (9:16 recommended), VBR <=100 Mbps, <=300s, <=1 GB. (same URL)
- Carousel: 2-20 children, mixed image/video; each child validated against single-post specs. (https://developers.facebook.com/documentation/threads/posts)
- Links: first URL in `text` becomes link preview; `link_attachment` attaches explicit URL. (same URL)
- `alt_text` <=1,000 chars; image/video/carousel only, not text posts. (https://developers.facebook.com/docs/threads/posts/accessibility/)

## 5. Scheduling & automation
- No scheduling parameter in publishing reference; docs only tell apps to enforce limits "especially if it allows app users to schedule posts", so scheduling is app-side. **UNVERIFIED**: any native scheduled-publish endpoint. (https://developers.facebook.com/docs/threads/overview/, /reference/publishing)
- Quotas (rolling 24h, per profile): **250 posts** (carousels count as 1), **1,000 replies**, **100 deletions**, **500 location searches**, **2,200 keyword-search queries** (per user across all apps; empty results don't count). (https://developers.facebook.com/docs/threads/overview/, /docs/threads/keyword-search/)
- Check usage: `GET /{threads-user-id}/threads_publishing_limit` -> `quota_usage`, `reply_quota_usage`, `delete_quota_usage`, `location_search_quota_usage` + configs. (https://developers.facebook.com/documentation/threads/troubleshooting)
- Generic call-count rate limit: per app+user pair, rolling 24h + CPU-time component. (https://developers.facebook.com/documentation/threads/overview)
- Webhooks: reply, mention, publish, delete events; private accounts don't emit reply/mention events. (https://developers.facebook.com/docs/threads/webhooks/)

## 6. Analytics
- Media-level: `GET /{threads-media-id}/insights`: `views`*, `likes`, `replies` (root->total; reply->direct only), `reposts`, `quotes`, `shares`* (*marked "in development"). Nested-reply metrics excluded. (https://developers.facebook.com/docs/threads/insights/)
- User-level: `GET /{threads-user-id}/threads_insights`: `views` (profile, time series), `likes`, `replies` (top-level only), `reposts`, `quotes`, `clicks` (link clicks), `followers_count`, `follower_demographics` (breakdown: `country`/`city`/`age`/`gender`; needs >=100 followers). (same URL)
- `since`/`until` Unix timestamps; default = yesterday-today; earliest `1712991600`; followers metrics ignore range. (same URL)
- Scope: `threads_manage_insights`. (https://developers.facebook.com/docs/threads/get-started/)

## 7. Professional usage
- Confirmed API features: polls, GIFs, text attachments, spoiler flags, topic tags, location tags, link attachments, alt text, reply approvals, quote posts, reposts, mentions feed (`threads_manage_mentions`), public profile discovery, oEmbed-style embeds. (https://developers.facebook.com/documentation/threads/reference/publishing, /changelog)
- Fediverse/ActivityPub sharing: **UNVERIFIED**: no mention found in API docs.
- Cadence guidance: none official; only the 250/24h quota. (https://developers.facebook.com/docs/threads/overview/)

## 8. Gotchas
- Video containers are async: poll `GET /{container-id}?fields=status` -> `EXPIRED`(24h)/`ERROR`/`FINISHED`/`IN_PROGRESS`/`PUBLISHED`; recommended 1 poll/min, <=5 min. Error codes include `INVALID_ASPEC_RATIO` (sic), `FAILED_DOWNLOADING_VIDEO`, `INVALID_DURATION`, etc. (https://developers.facebook.com/docs/threads/troubleshooting/)
- Containers expire 24h after creation if unpublished. (same URL)
- Media must be publicly fetchable URL; local files need hosting first. (https://developers.facebook.com/documentation/threads/posts)
- Retrieved `media_type` differs from publish `media_type`: returns `TEXT_POST`, `IMAGE`, `VIDEO`, `CAROUSEL_ALBUM`, `AUDIO`, `REPOST_FACADE`. (https://developers.facebook.com/docs/threads/retrieve-and-discover-posts/retrieve-posts/)
- Without approved `threads_keyword_search`, search returns only own posts; unapproved `threads_location_tagging` returns only "Menlo Park". (https://developers.facebook.com/docs/threads/keyword-search/, /create-posts/location-tagging)
- Emoji byte-counting breaks naive 500-char validators. (https://developers.facebook.com/docs/threads/posts/)
- UI-only / API gaps vs app: no scheduling param, no draft API, no edit-post endpoint found, nested replies can't be hidden individually (top-level only), fediverse toggle not exposed. **UNVERIFIED**: exhaustive feature-parity list.
