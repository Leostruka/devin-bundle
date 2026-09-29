# Mode: Dependency bumps (fast path for bot PRs)

Merge bot-authored, dependency-only PRs quickly and safely. Anything
touching application code, migrations, Dockerfiles, or non-dependency
config leaves this fast path and goes to `modes/pr-audit.md`.

**Batch, never serialize:** several bump PRs are one unit of work.
Consolidate all of them, resolve each dependency to the newest compatible
version (which may be newer than any PR proposes), verify the whole set
with a single CI-equivalent pass, and fix whatever that exposes in
subsequent commits. Merging and testing one bump at a time is exactly the
pipeline churn this mode avoids.

## Preconditions and guardrails

- Never commit unrelated local changes. Inspect `git status --short
  --branch`, `git diff --stat`, `git diff -- <intended files>`, and
  `git log --oneline -10` before committing; leave anything unrelated
  unstaged.
- If a deploy command builds from the working tree, temporarily stash
  unrelated local files that would enter the build context, then restore
  them after deploy.
- Do not run broad auto-formatters as a fix for dependency PRs. If lint
  fails on pre-existing style, prefer a tiny config or targeted fix; if an
  autoformatter changes dozens of files, revert it and narrow the fix.
- If any PR changes application code, migrations, Dockerfiles, or config
  that is not clearly dependency metadata, stop and run
  `modes/pr-audit.md` instead.
- **Disposition for every PR you do NOT consolidate:** leave it in a clean,
  self-explaining state on the forge before finishing: comment why it was
  not merged (major bump, failing build, non-metadata changes, suspicious
  source), then either close it or open a tracking issue and link it. Never
  leave a rejected or deferred bump silently open with a red build.
  Mentioning it only in your final summary is not resolving it.
- **Supply-chain floor:** before running the update, verify each bumped
  dependency resolves from the default public registry (rubygems.org, npm,
  pypi, crates.io) with the expected name, version, and checksums. Git/path
  sources, renamed or republished packages, typosquat-adjacent names, or
  new install-time/build hooks appearing in the resolution are
  stop-and-audit: hand the PR to `modes/pr-audit.md`. Advisory scanners
  only flag known advisories; a well-formed lockfile bump to a trojaned
  package passes every file-shape check, which is what this floor exists
  for.

## Step 1: Inspect open PRs

```bash
gh pr list --state open \
  --json number,title,headRefName,baseRefName,author,labels,mergeStateStatus,isDraft,updatedAt,url
```

For each candidate:

```bash
gh pr diff <number> --name-only
gh pr view <number> --json commits,files,statusCheckRollup,mergeable,mergeStateStatus
```

Safe routine signals: author is a dependency bot (`dependabot[bot]`,
`app/dependabot`, renovate, or the repo's equivalent); label includes
`dependencies`; title is a simple bump; changed files are dependency
metadata only (`Gemfile.lock`, `package-lock.json`, `poetry.lock`,
`Cargo.lock`); bump type is patch/minor unless the project has already
accepted the major and tests are strong.

Branch CI may fail because the bot updated a partial/stale lockfile that a
frozen mode rejects. Inspect the logs, but do not assume the bump is bad
until a consolidated local update fails.

## Step 2: Consolidate with the package manager

Update all open bump dependencies together on the current default branch.
Do not merely apply the exact version from the bot PR: treat the PR as a
signal that the dependency needs attention, then let the package manager
resolve the newest version the existing manifest constraints allow.

```bash
# Examples per ecosystem (run the repo's own tooling):
bundle update <gem_one> <gem_two> ...     && bundle check
npm update <pkg_one> <pkg_two> ...        # or pnpm/yarn equivalent
cargo update -p <crate_one> -p <crate_two>
```

This resolves lockfile conflicts and refreshes transitive checksums
correctly. Include small transitive updates in the final summary.

Do not widen manifest constraints, jump to a new major, or make
application changes chasing upstream latest unless the user explicitly
asks. If the true latest requires changing constraints, stop and report
that the latest compatible version was applied and what going further
would require.

Do not merge each bot branch individually when several lockfile PRs are
open and likely to conflict: a single consolidated commit with `Closes #N`
references produces a clean lockfile.

## Step 3: Verify locally

Run the project's CI-equivalent checks from its instructions, once over
the whole consolidated set: dependency install/check, the test suite,
lint/format, and any configured security/advisory scanner. Run independent
checks in parallel when possible, ensuring install succeeds first.

If tests fail:

1. Reproduce the failing subset locally.
2. Determine whether the failure comes from the dependency change, CI env,
   or pre-existing fragility.
3. Make only minimal robust fixes.
4. Re-run the focused test and the full CI-equivalent set.
5. Fix forward: land the consolidated bump, then repair commits on top; do
   not un-bundle the batch back into per-PR merges. To isolate a culprit
   dependency, do it in a scratch worktree, then express the outcome inside
   the consolidated change (version pin, constraint tweak, or code fix).

## Step 4: Commit and push

Detect the default branch first; never assume `master`:

```bash
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

`Closes #N` only closes the PR when the commit lands on the default
branch; pushing to another branch strands the PRs open.

Stage only intended files, usually just the lockfile:

```bash
git add <lockfile>
git diff --cached --stat && git diff --cached
git commit -m "Bump <dep_one> and <dep_two>" -m "Closes #<pr1>. Closes #<pr2>."
git push origin <default-branch>
```

CI/test hardening fixes go in a separate commit with a specific message;
keep dependency and test-infra changes easy to audit.

After push:

```bash
gh pr list --state open --json number,title,url
gh run list --branch <default-branch> --limit 5 --json databaseId,status,conclusion,headSha,displayTitle
gh run watch <push-ci-run-id> --exit-status
```

Do not deploy until the relevant push CI run passes, unless the user
explicitly accepts that risk.

## Step 5: Deploy when requested

Use the project's deploy command. If unrelated local changes would enter
the build context, stash them first and restore afterward.

## Final report checklist

- PR numbers closed.
- Direct and transitive versions changed; note where the final version is
  newer than the bot's proposed target.
- Local checks run and pass/fail.
- Hosted CI result.
- Deploy result and service health (when requested).
- PRs intentionally not consolidated, why, and the concrete state each was
  left in (commented + closed, or commented + tracked in issue #N). Every
  not-consolidated PR must already be in one of those states before you
  report.
- Any remaining local uncommitted changes intentionally left alone.
