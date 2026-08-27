---
name: jira
description: Use when the user asks to interact with Jira — search issues, read or update tickets, transition status, add comments, list projects, or run JQL. Routes operations through the Atlassian Rovo MCP server (mcp__atlassian__* tools).
allowed-tools:
  - mcp_call_tool
  - mcp_list_tools
  - ask_user_question
---

# Jira operations via Atlassian Rovo MCP

This skill routes Jira interactions through the **Atlassian Rovo MCP server** (`atlassian`), configured at **user scope** via `devin mcp add atlassian -s user https://mcp.atlassian.com/v1/mcp/authv2` + `devin mcp login atlassian`. The config lives in `%APPDATA%\devin\mcp_config.json` so it works in any project directory. All operations respect the authenticated user's Jira permissions and scopes (`read:jira-work`, `write:jira-work`).

## Prerequisites

- MCP server `atlassian` must be configured (`devin mcp list` shows it).
- OAuth completed (`devin mcp login atlassian` if expired).
- Jira Cloud only (the official Rovo MCP does not support Server/Data Center).

## Known site (this user)

- **cloudId:** `38e12517-1995-4445-8efd-27a717f131dc`
- **site:** `guilhermerissi04112006.atlassian.net`
- **project:** `PW` — "Fingertech" (software, next-gen), id `10033`
- **issue types:** Subtarefa(10039), Epic(10040), Tarefa(10041), História(10042), Função(10043), Bug(10044), Test(10045), Refactor(10046), Security(10047)

Pass `cloudId: "38e12517-1995-4445-8efd-27a717f131dc"` to every Jira tool call. If a new site is added, run `getAccessibleAtlassianResources` and update this section.

## Tool namespace

All Jira tools are exposed under the `atlassian` MCP server as `mcp__atlassian__<tool>`. Call them via `mcp_call_tool` with `server_name: "atlassian"`.

To discover the current tool set at runtime:

```
mcp_list_tools  ->  server_name: "atlassian"
```

## Core operations

### 1. Discover available tools
```
mcp_list_tools(server_name="atlassian")
```
Use this first in a new session to confirm the exact tool names (Atlassian may add/rename tools between releases).

### 2. List visible projects
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="getVisibleJiraProjects",
  arguments={}
)
```

### 3. JQL search
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="searchJiraIssuesUsingJql",
  arguments={"jql": "project = PROJ AND status = Open ORDER BY created DESC", "maxResults": 25}
)
```
Common JQL patterns:
- My open issues: `assignee = currentUser() AND statusCategory != Done`
- Sprint issues: `project = PROJ AND sprint in openSprints()`
- Recently updated: `project = PROJ AND updated >= -7d ORDER BY updated DESC`
- Blocked: `project = PROJ AND status = Blocked`

### 4. Get a single issue
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="getJiraIssue",
  arguments={"issueKey": "PROJ-123"}
)
```

### 5. Create an issue
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="createJiraIssue",
  arguments={
    "projectId": "<numeric id from getVisibleJiraProjects>",
    "issueTypeId": "<id from getJiraProjectIssueTypesMetadata>",
    "summary": "Short title",
    "description": "Markdown or ADF description"
  }
)
```
Always fetch project + issue type metadata before creating — IDs are numeric, not string keys.

### 6. Edit an issue
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="editJiraIssue",
  arguments={"issueKey": "PROJ-123", "summary": "Updated title"}
)
```

### 7. Transition status
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="transitionJiraIssue",
  arguments={"issueKey": "PROJ-123", "transitionId": "<id>"}
)
```
Transition IDs are workflow-specific. Fetch them via the issue's available transitions before calling.

### 8. Add a comment
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="addCommentToJiraIssue",
  arguments={"issueKey": "PROJ-123", "comment": "Comment text in Markdown"}
)
```

### 9. Link two issues
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="createIssueLink",
  arguments={
    "issueKey": "PROJ-123",
    "linkedIssueKey": "PROJ-456",
    "linkTypeId": "<id from getIssueLinkTypes>"
  }
)
```

### 10. Worklog (time tracking)
```
mcp_call_tool(
  server_name="atlassian",
  tool_name="addWorklogToJiraIssue",
  arguments={"issueKey": "PROJ-123", "timeSpent": "2h", "comment": "Refactored auth module"}
)
```

## Workflow patterns

### Triage an issue end-to-end
1. `getJiraIssue(issueKey)` — read full context
2. `searchJiraIssuesUsingJql` — find related/blocked issues
3. Read the codebase (`grep`, `read`) to understand the change
4. Implement the fix
5. `addCommentToJiraIssue` — post a summary of what was changed
6. `transitionJiraIssue` — move to Review/Done

### Create a ticket from a finding
1. `getVisibleJiraProjects` — confirm project ID
2. `getJiraProjectIssueTypesMetadata` — pick issue type
3. `createJiraIssue` — with summary + description referencing the code location
4. Confirm the created key to the user

## Safety rules

- **Never transition or delete without user confirmation.** Use `ask_user_question` before destructive state changes.
- **Write operations need explicit user intent.** Don't auto-comment or auto-transition because a task "looks done".
- **Rate limits:** Free 500/hr, Standard 1k/hr, Premium/Enterprise up to 10k/hr. For bulk operations, batch and pause on 429.
- **No secrets in arguments.** The MCP server holds the OAuth token; never pass tokens, passwords, or API keys in tool arguments.

## When this skill does NOT apply

- **Jira Server/Data Center:** the official Rovo MCP is Cloud-only. Use `sooperset/mcp-atlassian` (self-hosted) and a different skill.
- **Confluence-only operations:** the same `atlassian` server exposes Confluence tools, but prefer a dedicated `confluence` skill if one exists.
- **Bulk exports / reporting:** the MCP is not designed for large dumps; use the REST API directly for those.

## Cross-skills

- Use `triage` when moving issues through a triage state machine.
- Use `planning-pipeline` to turn Jira issues into specs or tickets.
- Use `implement` once a Jira ticket is ready for code changes.

## Troubleshooting

- **`mcp_list_tools` returns empty:** run `devin mcp login atlassian` to refresh the OAuth token.
- **403 / permission denied:** the authenticated user lacks the Jira project permission; check with the Jira admin, not Devin.
- **429 rate limit:** pause for 60s, reduce batch size, or upgrade the Atlassian tier.
- **Tool name not found:** Atlassian renames tools between releases; always call `mcp_list_tools` first and use the exact returned name.
