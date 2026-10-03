# YouTube - API reference

Doc hub: https://developers.google.com/youtube/documentation

## API landscape
- Data API v3: `https://www.googleapis.com/youtube/v3`: https://developers.google.com/youtube/v3/docs
- Live Streaming API: part of v3 (liveBroadcasts, liveStreams, liveChat*), same quota: https://developers.google.com/youtube/v3/live/docs
- Analytics API: `https://youtubeanalytics.googleapis.com/v2`; `reports.query` = `GET /reports`: https://developers.google.com/youtube/analytics
- Reporting API: scheduled bulk CSV reports, retained ~30-60d: https://developers.google.com/youtube/reporting

## Auth & access
- OAuth2 for all insert/update/delete and private reads; API key for public reads only: https://developers.google.com/youtube/registering_an_application
- Scopes (`https://www.googleapis.com/auth/` prefix): `youtube`, `youtube.readonly`, `youtube.upload`, `youtube.force-ssl`, `youtubepartner`, `youtube.channel-memberships.creator`: https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps
- Analytics scopes: `yt-analytics.readonly`, `yt-analytics-monetary.readonly`: https://developers.google.com/youtube/reporting/guides/authorization
- `videos.insert` accepts `youtube.upload`, `youtube`, `youtubepartner`, `youtube.force-ssl`: https://developers.google.com/youtube/v3/docs/videos/insert
- Service accounts NOT supported -> `NoLinkedYouTubeAccount`: https://developers.google.com/youtube/v3/guides/authentication
- Quota: 10,000 units/day shared + `search.list` own 100/day + `videos.insert` own 100/day; resets midnight PT; extensions via compliance audit: https://developers.google.com/youtube/v3/determine_quota_cost ; https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits

## Publishing
- `videos.insert` (`POST /upload/youtube/v3/videos`): <=256GB, `video/*` or octet-stream: https://developers.google.com/youtube/v3/docs/videos/insert
- Resumable: init POST `uploadType=resumable` -> `Location` session URI -> PUT chunks `Content-Range`; status via empty PUT; resume from `Range` in 308: https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
- Client libs wrap upload + backoff (`MediaFileUpload`): https://developers.google.com/youtube/v3/guides/uploading_a_video
- `thumbnails.set`: <=2MB JPEG/PNG: https://developers.google.com/youtube/v3/docs/thumbnails/set
- `videos.update`: overwrites ALL mutable props in each included `part`: https://developers.google.com/youtube/v3/docs/videos/update
- Playlists: `playlists.insert/update/delete`; `playlistItems.*` (position, note, startAt/endAt): https://developers.google.com/youtube/v3/docs/playlists
- Live: `liveBroadcasts.insert` -> `liveStreams.insert` -> `liveBroadcasts.bind`: https://developers.google.com/youtube/v3/live/life-of-a-broadcast
- Shorts: regular `videos.insert`; Analytics `creatorContentType=SHORTS`: https://developers.google.com/youtube/analytics/dimensions
- Community posts: no API.

## Formats & limits
- `snippet.title` <=100 chars (no `<` `>`): https://developers.google.com/youtube/v3/docs/videos
- `snippet.description` <=5000 BYTES; `snippet.tags[]` <=500 chars total.
- Thumbnail <=2MB; resized not cropped (black bars possible).
- Quota costs: `videos.insert` ~1 unit own bucket; `videos.update` 50; `thumbnails.set` ~50; playlist writes 50; `*.list` 1: https://developers.google.com/youtube/v3/determine_quota_cost

## Scheduling & automation
- `status.publishAt` (ISO 8601): requires `privacyStatus=private`, never-published video; past = immediate: https://developers.google.com/youtube/v3/docs/videos
- `privacyStatus`: `public`/`private`/`unlisted`.
- Unverified API projects (post-2020-07-28): all `videos.insert` locked private until compliance audit: https://developers.google.com/youtube/v3/revision_history
- Above-default quota: API Compliance Audit form; periodic re-audits.
- Processing: poll `videos.list` -> `processingDetails.processingStatus`.

## Analytics
- `reports.query` params: `ids`, `startDate`/`endDate`, `metrics`, `dimensions`, `filters`, `sort`; <=500 IDs per multi-value filter: https://developers.google.com/youtube/analytics/reference/reports/query
- `creatorContentType`: `SHORTS|LIVE_STREAM|STORY|VIDEO_ON_DEMAND|UNSPECIFIED` (from 2019-01-01).
- Not true realtime: data through last complete day.
- Reporting API flow: `reportTypes.list` -> `jobs.create` -> `jobs.reports.list` -> `downloadUrl`.
- 2025-03-31: Shorts views count on play start; affects `viewCount` fields.

## Gotchas
- Unverified project -> uploads forced private.
- Service accounts fail: use installed/web OAuth + refresh token.
- `videos.update` is destructive per-part; missing `status` resets privacy.
- `publishAt` only on never-published private videos; resend `privacyStatus=private` in same update.
- Description limit is bytes, not chars.
- `uploadLimitExceeded` = channel daily cap, not API quota.
- `thumbnails.set` can hit `uploadRateLimitExceeded` (24h channel cap).
- `search.list` own 100/day bucket: exhausts fast.
- Raw-HTTP resumable is multi-step; prefer official client libs.

Provenance: `.devin/research/social-midia/youtube.md`
