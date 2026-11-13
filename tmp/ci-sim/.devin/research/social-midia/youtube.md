# YouTube Official APIs - Research Digest

## 1. API landscape
- **YouTube Data API v3**: read/write YouTube resources (videos, playlists, channels, comments, captions). Base `https://www.googleapis.com/youtube/v3`. Home: https://developers.google.com/youtube/v3 ; API ref: https://developers.google.com/youtube/v3/docs
- **YouTube Live Streaming API**: technically part of Data API v3 (liveBroadcasts, liveStreams, liveChat*), consumes same quota. https://developers.google.com/youtube/v3/live/docs
- **YouTube Analytics API**: targeted, on-demand queries; base `https://youtubeanalytics.googleapis.com/v2`; `reports.query` = `GET /reports`. https://developers.google.com/youtube/analytics ; https://developers.google.com/youtube/analytics/reference
- **YouTube Reporting API**: scheduled bulk `.csv` reports (jobs -> daily files per 24h period; retained ~30-60 days). https://developers.google.com/youtube/reporting ; https://developers.google.com/youtube/reporting/v1/reports
- Doc hub: https://developers.google.com/youtube/documentation

## 2. Auth & access
- OAuth 2.0 required for all insert/update/delete and any private-data read; API key suffices for public-data reads only. https://developers.google.com/youtube/registering_an_application ; https://developers.google.com/youtube/v3/docs
- Every request must carry `key=` (API key) or OAuth token. https://developers.google.com/youtube/v3/docs
- Data API scopes (full `https://www.googleapis.com/auth/` prefix): `youtube` (manage account), `youtube.readonly`, `youtube.upload` (upload/manage videos only), `youtube.force-ssl`, `youtubepartner`, `youtube.channel-memberships.creator`, `youtubepartner-channel-audit`. https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps
- Analytics/Reporting scopes: `yt-analytics.readonly` (non-monetary), `yt-analytics-monetary.readonly` (revenue/ad metrics). https://developers.google.com/youtube/reporting/guides/authorization
- `videos.insert` accepts `youtube.upload`, `youtube`, `youtubepartner`, or `youtube.force-ssl`. https://developers.google.com/youtube/v3/docs/videos/insert
- **Service accounts are NOT supported** -> `NoLinkedYouTubeAccount` error. https://developers.google.com/youtube/v3/guides/authentication
- Quota: default 100 `search.list` + 100 `videos.insert` calls/day (own buckets) + 10,000 units/day shared for all other methods; resets midnight PT; extensions via compliance audit. https://developers.google.com/youtube/v3/determine_quota_cost ; https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- Env var names (common convention, no official Google standard, UNVERIFIED): `YOUTUBE_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `YOUTUBE_OAUTH_TOKEN` / refresh-token store.

## 3. Publishing capabilities
- `videos.insert` (`POST /upload/youtube/v3/videos`): upload + metadata in one call; supports resumable upload. Max file 256GB; MIME `video/*` or `application/octet-stream`. https://developers.google.com/youtube/v3/docs/videos/insert
- Resumable protocol: POST session-init to `uploadType=resumable` endpoint -> `Location` header session URI -> PUT chunks with `Content-Range`; query status via empty PUT, resume from `Range` in `308` response. https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
- Client libraries wrap resumable upload + exponential backoff (`MediaFileUpload`, `chunksize=-1` = single request). https://developers.google.com/youtube/v3/guides/uploading_a_video
- `thumbnails.set` (`POST /upload/youtube/v3/thumbnails/set`): max 2MB, `image/jpeg`/`image/png`. https://developers.google.com/youtube/v3/docs/thumbnails/set
- `videos.update` edits title/description/tags/category/privacy, overwrites ALL mutable properties in each `part` included. https://developers.google.com/youtube/v3/docs/videos/update
- Playlists: `playlists.insert/update/delete`; items via `playlistItems.insert/update/delete` (position, note, startAt/endAt). https://developers.google.com/youtube/v3/docs/playlists ; https://developers.google.com/youtube/v3/docs/playlistItems
- Live: `liveBroadcasts.insert` -> `liveStreams.insert` -> `liveBroadcasts.bind`; auto-start/stop, DVR, closed captions settable. https://developers.google.com/youtube/v3/live/life-of-a-broadcast
- **Shorts: no Shorts-specific upload API**: Shorts are regular `videos.insert` uploads; Analytics identifies them via `creatorContentType=SHORTS` dimension. https://developers.google.com/youtube/analytics/dimensions ; https://developers.google.com/youtube/v3/docs/videos/insert
- **Community posts: no API exists**: not among Data API v3 resources. https://developers.google.com/youtube/v3/docs

## 4. Formats & limits
- `snippet.title`: max 100 chars; all UTF-8 except `<` `>`. https://developers.google.com/youtube/v3/docs/videos
- `snippet.description`: max 5000 **bytes** (not chars); same char restriction. https://developers.google.com/youtube/v3/docs/videos
- `snippet.tags[]`: max 500 chars total; commas between items count; tags with spaces count +2 (implicit quotes). https://developers.google.com/youtube/v3/docs/videos
- Thumbnail upload: 2MB, JPEG/PNG; non-matching dimensions resized (not cropped, may get black bars). https://developers.google.com/youtube/v3/docs/thumbnails/set ; https://developers.google.com/youtube/v3/docs/thumbnails
- Video file: max 256GB; `video/*` MIME. https://developers.google.com/youtube/v3/docs/videos/insert
- Quota costs: `videos.insert` 1 unit in own bucket (default 100/day); `videos.update` 50; `thumbnails.set` ~50; `playlists.*`/`playlistItems.*` writes 50; `*.list` 1. https://developers.google.com/youtube/v3/determine_quota_cost ; https://developers.google.com/youtube/v3/docs/playlistItems/insert
- Historical note: upload cost was ~1600 units -> now ~1/call in granular bucket. https://developers.google.com/youtube/v3/revision_history

## 5. Scheduling & automation
- `status.publishAt` (ISO 8601) schedules publish; **requires** `status.privacyStatus=private` and video must never have been published; past timestamp = publishes immediately. https://developers.google.com/youtube/v3/docs/videos ; https://developers.google.com/youtube/v3/docs/videos/update
- `privacyStatus` values: `public`, `private`, `unlisted`. https://developers.google.com/youtube/v3/docs/videos
- **Unverified API projects created after 2020-07-28: all `videos.insert` uploads locked private**; creators emailed; lifted only by compliance audit. https://developers.google.com/youtube/v3/revision_history ; https://developers.google.com/youtube/v3/docs/videos/insert
- Above-default quota requires API Compliance Audit (Audit and Quota Extension Form); periodic re-audits occur. https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- Processing status after upload: poll `videos.list` -> `processingDetails.processingStatus`. https://developers.google.com/youtube/v3/guides/implementation/videos

## 6. Analytics
- `reports.query`: params `ids` (channel/content owner), `startDate`/`endDate`, `metrics`, `dimensions`, `filters`, `sort`; multi-value filters via comma lists (<=500 IDs for video/playlist/channel). https://developers.google.com/youtube/analytics/reference/reports/query
- Data model: metrics (views, likes, watch time, revenue) x dimensions (video, country, date, `creatorContentType`...); groups up to 500 items. https://developers.google.com/youtube/analytics/data_model
- Shorts/live split: `creatorContentType` = `SHORTS|LIVE_STREAM|STORY|VIDEO_ON_DEMAND|UNSPECIFIED` (data from 2019-01-01). https://developers.google.com/youtube/analytics/dimensions
- Response includes data only through last day all requested metrics are available -> not true real-time despite "real-time queries" wording. https://developers.google.com/youtube/analytics/reference/reports/query ; https://developers.google.com/youtube/analytics
- Reporting API flow: `reportTypes.list` -> `jobs.create` -> `jobs.reports.list` -> download `downloadUrl`; daily CSV per 24h. https://developers.google.com/youtube/reporting/v1/reference/rest
- 2025-03-31: Shorts view counting aligned (count on play start); affects `videos.statistics.viewCount`, `channels.statistics.viewCount`. https://developers.google.com/youtube/v3/revision_history

## 7. Professional usage
- Playlists, chapters, premieres, cadence: only playlist CRUD + `publishAt` scheduling are API-confirmed. **Premiere creation via API is UNVERIFIED** (docs mention no premiere flag; `publishAt` yields scheduled-watch-page behavior per docs). https://developers.google.com/youtube/v3/docs/videos
- Video chapters: no dedicated API field; convention is timestamp lines in description, UNVERIFIED in API docs.
- `snippet.categoryId` must come from `videoCategories.list`. https://developers.google.com/youtube/v3/guides/implementation/videos
- No official posting-cadence guidance in developer docs: UNVERIFIED / none found.

## 8. Gotchas
- Unverified OAuth/API project -> uploads forced private (biggest agent trap). https://developers.google.com/youtube/v3/revision_history
- Service accounts don't work; must use installed-app/web OAuth with refresh token. https://developers.google.com/youtube/v3/guides/authentication
- `videos.update` is destructive per-part: including `status` in `part` without a value resets privacy to default. https://developers.google.com/youtube/v3/docs/videos/update
- `publishAt` only on never-published private videos; must resend `privacyStatus=private` in same update. https://developers.google.com/youtube/v3/docs/videos/update
- Description limit is bytes -> multibyte UTF-8 chars exhaust it faster than char count suggests. https://developers.google.com/youtube/v3/docs/videos
- `uploadLimitExceeded` (400) on `videos.insert` = channel-level daily upload cap, independent of API quota. https://developers.google.com/youtube/v3/docs/videos/insert
- `thumbnails.set` can return `uploadRateLimitExceeded`, a 24h channel thumbnail cap. https://developers.google.com/youtube/v3/revision_history
- `playlistOperationUnsupported`: e.g., can't delete the auto "uploads" playlist. https://developers.google.com/youtube/v3/revision_history
- `search.list` is in its own 100/day bucket; agents assuming "just another read" exhaust it fast. https://developers.google.com/youtube/v3/determine_quota_cost
- Raw-HTTP resumable upload is multi-step (session URI, chunk PUTs, 308 resume); prefer official client libs. https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
