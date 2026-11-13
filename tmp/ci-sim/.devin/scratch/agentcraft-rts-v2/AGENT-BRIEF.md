# RTS v2 milestone brief (v3.8.0) - implementer rules

Repo: `D:\Programing\ai_workspace\devin-bundle` (GitHub Leostruka/devin-bundle).
Read first: `.devin/scratch/agentcraft-rts-v2/gdd.md` (the spec),
`gh issue view <N>` (your issue body, incl. acceptance criteria + "Blocked by").

## Workflow (per issue)

1. `git checkout milestone/v3.8.0 && git pull` then
   `git checkout -b rts-v2/<N>-<slug>`.
2. Implement EXACTLY the issue scope. Every visible UI element must map to a
   real bundle/CLI surface (file, event, endpoint, ledger). No fake data, no
   pretend actions. Intents never execute automatically - they are written to
   `.devin/rts/intents/` for `scripts/rts-intents.py`.
3. Gates, ALL must pass before commit:
   - `python -m py_compile` on every .py you touched
   - `node --check` on every .js you touched
   - `python extensions/rtsd/selftest.py` must print ALL PASS
   - `python audit.py` must print 0 errors / 0 warnings
   - `python -m pytest -x -q` green
4. Add a `CHANGELOG.md` `[Unreleased]` entry (### Added), bullet describing
   real surfaces, ends with `(#N)`.
5. Commit: `git add <files>` explicit paths only. Conventional message
   `feat(rtsd): ...` or `fix(rtsd): ...`. NO AI signature, NO Co-Authored-By.
6. `git push -u origin rts-v2/<N>-<slug>`, then
   `gh pr create --base milestone/v3.8.0 --title "<issue title>" --body ...`
   Body: Summary + acceptance coverage bullets + test evidence + `Refs #<N>`
   (NEVER "Closes").
7. Squash-merge: `gh pr merge <PR> --squash --delete-branch`, then
   `git checkout milestone/v3.8.0 && git pull`.
8. Report back: PR number/url, files changed, gate outputs (verbatim tails),
   acceptance items mapped to evidence, known gaps.

## Hard rules

- stdlib-only Python in `scripts/` + `extensions/rtsd/`; frontend is
  zero-dependency canvas 2D, no CDN, no build step (`web/js/*.js`, ES5-ish).
- `events.jsonl` is the ONLY authoritative history: `World.apply(ev)` +
  `snapshot(now)` must replay byte-identically. Never store derived time state
  in ways that break replay; compute time-derived fields at snapshot time.
- No em-dashes (U+2014) anywhere in prose files - repo stop-guard rejects them.
  Use hyphens, colons, semicolons.
- Fail open for hook ingestion; fail closed for security decisions
  (decisions stay pending without explicit answer).
- Never weaken/delete tests or checks. Assertions may only be corrected when
  the check itself encodes a wrong assumption; document why in the PR.
- Don't commit `.devin/scratch/agentcraft-rts-v2/issues/` (untracked copies).
- Never expose secrets/tokens to frontend data; remote listener reports only
  token-existence booleans.
- Update `data/` counts, manifest, README, `.devin/docs/TOOLS-MAP.md` ONLY if
  the issue actually adds exported resources.
- If blocked mid-issue: leave branch green, document blocker in the PR body,
  report BLOCKED - do not half-merge.

## Key files

- `extensions/rtsd/world.py` - event-sourced world (apply/snapshot/tick).
  Helpers: `_input_path`, `file_tile`, `region_of`, `HERO_CLASSES`,
  `BUILDINGS`, `assign_sites`, `profile_kit`, `profile_tier`, `_KIT_TOOLS`,
  `TOOL_TO_BUILDING`.
- `extensions/rtsd/rtsd.py` - HTTP/WS daemon. `append_event` appends jsonl,
  applies to world, broadcasts upsert `{event, hint}`. Routes: GET /snapshot,
  /buildings/<id>, /ws, POST /event, /intent, static web/*.
- `extensions/rtsd/web/js/engine.js` - renderer (camera, tilemap, fog, marks,
  pings, workers, fades, barks, minimap).
- `extensions/rtsd/web/js/app.js` - state, WS client, picking, portrait,
  intents, ping queue, council modal, feed.
- `extensions/rtsd/web/js/theme.js` - palettes/glyphs (battlefield + office).
- `extensions/rtsd/selftest.py` - integration gate; extend, don't weaken.
- Snapshot `world` keys: units, buildings, resources, quests, regions,
  workers, map (tile_region/fog/mark/pois), goal, score.
- Intent kinds accepted: spawn, message, goal, answer, order (extend only if
  the issue requires).
