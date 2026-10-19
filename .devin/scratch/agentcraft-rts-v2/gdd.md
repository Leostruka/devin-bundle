# AgentCraft RTS v2 Game Design Document (GDD)

The metaphor bible for milestone v3.8.0. Every subsequent issue (#120–#136)
implements against this document. Prime directive: **no invented features**:
every RTS element traces to a real bundle or Devin CLI surface.

References: Warcraft 3 (heroes, command card, minimap, upkeep), StarCraft 2
(macro loop, supply, alerts), LotR: BFME (fixed building plots, palantir
powers, battalions), `blendi-remade/agentcraft` office mode (re-skinned here
as a BFME-style base-interior view), `app.agentcraft.gg` battlefield mode.

Canon name for the daemon/session being rendered: **the Keep** (rtsd is the
Keep's scribe; it observes, projects, and relays; it never dispatches).

---

## 1. Entity mapping table (bundle/CLI → RTS)

### 1.1 Hero classes: agent profiles

Heroes are units with stats, inventory, voice barks, and a class kit derived
from the profile's real `allowed-tools` and `model` tier in `agents/*.md`.
Model tier sets the unit tier: `swe-2-medium` = Footman-tier,
`swe-2-max` = Knight-tier. Parent model (`swe-2-high`) is the **Commander**
(the user session itself, not a spawnable hero).

| Profile | Class | Tier | Kit (from real allowed-tools) | Justification |
|---|---|---|---|---|
| `implementer` | Knight | Footman | Full kit: Write (write/edit/notebook_edit), March (exec+shell tools), Cartography (read/grep/glob/find), Envoy (mcp_*) | Only profile with full read+write+exec+shell+MCP: the main combat unit that builds the world. |
| `debugger` | Ranger | Footman | Track (exec+get_output+write_to_process+kill_shell), Cartography, Scouting (web_search), Camp (todo_write) | Read+exec chases bugs across process boundaries; no write = no build, pure tracker. |
| `qa-ci` | Cleric | Footman | Verify (read-only exec+get_output), Cartography | Re-executes gates on clean checkout; heals the build, never edits. |
| `reviewer` | Spellbreaker | Knight | Verify (exec+get_output), Cartography, Scouting | Two-axis review (Standards vs Spec); dispels bad code before merge. |
| `researcher` | Far Seer | Knight | Farsight (web_search+webfetch), Envoy (mcp_*), Cartography | Read-only recon; range = the open web + MCP. No attack (no write/exec). |
| `architect` | Archmage | Knight | Cartography, Farsight, Envoy | High-level design judgments; never touches code. |
| `tech-lead` | Runesmith | Knight | Write, Cartography, exec, Scouting | Forges architecture specs (docs): writes runes, not product code. |
| `product-manager` | Herald | Knight | Write, Cartography, exec, Farsight | Authors the PRD that starts a campaign; docs-only writer. |
| `scrum-master` | Marshal | Knight | Write, Cartography, exec | Declares DONE/REWORK/BLOCKED: command voice of the agency pipeline. |
| `art-director` | Enchanter | Footman | Write, Cartography, exec | Conjures the design system spec (tokens, WCAG matrix). |
| `copywriter` | Bard | Footman | Write, Cartography, exec | Sings the docs map; claims traceable to spec. |
| `security-auditor` | Inquisitor | Knight | Write, Cartography, exec | STRIDE/DPIA audit; the only rework channel is 04_BLOCKERS.md. |
| `red-team-lead` | Shadowblade | Knight | Cartography, exec, Farsight, Parley (ask_user_question), Camp | Authorized offense under engagement contract: special ops. |
| `subagent_explore` (builtin) | Scout | router | Cartography, Scouting | Built-in read-only recon unit. |
| `subagent_general` (builtin) | Squire | parent | Full kit (foreground) / pre-approved (background) | Generic infantry; inherits the Commander's gear. |
| `domain` (project) | Cartographer | Knight | Cartography | Reads repo terrain into domain maps. |
| `issue-tracker` (project) | Chronicler | Footman | Write, Cartography | Keeps the quest ledger (`.devin/scratch/` issues). |
| `repo-reviewer` (project) | Inspector | Knight | Cartography, Verify | Local two-axis reviewer of this keep's own works. |
| `triage-labels` (project) | Steward | Footman | Cartography | Sorts incoming quests into canonical status. |

Kit vocabulary (shared): **Cartography** = read/grep/glob/find_file_by_name,
**Write** = write/edit/notebook_edit, **March** = exec+get_output+
write_to_process+kill_shell, **Verify** = exec restricted to tests/lint,
**Farsight** = web_search+webfetch, **Envoy** = mcp_* tools, **Parley** =
ask_user_question, **Camp** = todo_write. These are the only buttons a hero's
command card may show: the card is generated, not hardcoded (#126).

### 1.2 Core loop surfaces → production/economy

| Bundle/CLI surface | RTS entity | Justification |
|---|---|---|
| `run_subagent` (tool) | **Barracks production** | Dispatching a hero is literally training a unit at the barracks; `profile` picks the class, `is_background` = remote deploy. |
| `exec` background shells (`get_output`/`write_to_process`/`kill_shell`) | **Summoned minions with TTL** | A background shell is a conjured creature bound to its summoner; it dies when the shell dies (`kill_shell`, process exit, or close). |
| Hooks firing (`scripts/*.py` on events) | **Worker peasants** | Each hook invocation is a peasant scurrying between buildings carrying a payload (the hook event). Ambient life of the base. |
| `.devin/memory/` + RAG chunking strategies | **Library building + archival doctrines** | Memory files are tomes; the 8 chunking strategies (fixed/recursive/document/semantic/LLM/agentic/late/hierarchical) are researchable doctrines shown as Library upgrades. |
| `.devin/ledgers/*.md` | **Trophy Hall** | Gates ledgers are the evidence vault; completed gates mount trophies (evidence lines) on the wall. |
| `gates` (skill + ledger checks) | **Fort walls** | A gate is a wall segment: pass = standing, fail = breach (persistent alarm until repaired). |
| `.devin/mailboxes/` (A2A inbox) | **Ravens** | Mailbox deposits are ravens flying between units; `rts-intents.py` message intents release them. |
| MCP servers (`mcp_config.json`) | **Marketplace / allied emissaries** | External servers are allied factions sending emissaries; each stall shows that server's real tool count. |
| `extensions/*` (22 dirs) | **Allied arsenal buildings** | Each extension is a specialized siege/workshop unit donated by an ally; rtsd itself is the Keep's scribe tower. |
| `skills/*` (83) | **Spellbook** | 83 spells grouped by domain school (§1.4); a spell is "cast" when the `skill` tool invokes it: cast state from `hook.posttooluse` events, never faked. |
| Git worktrees | **Expansions** | A worktree is a second base on the same map; its lane owns its territory. |
| Sessions / session picker | **Campaign saves** | Each CLI session is a saved game; `events.jsonl` is the save file (replayable). |
| `devin cloud` / `connect` / `ssh` / `forward` / `/handoff`+`/pickup` | **Portals** | Cloud commands open portals to remote worlds; `devin connect` tethers a foreign hero to this map. |
| `computer-use` extension (+ `cu-realtime`) | **Golem** | A heavy construct that moves the real desktop: slow, powerful, scoped. |
| `laya` engine (`laya-*`, `implement-laya`) | **Oracle** | Fast typed divination over states (guard, compact trigger); whispers verdicts, never proves them. |
| `prompt-compiler` skill | **Runeforge** | Crafts prompts/artifacts: the forge where raw intent becomes a weapon. |
| `audit.py` | **Royal Inspection** | Periodic inspection of the whole keep; 0 errors = parade ground clean. |
| `destructive-gate.py` | **Gate Guard** | Stands at the portcullis checking every `exec` for siege damage. |
| `constraint-pinning.py` | **Decree Board** | Re-posts the realm's laws (pinned rules) after every compaction storm. |
| `afk-loop` (skill) | **AI Commander autopilot** | Hands the campaign to an AI commander that walks the quest DAG unattended. |

### 1.3 Runtime tools → commands/build actions (all 28)

| Tool | RTS surface |
|---|---|
| `read` | Scout report: reveals a fog tile (the file's region) |
| `write` | Raise terrain: reveals tile + marks ownership |
| `edit` | Raise terrain (same, smaller blast) |
| `apply_patch` | Raise terrain (mode-dependent) |
| `notebook_read` | Scout report on a tome |
| `notebook_edit` | Inscribe a tome |
| `grep` | Sweep: reveals tiles matching the pattern |
| `glob`/`find_file_by_name` | Survey: light fog-lift on matched regions |
| `exec` | March order: spawns worker/minion activity |
| `get_output`/`write_to_process`/`kill_shell` | Command a summoned minion (inspect/order/banish) |
| `web_search`/`webfetch` | Farsight: hero casts outward, no map change |
| `run_subagent` | Train hero (Barracks) |
| `read_subagent` | Debrief: hero returns with loot (result) |
| `skill` | Cast spell from the spellbook |
| `todo_write` | War map: updates the campaign plan overlay |
| `ask_user_question` | Council summons: raises a war-council alert |
| `browser_preview`/`close_browser_preview` | Observation balloon over a local web region |
| `request_scope` | Envoy to the realm border (permission to roam) |
| `mcp_call_tool`/`mcp_list_tools`/`mcp_list_servers`/`mcp_read_resource` | Trade with a Marketplace emissary |
| `exit_plan_mode` | Leave the war room: orders go live |

### 1.4 Skills → spellbook (83 spells, 6 schools)

A spell's *known* state comes from the manifest; *cast* state comes from
`hook.posttooluse` events with `tool == "skill"`. Grey = known but never cast
this session; glowing = cast this session. No fake progression.

| School | Spells (skill names) |
|---|---|
| **Command** (orchestration, 14) | ask-bundle, dispatching-parallel-agents, execution, gates, grilling, handoff, intake, learn-mode, planning, playbook, project-orchestrator, scheduled-turns, skill-discovery, wizard |
| **War** (offsec, 8) | firmware-probe, mobile-probe, net-probe, re-binary, red-team, scan, web-probe, wireless-probe |
| **Lore** (knowledge, 12) | ai-coding-dictionary, ai-tools, context-hygiene, context7, data-analyst, fact-check, jira, knowledge-modeling, memory-management, obsidian-workflow, research, wait-what |
| **Craft** (engineering, 30) | a11y-audit, api-spec, architecture, architecture-diagrams, brag, code-review, database, debugging, deploy, devin-config, docker, e2e-testing, finishing-a-development-branch, gh, git-workflows, i18n, impeccable, observability-quality, performance, pr, project-bootstrap, prompt-compiler, prototype, retro, security, self-improvement, setup-pre-commit, teach, testing, writing-skills |
| **Creation** (media/3D, 14) | ai3d-gen, animation-direction, ascii-art, creative-engineering, humanizer, image-forensics, media-tools, mesh-utils, operate-blender, operate-godot, scrape-tools, social-midia, youtube-fetcher, mcp-governance |
| **Summoning** (machine control, 5) | computer-use, cu-realtime, implement-laya, laya-orchestrator, system-control |

Total: 14+8+12+30+14+5 = 83 ✓ (matches `manifest.json` skill_count).
`mcp-governance` sits in Creation as the emissary-quartermaster spell
(audits what the Marketplace emissaries carry). Rationale over purity: the
table must have exactly 83 rows and every manifest skill appears once.

### 1.5 Scripts → worker/building staff (all 35)

| Script | Role |
|---|---|
| `_hookrun.py` | Peasant dispatcher: routes hook payloads to workers |
| `architecture-gate.py` | Mason: blocks building without the architecture manifest |
| `behavioral-nudge.py` | Herald: whispers the self-check rules each prompt |
| `check-ai-signature.py` | Censor: strips foreign seals from decrees |
| `check-push-green.py` | Supply Sergeant: no caravan (push) leaves without green |
| `compact-gate.py` | Siege Engineer: decides when the context walls must be torn down |
| `constraint-pinning.py` | Decree Scribe: reposts pinned law after compaction |
| `context-budget.py` | Treasurer: counts the gold (token) cost of rules |
| `context-pressure.py` | Granary Keeper: measures the lumber (context) reserves |
| `destructive-gate.py` | Gate Guard: inspects every exec at the portcullis |
| `gh-pr-assignee.py` | Emissary: carries PR banners to GitHub |
| `laya-guard.py` | Oracle Acolyte: asks the Oracle about risky commands |
| `memory-post-edit.py` / `memory-post-exec.py` | Archivists: file fresh memories after writes/execs |
| `memory-retrieval.py` / `memory-stop.py` | Librarians: fetch tomes at prompt time, log the stacks at close |
| `mermaid-parse-check.js` | Illuminator: validates diagram marginalia |
| `no-em-dash.py` | Style Monk: enforces scriptorium punctuation |
| `post-exec.py` / `pre-exec-guard.py` / `pre-write-guard.py` | Sentries: standing guard around exec/write paths |
| `refine-review-prompt.py` | Chronicler: records the refinement review |
| `render-user-hooks.py` | Quartermaster: renders hook deployments |
| `rts-decision.py` | Council Usher: carries war-council questions and answers |
| `rts-emit.py` | Signal Runner: taps every hook event into the war log |
| `rts-intents.py` | Steward of Intents: surfaces UI orders to the session |
| `session-start.py` | Doorwarden: opens the keep each session |
| `silent-error-review.py` | Investigator: examines quiet failures after execs |
| `spec-consistency.py` | Law-keeper: checks specs agree with each other |
| `stop-guard.py` | Last Watch: verifies before the session may stand down |
| `user-prompt.py` | Town Crier: announces the user's words to the keep |
| `validate-mermaid.py` | Cartographer's Checker: validates mermaid in writes |
| `validate-refinement-evidence.py` | Evidence Warden: verifies refinement claims |
| `validate-skill-format.py` | Spellbinder: checks spell scroll format |
| `validate-tool-args.py` | Arms Inspector: validates tool arguments (ALTK SPARC) |

### 1.6 Extensions → allied arsenal (all 22)

| Extension | Arsenal role |
|---|---|
| `rtsd` | **The Keep's Scribe Tower**: this daemon; map, fleet, event log |
| `computer-use` | Golem works: desktop automation constructs |
| `system-control` | Siege yard: authorized OS-level engines |
| `laya-compactor`, `laya-tools` | Oracle's chapel: the resident Laya worker |
| `rea-ops`, `rz-ops`, `offsec-tools` | War quarter: RE/offsec engines |
| `blender-operator`, `spline-operator`, `comfyui-operator`, `asr`, `remotion-render` | Artisan quarter: 3D/media forges |
| `craft-bridge` | Merchant guild: uniform dispatch over craft suites |
| `image-forensics` | Assay office: provenance testing of captured images |
| `mesh-utils` | Stoneworks: mesh conversion/inspection |
| `ppisp-prep` | Lens grinding: photometric QC |
| `scrape-tools` | Forager's camp: structured web extraction |
| `media-tools`, `diagram-tools`, `ai-tools` | Workshop row: media/diagram/AI utilities |
| `rust-core` | Iron mines: hybrid Rust extensions (ADR-003) |

### 1.7 Configs, docs, data → infrastructure

| Surface | RTS surface |
|---|---|
| `AGENTS.md` + `.devin/global_rules.md` + rules | **The Law**: realm decrees every citizen obeys |
| `manifest.json` | **Census**: the official count of souls and structures |
| `config.json`, `hooks.v1.json` | **Keep blueprints**: how the keep is wired |
| `data/bundle-models.json` | **Armory ledger**: which tiers exist (Footman/Knight/Commander) |
| `data/context-budget.json`, `data/recipes.json` | **Treasury records**: thresholds and campaign recipes |
| `data/bundle-identity.json`, `data/bundle-integrations.json` | **Royal seal + trade charters** |
| `.devin/ledgers/` | Trophy Hall contents (see §1.2) |
| `.devin/scratch/` | Quest board shelves (see §2 quests) |
| `.devin/rts/` | **The war room floor**: events.jsonl, fleet, decisions, intents |
| `install.ps1/.sh`, `export.ps1/.sh` | **Caravan masters**: move the keep between machines |
| `mcp_config.json` | Marketplace charter (who may set a stall) |
| Docs (`MODEL-GUIDE`, `SKILL-TIERS`, `TOOLS-MAP`, `CHANGELOG`, `README`, `AI-CODING-DICTIONARY`) | **Library reference shelf** |

### 1.8 CLI commands, modes, events → meta-game

| CLI surface | RTS surface |
|---|---|
| `/goal` | **Grand campaign objective**: the main quest banner |
| `/billing` | Treasury ledger toggle |
| `/model` picker + `Alt+Enter` | Armory: re-forge the Commander's/hero's tier mid-battle |
| `devin cloud`/`ssh`/`forward`/`connect`/`drs` | Portals (see §1.2) |
| `devin rules`/`skills`/`plugins`/`doctor` | Royal inspectors of law/spells/allies |
| Modes (Normal/Accept-Edits/Smart/Plan/Bypass/Autonomous) | **Rules of engagement**: how freely units may act |
| Hook events: `PreToolUse`, `PostToolUse`, `PostCompaction`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`, `Stop`, `PermissionRequest` | **Bells of the keep**: each ring spawns peasant activity; `PermissionRequest` rings the war-council bell |

Unmapped residue: **none**. Everything above cites a real file, tool, or
command. Where a capability does not exist (e.g. token spend per turn (the
CLI does not expose it), the GDD says so explicitly and the UI must degrade
rather than invent (§6).

---

## 2. Mechanics mapping

| RTS mechanic | Real data source | Notes |
|---|---|---|
| HP | Task progress %: heartbeat `status.json` `pct`, else derived from ledger gates passed/total in the hero's lane, else 100 while running | Falls back honestly; 0 = failed/dropped |
| Mana | Context remaining estimate for the hero = `1 - (context-pressure marker share)` (chars/4 heuristic: the same number `context-pressure.py` computes); per-agent share when heartbeats report it | Low mana flashes the portrait; at 0 the hero is spent (compaction imminent) |
| XP / level | Count of gates passed + tasks completed attributed to the hero's lane | Level badge on portrait; +1 per completed quest |
| Supply / food | Active subagents vs cap (concurrent run_subagent running) | Over-cap → supply warning banner |
| Gold | Token spend estimate: `context-pressure.json` `tool_output_tokens + calls*200` cumulative | Real tracked estimate, labeled `~` |
| Lumber | Context window % consumed (same marker, vs `bundle-models.json` window) | Shared pool per session |
| Upkeep | WC3 tiers on lumber: <50% none, 50–75% low (`WARN`), 75–80% high (`CRITICAL`), ≥80% `CLEAR NOW`: mapped 1:1 to context-pressure thresholds | Upkeep tier change fires an alert |
| Fog of war | Untouched repo paths; `read/write/edit/grep`/`glob` PostToolUse events reveal the tile containing `tool_input.file_path`/`pattern` | Explored-but-dark model: stale tiles re-dim |
| Quests | `.devin/scratch/*/issues/*.md` DAG (`Status:`/`Blocked by:`) + `/goal` as main quest | Blocked quests grey with chain shown |
| Loot drops | Ledger `EVIDENCE:` lines on `pass` gates → item cards in the hero's inventory grid | Trophy Hall shows all loot |
| Attack order | Assign task: intent `{kind:"order", to, task}` → mailbox/rts-intents path | Never auto-executes: surfaces to session |
| Patrol | afk-loop lane assignment = patrol route between quest markers | |
| Voice barks | `status.json` `note` field verbatim, class-flavored fallback lines (§5) | Barks never fabricate: no note → class line |
| Terrain | Repo top-level dirs = named regions; `.devin/rts/map.json` persists layout | BFME fixed building plots inside regions |
| Contested tiles | Files whose path appears in events from >1 lane | Conflict visualization |
| Raven | Mailbox deposit `msg-*.json` → raven flies sender→recipient | |
| Decisions | `.devin/rts/decisions/*.json` pending → war council | Timeout → last option (deny-safe, unchanged) |
| Day/night | Wall-clock session time; cosmetic dim layer | Toggleable, zero-cost when off |
| Score screen | Aggregates from events.jsonl: quests done, gates passed, heroes by XP, est. tokens | Warcraft victory screen |

---

## 3. Two render modes: one engine, two themes

The engine renders `world` state through a **theme**: a pure-frontend bundle
of palettes, tile/unit/building sprites, and chrome. Switching themes never
touches world state. Theater of the same war.

### 3.1 Battlefield (default)

Top-down WC3-style map. Repo regions are terrain; building plots are stone
circles; units walk, peasants scurry, fog shrouds unexplored dirs.

### 3.2 Office (BFME base-interior)

Isometric office interior, the same entities re-skinned:

| Entity | Battlefield | Office |
|---|---|---|
| Hero at work | Unit on territory | Sprite typing at a desk |
| Idle hero | Standing unit | At the water cooler |
| Minion | Summoned creature | Junior at shared bench |
| Spawn | Unit exits barracks | New hire walks in the door |
| Decision pending | War-council banner | Meeting-room summons (units walk to table) |
| Gate fail | Wall breach fire | Printer fire (red flash) |
| Quest board | Map markers | Kanban wall |
| Library | Arcane library | Bookshelf |
| rtsd | Scribe tower | Server rack |
| Mailbox | Raven | Phone booth call |
| Done | Victory pose | High-five anim |
| Workers (hooks) | Peasants | Staff carrying papers |

### 3.3 Theme switcher

`?` menu or `T` key toggles `theme.name`; renderer re-reads the theme table
and redraws the same world. State, selection, camera, and control groups are
theme-agnostic. Spec contract: a theme must provide `tiles`, `units`,
`buildings`, `ui`. Missing keys fall back to programmer-art defaults, never
to external assets.

---

## 4. Screen layout spec

### 4.1 Desktop

```
+------------------------------------------------------------------------+
| GOLD ~12.4k | LUMBER 41% | SUPPLY 3/8 | UPKEEP: low   [alerts:2] [!] [!]|  top bar (resources + alert stack)
+---+--------------------------------------------------------------------+
| C |                                                                    |
| O |                                                                    |
| M |                          W O R L D                                  |
| M |                    (tilemap + fog + units +                         |
| S |                     buildings + waypoints)                          |
|   |                                                                    |
| f |                                                                    |
| e |                                                                    |
| e +------------------------------------------------------+-------------+
| d | QUEST LOG                          | PORTRAIT+STATS   | COMMAND     |
+---| - main: /goal ...                  | [face] Knight-2  | CARD 3x4    |
| M | - side: issue-12 (blocked by 10)   | HP ████░ MP ██░░ | [Mv][St][At]|
| I | - side: issue-14 in-progress       | Lv3 inv:[o][x][] | [Ab1]...[Ab]|
| N +--------------------------+---------+------------------+-------------+
| I | CHAT IN (steering @hero) | map     | abilities detail  | idle:2 ??  |
+---+--------------------------+---------+------------------+------------+
        ^ minimap bottom-left (viewport rect, pings)   ^ command card bottom-right
        War council = modal over world; comms feed = left column.
```

### 4.2 PWA / mobile (<700px)

Polling mode (no WS dependency: fetch `/snapshot` every 2s; existing
service worker stays). World canvas hidden; the keep becomes a tabbed
commander view:

```
+------------------------------------------+
| GOLD ~12k | LUM 41% | SUP 3/8  [alerts:2]|
+------------------------------------------+
| [tab: fleet | quests | council | feed]   |
|  (active pane scrolls; council auto-     |
|   jumps front on new decision)           |
+------------------------------------------+
| tap unit = select; long-press = orders   |
+------------------------------------------+
```

---

## 5. Asset direction

Programmer-art first: colored shapes + letters on canvas 2D, sprite-sheet
loader designed so real art drops in later **without code changes**
(`theme.units[knight] = {shape, color, glyph}` today; `{sheet, sx, sy}` later).

Naming conventions:
- Units: `<class>-<n>` (Knight-2, Ranger-1); heroes keep real `agent_id` in tooltip.
- Buildings: canonical ids `town-hall, barracks, tavern, library, watchtower,
  runeforge, vault, portal, marketplace, altar, trophy-hall`.
- Intents: existing kinds + `order` (assign/patrol/attack target). All still
  surface through `rts-intents.py`; nothing auto-executes.

Voice-line table (bark fallbacks when `status.json` has no `note`):

| Class | Selected | Ordered | Done |
|---|---|---|---|
| Knight | "At your command." | "For the keep." | "Work complete." |
| Ranger | "On the trail." | "Tracking." | "Prey found." |
| Cleric | "The gates call." | "Verifying." | "All gates green." |
| Spellbreaker | "Show me the diff." | "Reviewing." | "Judgment passed." |
| Far Seer | "I see far." | "Scouting." | "Report delivered." |
| Archmage | "A grand design." | "Drafting." | "The plan stands." |
| Runesmith | "Blueprints ready." | "Forging spec." | "Architecture set." |
| Herald | "What do users need?" | "Writing the PRD." | "Spec authored." |
| Marshal | "Status report." | "Checking artifacts." | "DONE declared." |
| Enchanter | "Design calls." | "Styling." | "System specced." |
| Bard | "A tale to tell." | "Drafting docs." | "Published." |
| Inquisitor | "Trust nothing." | "Auditing." | "Audit filed." |
| Shadowblade | "Rules of engagement?" | "Probing." | "Target assessed." |
| Scout | "Eyes open." | "Sweeping." | "Map updated." |
| Squire | "Ready." | "On it." | "Done, sir." |

---

## 6. Honesty rules (binding for all issues)

1. Every counter, bar, icon, and button reads from a real file or event.
   Absent data → element hidden or marked `~`/`-`, never invented.
2. Intents never execute: they surface via `rts-intents.py` to the session;
   the orchestrator decides.
3. Deny-safe preserved: decision timeout = last option; remote listener
   expires; rtsd offline never blocks hooks.
4. `events.jsonl` is the only history: replay must rebuild identical state.
5. Stdlib-only in `scripts/` and `extensions/rtsd/`; frontend zero-dep
   (canvas 2D, no CDN).
