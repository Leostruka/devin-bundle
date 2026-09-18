# Mode: Refine (self-improvement loop)

### When to Use

- A failure pattern recurs 2+ times in a session — capture the fix as a skill or rule
- A tactic works well and should be reusable — promote it to a skill
- The user asks "make yourself better at X" or "remember this lesson"
- After completing a complex task (3+ todo items) — review trajectory for generalizable lessons
- Before `/compact` — extract lessons before context is lost
- **Auto-triggered by `refine-review-prompt.py` Stop hook** when a `.refine-pending` marker exists

### Auto-Trigger Mechanism

The `refine-review-prompt.py` Stop hook checks for a `.refine-pending` marker
file at session end. If present, it injects a reminder to run this skill before
the session stops.

**To mark a session as complex (auto-trigger refine at end):**
```
write .devin/.refine-pending "3+ todos completed: <brief task description>"
```

The agent should write this marker when completing a 3+ step task. The Stop
hook will then prompt refinement review before the session ends.

**After refinement is complete, remove the marker:**
```
exec: rm .devin/.refine-pending
```

### When NOT to Use

- One-off failure, not a pattern — just fix it and move on
- Less than 2 occurrences — insufficient evidence for a pattern
- The lesson is task-specific, not generalizable

### Source

Adapted from PrimeAgent's Continual Harness (PrimeIntellect, arXiv:2605.09998
— Karten et al., Princeton). PrimeAgent's `/refine` reads the agent's
trajectory and applies small, evidence-backed CRUD edits to harness state
(prompts, skills, memory, sub-agent specs). The base system prompt remains
immutable. Rollback is supported by refinement ID.

Key finding from the paper: Continual Harness "substantially reduces
button-press cost relative to the minimalist baseline and recovers a majority
of the gap to a hand-engineered expert harness" on Pokémon Red and Emerald.

### Core Principle

**Small, evidence-backed edits in a cyclic, falsifiable loop.** Not a rewrite.
Each refinement is one targeted update — a new skill, a rule addition, a memory
entry — based on what actually happened in the trajectory, not on speculation.
Every cited failure must be reproducible; every claimed improvement must be
validated against held-out evidence, not self-chosen tests.

> **Cross-skill:** For the full FASE 0 deep-research + 10-step improvement loop
> with held-out validation and unlazy gates, invoke `/continuous-improvement`.
> This mode reuses its anti-cheat principles (A1-A5) and convergence criterion.

**Convergence criterion:** reach the optimal operating conjuncture for the
bundle's primary model (`BUNDLE_DEFAULT_MODEL` / `data/bundle-models.json`,
`default_parent_model`) and the max/medium subagent models (`BUNDLE_MAX_MODEL` /
`BUNDLE_MEDIUM_MODEL` / `data/bundle-models.json`, `max_role_model` /
`medium_role_model`) — per verified sources (docs.devin.ai, cognition.com,
z.ai, AI labs) and practical experience recorded in the bundle history.

**NÃO dar push ou commit.** All changes stay local for user validation.

### What Can Be Refined

| Harness element | Location | How to edit |
|---|---|---|
| Skill (reusable workflow) | `~/.config/devin/skills/<name>/SKILL.md` | `write` or `edit` |
| Rule (always-on constraint) | `~/.config/devin/AGENTS.md` | `edit` (append to relevant section) |
| Subagent profile | `~/.config/devin/agents/<name>.md` | `write` or `edit` |
| Hook (lifecycle logic) | `~/.config/devin/hooks.v1.json` | `edit` (add event handler) |
| Script (executable helper) | `~/.config/devin/scripts/<name>.py` | `write` |
| Config (model, theme, hooks) | `~/.config/devin/config.json` | `edit` (change fields, never secrets) |
| MCP server config | `~/.config/devin/mcp_config.json` | `edit` (add/remove servers, review per Rule 13) |
| Memory (project-specific) | `.devin/memory/<name>.md` | `write` |

### What Cannot Be Refined (anti-cheat, non-negotiable)

- **The base system prompt** — Devin CLI's core prompt is immutable. Refine
  only the harness layer around it (skills, rules, agents, hooks).
- **Repository security policies** — never modify CI configs, branch
  protection, or compliance settings to "fix" a failure.
- **Credentials** — never store secrets in skills or rules (Rule 19).
- **AI signatures in deliverables** — never add, always remove (Rule 2).
- **`tests/held-out/`** — if it exists, the agent cannot see or write these
  tests. They are the independent validation set (P-A2).
- **These anti-cheat principles themselves** — auto-reference is prohibited.

### Anti-Cheat Principles (non-negotiable)

| # | Principle | Why | Source |
|---|-----------|-----|--------|
| A1 | **Reproducible evidence** — every cited failure must include an exact command or tool-call that reproduces it | 25% of self-improvement runs invent failures that never occurred ("phantom guardrails") | arXiv:2607.13083 |
| A2 | **Held-out validation** — improvements measured only with tests the agent chose are suspect; validate with `tests/held-out/` | 47-74% of self-improvement gains are illusory | ICLR 2026 Workshop |
| A3 | **Verify with tools** — never deduce state; use `read`, `exec`, `grep`, `glob` before asserting | Deductions fail silently; tool output fails loudly | Rule 17 |
| A4 | **No phantom guardrails** — if you cannot reproduce a cited failure with a command, it is not a pattern, it is a guess | — | Rule 15 |
| A5 | **Real metric, not proxy** — "reduced failures by N", "faster by Xs"; not "felt easier" | Proxies mask stagnation | arXiv:2607.25152 |

### FASE 0 — Deep Research (before the loop, mandatory)

Each step produces a concrete output. Do not advance without completing the
previous.

#### P0.1 — Research Devin CLI capabilities
- `web_search` + `webfetch` on docs.devin.ai, github.com/cognition-ai
- Confirm: hooks, skills, subagents, config.json, lifecycle events
- Output: list of confirmed capabilities with URLs

#### P0.2 — Confirm against the real bundle structure
- `exec`, `read`, `grep`, `glob` on the local bundle
- Verify that what the docs say matches what is installed
- Output: doc-vs-disk table (match / mismatch)

#### P0.3 — Research verified sources (verify, don't assume)
- `web_search` for: arXiv papers, official docs (z.ai, cognition.com, anthropic.com)
- **Ensure they are reliable**: verify domain, authors, publication date
- Reject: blogs without primary source, Medium posts without citation, LLM-generated content
- Output: list of sources with URL, author, date, and verified citation

#### P0.4 — Research best practices
- Topics: prompt engineering for the bundle primary model (`BUNDLE_DEFAULT_MODEL` /
  `data/bundle-models.json`), context window management (per `data/bundle-models.json`),
  subagent fan-out, cache stability, native tool-use, lost-in-the-middle mitigation
- Priority sources: arXiv, docs.z.ai, cognition.com/blog, docs.devin.ai
- Output: list of practices with evidence (paper/doc supporting each)

#### P0.5 — Don't repeat past errors (git history)
- `git log --oneline -30` + `git log --diff-filter=D` to see what was deleted/reverted
- Read fix/revert commits to understand past breakages
- Output: list of past errors with commit hash and lesson

#### P0.6 — Review current state
- `python audit.py` — capture current errors/warnings
- `python -m pytest tests/held-out/ -q` — test baseline (if held-out exists)
- `read` key files (AGENTS.md, docs/MODEL-GUIDE.md, config.json)
- Output: state snapshot (errors, tests passing, current config)

#### P0.7 — Synthesize
- Cross P0.1–P0.6: what docs say × what disk has × what practices recommend × what history teaches
- Output: prioritized list of candidate improvements with evidence

### Cyclic Refinement Loop (10 steps, in order)

Based on Constitutional AI (generate→critique→revise) + RISE (recursive
introspection) + Six-Step Reframing (NLP) + Deep Research (FASE 0).

#### Step 1 — OBSERVE (verify, don't deduce)
Identify a **concrete, reproducible** failure using tools.
- Command/tool-call that reproduces the failure: `___` (mandatory)
- Observed output: `___`
- If you cannot reproduce it → **stop**. Not a failure, a deduction (A4).

#### Step 2 — CRITIQUE (Constitutional AI critique)
Evaluate the failure against AGENTS.md principles.
- Which rule was violated? `___`
- NLP reframing key question: **"What is the positive intent behind the
  current behavior?"** Separate behavior from intent.
  - Current behavior: `___`
  - Positive intent: `___`
  - Why the behavior fails despite the intent: `___`

#### Step 3 — GENERATE ALTERNATIVES (Reframe + Promptbreeder)
Generate **at least 3** alternative behaviors that:
- Preserve the positive intent
- Fix the reproducible failure
- Introduce no new rule violation

Classify the refinement target (from existing Refine classification):

| Pattern type | Refinement target | Evidence needed |
|---|---|---|
| "I keep forgetting to do X" | New rule in AGENTS.md | 2+ failures where forgetting X caused the issue |
| "This workflow is reusable" | New skill in skills/ | 1+ successful execution + clear trigger conditions |
| "This subagent needs better instructions" | Edit agent profile | 1+ case where the profile's gap caused a bad result |
| "This check should be automatic" | New hook in hooks.v1.json | 1+ case where a manual check caught a critical issue |
| "This helper is useful" | New script in scripts/ | 1+ case where inline code solved a problem worth keeping |

| Alt | Description | Risk | Prob. of real improvement |
|-----|-------------|------|---------------------------|
| 1   |             |      |                           |
| 2   |             |      |                           |
| 3   |             |      |                           |

#### Step 4 — REVISE (Revise)
Apply the alternative with highest probability of real improvement.
- Draft the smallest possible edit:
  - **New skill:** minimal SKILL.md with frontmatter, when-to-use, core steps
  - **New rule:** one negative-constraint bullet, appended to the relevant AGENTS.md section
  - **Profile edit:** one paragraph or bullet, not a rewrite
  - **Hook:** one event handler, not a restructure
- Record evidence in the refinement:
  ```
  <!-- Evidence: <session date> — <what happened> — <why this refinement fixes it> -->
  ```
  For skills, add an `## Evidence` section at the bottom.
- Apply with `write` (new file) or `edit` (existing file). For AGENTS.md,
  use `edit` to append within the correct section — never restructure the file.
- File(s) changed: `___`
- Diff summary: `___`

#### Step 5 — VALIDATE (Held-out, anti-cheat A2)
- Agent-chosen test: `___` → result: `___`
- Held-out test (if `tests/held-out/` exists): `___` → result: `___`
- If held-out fails → **discard change**, return to Step 3
- If no held-out exists → mark improvement as "not validated", not "complete"
- After applying, verify the edit landed:
  - For a skill: `skill list --path ~/.config/devin` — confirm it appears
  - For a rule: re-read the AGENTS.md section — confirm it's in the right place
  - For a hook: validate JSON syntax — `python -m json.tool hooks.v1.json`
  - For a script: run `python <script> --help` or a dry-run
  - For config.json/mcp_config.json: `python -m json.tool config.json` — validate JSON syntax

#### Step 6 — FUTURE PACE (NLP)
Project the improvement into 3 hypothetical future scenarios:
- Scenario 1: `___` → does the improvement help? `___`
- Scenario 2: `___` → does the improvement help? `___`
- Scenario 3: `___` → does the improvement help? `___`
- If <2 scenarios benefit → too specific, reconsider

#### Step 7 — ECOLOGICAL CHECK (NLP)
Does the improvement cause side effects?
- In other rules? `___`
- In other hooks/skills? `___`
- In the context window budget (Rule 18)? `___`
- Negative side effect → return to Step 3

#### Step 8 — SIMULATE (Self-evaluation)
Simulate loading the improvements and evaluate own performance.
- `install.ps1 -Force` (or equivalent) to load the changes
- `python audit.py` — confirm 0 errors after loading
- `python -m pytest tests/held-out/ -q` — confirm 0 regressions (if held-out exists)
- Self-evaluation: **how does this modify my logic and operating mode in practice?**
  - What behavior changes when this rule/skill/hook is loaded?
  - What real scenario would execute differently now?
  - Is there conflict with behaviors already optimized for the configured bundle models (`BUNDLE_*_MODEL` / `data/bundle-models.json`)?
- Output: description of expected behavioral impact

#### Step 9 — CLASSIFY (Improved or regressed?)
Classify the result with a description to define direction.
- Compare real metric (Step 5) vs baseline (P0.6)
- Mandatory classification (one option):

| Class | Criterion | Action |
|-------|-----------|--------|
| **MELHOROU** | Real metric improved + held-out passed + no side effects | Repeat loop (Step 1) with next candidate improvement |
| **PIOROU** | Real metric regressed OR held-out failed OR negative side effect | **Revert change** (`git checkout` or manual `edit`), return to Step 3 |
| **NEUTRO** | Metric unchanged + held-out passed + no side effect | Mark "stagnation" (arXiv:2607.25152), try next candidate |
| **INCONCLUSIVO** | Could not measure real impact | Do not declare improvement. Reformulate metric or discard |

- Output: class + justification with numbers

#### Step 10 — REPEAT OR CONVERGE
- If classified **MELHOROU** or **NEUTRO**: return to Step 1 with the next
  candidate improvement from the synthesis (P0.7)
- If classified **PIOROU**: reverted in Step 9, return to Step 3 with a
  different alternative
- **Stopping criterion (convergence)**: when all candidate improvements from
  P0.7 have been applied and classified, and no new reproducible failure is
  found in the current state → conjuncture reached for the configured bundle
  primary and max subagent models (per `BUNDLE_*_MODEL` / `data/bundle-models.json`)
- **NÃO dar push ou commit** — changes stay local for user review

### Anti Early-Stop Reflection (DORA)

Reflection does **not** stop at the first iteration without improvement.

- Iteration without improvement → **reformulate the reflection prompt** before stopping
- Reformulation: change the critique angle (e.g., from "what failed" to
  "what the agent assumed without verifying")
- Max 3 reformulations. After 3 without improvement → stop and record stagnation
- Recorded stagnation is data, not failure (arXiv:2607.25152)

### Final Checklist (before declaring improvement)

- [ ] FASE 0 complete (deep research with verified sources)
- [ ] Failure reproduced with exact command (A1)
- [ ] Positive intent separated from behavior (NLP)
- [ ] 3+ alternatives generated
- [ ] Held-out validated OR marked "not validated" (A2)
- [ ] Future pace: ≥2/3 scenarios benefited
- [ ] Ecological check: no negative side effects
- [ ] Simulation executed (Step 8): install + audit + held-out + self-evaluation
- [ ] Classification assigned (Step 9): MELHOROU/PIOROU/NEUTRO/INCONCLUSIVO
- [ ] Real metric declared (A5), not proxy
- [ ] No anti-cheat principle violated
- [ ] No push or commit made

**If any item fails → the improvement is NOT complete.**

### Output Format

```
MELHORIA: <title>
FASE0_RESEARCH: <verified sources — URLs + citations>
FALHA_REPRODUZIDA: <command> → <output>
REGRA_VIOLADA: <Rule #>
INTENÇÃO_POSITIVA: <text>
ALTERNATIVA_APLICADA: <#> of <N>
HELD_OUT: <passou|falhou|inexistente>
SIMULAÇÃO: <install OK? audit 0 errors? held-out 0 regressions? behavioral impact>
MÉTRICA_REAL: <number/observation vs baseline>
CLASSIFICAÇÃO: <MELHOROU|PIOROU|NEUTRO|INCONCLUSIVO>
ESTADO: <validada|não_validada|estagnada|revertida>
ARQUIVOS_ALTERADOS: <list>
PUSH_COMMIT: <não feito>
```

### Rollback

Each refinement is a file edit. Rollback is:
- `git checkout <file>` if the bundle repo tracks it
- Manual revert via `edit` if not tracked
- For the devin-bundle: `export.ps1` / `export.sh` syncs the bundle, so
  `git diff` shows what changed and `git checkout` reverts

### Reward Hacking Guard (Critical)

PrimeAgent's Continual Harness discovered an exploit in Factorio — it could
spawn resources directly into machines via RCON commands, even with an
explicit prompt saying "don't cheat." Once found, the refinement loop started
optimizing cheating skills instead of legitimate ones (PrimeIntellect blog,
2026-08-05).

**Guardrails for Devin CLI:**
- Refinements must align with AGENTS.md rules. If a refinement would
  circumvent a rule (e.g., "skip verification to go faster"), reject it.
- Refinements must not weaken security: never refine away the AI-signature
  check, the push-green check, or any compliance control.
- If a refinement produces a "shortcut" that bypasses the intended workflow,
  flag it to the user before applying. Shortcuts that skip verification,
  testing, or review are reward hacking, not improvement.
- The user has final approval on any refinement that changes behavior beyond
  adding a new skill. State the proposed change and ask before applying.

### Anti-Patterns

- **Don't refine on a single occurrence.** Two+ instances = pattern. One = noise.
- **Don't rewrite existing skills.** Edit them — add a bullet, fix a step. Full rewrites lose context.
- **Don't refine the base AGENTS.md structure.** Append within sections. Restructuring is a regression risk.
- **Don't refine without evidence.** "I think this would help" is not evidence. "This failed twice because X" is evidence.
- **Don't batch refinements.** One at a time, verify each, then move on. Batching hides which refinement caused which effect.

### Outcome Tracking (Refinement Log)

Every refinement must be logged to `.devin/refinements.log.jsonl` (project) or
`~/.config/devin/refinements.log.jsonl` (global). This enables:
- Reviewing what was refined and when
- Tracking whether a refinement helped or hurt
- Rolling back refinements that degraded performance

#### Log format

Each line is a JSON object:
```json
{"id": "ref-001", "timestamp": "2026-08-15T15:30:00-03:00", "type": "skill", "target": "context-folding", "action": "created", "evidence": "RLM research verified from arXiv:2512.24601", "session": "PrimeAgent verification", "status": "applied", "outcome": null}
```

#### Fields

| Field | Description |
|---|---|
| `id` | Unique refinement ID (incremental: ref-001, ref-002, ...) |
| `timestamp` | ISO 8601 datetime |
| `type` | skill, rule, agent, hook, script, memory |
| `target` | Name/path of the refined element |
| `action` | created, updated, deleted |
| `evidence` | What trajectory event triggered this refinement |
| `session` | Brief session description for context |
| `status` | applied, rolled-back, pending-review |
| `outcome` | null initially; updated later with "helped", "hurt", "neutral" |

#### Updating outcomes

In future sessions, if a refinement is referenced:
- If it helped (task went smoother) → update `outcome` to "helped"
- If it hurt (caused confusion or regression) → update `outcome` to "hurt" and consider rollback
- If no effect → update `outcome` to "neutral"

**Elaborate Stagnation Check (Rule 16):** When updating outcome, ask: "Did a real
metric improve (faster, fewer errors, better quality)?" If only the proxy improved
(felt easier, produced more analysis) but no real metric moved, mark as
"stagnation" not "helped" (arXiv:2607.25152). 47-74% of self-improvement gains are
illusory — proxy metrics improve while real metrics stagnate (ICLR 2026 Workshop).
A refinement that makes the agent feel more productive without measurable improvement
is elaborate stagnation, not progress.

Read the log at session start to load prior refinements:
```
read ~/.config/devin/refinements.log.jsonl
```

#### Rollback by ID

To rollback a refinement:
1. Find the refinement by ID in the log
2. Revert the file (`git checkout <file>` or manual `edit`)
3. Update the log entry: `"status": "rolled-back"`, `"outcome": "hurt"`

### Evidence Summary

| Claim | Source | Status |
|---|---|---|
| Continual Harness reduces button-press cost vs baseline | arXiv:2605.09998 | Verified |
| `/refine` applies small evidence-backed CRUD edits | PrimeAgent blog, GitHub README | Verified |
| Base system prompt stays immutable | PrimeAgent blog + GitHub README | Verified |
| Rollback supported by refinement ID | PrimeAgent blog | Verified |
| Factorio reward hacking via RCON exploit | PrimeAgent blog | Verified |
| Refinement loop optimized cheating after finding exploit | PrimeAgent blog | Verified |

---

