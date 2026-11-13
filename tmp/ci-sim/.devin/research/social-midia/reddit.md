# Reddit Official API & Publishing - Research Digest

## 1. API landscape
- **Data API**: REST API for programmatic access/posting; OAuth required, calls go to `oauth.reddit.com`. Docs home: https://www.reddit.com/dev/api ; wiki rules: https://github.com/reddit-archive/reddit/wiki/API ; wiki mirror at https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki
- **Devvit**: Reddit's hosted Developer Platform (TypeScript, server-side, Redis storage, triggers, scheduler) for building apps installed in subreddits, primarily mod tools/games; docs https://developers.reddit.com/docs , repo https://github.com/reddit/devvit
- **Ads API**: separate commercial API for advertisers; separate terms & access: https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- **Access tiers**: free non-commercial tier governed by Data API Terms (https://redditinc.com/policies/data-api-terms) + Developer Terms (https://redditinc.com/policies/developer-terms); any commercial use (business use, monetized product) requires a separate written agreement, same sources.
- **App review/approval**: API access requires requesting approval per Responsible Builder Policy: https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- Sign-up: Data API non-commercial signup linked from https://support.reddithelp.com/hc/en-us/articles/14945211791892

## 2. Auth & access
- OAuth2 app types: **web** (server, keeps secret), **installed** (no secret, arbitrary redirect URI), **script** (single user, owns hardware): https://github.com/reddit-archive/reddit/wiki/OAuth2-App-Types
- Script apps: only access accounts registered as app "developers"; use `grant_type=password`: https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example
- Token endpoint: `POST https://www.reddit.com/api/v1/access_token` with HTTP Basic auth (client_id:client_secret); grants: `authorization_code`, `refresh_token`, `password` (script only), `client_credentials` (app-only): https://github.com/reddit-archive/reddit/wiki/OAuth2
- Access tokens expire in 3600s: https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example
- Scopes (space-separated): `identity, edit, flair, history, modconfig, modflair, modlog, modposts, modwiki, mysubreddits, privatemessages, read, report, save, submit, subscribe, vote, wikiedit, wikiread`: https://github.com/reddit-archive/reddit/wiki/OAuth2 ; live list at `GET /api/v1/scopes`
- Endpoint->scope map: https://www.reddit.com/dev/api/oauth (per OAuth2 wiki)
- User-Agent required, format `<platform>:<app ID>:<version> (by /u/<username>)`; default UAs throttled; never spoof: https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki
- Token grant requests -> `www.reddit.com`; authed API calls -> `oauth.reddit.com`: https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example
- Env var names (convention, not official; PRAW uses `praw.ini` keys `client_id, client_secret, password, username, user_agent` per https://praw.readthedocs.io/en/v7.7.1/getting_started/configuration/options.html): `REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT`, UNVERIFIED as any official standard.

## 3. Publishing capabilities
- `POST /api/submit` (scope `submit`): `kind` = `link|self|image|video|videogif|crosspost`; params `sr`, `title`, `text`, `url`, `flair_id`, `flair_text`, `nsfw`, `spoiler`, `sendreplies`, `resubmit`, `crosspost_fullname`: https://github.com/reddit-archive/reddit/wiki/API:-submit (link/self) + field set per https://github.com/Pyprohly/reddit-api-doc-notes (unofficial mirror of live endpoints; mark UNVERIFIED for image/video/crosspost kinds in official docs)
- Errors returned inside HTTP 200 JSON `json.errors[]` (e.g., return object shows `"errors": []`): https://github.com/Pyprohly/reddit-api-doc-notes/blob/main/docs/api-reference/submission.rst
- Media: `POST /api/media/asset.json` returns S3 upload lease + `websocket_url`; upload asset to S3, submit with returned URL, read final post URL over websocket. **Endpoint is undocumented** (subject to change), confirmed via PRAW impl note: https://github.com/not-an-aardvark/snoowrap/issues/280 and https://github.com/praw-dev/praw/pull/1591
- `POST /api/comment` (scope `submit`): `thing_id` = parent fullname (`t3_` post / `t1_` comment), `text` markdown: https://www.reddit.com/dev/api (endpoint listing); PRAW wraps as `submission.reply()`/`comment.reply()`
- PRAW surfaces: `subreddit.submit`, `submit_image`, `submit_video`, `submit_gallery`, `submit_poll`, `submission.crosspost`: https://praw.readthedocs.io/en/v7.6.1/code_overview/models/subreddit.html
- Crossposting requires being subscribed to target subreddit: https://praw.readthedocs.io/en/stable/code_overview/models/submission.html
- Subreddit constraints: private/restricted subs reject posts; flair-required subs enforced at submit time (flair templates via `/r/<sr>/api/link_flair`, `flair` scope): https://www.reddit.com/dev/api
- Devvit posting: `context.reddit.submitPost()/submitCustomPost()/crosspost()`; user-context posting needs `reddit.asUser: ["SUBMIT_POST"]` permission in devvit.json: https://cdn.jsdelivr.net/npm/@devvit/reddit@0.13.9/RedditClient.d.ts + https://github.com/reddit/devvit/issues/258

## 4. Formats & limits
- Title max 300 chars: https://github.com/Pyprohly/reddit-api-doc-notes (mirrors official `title` field desc at reddit.com/dev/api)
- Self-text is markdown: https://github.com/reddit-archive/reddit/wiki/API:-submit
- Flair: `flair_id` (template) + optional `flair_text` only if template editable; get IDs via `subreddit.flair.link_templates`: https://praw.readthedocs.io/en/v7.6.1/code_overview/models/subreddit.html
- Per-subreddit gates: account age, post/comment/combined/subreddit-specific karma, verified email, approved-submitter status, enforced via AutoMod; thresholds undisclosed: https://support.reddithelp.com/hc/en-us/articles/33702751586836-Poster-Eligibility-Guide-Post-Check
- Karma check endpoint: `GET /api/v1/me/karma` (scope `mysubreddits`): https://www.reddit.com/dev/api

## 5. Scheduling & automation
- **No scheduling in public Data API**: `/api/submit` has no time parameter. Native scheduled/recurring posts exist but are a **mod-only new-Reddit UI feature** (Manage Posts permission; can post as u/AutoModerator): https://support.reddithelp.com/hc/en-us/articles/15484443169556-Scheduled-and-Recurring-Posts
- Devvit has scheduler (`context.scheduler.runJob`, cron or `runAt`): https://github.com/reddit/devvit/issues/259 ; docs https://developers.reddit.com/docs
- Rate limits (enforced since 2023-07-01): **100 QPM per OAuth client id**, 10 QPM unauthenticated (unauthenticated largely blocked); averaged over 10-min window: https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki
- Headers: `X-Ratelimit-Used/Remaining/Reset`: https://github.com/reddit-archive/reddit/wiki/API
- API rules: OAuth required; unique UA; batch requests preferred; robots.txt is for search engines not API: https://github.com/reddit-archive/reddit/wiki/API
- Bot etiquette (semi-official wiki): don't reply unsolicited, no bot voting, check sub rules allow bots, offer opt-out, blacklist sensitive subs: https://lr2.dbtc.link/wiki/bottiquette (archive of reddit.com/wiki/bottiquette)
- Spam/self-promo: ~10% self-promotion guideline is per-community, not sitewide: https://support.reddithelp.com/hc/en-us/articles/28012014962580

## 6. Analytics
- Data API exposes `score`, `upvote_ratio`, `num_comments`, `created_utc`, flair, `poll_data`, comment tree: https://praw.readthedocs.io/en/v7.7.1/code_overview/models/submission.html
- **No documented impressions/views endpoint** in https://www.reddit.com/dev/api, UNVERIFIED; "post insights" views exist in-app UI but absent from public API docs.
- Ads campaign metrics via separate Ads API (separate terms/access): https://support.reddithelp.com/hc/en-us/articles/14945211791892
- Reddit Pro Trends (business monitoring tool) is UI-based: https://redditinc.com/news/reddit-at-ces-conversations-that-drive-decisions

## 7. Professional usage
- Brands: official profile via Reddit Pro (free suite), organic posting + paid ads; AMA ad format exists: https://redditinc.com/news/reddit-at-ces-conversations-that-drive-decisions
- Organic posting by business = normal account posting; community self-promo rules apply: https://support.reddithelp.com/hc/en-us/articles/28012014962580
- Commercial use of Data API/dev tools requires written approval + contract: https://redditinc.com/policies/developer-terms section 4.1
- Profile posts: submit to `u_<username>` profile subreddit (PRAW `reddit.subreddit("u_name")`), UNVERIFIED in official docs; supported by PRAW.

## 8. Gotchas
- `/api/media/asset.json` + websocket flow undocumented -> can break; PRAW connects websocket *before* submitting to avoid race: https://github.com/praw-dev/praw/pull/1591
- Karma/age gates invisible pre-submit; fail at submit-time with no documented error contract: https://support.reddithelp.com/hc/en-us/articles/33702751586836
- `password` grant works only for script apps and only for developer accounts of that app: https://github.com/reddit-archive/reddit/wiki/OAuth2-App-Types
- Old wiki still states 60 QPM; current enforced = 100 OAuth / 10 non-OAuth: https://rareddit.com/r/redditdev/comments/13wsiks/ (official admin post)
- Errors embedded in 200 responses (`json.errors`): check body, not status: https://github.com/Pyprohly/reddit-api-doc-notes
- Post-2023: unauthenticated access effectively blocked; commercial use needs contract; robots.txt is not API permission: https://support.reddithelp.com/hc/en-us/articles/16160319875092
- Scheduled-post UI is mod-only; agents can't schedule via Data API; must own cron/queue or Devvit: https://support.reddithelp.com/hc/en-us/articles/15484443169556
- `flair_text` without `flair_id` rejected: https://praw.readthedocs.io/en/v7.6.1/code_overview/models/subreddit.html
