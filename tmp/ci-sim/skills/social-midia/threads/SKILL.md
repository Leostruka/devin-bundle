---
name: social-midia-threads
description: Use when the user wants to draft, post, moderate, or analyze Threads content (text/image/video posts, carousels, replies, polls), or asks about the Meta Threads API (scopes, containers, quotas, insights).
triggers: [user, model]
---

# Threads

Meta Threads API, GA since Jun 2024. Hosts `graph.threads.com` /
`graph.threads.net`, versioned `v1.0`. Docs:
https://developers.facebook.com/docs/threads

## Capabilities (official)

- Two-step publish: `POST /{threads-user-id}/threads` (container) then
  `POST /{threads-user-id}/threads_publish` (`creation_id`). Carousel =
  child containers -> CAROUSEL container -> publish.
- `media_type`: TEXT, IMAGE, VIDEO, CAROUSEL. Media must be a **public
  URL**; no binary upload.
- Attachments: `link_attachment`, `poll_attachment`, `gif_attachment`,
  `text_attachment`, `alt_text`, `is_spoiler_media`, `text_entities`,
  `topic_tag`, `location_id`.
- Replies: `reply_to_id` + `reply_control` audience; quotes:
  `quote_post_id`; repost `POST /{id}/repost`; delete `DELETE /{id}`.
- Reply moderation: hide/approve via `manage_reply` /
  `manage_pending_reply`; `/replies` + `/conversation` readers.
- Keyword search, mentions feed, profile discovery, oEmbed embeds,
  webhooks (scope-gated).

Detail: `api.md`.

## Auth & access

- OAuth2 on the **Threads App ID** (distinct from Meta App ID).
- Scopes: `threads_basic`, `threads_content_publish`,
  `threads_read_replies`, `threads_manage_replies`,
  `threads_manage_insights`, `threads_keyword_search`,
  `threads_manage_mentions`, `threads_delete`, `threads_location_tagging`,
  `threads_profile_discovery`.
- Short-lived token 1h; long-lived 60d via `th_exchange_token`; refresh
  `GET /refresh_access_token` (server-side only, >=24h old).
- App Review only needed for users without a role on your app.
- Env vars (convention): `THREADS_APP_ID`, `THREADS_APP_SECRET`,
  `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`.

## Formats & limits

- Text <=500 chars; **emoji count as UTF-8 bytes** (4-byte emoji = 4
  chars): naive char checks break.
- Image: JPEG/PNG, 8MB, AR <=10:1, width 320-1440, sRGB.
- Video: MOV/MP4, H.264/HEVC, AAC <=48kHz, 23-60fps, <=1920px, <=300s,
  <=1GB, 9:16 rec.
- Carousel: 2-20 children, mixed.
- `alt_text` <=1,000 chars (not on text posts).

## Scheduling & automation

- No native scheduling param; app-side queues only.
- Quotas per rolling 24h per profile: **250 posts**, 1,000 replies,
  100 deletions, 500 location searches, 2,200 keyword queries (shared
  across all apps).
- Check usage: `GET /{id}/threads_publishing_limit`.
- Video containers async: poll `?fields=status` (1/min, <=5min);
  unpublished containers expire 24h.

## Analytics

- Media: `GET /{media-id}/insights` (views, likes, replies, reposts,
  quotes, shares).
- User: `GET /{user-id}/threads_insights` (profile views, likes,
  replies, reposts, quotes, clicks, followers_count,
  follower_demographics >=100 followers).
- Scope `threads_manage_insights`.

## Professional routines

- Confirmed: polls, GIFs, spoilers, topic/location tags, quote posts,
  reply approvals, mentions tracking.
- Fediverse sharing not exposed via API (UNVERIFIED).
- No official cadence guidance; 250/24h is the only documented bound.

## Reference

- `api.md`: container lifecycle, token flow, quota endpoints, errors.
- Provenance: `.devin/research/social-midia/threads.md`.
