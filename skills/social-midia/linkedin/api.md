# LinkedIn - API reference

Official doc home: https://learn.microsoft.com/en-us/linkedin/

## API landscape
- **Community Management API**: org page mgmt, posts, comments, reactions, org analytics; requires application approval: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview
- **Posts API** (`/rest/posts`): current creation/retrieval API; replaces ugcPosts API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Legacy Share API + UGC Post API sunset June 30, 2023 with unversioned APIs: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/archived-recent-changes/2023/marketing-api-changes
- Marketing Developer Platform: ads/sponsored content (rw_ads, r_ads): https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access
- Consumer self-serve: Sign In with LinkedIn (OIDC), Share on LinkedIn, Add to Profile, Plugins: https://learn.microsoft.com/en-us/linkedin/consumer/
- Media APIs: Images, Videos, Documents (replace legacy Assets API); also Poll, MultiImage, Social Actions: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares
- Versioning: monthly `YYYYMM`; required headers `Linkedin-Version` + `X-Restli-Protocol-Version: 2.0.0`; sunset ~1 yr: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api

## Auth & access
- OAuth2 Authorization Code Flow (3-legged); auth code lifespan 30 min: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
- Access token 60 days; programmatic refresh token 365 days (approved apps): https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens
- Tokens ~500 chars; storage plan >=1000 chars.
- Introspection: `/introspectToken` for TTL/status/scope: https://learn.microsoft.com/en-us/linkedin/shared/authentication/token-introspection
- Self-serve scopes: `openid`, `profile`, `email` (OIDC); `w_member_social` (Share on LinkedIn): https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- Community Management scopes (approval gate): `r_organization_social`, `w_organization_social`, `rw_organization_admin`, `r_member_social` (closed), `w_member_social_feed`, `w_organization_social_feed`, `r_member_profileAnalytics` (v202504+), `r_member_postAnalytics` (v202506+): https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access
- `r_liteprofile`/`r_emailaddress` deprecated Aug 1, 2023 -> OIDC `openid profile email`: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin
- Org scopes restricted to page roles ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, CONTENT_ADMIN: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-access-control-by-role

## Publishing
- `POST https://api.linkedin.com/rest/posts`; author `urn:li:person:{id}` or `urn:li:organization:{id}`; returns `x-restli-id`: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Content matrix: Text/Images/Videos/Documents/Article = organic+sponsored; Carousels sponsored-only; MultiImage, Poll, Celebration organic-only (Celebration not creatable externally): same + https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/post-api-schema
- Article content = link-share w/ supplied source+title+description+thumbnail; no URL scraping.
- `lifecycleState`: PUBLISHED only at creation; no API drafts: post-api-schema URL above.
- `commentary` = `little` format; escape `\| { } @ [ ] ( ) < > # \ * _ ~`; hashtags `{hashtag|#|tag}`; mentions need URN annotation, case-sensitive entity match: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/little-text-format
- Articles/newsletters UI-only; legacy Articles API read-only: https://www.linkedin.com/help/linkedin/answer/a522427/publish-articles-on-linkedin
- Retrieval: GET by URN, batch-get, finder by `author` with `viewContext` READER/AUTHOR; person-author find needs closed `r_member_social`.

## Formats & limits
- Text ~3,000 chars (number not published; enforced via 400 `*_LENGTH_TOO_LONG`).
- Images: JPG/GIF/PNG, <36,152,320 px, GIF <=250 frames: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api
- Videos: 3s-30min, MP4; docs conflict 500MB vs 5GB `fileSizeBytes`: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api
- Documents: <=100MB, <=300 pages; PPT/PPTX/DOC/DOCX/PDF: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api
- Upload: `initializeUpload` -> PUT binary to returned URL -> reference media URN in post.

## Scheduling & automation
- No scheduling field; PUBLISHED-only lifecycle.
- UI scheduler: 10min-3months; Pages restricted to super/content admins: https://www.linkedin.com/help/linkedin/answer/a1347212/schedule-posts
- API ToS 3.1 item 26 bans automated posting: https://www.linkedin.com/legal/l/api-terms-of-use
- Rate limits unpublished; app+member daily limits reset midnight UTC; portal Analytics/Usage & Limits; 429; 75% email alerts (~1-2h delay): https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits

## Analytics
- `GET /rest/organizationalEntityShareStatistics` (`q=organizationalEntity`): organic only, 12-month window, DAY granularity; impressionCount, clickCount, likeCount, commentCount, shareCount, engagement: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/share-statistics
- `GET /rest/memberCreatorPostAnalytics` (finders `q=entity`, `q=me`): queryType IMPRESSION|MEMBERS_REACHED|RESHARE|REACTION|COMMENT; aggregation DAILY|TOTAL; needs `r_member_postAnalytics` (v202506+): https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics
- `r_member_profileAnalytics` added v202504: https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access

## Gotchas
- Person posting: `w_member_social` self-serve; reading person's posts: `r_member_social` closed.
- URNs must be URL-encoded in query params.
- Unescaped `(`, `#`, `|` in `little` text fails or mangles; domain-shaped strings autolink.
- Article posts do not scrape the URL.
- Versions retire yearly: pin and rotate `Linkedin-Version`.
- API "carousel" = sponsored only; organic carousels = Documents API PDFs.
- Finder results may return fewer than `count`; follow `links`; `isDsc` deprecated.

Provenance: `.devin/research/social-midia/linkedin.md`
