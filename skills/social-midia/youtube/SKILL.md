---
name: social-midia-youtube
description: Use when the user wants to upload, schedule, update, or analyze YouTube content (videos, Shorts, thumbnails, playlists, live), or asks about the YouTube Data API v3 / Analytics API (OAuth scopes, quota, resumable upload, publishAt, reports).
triggers: [user, model]
---

# YouTube

Data API v3 for read/write; Analytics API + Reporting API for metrics.
Docs: https://developers.google.com/youtube/documentation

## Capabilities (official)

- `videos.insert`: upload + metadata, resumable, <=256GB.
- `thumbnails.set`: <=2MB JPEG/PNG.
- `videos.update`: title/description/tags/category/privacy (destructive
  per `part` included).
- Playlists: `playlists.*` + `playlistItems.*` (position, notes,
  startAt/endAt).
- Live: `liveBroadcasts.insert` -> `liveStreams.insert` -> `bind`.
- Shorts: no dedicated API; regular uploads, identified in Analytics by
  `creatorContentType=SHORTS`.
- Community posts: no API exists.
- **Native scheduling**: `status.publishAt` (ISO 8601) with
  `privacyStatus=private`, never-published videos only.

Detail: `api.md`.

## Auth & access

- OAuth2 required for writes and private reads; API key only for public
  reads (`key=` param).
- Scopes: `youtube.upload` (upload/manage), `youtube.readonly`,
  `youtube.force-ssl`, `youtube` (full), `yt-analytics.readonly`,
  `yt-analytics-monetary.readonly`.
- **Service accounts do not work** (`NoLinkedYouTubeAccount`).
- **Unverified API projects (post-2020-07-28): all uploads locked
  private** until a compliance audit clears the app. Biggest trap.
- Env vars (convention): `YOUTUBE_API_KEY`, `GOOGLE_CLIENT_ID`,
  `GOOGLE_CLIENT_SECRET`, `YOUTUBE_OAUTH_TOKEN`.

## Formats & limits

- Title <=100 chars (no `<` `>`); description <=5000 **bytes** (multibyte
  burns it faster); tags <=500 chars total.
- Thumbnail <=2MB JPEG/PNG; non-matching dimensions resized with bars.
- Quota: 10,000 units/day shared + `search.list` own bucket (100/day) +
  `videos.insert` own bucket (100/day); write ops ~50 units each.

## Scheduling & automation

- `status.publishAt` requires `privacyStatus=private` and a
  never-published video; past time = immediate publish.
- `publishAt` must be resent with `privacyStatus=private` in updates.
- Upload processing: poll `videos.list` ->
  `processingDetails.processingStatus`.
- `uploadLimitExceeded` (400) = channel-level daily cap, not quota.

## Analytics

- Analytics API `reports.query`: metrics x dimensions; `creatorContentType`
  splits SHORTS/LIVE_STREAM/STORY/VOD; data complete through last day all
  metrics available (not true realtime).
- Reporting API: scheduled bulk CSV (jobs -> daily files, ~30-60d).

## Professional routines

- Confirmed: uploads, scheduled publish, playlists, thumbnails, live
  broadcast lifecycle, Shorts as normal uploads.
- Chapters: no API field; convention is timestamp lines in description
  (UNVERIFIED in docs).
- Premieres: no documented premiere flag; `publishAt` yields scheduled
  watch-page behavior (UNVERIFIED).

## Reference

- `api.md`: resumable protocol, quota table, gotchas.
- Provenance: `.devin/research/social-midia/youtube.md`.
