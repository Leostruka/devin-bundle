---
name: social-midia-tiktok
description: Use when the user wants to draft, post, or analyze TikTok content (video posts, photo posts, drafts/inbox), or asks about the TikTok Content Posting API (direct post vs upload, scopes, creator_info, rate limits, status polling).
triggers: [user, model]
---

# TikTok

Two publishing modes via the Content Posting API:

- **Direct Post** (`video.publish`): straight to profile; requires an
  audited app.
- **Upload to drafts** (`video.upload`): lands in the creator's inbox;
  they finish posting in-app. The only path for unaudited apps.

## Capabilities (official)

- Video direct post: `POST /v2/post/publish/video/init/`.
- Video draft: `POST /v2/post/publish/inbox/video/init/`.
- Photos (both modes): `POST /v2/post/publish/content/init/` with
  `post_mode` + `media_type=PHOTO` (PULL_FROM_URL only).
- Pre-flight required: `POST /v2/post/publish/creator_info/query/` gives
  `privacy_level_options`, `max_video_post_duration_sec`, interaction
  flags. Re-query before every post.
- Status: `POST /v2/post/publish/status/fetch/` with `publish_id`.
- Commercial flags: `brand_content_toggle`, `brand_organic_toggle`,
  `is_aigc` disclosure, `disable_comment/duet/stitch`.

Detail: `api.md`.

## Auth & access

- OAuth2 via Login Kit; `access_token` 24h, `refresh_token` 365d
  (rotates; persist the new one).
- Scopes: `video.upload` (drafts), `video.publish` (direct),
  `user.info.basic/profile/stats`, `video.list`. No `photo.upload` scope
  exists; photos reuse the video scopes.
- Dual gate: app approved for the scope AND user authorizes it.
- **Unaudited client**: `SELF_ONLY` posts, <=5 users/24h, private
  accounts only.
- Env vars (convention, UNVERIFIED): `TIKTOK_CLIENT_KEY`,
  `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN`, `TIKTOK_REFRESH_TOKEN`.

## Formats & limits

- Video: MP4/WebM/MOV; H.264/H.265/VP8/VP9; 23-60fps; 360-4096px; <=4GB;
  <=10min API max but per-creator `max_video_post_duration_sec` governs.
- Photos: JPEG/WebP <=1080p, <=20MB, up to 35, `photo_cover_index` req.
- Captions: video `title` <=2200 UTF-16 runes; photo `title` <=90,
  `description` <=4000 runes. Emoji cost 2 runes.

## Scheduling & automation

- No scheduling endpoint; Direct Post is immediate, Upload goes to
  drafts. Scheduling = external queue or drafts.
- ~15 posts/day/creator via Direct Post, shared across ALL API clients
  (`spam_risk_too_many_posts`); 5 pending drafts/24h.
- Init endpoints 6 req/min/user; `creator_info` 20 req/min.
- ToS: no superimposed branding/watermarks/promo text.

## Analytics

- `GET /v2/user/info/`: follower/following/likes/video counts
  (`user.info.stats`), bio/verified (`user.info.profile`).
- `POST /v2/video/list/`: recent videos, <=20/page; `/v2/video/query/`
  by ID. Video object: like/comment/share/view counts, duration.

## Professional routines

- Draft-based flow fits human-in-the-loop publishing: agent uploads to
  inbox, creator finishes in-app.
- Music/cover/disclosure flags exist at post time (`auto_add_music`,
  `video_cover_timestamp_ms`, `is_aigc`).
- No official cadence guidance.

## Reference

- `api.md`: full endpoint list, chunking, polling, error names.
- Provenance: `.devin/research/social-midia/tiktok.md`.
