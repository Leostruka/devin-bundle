# Plan: `social-midia` skill tree for devin-bundle

Date: 2026-10-02. Status: Phase 1 complete, awaiting approval to implement.
Spec source: `.devin/scratch/optimized_ready.md` + `prompt_spec_social_midia.json`.

## 1. Objective

Create `.devin/skills/social-midia/`: a router skill plus one skill per network
covering both practical publishing workflows and official-API technical
knowledge, researched from primary sources only. Networks: LinkedIn,
X/Twitter, Instagram, Facebook, TikTok, YouTube, Threads, Reddit.

## 2. Reference repo inspection (read-only)

Repo: `https://github.com/Jakeschincariol/linkedin-agent-skill`, single commit
`add2c23` ("The LinkedIn agent skill: 11 Claude skills, v1.0"). Inspected at
`D:\Programing\ai_workspace\_external_ref\linkedin-agent-skill`.

Format takeaways adopted as inspiration (not copied):

- Task-scoped skills (`skills/li-post`, `li-plan`, `li-human`, ...), each a
  `SKILL.md` with `name` + `description` frontmatter written as triggers.
- Heavy data pushed to side files (`hooks.json`, `rubric.json`, `slop.json`).
- "Never publish" design: every skill ends in a copy-ready block; the human
  posts it. We adopt this as the cross-network **approval gate**.
- Shared user-state file (`templates/voice.md`) all skills read.
- Honest fine print about what the API cannot do (README lines 131-158).

Not adopted: `~/.claude/` paths, Claude plugin packaging, vendored scripts
(spec forbids vendoring; our deliverable is docs-only), task-per-skill split
(spec requires network-per-skill under one router).

## 3. Capability inventory (from `.devin/research/social-midia/*.md`)

| Network | Official publish API | Auth model | API scheduling | Analytics | Hard gate |
|---|---|---|---|---|---|
| LinkedIn | Posts API `/rest/posts` | OAuth2, `w_member_social` self-serve; org scopes gated | No (UI only); ToS 3.1 bans automated posting | org + member analytics APIs | `r_member_social` closed; `little` text format |
| X/Twitter | v2 `POST /2/tweets` | OAuth2 PKCE or 1.0a; `tweet.write` | No (Ads API only) | `public/non_public/organic_metrics` | self-serve replies gated by @mention; tokens 2h |
| Instagram | Graph API content publishing (`/media` + `/media_publish`) | `instagram_business_content_publish` (IG Login) or `instagram_content_publish` (FB Login) | No; 50-100/24h publish quota | Insights (`views` metric) | professional accounts only; media must be public URL |
| Facebook | Pages API `/{page}/feed|photos|videos|video_reels|*_stories` | Page access token + `pages_manage_posts` | Yes: `scheduled_publish_time` | Page Insights | personal profile + groups impossible |
| TikTok | Content Posting API `/v2/post/publish/*` | OAuth2, `video.publish`/`video.upload` | No; ~15 posts/day/creator | `user.info.stats`, video object counts | unaudited app -> SELF_ONLY drafts only |
| YouTube | Data API v3 `videos.insert` | OAuth2 `youtube.upload`; no service accounts | Yes: `status.publishAt` | Analytics + Reporting APIs | unverified project -> uploads forced private |
| Threads | Threads API `/{user}/threads` + `threads_publish` | OAuth2 `threads_content_publish`; 60d tokens | No; 250 posts/24h | `threads_insights` | media must be public URL; containers expire 24h |
| Reddit | Data API `POST /api/submit` | OAuth2 script/web apps; `submit` scope | No (mod UI/Devvit only) | score/upvote_ratio only; no impressions | karma/age gates invisible; errors inside HTTP 200 |

Cross-cutting findings that shape the skills:

- Only Facebook and YouTube expose native scheduled publishing. All others
  require an external queue or drafts model (TikTok inbox drafts).
- LinkedIn's API ToS explicitly prohibits automated posting (section 3.1
  item 26): the LinkedIn skill must be write-only-by-hand (draft + paste).
- Media-via-URL is the dominant pattern (Instagram, Threads); chunked binary
  upload for TikTok, YouTube (resumable), Facebook video, X (v2 media upload).
- Every platform gates real publishing behind app review or account type;
  several force unverified apps into private/drafts-only modes.

## 4. Proposed tree

Location: `.devin/skills/social-midia/` (project skills). Justification:
spec scope pins writes to `.devin/skills/social-midia*`; root `skills/` is
bundle-distributed content requiring `manifest.json` and installer changes,
which the spec's out-of-scope forbids.

```
.devin/skills/social-midia/
  SKILL.md                      router (model-invoked): picks the network,
                                states the never-post gate, points onward
  reference/
    cross-network.md            scheduling matrix, auth/app-review summary,
                                ToS automation constraints, approval gate,
                                env-var conventions (names only)
  linkedin/SKILL.md             lean: triggers, capability snapshot, formats,
    api.md                      routines; pointer -> api.md for deep detail
  x-twitter/SKILL.md + api.md   endpoints, scopes, rate limits, quota,
  instagram/SKILL.md + api.md   upload flows, error traps, changelog flags
  facebook/SKILL.md + api.md
  tiktok/SKILL.md + api.md
  youtube/SKILL.md + api.md
  threads/SKILL.md + api.md
  reddit/SKILL.md + api.md
```

18 files. Network `api.md` files are the disclosed heavy reference; SKILL.md
files stay under ~10KB each (writing-skills hierarchy).

Frontmatter: `name: social-midia-<net>` (router: `social-midia`),
`description` written as "Use when..." triggers, `triggers: [user, model]`.
Nested SKILL.md files are reached via router pointers (read), matching the
bundle's router pattern (`ask-bundle`, `planning/modes/`).

## 5. Per-network SKILL.md contract (acceptance criterion 3)

Sections: `Capabilities` (what official API can/can't do), `Auth & access`
(scopes, token model, app-review gate, env var names), `Formats & limits`
(posting formats table with numbers), `Scheduling & automation` (native or
queue; rate limits), `Analytics` (metrics endpoints), `Professional routines`
(workflow guidance; flag non-official advice as craft knowledge), `Pointers`
(api.md + research digest path). Every factual claim cites the official doc
URL; unverifiable claims marked UNVERIFIED.

## 6. Implementation tickets (Phase 2, branch `feat/social-midia-skills`)

1. Shared: router `SKILL.md` + `reference/cross-network.md`.
2. Per network (8): `<net>/SKILL.md` + `<net>/api.md`, sourced from
   `.devin/research/social-midia/<net>.md` (already persisted, cited).
3. Structure verification: file existence, frontmatter parse, em-dash and
   signature checks, `skill list` discovery of the router.
4. Commits (clean, no AI trailers) + `gh pr create` (summary + test plan).

## 7. Gates ledger

- [x] G1: tree exists; 8 network SKILL.md + 8 api.md + router + shared ref
  CHECK: `ls .devin/skills/social-midia/*/SKILL.md | wc -l` = 8
  EXPECT: 8
  EVIDENCE: `8` (find listed all 18 files)
- [x] G2: frontmatter valid on all 9 SKILL.md files
  CHECK: python frontmatter parse of every SKILL.md (name/description/triggers)
  EXPECT: all parse, `triggers: [user, model]` present
  EVIDENCE: "ALL OK", 9 files with name + description + triggers
- [x] G3: no U+2014 or AI-signature patterns in any new file
  CHECK: `scripts/no-em-dash.py` + `check-ai-signature.py` equivalents per file
  EXPECT: 0 violations
  EVIDENCE: `em-dash violations: []`, `signature hits: []`
- [x] G4: router discoverable
  CHECK: CLI skill loader lists social-midia after creation
  EXPECT: listed
  EVIDENCE: `social-midia` appeared in the session `<available_skills>`
  block sourced from `.devin/skills/social-midia/SKILL.md`
- [x] G5: bundle audit unaffected
  CHECK: `python audit.py`
  EXPECT: 0 errors introduced by this change
  EVIDENCE: `Errors: 0, Warnings: 2` (both pre-existing: pycache dirs,
  check-ai-signature live!=bundle)
- [x] G6: PR open with summary + test plan
  CHECK: `gh pr create`
  EXPECT: PR exists on feat/social-midia-skills
  EVIDENCE: https://github.com/Leostruka/devin-bundle/pull/77

## 8. Open decisions for approval

- **D1 (location):** `.devin/skills/` chosen over `skills/` (see section 4).
- **D2 (LinkedIn stance):** write-only-by-hand (copy-ready drafts) because API
  ToS bans automated posting; org-page posting still documented for
  completeness.
- **D3 (networks):** exactly the 8 agreed. No Mastodon/Pinterest/etc.
