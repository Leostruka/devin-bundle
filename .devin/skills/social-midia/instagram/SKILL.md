---
name: social-midia-instagram
description: Use when the user wants to draft, post, or analyze Instagram content (feed posts, reels, stories, carousels), or asks about the Instagram Platform/Graph API (content publishing, Instagram Login vs Facebook Login, scopes, quotas, insights).
triggers: [user, model]
---

# Instagram

**Professional accounts only.** Business or Creator; personal accounts have
no API since Basic Display died Dec 4, 2024.

Two login flavors: **Instagram Login** (`graph.instagram.com`, no FB Page)
and **Facebook Login** (`graph.facebook.com`, needs linked FB Page).
Permissions, features, and metric availability differ; do not assume parity.

## Capabilities (official)

- Two-step publishing: `POST /{ig-user-id}/media` (container) then
  `POST /{ig-user-id}/media_publish?creation_id=`.
- Supported: single images, feed videos, Reels (`media_type=REELS`),
  Stories (`STORIES`), carousels (`CAROUSEL`, <=10 items, no reels inside).
- Media must be a **publicly reachable URL**; no direct binary upload
  except resumable for large video (Facebook Login only).
- Extras: `collaborators` (<=3), `user_tags`, `location_id`, `cover_url`,
  `share_to_feed`, `audio_name`, `alt_text` (image posts only),
  `trial_params` (trial reels).
- Cannot: personal accounts, filters/edits, carousel child captions.

Detail: `api.md`.

## Auth & access

- Instagram Login scopes: `instagram_business_basic`,
  `instagram_business_content_publish`, `instagram_business_manage_insights`,
  `instagram_business_manage_comments`, `instagram_business_manage_messages`.
- Facebook Login scopes: `instagram_basic`, `instagram_content_publish`,
  `pages_read_engagement` (+ others for ads/shopping).
- Tokens: short-lived 1h; long-lived 60d, refreshable once (`ig_exchange_token`).
- Standard Access = own-app roles, no review; Advanced Access (other
  users' accounts) = App Review + Business Verification.
- Env vars (convention): `META_APP_ID`, `META_APP_SECRET`,
  `INSTAGRAM_ACCESS_TOKEN`, `IG_USER_ID`, `INSTAGRAM_REDIRECT_URI`.

## Formats & limits

- Caption: 2,200 chars, 30 hashtags, 20 @mentions (parent post only).
- Image: JPEG only, <=8MB, AR 4:5-1.91:1, width 320-1440px.
- Reel: MOV/MP4, H.264/HEVC, 3s-15min, <=300MB, <=1920px, 9:16 rec.
- Carousel: 2-10 mixed images/videos, counts as one post.

## Scheduling & automation

- No native scheduling param (`scheduled_publish_time` rejected).
- Publish quota: docs conflict (100 vs 50 posts/24h); check live
  `GET /{ig-user-id}/content_publishing_limit` before trusting either.
- App-side queues must self-enforce quota; enforcement point is
  `media_publish`.

## Analytics

- `GET /{ig-media-id}/insights`, `GET /{ig-account-id}/insights`.
- `impressions`/`plays` deprecated -> `views` metric with breakdowns.
- `follower_count`/`online_followers` need >=100 followers; data delayed
  <=48h; missing data returns empty, not 0.

## Professional routines

- Confirmed formats: reels (incl. trial reels), carousels, stories,
  collab posts, product/user tags, locations.
- Publishing blockers to check first: incomplete Page Publishing
  Authorization, Page 2FA, missing `CREATE_CONTENT`/`MANAGE` task rights.
- No official cadence guidance.

## Reference

- `api.md`: container lifecycle, login flavors, quota conflict, errors.
- Provenance: `.devin/research/social-midia/instagram.md`.
