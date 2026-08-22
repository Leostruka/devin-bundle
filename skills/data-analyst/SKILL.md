---
name: data-analyst
description: Use when the user asks to query a database, analyze data, create charts/visualizations, explore data patterns, or asks business questions about data. Replicates Devin cloud's Data Analyst Agent (DANA) for the CLI — SQL-first exploration, schema-aware querying, and seaborn-style visualizations via MCP data sources.
---

# Data Analyst (CLI replica of DANA — Data ANAlyst Agent)

## What this replicates

Cloud Devin has a **Data Analyst Agent** (DANA) — a specialized agent
optimized for querying databases, analyzing data, and creating
visualizations. It maintains a "Database Knowledge" note with schema
docs, auto-references it before queries, and outputs formatted tables,
charts, and plain-English interpretations.

The CLI has no "Data" agent mode. This skill fills that gap by
providing the DANA workflow as an invocable procedure using MCP data
sources already configured in `mcp_config.json`.

**Sources:**
- docs.devin.ai/work-with-devin/data-analyst (DANA overview)
- docs.devin.ai/use-cases/gallery/dana-slack-data-analyst (Slack usage)
- docs.devin.ai/release-notes/2025 (DANA release)
- devin.ai/ai-data-analyst-1/ (build-your-own guide)

## When to Use

- "Query the database for X"
- "How many users signed up last week?"
- "Show me a chart of daily revenue"
- "Analyze patterns in the orders table"
- "What's the churn rate by cohort?"
- Any SQL/data analysis task against an MCP-connected data source

## When NOT to Use

- No MCP data source is configured — DANA requires a connected database
- The question is about code, not data — use `deep-mode` or `grep`
- The task needs code changes, not analysis — use Normal mode
- Quick file inspection (CSV/JSON on disk) — use `read` + `exec` directly

## Prerequisites

1. At least one MCP data source configured in `mcp_config.json`
   (PostgreSQL, Redshift, Snowflake, BigQuery, SQLite, etc.)
2. Verify connectivity: `mcp_list_tools` for the data source server
3. If no data source is configured, say so and stop — do not guess
   schema or fabricate data

## Procedure

### Step 1 — Schema discovery (Database Knowledge)

DANA maintains a "Database Knowledge" note. In the CLI, build it
on-the-fly:

1. `mcp_call_tool` to list tables (`SELECT table_name FROM
   information_schema.tables` or the MCP's schema tool)
2. For relevant tables, describe columns (`DESCRIBE <table>` or
   `SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name = '<table>'`)
3. Cache findings in a file: `write` to `.devin/db-schema.md`
4. On subsequent queries, `read` `.devin/db-schema.md` first — only
   re-discover if the schema may have changed

Output: schema doc with table names, columns, types, and relationships.

### Step 2 — Query formulation

1. Translate the user's natural-language question into SQL
2. Start with a `SELECT ... LIMIT 10` to validate the query and
   preview results
3. Check for:
   - Correct table joins (use schema doc from Step 1)
   - Date/time handling (timezone awareness — DANA learns from
     feedback; here, ask the user if timezone is ambiguous)
   - NULL handling (use `COALESCE` or filter explicitly)
   - Performance (add `LIMIT` for exploratory queries)

Output: validated SQL query + preview results.

### Step 3 — Full query execution

1. Run the full query via `mcp_call_tool`
2. If the result is large (> 100 rows), write to a file
   (`query-results-<timestamp>.csv`) and summarize in chat
3. Format output as a Markdown table for small results (< 20 rows)

Output: result set (table or file reference) + row count.

### Step 4 — Analysis & interpretation

1. Summarize key findings in plain English
2. Identify patterns, anomalies, or trends
3. If the user asked for metrics, compute them explicitly:
   - Counts, sums, averages, medians, percentiles
   - Rates (conversion, churn, growth) with clear denominators
   - Cohort breakdowns if relevant
4. Compare to expectations: "This is X% higher/lower than typical"

Output: numbered findings with the supporting query/row cited.

### Step 5 — Visualization (if requested)

DANA uses seaborn for charts. In the CLI:

1. Write a Python script to generate the chart:
   ```python
   import matplotlib
   matplotlib.use('Agg')  # headless
   import matplotlib.pyplot as plt
   import pandas as pd
   # ... load data, plot, save
   plt.savefig('chart-<name>.png', dpi=150, bbox_inches='tight')
   ```
2. `exec` the script
3. `read` the PNG to display it inline
4. Report the file path for later reference

Output: chart file path + inline display + 1-sentence caption.

## Output format

```markdown
## Data Analysis: <question>

### Schema used
- `<table>`: <columns relevant to this query>

### Query
```sql
<SQL>
```

### Results
<Markdown table or file reference>

### Findings
1. <finding with data citation>
2. ...

### Chart
<if requested: file path + inline image>
```

## CLI-specific notes

- No persistent Database Knowledge: cloud DANA persists schema docs
  across sessions. The CLI caches to `.devin/db-schema.md` — check
  if it exists, re-discover if stale.
- No Slack integration: cloud DANA responds in Slack threads. The
  CLI outputs to the terminal; use `write` for large results.
- MCP-dependent: this skill only works if a data MCP server is
  configured. Check `mcp_config.json` and `mcp_list_servers` first.
- No auto-feedback learning: cloud DANA learns from user corrections
  ("remember that 'active user' means logged in within 7 days"). The
  CLI requires the user to update `.devin/db-schema.md` manually or
  tell the agent in-session.
- Schema safety: never run `DROP`, `DELETE`, `UPDATE`, `INSERT`, or
  any mutating SQL unless the user explicitly asks. DANA is
  read-only by design; this skill follows the same constraint.
