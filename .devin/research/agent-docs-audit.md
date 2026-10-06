# Agent-Docs Audit - devin-bundle

- **Contract**: 02-researcher-agent-docs-audit (track: agent-docs-rag)
- **Date**: 2026-10-05
- **Scope**: all agent-facing documentation surfaces in repo; read-only audit
- **Method**: full inventory (no sampling) via `find_file_by_name`/`read`/`grep`;
  every finding carries `file:line` evidence re-verified in source.

## 1. Surface inventory - 24 surfaces, ~110 files, 100% covered

| # | Surface | Files | Covered |
|---|---|---|---|
| 1 | `AGENTS.md` (root global rules) | 1 | full read |
| 2 | `README.md` (agent-facing parts) | 1 | full read |
| 3 | `CHANGELOG.md` | 1 | head + targeted greps |
| 4 | `LICENSE` / `NOTICE.md` / `SECURITY.md` / `CONTRIBUTING.md` | 4 | existence + LICENSE read |
| 5 | `manifest.json` | 1 | full read (713 lines) |
| 6 | `config.json` | 1 | full read |
| 7 | `hooks.v1.json` | 1 | full read |
| 8 | `mcp_config.json` + `mcp_config.json.example` | 2 | full read |
| 9 | `agents/*.md` | 6 | frontmatter + bodies read |
| 10 | `.devin/agents/*.md` | 5 (4 profiles + README) | full read |
| 11 | `skills/*/SKILL.md` | 75 (67 top-level + 8 nested) | frontmatter all; bodies spot-checked |
| 12 | `docs/` top-level | 0 — **absent** (dissolved to `.devin/docs/`) | verified via glob |
| 13 | `.devin/docs/*` | 7 | all read |
| 14 | `.devin/CONTEXT.md` | 1 | full read |
| 15 | `.devin/global_rules.md` | 1 | full read |
| 16 | `.devin/ARCHITECTURE_MANIFEST.md` | 1 | full read |
| 17 | `.devin/templates/ARCHITECTURE_MANIFEST.md` | 1 | existence verified (AGENTS.md Rule 29 pointer valid) |
| 18 | `data/*.json` | 6 | all read |
| 19 | `.devin/mcp_config.json` | 1 | full read (empty `mcpServers`) |
| 20 | `.devin/hooks.v1.json` | 0 — absent; generated per-project by `project-bootstrap` (`skills/project-bootstrap/modes/setup.md:99`) | verified via glob |
| 21 | `workers/researcher/role.md` | 1 | full read |
| 22 | `scripts/validate-tool-args.py` | 1 | read (VALID_PROFILES, CHECKS, block path) |
| 23 | `audit.py` / `install.ps1` / `install.sh` (doc wiring) | 3 | targeted greps |
| 24 | `skills/writing-skills/{SKILL.md,reference/writing-for-agents.md}` | 2 | full read (criteria source) |

Coverage: 24/24 surfaces = **100%**. 67/67 top-level skill dirs have SKILL.md
with `name:` matching dir and `Use when`-style `description:` (verified via
frontmatter grep, 75/75 files). Test fixtures under `tests/fixtures/` excluded.

## 2. Findings (severity x reach; ranked, Critical first)

| ID | Severity | Reach | Finding | Evidence | Fix class |
|---|---|---|---|---|---|
| DOC-001 | Critical | Every session trusting guardrail docs | TOOLS-MAP claims 19/28 tools have "validator + hook matcher" incl. `run_subagent` (profile + `max_parallel` guard). Reality: `hooks.v1.json` wires only `^exec$` → `pre-exec-guard.py` and `^(write|edit|notebook_edit)$` → `pre-write-guard.py`; `run_subagent` and 12 other validators in `CHECKS` never execute. | `.devin/docs/TOOLS-MAP.md:26,40-43,78`; `hooks.v1.json:2-45`; `scripts/validate-tool-args.py:295-330` | Doc/wiring realign |
| DOC-002 | High | Any `run_subagent` dispatch once wired | `VALID_PROFILES` missing `qa-ci` and `repo-reviewer`; both profiles exist on disk and are referenced by consumers (`qa-ci` dispatched by ask-bundle; `sidekick_profile: "qa-ci"`). Would hard-block dispatches if a matcher is added. | `scripts/validate-tool-args.py:56-60,184-188`; `agents/qa-ci.md:1-4`; `.devin/agents/repo-reviewer.md:1-4`; `data/recipes.json:15`; `README.md:166` | Sync registry |
| DOC-003 | High | Every session using 2-read routing (vision convenience bar) | SKILL-TIERS omits 14 of 67 top-level skills: `ai3d-gen`, `architecture-diagrams`, `creative-engineering`, `fact-check`, `humanizer`, `implement-laya`, `media-tools`, `mesh-utils`, `operate-blender`, `operate-godot`, `prompt-compiler`, `project-orchestrator`, `scrape-tools`, `social-midia` (+8 nested children). `scan` row has no tok value. | `.devin/docs/SKILL-TIERS.md:1-193` (index end-to-end); `skills/` disk listing (67 dirs) | Index completion |
| DOC-004 | Medium | Every installed doc reader | Language drift: 4 of 7 installed `.devin/docs/` files are pt-BR (`SKILL-TIERS`, `MODEL-GUIDE`, `TOOLS-MAP`, `3D-STACK-INSTALL`) while `AGENTS.md`, `DEVIN-CLI-COMPATIBILITY`, `RULES-DIRECTORY`, `AI-CODING-DICTIONARY` are EN; README/CHANGELOG pt-BR; stray pt line inside a skill mode file. Violates vision NFR-4 (English for distributed artifacts). | `.devin/docs/SKILL-TIERS.md:1`; `.devin/docs/MODEL-GUIDE.md:3`; `.devin/docs/TOOLS-MAP.md:1`; `.devin/docs/3D-STACK-INSTALL.md:1`; `skills/self-improvement/modes/improvement-loop.md:165` | Translation pass |
| DOC-005 | Medium | Manifest consumers (audit, installers) | `manifest.docs` lists 7 bare names mixing repo-root docs with `.devin/docs` files; omits `3D-STACK-INSTALL.md`, `DEVIN-CLI-COMPATIBILITY.md`, `RULES-DIRECTORY.md`; carries no paths so the list cannot be resolved unambiguously. | `manifest.json:660-668` vs `.devin/docs/` (7 files) | Manifest resync |
| DOC-006 | Medium | Agents following repo maps | Dead pointers to dissolved root `docs/`: CONTEXT.md "Important files" lists `docs/plans/`; ARCHITECTURE_MANIFEST layout lists `docs/` = reference docs. Root `docs/` does not exist. | `.devin/CONTEXT.md:88`; `.devin/ARCHITECTURE_MANIFEST.md:53-54`; `install.sh:583-610` (source now `.devin/{docs,plans,templates}`) | Pointer update |
| DOC-007 | Medium | Every install (doc ships to devin home) | `3D-STACK-INSTALL.md` is machine-state-specific ("nesta máquina" table, `C:\Program Files\Blender...`, `~/ComfyUI`) yet installs into every consumer's `docs/`. | `.devin/docs/3D-STACK-INSTALL.md:7-23` | Relocate/genericize |
| DOC-008 | Medium | TOOLS-MAP readers, dispatchers | Subagent table says "(7 perfis)" but omits `qa-ci` (8 profiles exist: 2 built-in + 6 custom); VALID_PROFILES caption claims 7 names validated (set actually has 10, missing 2). | `.devin/docs/TOOLS-MAP.md:45-65`; `agents/*.md`; `.devin/agents/*.md`; `scripts/validate-tool-args.py:56-60` | Table resync |
| DOC-009 | Medium | Context budget on invocation | 3 SKILL.md bodies exceed the ~10KB router budget: `obsidian-workflow` ~17485 tok (~70KB), `dispatching-parallel-agents` ~10590 tok (~42KB), `grilling` ~3508 tok (~14KB). | `.devin/docs/SKILL-TIERS.md:28,76,85`; `skills/writing-skills/SKILL.md:33-34` | Body slimming/defer |
| DOC-010 | Low | Doc readers | AGENTS.md size claims diverge 3 ways: README "~11KB" (~2750 tok), SKILL-TIERS "~4900 tok", TOOLS-MAP "~5605 tok (2.80%)". | `README.md:109`; `.devin/docs/SKILL-TIERS.md:172`; `.devin/docs/TOOLS-MAP.md:189` | Single source of truth |
| DOC-011 | Low | mcp-governance readers | Lone surviving personal-name citation in skills: "Pocock, 'Context Windows Explained for Coding Agents'". | `skills/mcp-governance/SKILL.md:77` | De-personalize cite |
| DOC-012 | Low | scan users | `scan` offers `(or subagent_explore)` as dispatch option — contradicts free-tier never-use policy. | `skills/scan/SKILL.md:39`; `AGENTS.md:147`; `.devin/docs/MODEL-GUIDE.md:64-69` | Reword pointer |
| DOC-013 | Low | Repo readers | CHANGELOG retains user paths/names: `C:\Users\Fingertech`, `C:\Users\leand`, `C:/Users/leand`, Matt Pocock (x2). | `CHANGELOG.md:114,566,575,709,774` | Mask history |
| DOC-014 | Low | Distribution consumers | Identity coupling persists despite `data/bundle-identity.json` placeholders: `Leostruka` hardcoded in README badges/clone URLs/license line and LICENSE copyright. | `README.md:3,15,23,587`; `LICENSE:3`; `data/bundle-identity.json:2-6` | Placeholder expansion |
| DOC-015 | Low | Frontmatter consistency | 4 skills lack the `triggers:` field most skills carry (optional per writing-skills): `ai3d-gen`, `mesh-utils`, `operate-blender`, `operate-godot`. | `skills/{ai3d-gen,mesh-utils,operate-blender,operate-godot}/SKILL.md:1-5` vs `skills/writing-skills/SKILL.md:29-32` | Normalize frontmatter |
| DOC-016 | Low | Manifest hygiene | `original_path` (`%APPDATA%\\devin\\skills\\...`) and `exported_at` timestamps versioned per entry — audit recommended dynamic generation, not versioned state. | `manifest.json:18-20` (pattern repeats per entry) | Generate at export |
| DOC-017 | Low | AGENTS.md readers | Rule index skips number 6 (5 → 7); cosmetic numbering gap. | `AGENTS.md:12-14` | Renumber or annotate |
| DOC-018 | Low | Stale-name readers | `afk-loop` referenced as a skill (now a mode of `execution`); TOOLS-MAP says "AGENTS.md … (20 regras)" vs actual 28 entries (20 bodies + 8 aliases). | `.devin/docs/DEVIN-CLI-COMPATIBILITY.md:57`; `.devin/docs/TOOLS-MAP.md:105`; `AGENTS.md:9-36` | Name/count refresh |

## 3. Recommended fix order

1. **DOC-001** - TOOLS-MAP hook/validator table (false safety claims; worst doc-vs-reality gap).
2. **DOC-002** - `VALID_PROFILES` sync (`qa-ci`, `repo-reviewer`) - latent hard block.
3. **DOC-003** - SKILL-TIERS coverage (14/67 skills unreachable via the designated router).
4. **DOC-008** - TOOLS-MAP subagent table (same file, piggyback on DOC-001 edit).
5. **DOC-004** - Language normalization of installed `.devin/docs/` (NFR-4).
6. **DOC-005** - `manifest.docs` resync with paths.
7. **DOC-006** - `docs/` → `.devin/docs` pointer cleanup (CONTEXT.md, ARCHITECTURE_MANIFEST).
8. **DOC-007** - Move/genericize 3D-STACK-INSTALL.
9. **DOC-009** - Slim the 3 oversized SKILL.md routers.
10. **DOC-010…DOC-018** - Batch: single-source token figure, de-personalize, policy wording, mask CHANGELOG paths, placeholder expansion, frontmatter normalization, renumber note, name refresh.

## 4. VF4 - SKILL-TIERS cross-check

- Every skill named in `.devin/docs/SKILL-TIERS.md` exists on disk: 55
  distinct names verified against `skills/` (all present; zero phantom names).
- Mismatch direction is one-sided: disk has 14 top-level skills the index
  never names (→ DOC-003). Nested `social-midia/<net>` children (8) are also
  unindexed.
- `scan` is indexed but its tok column is "-" (`.devin/docs/SKILL-TIERS.md:94`).

## 5. VF5 - manifest.json cross-check

- `manifest.skills` names == `os.listdir('skills')` dirs: **67 == 67, zero
  drift** (`manifest.json:13-471`; audit.py:86-93 encodes the same check).
- `skill_count: 67` matches disk (`manifest.json:472`).
- `agent_count: 6` matches `agents/*.md` (6 files).
- Nested skills: 8 `social-midia` children exist on disk but are not manifest
  entries - consistent with the top-level counting convention; noted as an
  inventory blind spot, not drift.
- Drift found: `manifest.docs` inventory (→ DOC-005); `original_path`/
  `exported_at` versioning (→ DOC-016).

## 6. GLOBAL_BUNDLE_AUDIT re-check (2026-09-09 audit vs current state)

| Audit item | Status | Evidence |
|---|---|---|
| README identity/version coupling | still-open | `README.md:3,15,23,587`; `LICENSE:3` (→ DOC-014) |
| CHANGELOG personal paths/names | still-open | `CHANGELOG.md:114,566,575,709,774` (→ DOC-013) |
| LICENSE holder placeholder | still-open | `LICENSE:3` |
| manifest `original_path`/`exported_at` | still-open (accepted-risk) | `manifest.json:18-20` (→ DOC-016) |
| AGENTS.md GLM-5.2/SWE-1.7 coupling | fixed | `AGENTS.md:141-149` SWE-2 + `data/bundle-models.json` |
| config.json `glm-5-2` | fixed | `config.json:8` `swe-2-high` |
| `mcp_config.json` atlassian hardcoded | fixed | `mcp_config.json:2` empty; `data/bundle-integrations.json:4-10` disabled |
| hooks.v1.json relative script paths | fixed | `scripts/render-user-hooks.py` renders into `config.json.hooks` at install (`README.md:28,195`) |
| `.devin/hooks.v1.json` template | stale | file no longer shipped; `project-bootstrap` generates it (`skills/project-bootstrap/modes/setup.md:99`) |
| agents/*.md all `swe-1-7`, no split | fixed | `agents/*.md` now `swe-2-max`/`swe-2-medium` split per role |
| `model-context-windows.json` GLM/SWE-1 catalog | fixed | `data/model-context-windows.json:2-6` SWE-2 only |
| context-pressure/context-budget defaults + Pocock refs | fixed | `data/context-budget.json`, `data/recipes.json` role-based; scripts grep clean |
| memory-*.py BASE hardcoded | fixed | `scripts/memory-*.py` honor `BUNDLE_MEMORY_DIR`/`DEVIN_MEMORY_DIR` |
| install.sh missing docs install | fixed | `install.sh:583-610` installs `.devin/{docs,plans,templates}` |
| install.ps1 docs parity | fixed | `install.ps1:592-613` same source set |
| `devin-N*` / session launcher at root | still-open (partial) | `devin-N.cmd`, `devin-N.ps1` remain; `devin-session-launcher.ps1` gone |
| SKILL-TIERS pocock/personal names | fixed | none remain; coverage gap is the new issue (→ DOC-003) |
| MODEL-GUIDE hardcoded glm/swe-1 | fixed | `{{BUNDLE_*}}` placeholders + registry |
| TOOLS-MAP atlassian/WSL coupling | fixed | parameterized via `mcp_config.json.example` + `bundle-integrations.json` |
| DEVIN-CLI-COMPATIBILITY version pin | fixed | `{{VALIDATED_CLI_VERSION}}` + `data/bundle-identity.json:8` |
| docs/plans as project docs | fixed | moved to `.devin/plans/` |
| jira hardcoded site/cloudId | fixed | `skills/jira/SKILL.md:23-29` reads `bundle-integrations.json`/env |
| `setup-matt-pocock-skills`, `ask-matt`, `triage`, `leo`, `project-setup`, `self-extend`, `tool-and-skill-discovery`, `mcp-context-audit`, `mcp-lazy-enablement`, `context-window-hygiene`, `memory-hygiene`, `effort-calibration`, `primeagent-reference`, `continuous-improvement`, `improve-codebase-architecture` | stale | skills removed/consolidated (82→67); successor names verified on disk |
| Person-name remnants in skills | still-open (1 remnant) | `skills/mcp-governance/SKILL.md:77` (→ DOC-011) |
| `youtube-fetcher` single-domain | still-open (partial) | still YouTube-named; hosts parameterized (`data/bundle-integrations.json:17-27`) |
| Delegation matrix (swe-1-7 Max/Medium) | stale→realized | intent implemented via swe-2-max/medium pins; matrix's skill names pre-consolidation |
| audit.py: add hardcoded-local checks | still-open (partial) | `audit.py` checks counts/badges/docs but no author-path scan (`audit.py:472-474`) |

## 7. Gaps

- Exact byte sizes of SKILL.md files not measured (no stat tool); oversize
  flags rely on SKILL-TIERS' own tok measurements (`.devin/docs/SKILL-TIERS.md:3`).
- `skills/*/modes/*.md` and `reference/*.md` bodies not read end-to-end;
  frontmatter + targeted stale-pattern greps only (swe-1|glm-|pocock|leand|
  Leostruka|3000.6 → 1 hit, DOC-011).
- Whether `run_subagent` non-dispatch of guards is intentional could not be
  verified against a design doc (DOC-001 reported as doc-vs-code mismatch).
- `.devin/` project-local artifacts (plans/, ledgers/, notes/, scratch/,
  research/, memory/, handoffs/) inventoried by listing, not audited
  file-by-file - out of the agent-facing runtime surface.
