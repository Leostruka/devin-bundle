# Instagram - API reference

Doc home: https://developers.facebook.com/docs/instagram-platform/

## API landscape
- One Instagram Platform, two flavors: **Instagram Login** (`graph.instagram.com`, no FB Page needed) and **Facebook Login** (`graph.facebook.com`, needs IG pro account linked to FB Page): https://developers.facebook.com/docs/instagram-platform/overview
- Parity differs: Hashtag Search, Product Tagging, Partnership Ads = Facebook Login only; Messaging native on Instagram Login.
- **Basic Display API deprecated Dec 4, 2024**: all requests error; personal accounts unsupported: https://developers.facebook.com/blog/post/2024/09/04/update-on-instagram-basic-display-api/
- Legacy `Instagram User/Media/Comment` objects deprecated v22 -> `IG User/IG Media/IG Comment`; migration deadline May 20, 2025: https://developers.facebook.com/blog/post/2025/01/21/making-it-easier-to-build-integrations-across-the-instagram-api-and-marketing-api/

## Auth & access
- Requirement: professional account (Business or Creator): https://developers.facebook.com/docs/instagram-platform/overview
- Instagram Login OAuth: `www.instagram.com/oauth/authorize` -> `api.instagram.com/oauth/access_token` (short) -> `graph.instagram.com/access_token` (long) -> `graph.instagram.com/refresh_access_token`: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login/
- Token lifetimes: short 1h; long 60d; refreshable another 60d via `grant_type=ig_exchange_token`: https://developers.facebook.com/docs/instagram-platform/reference/access_token/
- Scopes renamed Jan 27, 2025 (`business_*` -> `instagram_business_*`): https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login/
- Standard Access: accounts with role on your app, no review. Advanced Access: App Review + Business Verification: https://developers.facebook.com/docs/instagram-platform/app-review/ ; https://developers.facebook.com/docs/graph-api/overview/access-levels/
- FB Login perms: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` (+`ads_management`/`ads_read`, +`catalog_management`,`instagram_shopping_tag_products` for product tags): https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/

## Publishing
- `POST /{ig-user-id}/media` (container) -> `POST /{ig-user-id}/media_publish?creation_id=`: https://developers.facebook.com/docs/instagram-platform/content-publishing ; https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- Media = publicly cURL-able URL (`image_url`/`video_url`); resumable upload for large video is Facebook Login only (`rupload.facebook.com`).
- `media_type`: single image/feed video (omit), `REELS`, `STORIES` (since Graph v16.0), `CAROUSEL` (<=10 item containers with `is_carousel_item=true`; reels not allowed inside): https://developers.facebook.com/blog/post/2023/05/16/introducing-stories-publishing-to-the-content-publishing-api-on-instagram/ ; https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/
- Optional params: `caption`, `collaborators` (<=3; not Stories), `user_tags`, `location_id`, `cover_url`/`thumb_offset`, `share_to_feed`, `audio_name`, `alt_text` (image posts only), `trial_params`.
- Cannot: personal accounts, filters/edits, non-JPEG images; `product_tags` needs catalog perms and docs conflict.

## Formats & limits
- Caption: 2,200 chars, 30 hashtags, 20 @mentions; not on carousel children: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/error-codes/
- Image: JPEG only, <=8MB, AR 4:5-1.91:1, width 320-1440px auto-scaled.
- Reels: MOV/MP4, moov front, H.264/HEVC 4:2:0 closed-GOP, AAC <=48kHz, 23-60fps, <=1920px, AR 0.01:1-10:1 (9:16 rec), VBR <=25Mbps/128kbps, 3s-15min, <=300MB. Cover JPEG <=8MB sRGB.
- Story video: same spec, AR 0.1:1-10:1.
- Carousel: max 10 items, counts as 1 post.

## Containers (async)
- Poll `GET /{container-id}?fields=status_code`: `IN_PROGRESS`/`FINISHED`/`PUBLISHED`/`ERROR`/`EXPIRED`; 1 poll/min, <=5min; containers expire 24h unpublished: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-container/
- `status` field carries error subcode; `copyright_check_status` on video.

## Scheduling & quota
- No native `scheduled_publish_time` ("(#3) User must be on whitelist").
- Quota conflict: guide says 100/24h; `media_publish` + `content_publishing_limit` refs say 50 (`quota_total:50`, `quota_duration:86400`). Check `GET /{ig-user-id}/content_publishing_limit` live: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit/
- Enforcement at `media_publish`; apps must enforce quota for queues.

## Analytics
- `GET /{ig-media-id}/insights`, `GET /{ig-account-id}/insights`; perms `instagram_manage_insights`/`pages_read_engagement` (FB) or `instagram_business_manage_insights` (IG): https://developers.facebook.com/docs/instagram-api/guides/insights
- `impressions`, `plays`, `clips_replays_count`, `ig_reels_aggregated_all_plays_count` deprecated v22 -> `views` metric w/ `total_value` + `follower_type`/`media_product_type` breakdowns: https://developers.facebook.com/docs/instagram-platform/api-reference/instagram-user/insights
- `follower_count`/`online_followers` need >=100 followers; `online_followers` last 30d; demographics top 45; data <=48h delayed; user metrics retained 90d; missing data = empty set.
- `total_comments`/`total_likes`/`total_views` = Facebook Login only.

## Gotchas
- Published Stories report `media_type=IMAGE/VIDEO`; use `media_product_type`.
- Publishing blockers: Page Publishing Authorization incomplete; Page requires 2FA; user needs `MANAGE`/`CREATE_CONTENT` task rights on linked Page.
- `alt_text` image posts only.
- Carousel children can't have captions.
- Hashtag Search needs Facebook Login.
- No consumer API post-Dec 2024: personal-account designs are dead.

Provenance: `.devin/research/social-midia/instagram.md`
