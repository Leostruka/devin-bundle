---
name: social-midia-linkedin
description: Use when the user wants to draft, post, or analyze LinkedIn content (personal or organization page), plan a LinkedIn posting routine, or asks about the LinkedIn API (Posts API, OAuth scopes, versioning, analytics, rate limits).
triggers: [user, model]
---

# LinkedIn

Two lanes:

- **Draft + paste (default).** LinkedIn API Terms 3.1 item 26 prohibits
  using the APIs to automate posting. Personal publishing through this
  skill is always copy-ready text the user pastes. https://www.linkedin.com/legal/l/api-terms-of-use
- **Org-page API.** Community Management API posts to organization pages
  with approved scopes; legitimate for sanctioned tooling, still
  confirmation-gated.

## Capabilities (official)

| Action | Personal | Org page |
|---|---|---|
| Text/image/video/document post | `w_member_social` (self-serve) | `w_organization_social` (app approval + page role) |
| Document/"carousel" (PDF) post | yes | yes |
| Multi-image, poll | yes (organic) | yes (organic) |
| Carousel cards | sponsored-only | sponsored-only |
| Long-form article / newsletter | UI only, no API | UI only, no API |
| Scheduling | UI only (10min-3mo) | UI only; API has no scheduling field |
| Read own posts | `r_member_social`: closed | `r_organization_social` |

Detail: `api.md`.

## Auth & access

- OAuth2 Authorization Code (3-legged). Access token 60 days; refresh
  token 365 days for approved apps.
- Self-serve: `openid`, `profile`, `email` (OIDC sign-in) and
  `w_member_social` (Share on LinkedIn). No app review needed.
- Org posting: `w_organization_social` requires application approval and
  a page role (ADMINISTRATOR, CONTENT_ADMIN, or
  DIRECT_SPONSORED_CONTENT_POSTER).
- Every call needs headers `Linkedin-Version: {YYYYMM}` +
  `X-Restli-Protocol-Version: 2.0.0`; versions retire ~1yr, so pin and
  rotate.
- Env var names (convention, UNVERIFIED as official):
  `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`,
  `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`.

## Formats & limits

- Text post: ~3,000 chars (official number not published; API rejects
  with `*_LENGTH_TOO_LONG`).
- `commentary` is `little` format, not plain text: escape
  `\| { } @ [ ] ( ) < > # \ * _ ~`; hashtags as `{hashtag|#|tag}`.
- Images: JPG/GIF/PNG, <36,152,320 px, GIF <=250 frames.
- Video: 3s-30min, MP4 (docs conflict: 500MB vs 5GB).
- Documents: PPT/DOC/PDF, <=100MB, <=300 pages.

## Scheduling & automation

- No API scheduling. UI scheduler: 10min-3months ahead.
- Rate limits are unpublished; app+member daily limits reset midnight
  UTC; check Developer Portal Analytics tab.
- Do not build auto-posting: ToS bans it. Plan content, output drafts.

## Analytics

- Org: `GET /rest/organizationalEntityShareStatistics` (organic only,
  12-month window, DAY granularity).
- Member: `GET /rest/memberCreatorPostAnalytics` (IMPRESSION /
  MEMBERS_REACHED / RESHARE / REACTION / COMMENT; needs
  `r_member_postAnalytics`, v202506+).

## Professional routines

- Cadence: no official guidance. Working pattern from the reference
  format: ~4 posts/week, mix proof/opinion/teach/story/offer, engage
  20min/day before posting. Marked craft knowledge, not API doc.
- Document posts and multi-image posts are the confirmed organic formats
  professionals use.
- Profile/headline rewriting is UI-side work: draft sections, user pastes.

## Reference

- `api.md`: endpoints, upload flow, little-format rules, error traps.
- Provenance: `.devin/research/social-midia/linkedin.md`.
