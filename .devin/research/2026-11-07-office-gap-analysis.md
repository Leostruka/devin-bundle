# Office gap analysis - specialist coverage vs world-class bar

Date: 2026-11-07 · Branch: `office-specialists-wave` · Method: map every
office function to existing agents/skills/extensions; rank uncovered
functions by engagement value; ship the top gaps as agent profiles.

## 1. Coverage matrix (function -> surface)

| Office function | Agent profile | Skill(s) | Extension |
|---|---|---|---|
| Product management | product-manager | - | - |
| Architecture | architect, tech-lead | architecture, codebase-design | - |
| Implementation | implementer | writing-plans, using-git-worktrees | - |
| Review (2-axis) | reviewer, repo-reviewer | code-review | - |
| QA / verification | qa-ci | gates, autonomous-gates, verification-before-completion | - |
| Security | security-auditor, red-team-lead | security-audit, secure-defaults-check | - |
| Debugging | debugger | debugging, forensic-debugging | - |
| Copy / docs | copywriter | writing-skills, de-slop | - |
| Design direction | art-director | frontend-design, impeccable, a11y-audit | design-intelligence, design_lint |
| Program management | scrum-master, chief-of-staff | issue-tracker, triage-labels | agent-rts, rtsd |
| Research | researcher | research, agent-reach, context7 | code-graph, scrape-tools |
| Sentinel / observe | sentinel | - | - |
| Self-improvement | (controller) | self-improvement, continuous-improvement | harness-tree |
| Data analysis | **NONE** | data-analyst | - |
| SRE / incident response | **NONE** | forensic-debugging (partial) | system-control |
| UX research | **NONE** | a11y-audit (partial) | - |
| Performance engineering | **NONE** | performance, web-perf-checklist | - |

## 2. Gap rationale

Skills without agent profiles are the cheapest real gaps: the persona,
delegation contract, and tool whitelist already exist as conventions;
the profile just makes the function dispatchable via `run_subagent`.

- **data-analyst**: `skills/data-analyst` ships SQL-first exploration +
  seaborn-style visualization; no profile means every analytics task
  falls back to the controller or generic subagent. High-frequency
  office function.
- **sre**: incident response, deploy verification, rollback decisions,
  postmortem drafting. `forensic-debugging` + `system-control` cover
  pieces; no role owns the ops loop.
- **ux-researcher**: usability heuristics, accessibility audits beyond
  a11y-audit's checklist, journey tracing. art-director specifies;
  nobody researches users.
- **performance-engineer**: `performance` + `web-perf-checklist`
  skills exist; no profile owns budgets, profiling, regression
  triage.

Rejected: DBA (database skill is thin, demand unproven), legal/compliance
(security-auditor covers the audit surface), marketing (copywriter
covers), data-engineer (overlaps data-analyst + implementer).

## 3. Methodology layer (already covered - no new work)

World-class delivery bar exists in layers: `gates` +
`autonomous-gates` + `verification-before-completion` (acceptance),
agency pipeline docs/01-07 (spec chain), orchestrator_prompts v4 TEAM
guards (execution), thermo-nuclear review lanes (quality),
install-ledger + drift ledger (ops hygiene). Gap analysis found no
missing methodology layer worth a new doc; the binding constraint was
persona coverage, addressed here.

## 4. Wave plan

- O-01: this analysis + 4 agent profiles + VALID_PROFILES + manifest
  counts (agents 17 -> 21).
- Follow-ups (issues, not this wave): held-out benchmark of new
  profiles on real tasks; consider `dba` only if database skill grows.
