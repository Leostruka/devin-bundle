# Reddit - API reference

Docs home: https://www.reddit.com/dev/api ; wiki:
https://github.com/reddit-archive/reddit/wiki/API ; mirror:
https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki

## API landscape
- Data API: REST, OAuth required, calls to `oauth.reddit.com`.
- Devvit: hosted dev platform (TypeScript, triggers, scheduler) for in-subreddit apps: https://developers.reddit.com/docs
- Ads API: separate commercial API/terms.
- Terms: Data API Terms https://redditinc.com/policies/data-api-terms + Developer Terms https://redditinc.com/policies/developer-terms ; commercial use needs written agreement.
- Approval: Responsible Builder Policy: https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy

## Auth & access
- App types: web (server, secret), installed (no secret), script (single user): https://github.com/reddit-archive/reddit/wiki/OAuth2-App-Types
- Script apps: only accounts registered as app developers; `grant_type=password`: https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example
- Token: `POST https://www.reddit.com/api/v1/access_token` Basic auth (client_id:secret); grants `authorization_code`, `refresh_token`, `password` (script), `client_credentials`: https://github.com/reddit-archive/reddit/wiki/OAuth2
- Access token 3600s.
- Scopes: `identity, edit, flair, history, modconfig, modflair, modlog, modposts, modwiki, mysubreddits, privatemessages, read, report, save, submit, subscribe, vote, wikiedit, wikiread`; live list `GET /api/v1/scopes`.
- Endpoint->scope map: https://www.reddit.com/dev/api/oauth
- User-Agent required: `<platform>:<app ID>:<version> (by /u/<username>)`; default UAs throttled; never spoof.
- Token grants -> `www.reddit.com`; authed calls -> `oauth.reddit.com`.
- PRAW config keys: `client_id, client_secret, password, username, user_agent`: https://praw.readthedocs.io/en/v7.7.1/getting_started/configuration/options.html

## Publishing
- `POST /api/submit` (scope `submit`): `kind` = link|self|image|video|videogif|crosspost; params `sr`, `title`, `text`, `url`, `flair_id`, `flair_text`, `nsfw`, `spoiler`, `sendreplies`, `resubmit`, `crosspost_fullname`: https://github.com/reddit-archive/reddit/wiki/API:-submit (image/video/crosspost kinds: UNVERIFIED in official docs; field set per Pyprohly/reddit-api-doc-notes)
- Errors inside HTTP 200 `json.errors[]`; check body not status.
- Media: `POST /api/media/asset.json` -> S3 lease + `websocket_url`; upload to S3, submit with returned URL, read final URL on websocket. Undocumented/unstable; PRAW connects websocket before submitting to avoid race: https://github.com/praw-dev/praw/pull/1591
- `POST /api/comment` (scope `submit`): `thing_id` (`t3_`/`t1_`), `text` markdown: https://www.reddit.com/dev/api
- PRAW surfaces: `subreddit.submit`, `submit_image`, `submit_video`, `submit_gallery`, `submit_poll`, `submission.crosspost`: https://praw.readthedocs.io/en/v7.6.1/code_overview/models/subreddit.html
- Crosspost requires subscription to target sub.
- Flair-required subs enforced at submit; templates via `/r/<sr>/api/link_flair` (`flair` scope).
- Devvit posting: `context.reddit.submitPost()/crosspost()`; `reddit.asUser: ["SUBMIT_POST"]` in devvit.json.

## Formats & limits
- Title <=300 chars.
- Self-text: markdown.
- Flair: `flair_id` + `flair_text` only if template editable; `flair_text` alone rejected.
- Per-sub gates: account age, post/comment/combined/sub karma, verified email, approved submitter; AutoMod-enforced, thresholds undisclosed: https://support.reddithelp.com/hc/en-us/articles/33702751586836-Poster-Eligibility-Guide-Post-Check
- Karma check: `GET /api/v1/me/karma` (`mysubreddits`).

## Scheduling & automation
- No API scheduling; scheduled/recurring posts are mod-only UI (Manage Posts perm; can post as u/AutoModerator): https://support.reddithelp.com/hc/en-us/articles/15484443169556-Scheduled-and-Recurring-Posts
- Devvit scheduler: `context.scheduler.runJob` (cron or runAt): https://developers.reddit.com/docs
- Rate limits (since 2023-07-01): 100 QPM per OAuth client, 10 QPM unauthenticated; averaged 10min: https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki
- Headers: `X-Ratelimit-Used/Remaining/Reset`.
- API rules: OAuth required, unique UA, batch requests preferred; robots.txt is for search engines: https://github.com/reddit-archive/reddit/wiki/API
- Bot etiquette: no unsolicited replies, no bot voting, check sub rules allow bots, offer opt-out.
- Self-promo ~10% guideline is per-community: https://support.reddithelp.com/hc/en-us/articles/28012014962580

## Analytics
- Post fields: `score`, `upvote_ratio`, `num_comments`, `created_utc`, flair, `poll_data`, comment tree.
- No documented impressions/views endpoint; in-app insights UI-only.
- Ads metrics: separate Ads API.
- Reddit Pro Trends: UI tool, free suite for businesses.

## Gotchas
- `/api/media/asset.json` + websocket is undocumented; PRAW connects ws before submitting.
- Karma/age gates invisible pre-submit; fail at submit with undocumented error shapes.
- `password` grant: script apps + developer accounts only.
- Old wiki says 60 QPM; current is 100 OAuth / 10 non-OAuth.
- Errors embedded in 200 (`json.errors`): check body.
- Post-2023: unauthenticated effectively blocked; commercial needs contract; robots.txt is not API permission.
- Scheduled posts UI = mod-only; API can't schedule.

Provenance: `.devin/research/social-midia/reddit.md`
