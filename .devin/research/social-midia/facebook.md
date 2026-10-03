# Facebook/Meta Platform APIs - Publishing Digest (official docs)

## 1. API Landscape
- Graph API, latest version **v26.0** (released Jul 29 2026); versions retire ~2-year cadence. https://developers.facebook.com/docs/graph-api/changelog/versions/
- Versioning guide: https://developers.facebook.com/docs/graph-api/guides/versioning/
- Pages API docs home: https://developers.facebook.com/docs/pages-api/ (mirror: /documentation/pages-api)
- Video API docs: https://developers.facebook.com/docs/video-api/ ; Insights: https://developers.facebook.com/docs/insights/get-started/
- Hosts: `graph.facebook.com`; video file uploads use `graph-video.facebook.com`. https://developers.facebook.com/docs/video-api/guides/publishing/

## 2. Auth & Access
- **Page access token** required for Page actions; get via User token -> `GET /{user-id}/accounts` or `/me/accounts`. https://developers.facebook.com/docs/facebook-login/access-tokens
- Short-lived tokens ~1-2h; long-lived ~60 days; **long-lived Page tokens never expire** (unless invalidated). https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/
- Long-lived Page token = exchange short User token -> long-lived User -> query `/{user-id}/accounts`. Same URL above.
- Key permissions: `pages_manage_posts` (deps: `pages_read_engagement`, `pages_show_list`), `pages_read_engagement`, `read_insights`, `pages_manage_engagement`, `pages_messaging`, `business_management`, `publish_video` (Live). https://developers.facebook.com/docs/permissions/ ; https://developers.facebook.com/documentation/pages-api
- Task-based model: publishing needs `CREATE_CONTENT` task; insights need `ANALYZE`. https://developers.facebook.com/documentation/pages-api/overview
- Auth flow = **Facebook Login for Business**; App Review submission required for non-default permissions/features. https://developers.facebook.com/docs/pages-api/create-an-app/
- Business Manager/System User tokens are non-expiring (time-based). https://developers.facebook.com/docs/facebook-login/access-tokens
- Env var names: **no official names exist**, convention only (UNVERIFIED as official): `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `META_APP_ID`, `META_APP_SECRET`.

## 3. Publishing Capabilities
- Text/link post: `POST /{page-id}/feed` with `message` and/or `link` (either required). https://developers.facebook.com/docs/pages-api/posts/
- Photo: `POST /{page-id}/photos` with `url` or file upload; returns `id` + `post_id`. https://developers.facebook.com/docs/graph-api/reference/page/photos/
- Multi-photo post: upload photos `published=false`, then `POST /{page-id}/feed` with `attached_media[{i}].media_fbid`. Same URL above.
- Video: `POST /{page-id}/videos` (resumable upload, chunked). https://developers.facebook.com/docs/video-api/guides/publishing/
- Reel: 3-phase upload to `POST /{page-id}/video_reels` (`upload_phase`=start -> transfer -> finish; `video_state` DRAFT/PUBLISHED/SCHEDULED). https://developers.facebook.com/docs/video-api/guides/reels-publishing/
- Stories: `POST /{page-id}/photo_stories`, `POST /{page-id}/video_stories`. https://developers.facebook.com/docs/page-stories-api/
- Live video: Live Video API; needs `publish_video` + `pages_manage_posts`/`pages_read_engagement`. https://developers.facebook.com/docs/live-video-api/
- **Personal profile posting: NOT possible**: `publish_actions` deprecated Aug 1, 2018; only Share dialogs for users. https://developers.facebook.com/docs/facebook-login/changelog/ ; `POST` on user/feed returns "You can't perform this operation on this endpoint". https://developers.facebook.com/docs/graph-api/reference/user/feed/
- **Groups: NOT possible**: Groups API deprecated v19, removed Apr 22 2024 (`publish_to_groups`, `groups_access_member_info` gone). https://developers.facebook.com/docs/graph-api/changelog/version19.0/

## 4. Formats & Limits
- Photo: jpeg/bmp/png/gif/tiff; <=10MB (png <=1MB recommended); no animated. https://developers.facebook.com/docs/graph-api/reference/page/photos/
- Reel: .mp4, 9:16, 1080x1920 rec (min 540x960), 24-60fps, **3-90s** (story <=60s), H.264/H.265, AAC-LC 48kHz/128kbps+. https://developers.facebook.com/docs/video-api/guides/reels-publishing/
- Video: aspect 16:9->9:16; many container formats. https://developers.facebook.com/docs/video-api/reference/
- Story media: same photo specs; video via upload session. https://developers.facebook.com/docs/page-stories-api/
- Post `message` char limit: **UNVERIFIED**: official docs do not state a limit (the ~63,206 figure is community-cited only).
- Feed read: max `limit=100`; ~600 ranked posts/year returned. https://developers.facebook.com/docs/graph-api/reference/page/feed/

## 5. Scheduling & Automation
- Schedule: `POST /{page-id}/feed` with `published=false` + `scheduled_publish_time` (UNIX ts, ISO 8601, or strtotime string). https://developers.facebook.com/docs/pages-api/posts/
- **Doc conflict:** posts guide says 10 min-30 days; feed reference says 10 min-75 days; videos edge says 10 min-6 months. https://developers.facebook.com/docs/graph-api/reference/page/feed/ ; https://developers.facebook.com/docs/graph-api/reference/page/videos/
- List scheduled: `GET /{page-id}/scheduled_posts` (Page token). https://developers.facebook.com/docs/graph-api/reference/page/scheduled_posts/
- Reels limit: **30 API-published reels / 24h moving window**. https://developers.facebook.com/docs/video-api/guides/reels-publishing/
- Rate limits: Page-level BUC rate limit for Page/system-user tokens; throttle error codes 32/80001. https://developers.facebook.com/docs/graph-api/overview/rate-limiting/
- Policy: obtain consent before publishing on a person's behalf; don't prefill share text; automated access outside Platform APIs prohibited. https://developers.facebook.com/devpolicy/ ; https://developers.facebook.com/docs/development/terms-and-policies/automated-data-collection/

## 6. Analytics
- `GET /{page-id}/insights/{metric}` or `?metric=a,b`; needs `read_insights` + `pages_read_engagement` + `ANALYZE` task. https://developers.facebook.com/docs/graph-api/reference/insights/
- Constraints: Page needs >=100 likes; last **2 years** of data; max **90-day** since/until window; unpublished Pages: 5 days. https://developers.facebook.com/docs/platforminsights/page/
- **Deprecated Nov 15 2025:** `page_fans*` -> `page_follows`; `page_impressions*`/`post_impressions*` -> `page_media_view`/`post_media_view`. https://developers.facebook.com/docs/platforminsights/page/deprecated-metrics/
- Useful metrics: `page_engaged_users`, `page_media_view`, `page_follows`, `post_media_view`. Same insights ref URL.

## 7. Professional Usage
- Professionals post: feed posts, photos, videos, **Reels** (dedicated API), **Stories** (dedicated API, launched Nov 2023 for desktop/web tools). https://developers.facebook.com/blog/post/2023/11/01/introducing-facebook-stories-apis/
- Live video + **crossposting** to multiple Pages via `/{page-id}/crosspost_whitelisted_pages`. https://developers.facebook.com/docs/live-video-api/guides/crossposting/
- Page Events API: **restricted to Facebook Marketing Partners**, not generally usable. https://developers.facebook.com/docs/graph-api/reference/event/
- Meta Business Suite = official UI (scheduling/inbox); Page Insights API metrics being aligned with MBS. https://developers.facebook.com/blog/post/2025/08/15/page-insights-api-updates/

## 8. Gotchas
- **Page token differs from User token**: `/{page-id}/feed` with a User token won't post as the Page; token is per app+user+page. https://developers.facebook.com/documentation/pages-api/overview
- Agents often assume personal-timeline/group posting; both **impossible** (section 3).
- `/feed` returns published **and** unpublished posts; filter via `is_published`. https://developers.facebook.com/docs/graph-api/reference/page/feed/
- Unpublished photos live ~24h; use `temporary=true` for scheduled posts; multi-photo needs `attached_media` on `/feed`. https://developers.facebook.com/docs/graph-api/reference/page/photos/
- Scheduling window inconsistent across docs (30d vs 75d vs 6mo); verify at runtime, read-back `scheduled_publish_time`. https://developers.facebook.com/docs/pages-api/posts/
- Insights metric names churn (impressions->media_view, fans->follows); check deprecated-metrics list.
- App in dev mode: permissions work only for app roles/admins; production use of `pages_manage_posts` on others' Pages requires **App Review** with screencast. https://developers.facebook.com/docs/permissions/
- Photo `url` must be publicly reachable; local files need multipart upload (`source`/`file attachment`). Same photos ref.
