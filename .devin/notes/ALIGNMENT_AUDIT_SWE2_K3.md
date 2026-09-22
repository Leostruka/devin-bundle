# Ecosystem Alignment Audit — SWE-2 / K3

Date: 2025-12-19 · Scope: static deep-read, non-destructive. No files modified.

## Verdict (1 line)

Mapping integrity is clean (58/58/58, 9 hooks, single source); the debt is in **cross-skill wiring** (7 confirmed gaps) and **one monolithic skill** violating the modes/ pattern the repo itself established.

---

## [REDUNDANCY SCAN]

### Hooks — healthy
- `hooks.v1.json` = 9 bindings, sole source (`config.json.hooks` = `{}`, stale `.devin/hooks.v1.json` absent).
- 18 scripts in `scripts/` not directly bound are **sub-checks orchestrated via `_hookrun.py`** inside the 9 consolidated guards — not orphans. Verified: `pre-exec-guard` → architecture-gate, check-ai-signature, check-push-green, destructive-gate, validate-tool-args; `post-exec` → context-pressure, memory-post-exec, silent-error-review; `user-prompt` → behavioral-nudge, memory-retrieval; `stop-guard` → check-ai-signature, refine-review-prompt, memory-stop; `session-start` → context-budget.
- `render-user-hooks.py`: 0 inbound refs — standalone install utility (renders hooks.v1.json → user-level config.json). **Keep, but document** or move to `install/` semantics; it is not dead code.

### Skills-as-hooks — none found
No skill duplicates hook enforcement (verification gates live in hooks + `gates`/`code-review` skills as docs, not duplicated logic).

### Mermaid validation — triple implementation ⚠
| Implementation | Location |
|---|---|
| `scripts/validate-mermaid.py` | pre-write hook (bound) |
| `scripts/mermaid-parse-check.js` | unbound, referenced in CI pathing |
| `skills/obsidian-workflow/scripts/validate_mermaid.py` | skill-local copy |
| `skills/obsidian-workflow/validate_wiki_*.py`, `find_orphan_pages.py` | skill-local validators |

Action: unify on one mermaid validator; obsidian copies should import or call the canonical script.

### Extensions — no overlap
PlantUML (`diagram-tools`) vs Mermaid (inline/hook) is **already disambiguated** in `architecture-diagrams/SKILL.md` (physical artifact vs embedded) — user's example is a false positive.

### Brain/Muscle boundary ⚠
31 script files live inside `skills/` (obsidian-workflow: 6+ top-level `.py`; grilling, dispatching-parallel-agents, devin-config, knowledge-modeling, security, mcp-governance, memory-management, youtube-fetcher, context7, brag ship `scripts/` dirs). Per the bundle's own convention (`skills/`=brain, `extensions/`=muscle), shared/executable logic should live in extensions. Skill-scoped helpers are defensible; `obsidian-workflow`'s six loose root-level `.py` files are not.

---

## [MAPPING & ROUTING]

- `manifest.json` ↔ `skills/` disk ↔ README/TOOLS-MAP: **58/58/58**, zero drift both directions.
- Hook bindings ↔ scripts: 9/9 resolve.

### Routing-collision candidates (description keyword overlap ≥6)
| Pair | Shared tokens | Risk |
|---|---|---|
| `planning` ↔ `execution` | implementation, plan, spec, task, tickets, written (8) | "execute this plan" can hesitate between the two; `intake` and `ask-bundle` add 6-token overlap each — a 4-way cluster around plan→ticket→execute |
| `memory-management` ↔ `self-improvement` | session, rules, capturing, deciding, whether (7) | "remember this pattern" ambiguous |

Mitigation (next session): sharpen the `Use when…` boundaries — `planning` owns *authoring* specs/tickets; `execution` owns *running* them; `intake` owns *sizing/splitting*; `ask-bundle` is the meta-router and should defer, not compete.

---

## [CROSS-SKILL WIRING]

Confirmed gaps (grep count = 0 in the source skill):

| # | Source skill | Missing wire | Why it matters |
|---|---|---|---|
| 1 | `teach` | → `computer-use` | Stateful tutoring can't see the student's screen — verify the learner actually did the exercise (user's example, confirmed: 0 refs) |
| 2 | `teach` | → `media-tools`/`creative-engineering` | Lessons are HTML artifacts; the aesthetics KB + grainrad/ascii_mancer can generate visual teaching aids |
| 3 | `debugging` | → `computer-use` | GUI/runtime bugs need screenshots/UIA; skill currently shell-only |
| 4 | `data-analyst` | → `architecture-diagrams`/mermaid | Analysis output never routed to diagram generation for reporting |
| 5 | `code-review` | → `security`/`a11y-audit` | Review doesn't escalate to the specialist audits on relevant diffs |
| 6 | `e2e-testing` | → `computer-use` | UI e2e on desktop apps can't drive the screen |
| 7 | `impeccable` | → `a11y-audit`/`creative-engineering` | UI polish skill ignores both the audit and the aesthetics KB |
| 8 | `project-bootstrap` | → `devin-config`/`mcp-governance` | New-project setup doesn't wire repo's own config skills |

Already wired (verified, do NOT re-add): teach→research+context7, prompt-compiler→knowledge-modeling, creative-engineering→media-tools+tooooools.json, operate-spline→computer-use (fallback), observability-quality→testing+context7.

---

## [SWE-2 / K3 HYGIENE]

### Reward-hacking surface
- **TDD is documented, not enforced.** `testing`/`execution`/`planning` skills mention write-failing-test-first, but no hook blocks an impl-only PR path; `stop-guard` checks AI-signature + refine-review, not test evidence. `validate-refinement-evidence.py` exists but is only wired inside self-improvement flows, not general execution.
- **verify-before-completion** exists as a *global* skill, not a repo skill — repo has `gates` + `code-review` + hook checks. Acceptable, but the repo skill set doesn't mirror the anti-"claim done" gate locally.

### K3 context hygiene
- `skills/obsidian-workflow/SKILL.md` = **69,941 bytes (~17K tokens) monolith** — biggest file in the repo, loaded wholesale on invocation while `self-improvement`, `ask-bundle`, `planning`, `testing`, `writing-skills`, `code-review` already use the `modes/` deferred-load pattern this repo established. Clear outlier.
- `dispatching-parallel-agents/SKILL.md` 42KB — second outlier, though it carries scripts/ dir.
- Always-loaded surface is lean: manifest purposes ≈ 12.6KB (~3.2K tokens) for 58 skills; AGENTS.md 11.2KB. Good.
- Knowledge bases correctly deferred: `aesthetics/index.json` alias-map + per-archetype .md (272KB total, load-on-demand); `creative_tooooools.json` 16 entries.

---

## Tactical Execution Plan (DAG)

```
T1 [no deps]  Unify mermaid validators → scripts/validate-mermaid.py canonical;
              obsidian-workflow/scripts/validate_mermaid.py becomes caller.
T2 [no deps]  Split obsidian-workflow/SKILL.md → modes/ (build|reorganize|audit|compare),
              matching the established deferred-load pattern.
T3 [no deps]  Sharpen manifest purposes for the 4-way cluster
              (planning/execution/intake/ask-bundle) + memory-management/self-improvement.
T4 [no deps]  Wire gaps #1–#8: add 1-line "invoke X when Y" rules in the 8 source SKILL.mds.
T5 [dep: T4] Update TOOLS-MAP.md routing notes where new wires change boundaries.
T6 [no deps]  Move obsidian-workflow loose .py files into scripts/ subdir (boundary).
T7 [dep: all] Audit pass: manifest sync + hooks resolve + CI green.
```

Sequencing: T1–T4, T6 parallel-safe (disjoint files) → T5 → T7 gate.
