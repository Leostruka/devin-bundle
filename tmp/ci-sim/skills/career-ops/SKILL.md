---
name: career-ops
description: Use when the user wants help running a job hunt end to end: scanning public job boards, scoring role fit, tailoring a CV or cover letter, and tracking applications in a local tracker. The agent never submits applications.
triggers: [user, model]
---

# Career Ops

Slim port of the career-ops workflow modes.

Source: MIT, https://github.com/career-ops-hq/career-ops (aka santifer/career-ops)

Out of scope by design: no Go dashboard, no Playwright PDF generation, no
credentialed scraping, no browser automation of application forms.

## HARD RULE

The agent NEVER submits applications. No clicks on Apply, no form fills on
behalf of the user, no uploads to an ATS. The agent finds, scores, drafts,
and tracks; the user presses submit. If a listing requires login or
captcha to view, skip it and note it in the tracker as inaccessible.

## Mode 1: Pipeline scan

Find candidate roles on public boards only:

- Greenhouse public boards: `boards.greenhouse.io/<company>`
- Ashby: `jobs.ashbyhq.com/<company>`
- Lever: `jobs.lever.co/<company>`

Fetch listing pages with `webfetch` or the `scrape-tools` extension.
Public endpoints only; never authenticate, never scrape behind a login.

For each target company or role query the user provides, collect:
title, company, location, remote policy, posted date, apply URL, and the
job description text.

## Mode 2: Score fit

Score each role 1-5 per axis against the user's stated profile. Ask the
user for their profile once per session if not known (target stack,
seniority, minimum comp, location constraints).

| Axis | What to check |
|---|---|
| Stack match | Overlap between required skills and the user's stack |
| Seniority | Level and years vs the user's experience |
| Comp | Listed range vs the user's floor; unknown comp scores 3 |
| Location | Remote/onsite/hybrid vs the user's constraints |

Total out of 20. Present ranked results as a table with the apply URL.
Recommend applying to anything >= 14 unless the user says otherwise.

## Mode 3: Tailor CV and cover letter

For a role the user picks:

1. Read the user's base CV (ask for its path if unknown).
2. Map the job description's required/preferred skills to the CV.
3. Produce a tailored CV draft: reorder and rephrase real experience to
   surface the matching work. Never invent employers, titles, dates, or
   metrics.
4. Produce a cover letter draft: 3 short paragraphs, specific to the
   company and role, using the project's actual language where apt.

Write drafts to `.devin/scratch/career-ops/<company>-<role-slug>/`.
The user reviews and edits; the agent does not submit.

## Mode 4: Track applications

Maintain `.devin/scratch/career-ops/tracker.md` as a Markdown table:

| Date | Company | Role | Fit | Status | Applied URL | Notes |
|---|---|---|---|---|---|---|

Status vocabulary: `found`, `scored`, `drafted`, `submitted`, `interview`,
`offer`, `rejected`, `withdrawn`. The agent sets rows up to `drafted`;
`submitted` and later statuses are only recorded after the user confirms
they applied.

Update the tracker on every scan, draft, or user-reported status change.

## Workflow

```
Scan public boards
  -> Score each role (stack, seniority, comp, location)
  -> Present ranked table; user picks roles
  -> Tailor CV + cover letter drafts per role
  -> Update tracker (status: drafted)
  -> User applies manually, reports back
  -> Update tracker status
```
