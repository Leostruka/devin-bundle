# Threads - API reference

Doc home: https://developers.facebook.com/docs/threads ; reference:
https://developers.facebook.com/documentation/threads/reference/publishing

## API landscape
- GA 2024-06-18, self-serve: https://developers.facebook.com/blog/post/2024/06/18/the-threads-api-is-finally-here/
- Meta app with "Threads API" use case; use **Threads App ID** + Threads App Secret (distinct from Meta app creds): https://developers.facebook.com/docs/threads/get-started/
- Hosts `graph.threads.com` / `graph.threads.net`, version `v1.0`: https://developers.facebook.com/documentation/threads/overview
- Works without linked IG account except `followers_count`/`follower_demographics`: https://developers.facebook.com/documentation/threads/changelog

## Auth & access
- Scopes: `threads_basic` (all endpoints), `threads_content_publish`, `threads_read_replies` (GET), `threads_manage_replies` (POST), `threads_manage_insights`, `threads_keyword_search`, `threads_manage_mentions`, `threads_delete`, `threads_location_tagging`, `threads_profile_discovery`: https://developers.facebook.com/docs/threads/get-started/
- Flow: `https://threads.com/oauth/authorize` -> code -> `POST https://graph.threads.com/oauth/access_token` (1h): https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions/
- Long-lived: `GET /access_token?grant_type=th_exchange_token` -> 60d; `GET /refresh_access_token` (>=24h old, unexpired; 60d unrefreshed = dead). Server-side only: https://developers.facebook.com/docs/threads/get-started/long-lived-tokens/
- App Review only for users without a role on your app; "Threads Tester" for own-account tokens.
- Webhooks: reply, mention, publish, delete events; need published app + Advanced Access; private accounts emit no reply/mention events: https://developers.facebook.com/docs/threads/webhooks/

## Publishing
- `POST /{threads-user-id}/threads` (container) -> `POST /{threads-user-id}/threads_publish` (`creation_id`); carousel = children -> CAROUSEL container -> publish: https://developers.facebook.com/docs/threads/posts/
- `media_type`: TEXT, IMAGE, VIDEO, CAROUSEL; media = **public URL** (`image_url`/`video_url`), server-side fetch, no binary upload: https://developers.facebook.com/documentation/threads/posts
- Attachments: `link_attachment`, `poll_attachment`, `gif_attachment` (`gif_id`+`provider`), `text_attachment`, `alt_text`, `is_spoiler_media`, `text_entities`, `topic_tag`, `location_id`: publishing ref URL
- Replies: `reply_to_id`; `reply_control` = everyone | accounts_you_follow | mentioned_only | parent_post_author_only | followers_only; `enable_reply_approvals`; quotes `quote_post_id`.
- Moderation: `POST /{reply-id}/manage_reply` (hide), `/manage_pending_reply` (approve/ignore); `GET /{media-id}/replies` (top-level), `/conversation` (all depths): https://developers.facebook.com/documentation/threads/reply-management
- `POST /{threads-media-id}/repost`; `DELETE /{threads-media-id}` (`threads_delete`).

## Formats & limits
- Text <=500 chars; emoji counted as UTF-8 bytes.
- Images: JPEG/PNG, 8MB, AR <=10:1, width 320-1440 auto-scaled, sRGB.
- Video: MOV/MP4 (moov front, no edit lists), H.264/HEVC, AAC <=48kHz mono/stereo, 23-60fps, <=1920px, AR 0.01:1-10:1 (9:16 rec), VBR <=100Mbps, <=300s, <=1GB.
- Carousel: 2-20 children, mixed media.
- `alt_text` <=1,000 chars; image/video/carousel only: https://developers.facebook.com/docs/threads/posts/accessibility/

## Containers (async)
- Poll `GET /{container-id}?fields=status`: `EXPIRED`(24h)/`ERROR`/`FINISHED`/`IN_PROGRESS`/`PUBLISHED`; 1/min, <=5min; 24h expiry if unpublished: https://developers.facebook.com/docs/threads/troubleshooting/
- Error codes: `INVALID_ASPEC_RATIO` (sic), `FAILED_DOWNLOADING_VIDEO`, `INVALID_DURATION`.

## Scheduling & quotas
- No scheduling param; apps enforce own queues.
- Rolling 24h per profile: 250 posts (carousel = 1), 1,000 replies, 100 deletions, 500 location searches, 2,200 keyword queries (per user across apps; empty searches don't count): https://developers.facebook.com/docs/threads/overview/
- `GET /{threads-user-id}/threads_publishing_limit` -> usage + configs: https://developers.facebook.com/documentation/threads/troubleshooting
- Generic per app+user call-count + CPU-time limit.

## Analytics
- Media `GET /{threads-media-id}/insights`: views*, likes, replies (root->total, reply->direct), reposts, quotes, shares* (*in development): https://developers.facebook.com/docs/threads/insights/
- User `GET /{threads-user-id}/threads_insights`: views, likes, replies (top-level), reposts, quotes, clicks, followers_count, follower_demographics (country/city/age/gender; >=100 followers).
- `since`/`until` Unix; default yesterday-today; earliest 1712991600; follower metrics ignore range.
- Retrieved `media_type` differs from publish: `TEXT_POST`, `IMAGE`, `VIDEO`, `CAROUSEL_ALBUM`, `AUDIO`, `REPOST_FACADE`: https://developers.facebook.com/docs/threads/retrieve-and-discover-posts/retrieve-posts/

## Gotchas
- Media must be publicly fetchable; local files need hosting.
- Unapproved `threads_keyword_search` returns only own posts; unapproved `threads_location_tagging` returns only "Menlo Park".
- Emoji byte-counting breaks naive 500-char validators.
- No scheduling, no draft API, no edit-post endpoint; nested replies can't be hidden individually (top-level only).
- Fediverse toggle not exposed via API (UNVERIFIED).

Provenance: `.devin/research/social-midia/threads.md`
