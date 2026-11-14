# gh/git arsenal: command and API matrix

Complete command reference for the adaptive engine. Prefer `--json` +
`--jq` over scraping text output; add `--json` with no fields to
discover available fields. Non-interactive runs need explicit flags
(`--title`, `--body-file`); `gh` skips the pager and color on its own.

## Auth and repo context

| Command | Purpose |
| --- | --- |
| `gh auth status` | Token, host, scopes; missing scopes listed |
| `gh auth refresh -s project` | Add the `project` scope for Projects v2 |
| `gh auth token` | Print token - never echo into files/logs |
| `gh repo view --json <fields>` | Repo metadata as JSON |
| `gh repo view --json nameWithOwner,defaultBranchRef,hasIssuesEnabled,hasProjectsEnabled,hasDiscussionsEnabled,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge,repositoryTopics` | The Fase Zero capability probe |
| `gh repo create|fork|clone|sync|edit` | Repo lifecycle |
| `gh browse [--settings]` | Open repo/pages in browser |
| `gh api repos/{owner}/{repo}` | REST repo object |
| `gh api repos/{owner}/{repo} --jq '.permissions'` | Caller permissions on repo |
| `gh api rate_limit` | Remaining API quota |
| `gh api graphql -f query='...'` | GraphQL queries/mutations |

## Issues

| Command | Purpose |
| --- | --- |
| `gh issue create --title T --body-file f.md` | New issue from file body |
| `gh issue create --parent 100` | Create as sub-issue of #100 (gh >= 2.94) |
| `gh issue create --blocked-by 200,201 --blocking 300` | Dependency links at create time |
| `gh issue create --type Bug --label x --assignee @me --milestone M --project "Roadmap"` | Typed/organized issue |
| `gh issue list --state open --label bug --type Bug --json number,title,labels,parent,subIssues,blockedBy` | Structured listing |
| `gh issue view 42 --json title,body,labels,comments,subIssuesSummary,blockedBy,blocking` | Full issue as JSON |
| `gh issue edit 42 --body-file f.md --add-label x --remove-label y` | Update fields |
| `gh issue edit 100 --add-sub-issue 101,102` | Attach existing issues as sub-issues |
| `gh issue edit 101 --remove-parent` / `gh issue edit 100 --remove-sub-issue 101` | Detach |
| `gh issue edit 42 --add-blocked-by 7 --remove-blocked-by 8 --add-blocking 9` | Manage dependencies |
| `gh issue close 42 --comment "fixed in #55"` / `gh issue reopen 42` | State changes |
| `gh issue comment 42 --body-file f.md` | Comment from file |
| `gh issue develop 42 --checkout` | Branch for the issue |
| `gh issue pin 42` / `gh issue unpin 42` / `gh issue transfer 42 owner/repo` | Curation |
| `gh label list|create|edit|clone|delete` | Label taxonomy |
| `gh milestone list|create|edit|close` | Milestones |

JSON relationship fields are objects: `{"nodes": [...], "totalCount": N}`
- compare node count against `totalCount` for truncation (`subIssues`
caps at 100, `blockedBy`/`blocking` at 50).

REST fallbacks for hierarchy: `gh api repos/{o}/{r}/issues/{n}/sub_issues`
(POST to attach, DELETE to detach); GraphQL `addSubIssue` /
`removeSubIssue` mutations.

## Pull requests

| Command | Purpose |
| --- | --- |
| `gh pr create --title T --body-file f.md --base main --head feat/x` | PR from file body |
| `gh pr create --draft --reviewer @me --assignee @me --label x` | Metadata at create |
| `gh pr list --state open --json number,title,headRefName,statusCheckRollup` | Structured list |
| `gh pr view 55 --json title,body,files,reviews,statusCheckRollup,mergeable` | Full PR as JSON |
| `gh pr diff 55` / `gh pr checks 55` | Diff and check status |
| `gh pr checks 55 --watch` | Block until checks settle |
| `gh pr edit 55 --body-file f.md --add-reviewer u --remove-label x` | Update PR |
| `gh pr comment 55 --body-file f.md` / `gh pr review 55 --approve --body-file f.md` | Comment / review |
| `gh pr merge 55 --squash --delete-branch` | Merge per strategy |
| `gh pr merge 55 --auto --squash` | Auto-merge when checks pass |
| `gh pr ready 55` / `gh pr close 55` / `gh pr reopen 55` | State changes |
| `gh pr checkout 55` | Local checkout of PR head |

## Rulesets and branch protection

| Command | Purpose |
| --- | --- |
| `gh api repos/{o}/{r}/rulesets` | List repo rulesets (404/403 tolerated: feature off or no admin) |
| `gh api repos/{o}/{r}/rulesets/{id}` | Single ruleset detail |
| `gh api repos/{o}/{r}/rulesets -X POST --input ruleset.json` | Create ruleset |
| `gh api repos/{o}/{r}/rulesets/{id} -X PUT --input ruleset.json` | Update ruleset |
| `gh api repos/{o}/{r}/rulesets/{id} -X DELETE` | Delete ruleset |
| `gh api orgs/{org}/rulesets` | Org-level rulesets |
| `gh api repos/{o}/{r}/rules/branches/{branch}` | Effective rules for a branch |
| `gh api repos/{o}/{r}/branches/{branch}/protection` | Classic branch protection |

Ruleset JSON shape: `name`, `target` (`branch`/`tag`), `enforcement`
(`active`/`evaluate`/`disabled`), `conditions.ref_name.include/
.exclude`, `rules[]` (`pull_request`, `required_status_checks`,
`non_fast_forward`, `commit_message_pattern`, ...), `bypass_actors[]`.

## Environments and deployment gates

| Command | Purpose |
| --- | --- |
| `gh api repos/{o}/{r}/environments` | List environments |
| `gh api repos/{o}/{r}/environments/{env}` | Environment detail (protection rules, reviewers) |
| `gh api repos/{o}/{r}/environments/{env} -X PUT --input env.json` | Create/update |
| `gh api repos/{o}/{r}/environments/{env}/secrets` | Env secrets (names) |
| `gh api repos/{o}/{r}/deployments` / `.../deployments/{id}/statuses` | Deployment history |

## Secrets and variables (CI config)

| Command | Purpose |
| --- | --- |
| `gh secret list` / `gh secret list --env prod` | Names only, repo or env scope |
| `gh secret set NAME` (prompt) / `gh secret set NAME --body v` / `--env prod` | Set repo/env secret |
| `gh secret delete NAME [--env prod]` | Remove |
| `gh variable list` / `gh variable list --env prod` | Non-secret config values |
| `gh variable set NAME --body v [--env prod]` / `gh variable get NAME` / `gh variable delete NAME` | Manage |

Rules: values never appear in command lines that get logged (prefer
stdin/prompt), never in issues/PRs/commits; reference secrets as
`${{ secrets.NAME }}` and variables as `${{ vars.NAME }}` in workflows.

## Workflows, runs, cache

| Command | Purpose |
| --- | --- |
| `gh workflow list` | Workflow inventory (Fase Zero probe) |
| `gh workflow view <name>` / `gh workflow view <name> --yaml` | Definition |
| `gh workflow run <file> --ref main -f input=x` | workflow_dispatch trigger |
| `gh workflow enable|disable <name>` | Toggle |
| `gh run list --limit 10 --json databaseId,status,conclusion,name,headBranch` | Recent runs |
| `gh run view <id>` | Run summary |
| `gh run view <id> --log-failed` / `--log` | Failed-job logs |
| `gh run view <id> --json jobs,conclusion,statusCheckRollup` | Structured detail |
| `gh run watch <id>` / `gh run watch <id> --exit-status` | Stream until done |
| `gh run rerun <id>` / `gh run rerun <id> --failed` / `gh run cancel <id>` | Retry/cancel |
| `gh run download <id> -n artifact` | Fetch artifacts |
| `gh cache list` / `gh cache delete <key>` | Actions cache management |

## Releases and tags

| Command | Purpose |
| --- | --- |
| `git tag -a v1.2.3 -m "release notes"` + `git push origin v1.2.3` | Annotated tag (never lightweight for releases) |
| `gh release create v1.2.3 --generate-notes --target main` | Release from tag with generated notes |
| `gh release create v1.2.3 --notes-file notes.md --prerelease` | Custom notes / prerelease |
| `gh release view v1.2.3 --json tagName,isDraft,assets,url` | Inspect |
| `gh release upload v1.2.3 dist/*` / `gh release delete v1.2.3` | Assets / removal |
| `gh release edit v1.2.3 --latest=false` | Mark latest |
| `gh attestation verify <asset> --repo {o}/{r}` | Verify build provenance |
| `gh attestation download <asset>` | Fetch attestation bundle |

Attestations are produced by `actions/attest-build-provenance` in CI;
the CLI verifies them. For hotfix patch releases prefer
`--generate-notes` and confirm the tag is annotated.

## Projects (v2)

Requires `project` OAuth scope: `gh auth refresh -s project`.

| Command | Purpose |
| --- | --- |
| `gh project list --owner @me` | List projects |
| `gh project view <number> --owner @me --format json` | Project + fields as JSON |
| `gh project item-add <number> --owner @me --url <issue-or-pr-url>` | Add item |
| `gh project item-list <number> --owner @me --format json` | List items |
| `gh project field-list <number> --owner @me --format json` | Fields (Status, Priority, ...) |
| `gh project item-edit --project-id <id> --id <item-id> --field-id <fid> --single-select-option-id <oid>` | Set field value |

## Search and misc

| Command | Purpose |
| --- | --- |
| `gh search issues "query" --json number,title,state` | Cross-repo issue search |
| `gh search prs "query" --json number,title,state` | PR search |
| `gh search code "query"` | Code search |
| `gh extension list` / `gh extension install <repo>` | CLI extensions |
| `gh alias set <name> <expansion>` | Command aliases |
| `gh config get <key>` / `gh config set <key> <val>` | gh configuration |

## git side (quick reference)

| Command | Purpose |
| --- | --- |
| `git status -sb` / `git branch -a` / `git remote -v` / `git log -n 5 --oneline` | Fase Zero probes |
| `git fetch --all --prune` / `git pull --rebase` | Sync before branching |
| `git switch -c <type>/<issue>-<slug>` | Issue-named branch |
| `git commit -F <file>` | Density-compliant commit (see density-templates.md) |
| `git tag -a` / `git push origin <tag>` | Annotated release tags |
| `git revert <sha>` / `git cherry-pick <sha>` | Safe undo / hotfix backport |
| `git worktree add` (via `using-git-worktrees`) | Isolation |
