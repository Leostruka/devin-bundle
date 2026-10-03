---
name: social-midia-facebook
description: Use when the user wants to draft, post, schedule, or analyze Facebook Page content (feed posts, photos, videos, reels, stories), or asks about the Pages API / Graph API (page tokens, permissions, scheduled posts, insights).
triggers: [user, model]
---

# Facebook (Pages)

**Pages only.** Personal profile posting was removed Aug 2018
(`publish_actions` gone); Groups API removed Apr 2024. Any design needing
either is dead on arrival.

## Capabilities (official)

- `POST /{page-id}/feed`: text and/or link posts.
- `POST /{page-id}/photos`: single photo (url or upload); multi-photo via
  `published=false` uploads + `attached_media[]` on `/feed`.
- `POST /{page-id}/videos`: resumable chunked upload on
  `graph-video.facebook.com`.
- `POST /{page-id}/video_reels`: 3-phase upload (start -> transfer ->
  finish), `video_state` DRAFT/PUBLISHED/SCHEDULED.
- `POST /{page-id}/photo_stories`, `/video_stories`.
- Live Video API (`publish_video` scope) + crossposting to whitelisted
  Pages.
- **Native scheduling**: `published=false` + `scheduled_publish_time` on
  `/feed`; list via `GET /{page-id}/scheduled_posts`.

Detail: `api.md`.

## Auth & access

- **Page access token required** for Page actions; a User token won't
  post as the Page. Derive: User token -> `GET /me/accounts`.
- Long-lived Page tokens never expire (unless invalidated).
- Permissions: `pages_manage_posts` (+`pages_read_engagement`,
  `pages_show_list` deps), `read_insights` for analytics.
- Task model: `CREATE_CONTENT` to publish, `ANALYZE` for insights.
- Dev mode works for app roles only; production `pages_manage_posts` on
  others' Pages needs App Review + screencast.
- Env vars (convention): `FACEBOOK_PAGE_ACCESS_TOKEN`,
  `FACEBOOK_PAGE_ID`, `META_APP_ID`, `META_APP_SECRET`.

## Formats & limits

- Photos: jpeg/bmp/png/gif/tiff, <=10MB, no animation.
- Reel: mp4 9:16, 1080x1920 rec, 24-60fps, 3-90s, H.264/H.265.
- Post `message` char limit not documented officially (UNVERIFIED).
- Feed read: max `limit=100`; returns unpublished posts too
  (`is_published` filter).

## Scheduling & automation

- `scheduled_publish_time`: docs conflict on window (10min-30d vs
  10min-75d vs 10min-6mo); read back the field to verify.
- Reels: 30 API-published reels per rolling 24h.
- Page-level BUC rate limits; throttle errors 32/80001.
- Policy: consent before publishing for someone; no prefilled share
  text; no automation outside Platform APIs.

## Analytics

- `GET /{page-id}/insights/{metric}`; needs `read_insights` +
  `pages_read_engagement` + `ANALYZE` task.
- Page needs >=100 likes; 2-year data; 90-day windows.
- Metric churn (Nov 2025): `page_fans*` -> `page_follows`;
  `*_impressions*` -> `*_media_view`.

## Professional routines

- Confirmed formats: feed posts, photos, videos, reels, stories, live,
  crossposting.
- Meta Business Suite is the official UI for scheduling/inbox; Page
  Insights API metrics are being aligned to it.
- Page Events API is Marketing-Partner-only.

## Reference

- `api.md`: token derivation, upload phases, doc conflicts, errors.
- Provenance: `.devin/research/social-midia/facebook.md`.
