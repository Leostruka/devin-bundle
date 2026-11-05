# Reels batch-2 execution plan (2026-11-05)

**Status: EXECUTED 2026-11-05** - all 4 waves merged (#311, #313) + polish PRs (#314-#321). All 15 issues resolved with `## Answer` sections.

Source: `.devin/research/2026-11-05-reels-batch2-survey.md` | Issues: `.devin/scratch/reels-2/issues/` | Transcripts: `.devin/scratch/reels-2/transcripts/`

## Wave structure

### Wave 1: ADOPT skills (P2, independent, parallel lanes OK)

| Issue | Deliverable | Surface |
|---|---|---|
| R2-04 | `skills/web-perf-checklist/SKILL.md` | new skill |
| R2-05 | `skills/big-file-refactor/SKILL.md` | new skill |
| R2-11 | `agents/watchdog.md` + `context-hygiene` edit + MODEL-GUIDE edit | new agent + 2 doc edits |

Shared bookkeeping after each merge: manifest (skill/agent entries + hashes), README count, CHANGELOG [Unreleased] + PR ref, `audit.py` clean.

### Wave 2: ADAPT / routing (P2)

| Issue | Deliverable | Surface |
|---|---|---|
| R2-09 | `advisor` role in `data/bundle-models.json` + MODEL-GUIDE pattern (verify CLI support via devin-config first) | data + docs |
| R2-01 | `skills/cli-adapter/SKILL.md` citing `extensions/agent-reach/wrapper.py` | new skill |

### Wave 3: Backlog evals (P3, research-only, can batch as one PR)

| Issue | Deliverable |
|---|---|
| R2-02 | eval table: job-apply pipeline |
| R2-03 | coverage matrix for the 10-repo roundup |
| R2-07 | OSS alternatives note |
| R2-08 | Personaplex-7B eval (license/GPU/voicebox fit) |
| R2-10 | model-name decoder section in ai-tools |
| R2-12 | game-dev lane verdict table |
| R2-13 | file-size guard hook eval (implement only if non-spammy) |
| R2-14 | `.devin/docs/ARCHETYPE-MAP.md` |

### Wave 4: External deliverables

| Issue | Deliverable |
|---|---|
| R2-06 | `skills/verify-atlas/` via dogfooded create-verification-skill |
| R2-15 | MERIDIAN alt-data backlog append (leostruka/MERIDIAN repo or backlog file) |

## Cross-cutting notes

- R2-05 + R2-13 address the same pain (big files); R2-13 is the guard, R2-05 the cure: order R2-05 first so the guard can point at the skill.
- Reel 06/15 content is already shipped (#309, v3.19.0): no action beyond R2-06 dogfooding.
- Every wave ends with `install.ps1 -Force` + `devin doctor` + audit before the next starts.
- MERIDIAN deliverable lives outside this repo; only the backlog reference lands here.
