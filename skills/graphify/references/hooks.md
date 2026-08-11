# graphify reference: commit hook and agent rule integration

Load this when the user asked to install the post-commit hook or wire graphify into a project's agent rules.

## For git commit hook

Install a post-commit hook that auto-rebuilds the graph after every commit. No background process needed - triggers once per commit, works with any editor.

```bash
graphify hook install    # install
graphify hook uninstall  # remove
graphify hook status     # check
```

After every `git commit`, the hook detects which code files changed (via `git diff HEAD~1`), re-runs AST extraction on those files, and rebuilds `graph.json` and `GRAPH_REPORT.md`. Doc/image changes are ignored by the hook - run `/graphify --update` manually for those.

If a post-commit hook already exists, graphify appends to it rather than replacing it.

---

## For native agent rules integration

To make graphify always-on in Devin CLI sessions, add a `## graphify` section to the project's `AGENTS.md`:

```bash
graphify agents install  # for Devin CLI AGENTS.md (use this in Devin projects)
# graphify the agent install  # for other agents that use AGENTS.md
```

This writes a `## graphify` section that instructs the agent to check the graph before answering codebase questions and rebuild it after code changes. No manual `/graphify` needed in future sessions.

```bash
graphify the agent uninstall  # remove the section
```
