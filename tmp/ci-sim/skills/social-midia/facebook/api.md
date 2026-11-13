# Facebook - API reference

Doc homes: https://developers.facebook.com/docs/pages-api/ ;
Graph API changelog: https://developers.facebook.com/docs/graph-api/changelog/versions/

## API landscape
- Graph API v26.0 latest (Jul 29 2026); ~2yr version cadence.
- Pages API for posting; Video API for video/reels; Insights API for metrics.
- Hosts: `graph.facebook.com`; video uploads `graph-video.facebook.com`.

## Auth & access
- Page access token required for Page actions; derive via User token -> `GET /{user-id}/accounts` or `/me/accounts`: https://developers.facebook.com/docs/facebook-login/access-tokens
- Short-lived ~1-2h; long-lived ~60d; **long-lived Page tokens never expire**: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/
- Permissions: `pages_manage_posts` (deps `pages_read_engagement`, `pages_show_list`), `pages_read_engagement`, `read_insights`, `pages_manage_engagement`, `pages_messaging`, `business_management`, `publish_video` (Live): https://developers.facebook.com/docs/permissions/
- Task model: `CREATE_CONTENT` to publish, `ANALYZE` for insights: https://developers.facebook.com/documentation/pages-api/overview
- Facebook Login for Business; App Review for non-default perms: https://developers.facebook.com/docs/pages-api/create-an-app/
- Business Manager/System User tokens: non-expiring.

## Publishing
- `POST /{page-id}/feed` `message` and/or `link` (one required): https://developers.facebook.com/docs/pages-api/posts/
- `POST /{page-id}/photos` `url` or file upload -> `id` + `post_id`: https://developers.facebook.com/docs/graph-api/reference/page/photos/
- Multi-photo: upload each `published=false`, then `/feed` with `attached_media[{i}].media_fbid`.
- `POST /{page-id}/videos`: resumable chunked: https://developers.facebook.com/docs/video-api/guides/publishing/
- `POST /{page-id}/video_reels`: `upload_phase` start -> transfer -> finish; `video_state` DRAFT/PUBLISHED/SCHEDULED: https://developers.facebook.com/docs/video-api/guides/reels-publishing/
- Stories: `POST /{page-id}/photo_stories`, `/video_stories`: https://developers.facebook.com/docs/page-stories-api/
- Live: `publish_video` + `pages_manage_posts`/`pages_read_engagement`: https://developers.facebook.com/docs/live-video-api/
- Personal profile: impossible (`publish_actions` deprecated Aug 1 2018): https://developers.facebook.com/docs/facebook-login/changelog/
- Groups: impossible (Groups API removed Apr 22 2024): https://developers.facebook.com/docs/graph-api/changelog/version19.0/

## Formats & limits
- Photo: jpeg/bmp/png/gif/tiff, <=10MB (png <=1MB rec), no animated.
- Reel: mp4, 9:16, 1080x1920 rec (min 540x960), 24-60fps, 3-90s (story <=60s), H.264/H.265, AAC-LC 48kHz/128kbps+.
- `message` char limit: UNVERIFIED (not in official docs).
- `/feed` returns published + unpublished posts; filter `is_published`.

## Scheduling & rate limits
- Schedule: `published=false` + `scheduled_publish_time` (UNIX, ISO 8601, or strtotime): https://developers.facebook.com/docs/pages-api/posts/
- Window conflict: posts guide 10min-30d; feed ref 10min-75d; videos edge 10min-6mo: https://developers.facebook.com/docs/graph-api/reference/page/feed/ ; https://developers.facebook.com/docs/graph-api/reference/page/videos/
- List: `GET /{page-id}/scheduled_posts` (Page token).
- Reels: 30 API reels / 24h moving window.
- Page-level BUC rate limits; errors 32/80001: https://developers.facebook.com/docs/graph-api/overview/rate-limiting/
- Policy: consent before publishing on someone's behalf; no prefilled text; no automation outside Platform APIs: https://developers.facebook.com/devpolicy/

## Analytics
- `GET /{page-id}/insights/{metric}` or `?metric=a,b`: `read_insights` + `pages_read_engagement` + `ANALYZE`: https://developers.facebook.com/docs/graph-api/reference/insights/
- Constraints: Page >=100 likes; last 2 years; max 90-day window; unpublished Pages 5 days: https://developers.facebook.com/docs/platforminsights/page/
- Deprecated Nov 15 2025: `page_fans*` -> `page_follows`; `page_impressions*`/`post_impressions*` -> `page_media_view`/`post_media_view`: https://developers.facebook.com/docs/platforminsights/page/deprecated-metrics/

## Gotchas
- Page token != User token; token is per app+user+page.
- `/feed` includes unpublished posts.
- Unpublished photos live ~24h; `temporary=true` for scheduled posts.
- Scheduling window inconsistent across docs: read back `scheduled_publish_time`.
- Insights metric names churn: check deprecated-metrics list.
- Dev mode: perms work only for app roles; production on others' Pages needs App Review + screencast.
- Photo `url` must be public; local files need multipart `source`.

Provenance: `.devin/research/social-midia/facebook.md`
