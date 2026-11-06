---
name: criador-de-devin-app
description: Use when turning a recurring intent into a named devin-cli app - a repeatable agent automation with its own name, schedule, prompt and done-when contract. Covers the agentic-app naming framework and the APP.md scaffold.
disable-model-invocation: true
---

# Criador de devin-app

A devin-app is a named, repeatable agent automation: a fixed intent, a
prompt, a cadence and a done-when contract, stored under
`.devin/apps/<slug>/` so it can be re-run, scheduled and audited like the
rest of the bundle.

## Step 1 - Interview (always ask before scaffolding)

Do not guess. If the ask is vague, resolve these first:

- **What does the app do?** One sentence, verb-first ("triage my inbox",
  "watch CI and fix flakes"). If the user cannot say it in one sentence,
  the app is not scoped yet.
- **Corporate agent or human-facing app?** An agent that acts for the
  company (automation) is named and documented differently from an app
  an end-user operates. Agentic App / Agent-Native App / Autonomous
  Copilot are the market terms for the first kind.
- **Inputs and outputs:** what it reads (inbox, issues, feeds, repo
  state) and what it produces (report, PR, comment, commit).
- **Cadence:** on-demand, scheduled (`scheduled-turns`), or triggered by
  an issue becoming unblocked (`afk-loop`).
- **Done-when:** the verifiable end state per run.

## Step 2 - Name it

Pick one strategy; keep the name under ~11 characters so it fits under a
menu icon:

| Strategy | How | Examples |
|---|---|---|
| Sigla that reads as a name | functional acronym pronounced as a person | Eva (Engine Virtual Agent), Mae (Multi-purpose Admin Expert) |
| Function name | direct and corporate-friendly | Sales Coach, Techforce, Triage Desk |
| Short abstract | personality without literal meaning | Kai, Ada, Nova, Luna |
| Formula fallback | `[Action/Specialty] + [connector]` | DevAgent, FinCopilot, TaskBot, Triagem Express |

Slugs are kebab-case and must be unique under `.devin/apps/`.

## Step 3 - Scaffold

Create `.devin/apps/<slug>/APP.md`:

```markdown
# <Name> (<slug>)

intent: <one sentence from step 1>
kind: agentic-app | human-facing
schedule: on-demand | <cron-ish description> | on-issue-unblocked
inputs: <what it reads>
outputs: <what it produces>
done-when: <verifiable end state per run>

## Prompt
<the exact prompt/instruction set each run receives>

## Run log
- <date>: <result link or note>
```

If the app is recurring, register the run path: an `afk-loop` issue for
DAG-driven runs, or a `scheduled-turns` entry for clock-driven runs.
Keep the prompt self-contained - each run must not depend on chat
context to succeed.

## Step 4 - Verify

Dry-run once manually: run the prompt in a fresh session and confirm the
done-when state is actually reachable. An app whose prompt cannot
complete is a doc bug, not a run bug - fix APP.md before scheduling.
