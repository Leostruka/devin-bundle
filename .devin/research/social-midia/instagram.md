# Instagram Platform APIs - Research Digest

## 1. API landscape
- One unified "Instagram Platform"; two flavors: **Instagram API with Instagram Login** (Business Login for Instagram, host `graph.instagram.com`, no Facebook Page needed) and **Instagram API with Facebook Login** (Facebook Login for Business, host `graph.facebook.com`, requires IG pro account linked to a FB Page). https://developers.facebook.com/docs/instagram-platform/overview
- Feature parity differs: Hashtag Search, Product Tagging, Partnership Ads = Facebook Login only; Messaging native on Instagram Login. Same table URL above.
- **Instagram Basic Display API deprecated Dec 4, 2024**: all requests error; "no longer a set of Instagram APIs for consumer developer apps" (personal accounts unsupported). https://developers.facebook.com/blog/post/2024/09/04/update-on-instagram-basic-display-api/ ; https://developers.facebook.com/docs/instagram-platform/changelog/
- Doc homes: https://developers.facebook.com/docs/instagram-platform/ (current); legacy path `/docs/instagram-api/` redirects/mirrors.
- Legacy `Instagram User/Media/Carousel/Comment` Graph objects deprecated v22 -> `IG User/IG Media/IG Comment`; migration deadline May 20, 2025 (Marketing API Sept 9, 2025). https://developers.facebook.com/blog/post/2025/01/21/making-it-easier-to-build-integrations-across-the-instagram-api-and-marketing-api/

## 2. Auth & access
- **Requirement: Instagram professional account (Business or Creator). Personal accounts cannot use these APIs at all.** https://developers.facebook.com/docs/instagram-platform/overview
- Instagram Login OAuth: `www.instagram.com/oauth/authorize` -> code -> `api.instagram.com/oauth/access_token` (short-lived) -> `graph.instagram.com/access_token` (long-lived) -> `graph.instagram.com/refresh_access_token`. https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login/
- Token lifetimes: short-lived = 1 hour; long-lived = 60 days; long-lived refreshable for another 60 days via `grant_type=ig_exchange_token`. https://developers.facebook.com/docs/instagram-platform/reference/access_token/
- Permissions, Instagram Login: `instagram_business_basic`, `instagram_business_content_publish` (publishing), `instagram_business_manage_insights`, `instagram_business_manage_comments`, `instagram_business_manage_messages`. https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing/
- Permissions, Facebook Login: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` (+`ads_management`/`ads_read` if Page role via Business Manager; +`catalog_management`,`instagram_shopping_tag_products` for product tags). https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- Scope values renamed Jan 27, 2025 (`business_*` -> `instagram_business_*`; old values deprecated). https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login/
- Access levels: Standard Access = accounts with role on your app, no review; **Advanced Access requires App Review + Business Verification** for serving third-party accounts. https://developers.facebook.com/docs/instagram-platform/app-review/ ; https://developers.facebook.com/docs/graph-api/overview/access-levels/
- Token storage via App Dashboard "Generate token" yields long-lived 60-day token directly. https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started/
- Env var names (convention only, **UNVERIFIED** in official docs): `META_APP_ID`, `META_APP_SECRET`, `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, `INSTAGRAM_ACCESS_TOKEN`, `IG_USER_ID`/`INSTAGRAM_BUSINESS_ACCOUNT_ID`, `INSTAGRAM_REDIRECT_URI`.

## 3. Publishing capabilities
- Two-step container model: `POST /{ig-user-id}/media` (create container + upload) then `POST /{ig-user-id}/media_publish?creation_id=`. https://developers.facebook.com/docs/instagram-platform/content-publishing ; https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- Media must be **publicly cURL-able URL** (`image_url`/`video_url`), Meta fetches server-side; no direct multipart except `upload_type=resumable` for large videos (Facebook Login only, `rupload.facebook.com`). https://developers.facebook.com/docs/instagram-platform/content-publishing
- Supported via API: single images, feed videos, Reels (`media_type=REELS`), **Stories** (`media_type=STORIES`, since Graph v16.0/May 2023), carousels (`media_type=CAROUSEL`, <=10 item containers, items created with `is_carousel_item=true`; reels NOT allowed as items). https://developers.facebook.com/blog/post/2023/05/16/introducing-stories-publishing-to-the-content-publishing-api-on-instagram/ ; https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/
- CANNOT: publish to personal accounts; apply filters/edits; shopping tags unsupported per guide (though `product_tags` param exists with catalog perms, docs conflict, verify per use case); non-JPEG images. https://developers.facebook.com/docs/instagram-platform/content-publishing
- Optional params: `caption`, `collaborators` (<=3, feed/reels/carousel only, not Stories), `user_tags`, `location_id`, `cover_url`/`thumb_offset`, `share_to_feed`, `audio_name`, `alt_text` (image posts only, added Mar 24, 2025, not reels/stories), `trial_params` (trial reels). https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/

## 4. Formats & limits
- Caption: **2,200 chars max, 30 hashtags, 20 @mentions**; not supported on carousel child items. https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/ ; https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/error-codes/
- Image: JPEG only (no MPO/JPS), <=8 MB, aspect ratio 4:5-1.91:1, width 320-1440 px (auto-scaled). Same `/ig-user/media/` URL.
- Reels: MOV/MP4, moov atom front, HEVC or H.264 progressive closed-GOP 4:2:0, AAC <=48kHz, 23-60 FPS, <=1920 cols, AR 0.01:1-10:1 (9:16 recommended), VBR <=25 Mbps video/128 kbps audio, **3 s-15 min, <=300 MB**. Cover: JPEG <=8 MB sRGB. Same URL.
- Story video: same container/codec spec; AR 0.1:1-10:1. Same URL.
- Carousel: max 10 images/videos mixed; counts as 1 published post. https://developers.facebook.com/docs/instagram-platform/content-publishing

## 5. Scheduling & automation
- Publishing quota: **docs conflict**: Content Publishing guide says **100 API-published posts per rolling 24h**; `media_publish` reference + `content_publishing_limit` reference (updated Jul 2024) say **50 (`quota_total:50`, `quota_duration:86400`)**. Check live quota: `GET /{ig-user-id}/content_publishing_limit` (`quota_usage`,`config`). https://developers.facebook.com/docs/instagram-platform/content-publishing ; https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit/
- **No documented native scheduling parameter** (`scheduled_publish_time` unsupported -> "(#3) User must be on whitelist" error); docs explicitly expect app-side scheduling ("if your app allows app users to schedule posts"). Same content-publishing URL.
- Enforcement point = `media_publish` call; apps must enforce quota themselves for scheduled queues. Same URL.
- Meta Platform Terms govern automation generally: https://developers.facebook.com/terms ; specific anti-automation clauses UNVERIFIED for IG organic posting (API itself is the sanctioned path).

## 6. Analytics
- Endpoints: `GET /{ig-media-id}/insights` (per-media), `GET /{ig-account-id}/insights` (account). Perms: `instagram_manage_insights`/`pages_read_engagement` (FB) or `instagram_business_manage_insights` (IG). https://developers.facebook.com/docs/instagram-api/guides/insights
- `impressions`, `plays`, `clips_replays_count`, `ig_reels_aggregated_all_plays_count` deprecated (v22.0; sunset Apr 21, 2025) -> new `views` metric with `total_value` + `follower_type`/`media_product_type` breakdowns. https://developers.facebook.com/docs/instagram-platform/api-reference/instagram-user/insights
- Constraints: `follower_count`/`online_followers` need >=100 followers; `online_followers` = last 30 days only; demographic metrics return top 45; data delayed <=48 h; user metrics retained 90 days; missing data returns empty set not `0`. Same URL.
- `total_comments`/`total_likes`/`total_views` (incl. boosted media) = Facebook Login only. Insights guide URL above.

## 7. Professional usage
- Docs cover: Reels (incl. trial reels via `trial_params`), carousels, Stories, collab posts (`collaborators`), user/product tagging, `location_id`. https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/
- Publishing blockers: Page Publishing Authorization (PPA) incomplete, or Page requires 2FA -> publish fails. https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- App user needs `MANAGE` or `CREATE_CONTENT` task rights on linked Page. Same URL.
- Messaging: native on Instagram Login; via Messenger Platform for Facebook Login. Overview URL section 1.

## 8. Gotchas
- Containers are **async**: poll `GET /{container-id}?fields=status_code` -> `IN_PROGRESS`/`FINISHED`/`PUBLISHED`/`ERROR`/`EXPIRED`; **recommended once/min, <=5 min**; containers **expire 24 h** unpublished. https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-container/
- `status` field carries error subcode when `status_code=ERROR`. Same URL.
- Published Stories return `media_type=IMAGE/VIDEO`: check `media_product_type` to detect stories. https://developers.facebook.com/docs/instagram-platform/content-publishing
- 50 vs 100 post quota, conflicting official docs; query `content_publishing_limit` for truth (section 5 URLs).
- No consumer API exists post-Dec 2024; any "personal account" design is dead on arrival. Section 1 URLs.
- `alt_text` silently ignored scope: image posts only. Section 3 URLs.
- Carousel children can't have captions (only parent). Section 4 URLs.
- Hashtag Search needs Facebook Login; Insights/messaging perms differ per login flavor; don't assume parity. Section 1, 6 URLs.
- Copyright check on video: `copyright_check_status` field on container. See ig-container URL.
- Env vars: no official names; skill must define its own (section 2 UNVERIFIED).
