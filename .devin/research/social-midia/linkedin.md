# LinkedIn Official Platform APIs - Research Digest

## 1. API landscape
- Docs home (all business lines: Consumer, Marketing, Compliance, Sales, Talent, Learning): https://learn.microsoft.com/en-us/linkedin/
- **Community Management API**: org page mgmt, posts, comments, reactions, org analytics; requires application approval: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview
- **Posts API** (`/rest/posts`): current creation/retrieval API; officially **replaces ugcPosts API**: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Legacy **Share API + UGC Post API sunset June 30, 2023** along with unversioned APIs: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/archived-recent-changes/2023/marketing-api-changes
- **Marketing Developer Platform**: ads/sponsored content (rw_ads, r_ads): https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access
- Consumer self-serve products: **Sign In with LinkedIn (OIDC)**, **Share on LinkedIn**, Add to Profile, Plugins: https://learn.microsoft.com/en-us/linkedin/consumer/
- Media/asset APIs: **Images API, Videos API, Documents API** (all replace legacy Assets API); also Poll API, MultiImage API, Social Actions API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares
- Versioning: monthly `YYYYMM` versions; every request needs headers `Linkedin-Version: {YYYYMM}` and `X-Restli-Protocol-Version: 2.0.0`; versions sunset ~1 yr later (e.g. 202508 -> Aug 17 2026, 202510 -> Oct 15 2026): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api

## 2. Auth & access
- OAuth 2.0 Authorization Code Flow (3-legged); auth code lifespan **30 min**: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
- Access token lifespan **60 days**; programmatic refresh token **365 days** (approved apps only): https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens
- Tokens ~500 chars; plan storage for >=1000 chars: same URL as above
- Token introspection endpoint `/introspectToken` for TTL/status/scope: https://learn.microsoft.com/en-us/linkedin/shared/authentication/token-introspection
- **Self-serve scopes** (no approval): `openid`, `profile`, `email` (Sign In OIDC product); `w_member_social` (Share on LinkedIn product): https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- **Community Management API scopes** (application gate): `r_organization_social`, `w_organization_social`, `rw_organization_admin`, `r_member_social` (closed, "not accepting access requests"), `w_member_social_feed`, `w_organization_social_feed`, `r_member_profileAnalytics` (v202504+), `r_member_postAnalytics` (v202506+): https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access
- Legacy `r_liteprofile`/`r_emailaddress`: Sign In (non-OIDC) **deprecated Aug 1, 2023** -> use OIDC `openid profile email`: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin
- `w_organization_social`/`r_organization_social` restricted to page roles: ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, CONTENT_ADMIN: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-access-control-by-role
- Env var names, **convention only, UNVERIFIED as official** (docs use params `client_id`/`client_secret`): `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`

## 3. Publishing capabilities
- `POST https://api.linkedin.com/rest/posts`; author = `urn:li:person:{id}` or `urn:li:organization:{id}`; returns `x-restli-id` header (`urn:li:share:{id}` or `urn:li:ugcPost:{id}`): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Content-type matrix (official): Text/Images/Videos/Documents/Article = organic+sponsored; **Carousels sponsored-only**; MultiImage, Poll, Celebration = organic-only (Celebration "can't be created through external api"): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api + https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/post-api-schema
- "Article" content = link-share post w/ source+title+description+thumbnail; **no URL scraping**, fields must be supplied: posts-api URL above
- `lifecycleState`: **PUBLISHED is the only accepted value at creation**, so no API drafts: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/post-api-schema
- `commentary` uses `little` text format, NOT plain text; reserved chars `\| { } @ [ ] ( ) < > # \ * _ ~` must be escaped; hashtags sent as `{hashtag|#|tag}` template; mentions need URN annotation matching entity name (case-sensitive): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/little-text-format
- Long-form LinkedIn articles / newsletters: **UI-only** (no creation API; legacy Articles API is read-only): https://www.linkedin.com/help/linkedin/answer/a522427/publish-articles-on-linkedin
- Retrieve posts: GET by URN (`ugcPostUrn`/`shareUrn`), batch-get, finder by `author` (single author; `viewContext` READER/AUTHOR); person-author find requires restricted `r_member_social`: posts-api URL

## 4. Formats & limits
- Post text limit **3,000 chars**, attributed to LinkedIn Help by secondary sources; **exact official URL UNVERIFIED**; API enforces via 400 `*_LENGTH_TOO_LONG` errors without publishing the number: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Images API: JPG/GIF/PNG; **<36,152,320 pixels**; GIF <=250 frames: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api
- Videos API specs section: **3s-30min, 75KB-500MB, MP4**; note `fileSizeBytes` field doc states "Maximum allowed Videos size is 5GB", **internal doc discrepancy**: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api
- Documents API (doc/carousel-style posts): **<=100MB, <=300 pages; PPT, PPTX, DOC, DOCX, PDF**: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api
- Media upload flow: `initializeUpload` action -> upload binary to returned URL -> reference media URN in post: images-api URL above

## 5. Scheduling & automation
- **No scheduling field in Posts API**: `PUBLISHED`-only lifecycle; no `scheduledPosts`/datetime param in official docs: post-api-schema URL
- Native UI scheduling only: clock icon, **10 min-3 months** ahead; unsupported for certain post types; Page scheduling restricted to super/content admins: https://www.linkedin.com/help/linkedin/answer/a1347212/schedule-posts
- **API Terms of Use section 3.1 prohibits "Use the Content or the APIs to automate posting on the LinkedIn Services"** (item 26): https://www.linkedin.com/legal/l/api-terms-of-use
- Rate limits: per-endpoint values **not published**; app-level + member-level daily limits reset midnight UTC; lookup in Developer Portal -> app -> Analytics/Usage & Limits tab; 429 on breach; 75%-quota email alerts to Developer Admins (~1-2h delay): https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits

## 6. Analytics
- `GET /rest/organizationalEntityShareStatistics` (`q=organizationalEntity`): **organic only**, rolling **12-month** window, lifetime or time-bound (DAY granularity); metrics: impressionCount, clickCount, likeCount, commentCount, shareCount, engagement: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/share-statistics
- `GET /rest/memberCreatorPostAnalytics` (finders `q=entity` single post, `q=me` aggregate): queryType `IMPRESSION|MEMBERS_REACHED|RESHARE|REACTION|COMMENT`; aggregation `DAILY|TOTAL` (MEMBERS_REACHED+DAILY unsupported); requires `r_member_postAnalytics` (v202506+): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics
- Member profile analytics scope `r_member_profileAnalytics` added v202504: https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access
- Org page follower/page analytics via Organization APIs under `rw_organization_admin`/`r_organization_admin`: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-access-control-by-role

## 7. Professional usage (officially confirmed)
- Document posts (PDF "carousels") and multi-image posts supported organically: post-api-schema URL
- Long-form articles + article scheduling exist but are **UI-only**: https://www.linkedin.com/help/linkedin/answer/a522427/publish-articles-on-linkedin
- Official cadence guidance: **none found in docs, UNVERIFIED**; LinkedIn marketing blog points to 3rd-party partner tools for scheduling Pages: https://www.linkedin.com/business/marketing/blog/linkedin-pages/how-to-schedule-posts-on-your-companys-linkedin-page

## 8. Gotchas
- Agent trap: person posting needs only self-serve `w_member_social`; **reading** a person's posts needs `r_member_social`, which is closed: community-management-overview URL
- `author` must be `urn:li:person:{id}` / `urn:li:organization:{id}` (org posting gated by page role); URNs must be URL-encoded in query params
- `commentary` is `little` format: unescaped `(`, `#`, `|` etc. fail or mangle text; domain-shaped strings autolink
- Article posts do **not** scrape the URL: supply title/description/thumbnail yourself
- Versioned headers mandatory; versions retire yearly -> pin and rotate `Linkedin-Version`
- Carousel content via API = sponsored only; organic "carousels" = Documents API PDFs
- Video size docs conflict (500MB spec vs 5GB field doc): verify empirically
- Finder results may return fewer than `count`; follow `links` for next page; `isDsc` param deprecated
- API ToS anti-automation clause (section 3.1 item 26) sits in tension with posting APIs: flag for skill design
