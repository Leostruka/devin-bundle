# Spec-Driven Development (SDD) - Research Report

## 1. DEFINITION

**SDD (2025-2026):** structured, versioned specification is the primary dev artifact; code is derived output generated+checked by AI agents against it. GitHub: "specifications become executable, directly generating working implementations rather than just guiding them" [1][2]. IBM: "a detailed specification of implementation details is authored and agreed upon before development begins... a single source of truth" [27]. InfoQ: "fifth-generation programming shift", living specs "executable by design" [22].

**Bockeler maturity spectrum (ThoughtWorks taxonomy, widely adopted)** [59][60][61]:
| Level | Meaning | Tools |
|---|---|---|
| Spec-first | spec guides one task, then discarded | Spec Kit, Kiro (default) |
| Spec-anchored | spec persists, co-evolves with code | OpenSpec |
| Spec-as-source | humans edit only spec; code regenerated | Tessl (least proven; MDD parallel) |

- **vs spec-first docs:** spec-first is entry level - spec informs one build then rots; SDD keeps spec as governing artifact through verification (checklists, analyze, converge) [1][27].
- **vs TDD:** complementary granularity - spec = behavioral contract (what/why); tests = executable oracle. Frameworks combine both (Kiro property-based testing, Superpowers TDD-inside-plan) [52][12].
- **vs prompt engineering:** prompts ephemeral; specs durable/diffable/reviewable shared human+agent contracts (Sean Grove: "we communicate via prompts... then throw our prompts away") [17][18]. SDD = context engineering productized [23].

## 2. GITHUB SPEC-KIT

`github/spec-kit` - open-source toolkit, announced Sep 2 2025 [1][4]; 1.0 a year later [1]. Components: **Specify CLI** (Python, uvx, `specify init --ai <agent>`), templates+scripts in `.specify/`, agent-specific prompt files [1][9][36].

Pipeline (`/speckit.*`) [5][6][7]:
| Command | Role |
|---|---|
| constitution | one-time immutable principles; gates all later phases |
| specify | what/why tech-agnostic spec -> spec.md |
| clarify | optional; <=5 targeted questions folded into spec |
| plan | tech stack/architecture -> plan.md + research/data-model/contracts |
| checklist | custom "unit tests for requirements" - reviewer gate |
| tasks | dependency-ordered tasks.md |
| analyze | read-only cross-artifact consistency/coverage audit |
| implement | executes tasks; reads checklist state as gate |
| converge | codebase vs spec/plan/tasks; appends residual tasks |
| taskstoissues | tasks -> GitHub issues |

30-38 agent integrations (Copilot, Claude Code, Gemini CLI, Codex, Kiro, Cursor, Windsurf, Zed...; `generic` fallback) [1][3]. Per-feature `specs/NNN-<name>/` dir; branch per spec [5][6][61]. Bug-fix path ("Agentic Bug Fix") [5]. Extensible: presets, 150+ community extensions, replaceable process [3].

## 3. INDUSTRY POSITIONS

**ThoughtWorks**
- Radar Nov 2025 SDD = **Assess**: definition still evolving; Kiro/spec-kit/Tessl compared; cautions elaborate workflows, lengthy specs, unclear user, "relearning a bitter lesson - handcrafting detailed rules for AI ultimately doesn't scale" [8][10].
- Radar Apr 2026 Spec Kit = **Assess**: brownfield spec->plan->tasks->coding->review surfaces issues earlier; constitutions capture scope/domain/versions/standards/repo structure; rough edges = defensive checks, verbose markdown, high cognitive load; "experienced engineers extract most value" [11].
- Radar Apr 2026 OpenSpec = **Assess**: deltas + propose/apply/archive brownfield-friendly; keep re-evaluating SDD need as agents improve [12].
- Bockeler: spec-as-source = least proven; echoes failed MDD + non-determinism [59][60][61].

**InfoQ** [26]
- When Architecture Becomes Executable (Jan 2026): executable specs + drift detection + runtime invariants [22].
- Adoption at Enterprise Scale (Feb 2026): SDD = context engineering for long-horizon agents; gaps brownfield/workflow/progressive adoption [23].
- When SDD Pays Off (Sep 2026): controlled study - spec baseline did NOT raise bug-catching but made caught bugs accountable; spec as governance [25].
- Kiro launch news (Aug 2025) [24].

**Microsoft**
- MS Learn module: enterprise brownfield SDD w/ spec-kit+Copilot; constitution encodes security/perf/compliance; CI/CD+Azure DevOps [28].
- Dev blog (Delimarsky): Specify CLI, .specify/, constitution as "non-negotiables" [9][29].
- microsoft/agentic-sdlc-starter: 5-agent PRD->code pipeline [30].
- VS Code context-engineering guide + Copilot lab (/speckit.* in chat) [31][32].

**AWS / Kiro**
- Preview Jul 14 2025; Code-OSS IDE + CLI; claims "first to bring SDD to AI coding tools" [13][14][15].
- Spec mode: 3 gated files under .kiro/specs/ - requirements.md (EARS), design.md, tasks.md (requirement-linked, parallel "waves"); human approves each phase; hooks on file events [13][16][41].
- GA: property-based testing for spec correctness, checkpoints [14]. Quick Spec = gate-free mode [40]. EARS = Mavin et al., Rolls-Royce/IEEE RE'09 - not Kiro [41].

**IBM**
- Think page: definition; spec-first = entry; spec-as-source highest rigor [27].
- IBM/iac-spec-kit: spec-kit fork for Terraform/IaC (/iac.* commands) [33][34].
- IBM Bob: 4-stage SDD; warns over-detailed spec = "writing software in natural language" [35].

## 4. OTHER FRAMEWORKS

| Framework | Model | Distinction |
|---|---|---|
| OpenSpec (Fission-AI, ~67k*) | openspec/specs truth; changes/ with delta specs (ADDED/MODIFIED/REMOVED); /opsx:explore->propose->apply->archive | spec-anchored; best brownfield; cross-repo stores [42][43][44] |
| Agent OS | 3-layer context: standards+product+specs; /plan-product../orchestrate-tasks | v3 RETREATED from spec/task commands - native plan mode made them redundant; standards-injection only [45][46][47] |
| BMAD-METHOD | scale-adaptive agile AiDD; 12-21 persona agents, 34-50+ workflows | heaviest/most opinionated [48][49] |
| Taskmaster | PRD -> parse-prd -> tasks.json + expansion, complexity analysis; MCP | task-state machine, thin spec [50][51] |
| Superpowers (obra) | brainstorm->design->plan->subagent-driven dev w/ strict TDD->two-stage review | closest to this bundle's skill architecture; cross-harness incl Devin CLI [52][53] |
| Tessl | Spec Registry (10k+ lib specs vs API hallucination) + Framework ([@generate], capability<->test links); GENERATED-FROM-SPEC enforcement | only serious spec-as-source; private beta [54][55][56] |
| Matt Pocock skills | grill-with-docs->to-prd->to-issues->implement->code-review; vertical slices | skill-native chain; bundle already adopts (ledgers) [57][58] |
| Cline/Roo Memory Bank | hierarchical markdown (projectbrief, activeContext, decisionLog) read every session | persistent context, not spec pipeline [63][64][65] |
| Aider CONVENTIONS.md | single read-only conventions file | lightest end [66] |
| specdd/specdd | .sdd files colocated beside code | inline/local specs [62] |
| Yellhorn MCP | GitHub issues as planning boards | tracker-native [67] |

## 5. METHOD ANATOMY

Canonical pipeline (spec-kit superset; Kiro/OpenSpec subsets):

constitution (once) -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge

| Phase | Artifacts | Human gate |
|---|---|---|
| Constitution | constitution.md - principles, constraints, standards | approve once |
| Specify | spec.md - what/why, stories, AC, no stack | review spec |
| Clarify | updated spec.md + checklists/requirements.md | answer <=5 Qs/round |
| Plan | plan.md + research/data-model/contracts/quickstart | approve plan |
| Checklist | requirements-quality checklist | reviewer ticks [x] |
| Tasks | tasks.md ordered, dep-mapped | approve breakdown |
| Analyze | read-only consistency report | fix flagged gaps |
| Implement | code + per-task commits | checklist gates start; review PRs |
| Converge | residual-work tasks appended | close-out review |

Kiro collapses to Requirements->Design->Tasks w/ gate each; Quick Spec removes gates [13][40]. OpenSpec inverts: propose->apply->archive folds changes into canonical specs [44].

## 6. EVIDENCE - OUTCOMES AND FAILURES

**Reported benefits:**
- Brownfield: spec->plan->tasks->coding->review surfaces hidden assumptions earlier; constitution aligns agents to arch boundaries (TW field reports) [11].
- Accountability: spec baseline makes review verdicts auditable even without raising raw bug-detection (InfoQ study) [25].
- Token/context economy + sustained agent focus at enterprise scale [23].
- Senior engineers naturally spec for complex problems [68].

**Documented failures/limits:**
- **Spec rot:** stale spec misleads agents WORSE than stale docs mislead humans - agents execute outdated plans confidently, no flag (Augment) [69].
- **Suggestions-not-contracts:** markdown loses intent; agents implement ~70-90% of spec; missing parts invisible until QA (Sibylline - argues for structured/validatable artifacts) [70].
- **Review burden:** stacks of generated markdown "potentially worse than reviewing code"; verbose + defensive checks (TW; ianhxu study) [8][11][71].
- **Size mismatch:** same heavyweight workflow for bug fix and greenfield; Kiro turned small bug into user stories + dozens of AC [8][71].
- **Illusory control:** agents ignore elaborate instructions, duplicate existing code [71]; real audit caught agent drifting from rules present in every CLAUDE.md - "optimises locally and drifts silently" [72].
- **Slop accelerates:** agents double down on bad decisions, clone types, trivial tests (jlevy/speculate) [73].
- **MDD deja vu:** spec-as-source repeats model-driven failure + non-determinism - Verschlimmbesserung risk [59][71].
- **Tool churn:** Agent OS v3 deleted spec/task commands once native plan mode improved - scaffolding being absorbed by agents [47][12].

## 7. MAPPING ONTO devin-bundle

Verified local state: `.devin/plans/YYYY-MM-DD-slug.md` (Goal + Architecture + Tech Stack + Global Constraints + Modules/Interfaces + File Structure + Tasks w/ checkbox TDD steps), `.devin/adr/NNNN-slug.md`, `.devin/ARCHITECTURE_MANIFEST.md` (paradigm, patterns, style contracts, testing, error model, directory boundaries, non-negotiables - enforced by architecture-gate.py), `.devin/ledgers/<task>.md` (OUTCOME/CHECK/EXPECT/EVIDENCE per step), skills: grilling, gates, planning, execution, dispatching-parallel-agents, finishing-a-development-branch, prompt-compiler. Pocock chain internalized (ledgers: prd-to-issues-pocock, grill-me-pocock, afk-loop-pocock, tdd-feedback-pocock).

| Spec-Kit artifact | Bundle equivalent | Verdict |
|---|---|---|
| constitution.md | ARCHITECTURE_MANIFEST.md + AGENTS.md + ADRs | COVERED - manifest stronger (gate-enforced). Optional: product/UX principles section |
| spec.md (what/why tech-agnostic) | plan Goal/Architecture sections | PARTIAL GAP - plans mix what+how from line 5. Add "Spec/user stories/AC" front-matter to plan template |
| clarify | skills/grilling | COVERED, arguably stronger (frontier rounds) |
| plan.md + research/data-model/contracts | plan Modules/Interfaces/File Structure | COVERED |
| checklist (unit tests for requirements) | gates skill + ledger EXPECT | PARTIAL GAP - ledger verifies execution not spec quality pre-build. Add spec-quality checklist to planning |
| tasks.md | checkbox steps in plan | COVERED |
| taskstoissues | prd-to-issues pattern | COVERED |
| analyze (cross-artifact consistency) | none | GAP - nothing checks plan<->manifest<->ADR<->ledger consistency. Candidate: consistency-audit skill/script |
| implement | execution / dispatching-parallel-agents | COVERED |
| converge (codebase vs artifacts) | none | GAP - add converge step to finishing-a-development-branch: diff delivered code vs plan+ledger, append leftover tasks |
| Kiro bugfix / spec-kit bug path | debugging skill | COVERED |

**Do NOT adopt:** per-feature specs/NNN/ dirs + branch-per-spec (dated flat plans equivalent and leaner - Rule 18); EARS unless ambiguity is a measured problem; separate tasks.md (checkboxes inline); full spec-kit install (duplicates ~80% of existing pipeline).

**Highest-value additions:** (1) spec front-matter block in plan template; (2) analyze-style consistency check (novel capability); (3) converge-style post-implementation audit (targets documented agent-drift, complements ledger EXPECT/EVIDENCE).

## 8. SOURCES (80)

1. github/spec-kit README - repo - SDD def, commands, integrations - github.com/github/spec-kit/
2. Spec Kit docs index - repo docs - "intent-driven harness", Spec->Plan->Tasks->Implement - github.com/github/spec-kit/blob/main/docs/index.md
3. Spec Kit docs site - 30 integrations, presets/extensions - github.github.com/spec-kit/
4. GitHub Blog: SDD with AI (Delimarsky 2025-09-02) - launch, "steer" role - github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
5. Spec Kit reference: Agentic SDD - full pipeline, clarify <=5, analyze read-only - github.github.io/spec-kit/reference/agentic-sdd.html
6. Spec Kit quickstart - quality gates - github.github.io/spec-kit/quickstart.html
7. Spec Kit installation doc - command inventory incl converge/taskstoissues - github.com/github/spec-kit/blob/main/docs/installation.md
8. ThoughtWorks Radar: SDD (Nov 2025, Assess) - Kiro/spec-kit/Tessl, bitter-lesson caution - thoughtworks.com/radar/techniques/spec-driven-development
9. MS Dev Blog: Diving Into SDD with Spec Kit - Specify CLI, .specify/, constitution - developer.microsoft.com/blog/spec-driven-development-spec-kit
10. ThoughtWorks Decoder: SDD - benefits/limits, "sledgehammer" for bugs - thoughtworks.com/insights/decoder/s/spec-driven-development
11. TW Radar: GitHub Spec Kit (Apr 2026, Assess) - brownfield results, constitution contents - thoughtworks.com/radar/languages-and-frameworks/github-spec-kit
12. TW Radar: OpenSpec (Apr 2026, Assess) - delta specs, brownfield, re-evaluate - thoughtworks.com/radar/tools/openspec
13. Kiro: Introducing Kiro (Jul 14 2025) - launch, EARS - kiro.dev/blog/introducing-kiro/
14. Kiro GA blog - property-based testing, CLI, "first SDD" claim - kiro.dev/blog/general-availability/
15. AWS re:Post Kiro - requirements/design/tasks, EARS - repost.aws/articles/AROjWKtr5RTjy6T2HbFJD_Mw/
16. Kiro specs docs - 3-file spec, 3-phase, hooks - kiro.dev/docs/specs.md
17. Sean Grove: The New Code (AI Engineer World Fair 2025) - specs vs prompts, code=10-20% value - youtube.com/watch?v=8rABwKRsec4
18. Sean Grove blog post - spec as real source code - riseos.com/blog/2025-06-15-the-new-code/
19. GeekWire: Amazon targets vibe-coding chaos - Kiro launch - geekwire.com/2025/amazon-targets-vibe-coding-chaos-with-new-kiro-ai-software-development-tool/
20. SiliconANGLE: AWS Kiro spec coding - spec sync, pricing - siliconangle.com/2025/07/14/aws-launches-kiro-spec-coding-developer-environment-integrated-ai-agents/
21. Forbes: AWS agentic IDE - fuzzy-requirements motivation - forbes.com/sites/adrianbridgwater/2025/07/14/aws-builds-agentic-integrated-developer-environment/
22. InfoQ: SDD When Architecture Becomes Executable (Jan 2026) - executable specs, persona mapping - infoq.com/articles/spec-driven-development/
23. InfoQ: SDD Adoption at Enterprise Scale (Feb 2026) - context engineering, gaps - infoq.com/articles/enterprise-spec-driven-development/
24. InfoQ: Amazon Introduces Kiro (Aug 2025) - 3-phase, hooks - infoq.com/news/2025/08/aws-kiro-spec-driven-agent/
25. InfoQ: When SDD Pays Off (Sep 2026) - study: accountability not detection - infoq.com/articles/when-spec-driven-development-pays-off/
26. InfoQ SDD topic index - corpus - infoq.com/spec-driven-development/
27. IBM Think: What is SDD - definition, levels - ibm.com/think/topics/spec-driven-development
28. MS Learn: Implement SDD w/ Spec Kit - enterprise brownfield, constitution compliance, CI/CD - learn.microsoft.com/en-us/training/modules/spec-driven-development-github-spec-kit-enterprise-developers/
29. MS Learn lab greenfield w/ Spec Kit - /speckit.* in VS Code - microsoftlearning.github.io/mslearn-github-copilot-dev/Instructions/Labs/LAB_AK_13_get-started-spec-driven-development.html
30. microsoft/agentic-sdlc-starter - 5-agent PRD->code - github.com/microsoft/agentic-sdlc-st
31. VS Code context-engineering guide - custom instructions/plan flow - github.com/microsoft/vscode-docs (context-engineering-guide.md)
32. Kiro changelog 0.1 - preview date - kiro.dev/changelog/ide/0-1/
33. IBM/iac-spec-kit repo - spec-kit fork IaC, /iac.* - github.com/ibm/iac-spec-kit
34. iac-spec-kit spec-driven.md - "code serves specifications" - github.com/IBM/iac-spec-kit/blob/main/spec-driven.md
35. Heidloff: SDD with IBM Bob - 4 stages, spec-detail balance - heidloff.net/article/spec-driven-development-ibm-bob/
36. Spec Kit README historical - earlier pipeline - github.com/github/spec-kit/blob/4a323449/README.md
37. Caylent: Kiro first impressions - 3-doc walkthrough - caylent.com/blog/kiro-first-impressions
38. AWS Builder Center Kiro SaaS walkthrough - REQ/AC->design->tasks - builder.aws.com/content/3FyqehjwdWx0Gs0PBiU4VJKdt6x/
39. AWS Builder Center Kiro Specs - living artifacts - builder.aws.com/content/3DWagLjqsjIIIJ9evVne8P4ZbD6/
40. Kiro Quick Spec docs - gate-free mode - kiro.dev/docs/specs/quick-spec/
41. codemyspec: Kiro Specs Explained - EARS provenance (Mavin/Rolls-Royce RE'09), waves - codemyspec.com/blog/kiro-specs-explained
42. Fission-AI/OpenSpec repo - propose/apply/archive, stores, ~67k* - github.com/fission-ai/openspec
43. OpenSpec getting-started - /opsx:* commands - github.com/Fission-AI/OpenSpec/blob/HEAD/docs/getting-started.md
44. OpenSpec overview - specs-as-truth, delta specs, archive fold-back - github.com/Fission-AI/OpenSpec/blob/main/docs/overview.md
45. buildermethods/agent-os repo - standards+spec system - github.com/buildermethods/agent-os
46. Agent OS v2 workflow - plan-product->orchestrate-tasks - buildermethods.com/agent-os/v2/workflow
47. Agent OS releases v3 - retreat from spec/task commands to plan mode - github.com/buildermethods/agent-os/releases
48. BMAD-METHOD repo - agile AiDD, agents/workflows - github.com/bmad-code-org/BMAD-METHOD
49. bmad-autonomous-development (BAD) - autonomous story pipeline - github.com/stephenleo/bmad-autonomous-development
50. claude-task-master README - PRD->tasks via MCP - github.com/eyaltoledano/claude-task-master
51. Task Master command reference - parse-prd, expand, complexity - github.com/eyaltoledano/claude-task-master/blob/main/docs/command-reference.md
52. obra/Superpowers repo - skill-chain, subagent-driven dev + TDD - github.com/obra/Superpowers/
53. Superpowers workflow (ClaudeMod mirror) - brainstorm->plan->SDD->review - claudemod.com/mods/obra-superpowers
54. Tessl blog: SDD framework + registry - spec parts, [@generate], 10k+ specs - tessl.io/blog/tessl-launches-spec-driven-framework-and-registry
55. Tessl docs SDD - question->spec->approve->implement - docs.tessl.io/use/spec-driven-development-with-tessl
56. Tessl registry spec-as-source tile - GENERATED-FROM-SPEC headers - tessl.io/registry/spec-driven-development/spec-as-source
57. mattpocock/skills: to-issues - vertical-slice breakdown - github.com/mattpocock/skills/blob/HEAD/skills/engineering/to-issues/SKILL.md
58. mattpocock/skills: to-prd + chain - grill-with-docs->to-prd->to-issues - github.com/mattpocock/skills
59. Conffab: Understanding SDD - Bockeler 3 levels summarized - conffab.com/elsewhere/understanding-spec-driven-development-kiro-spec-kit-and-tessl/
60. martinelli.ch: Three Levels of SDD - levels applied; OpenSpec spec-anchored - martinelli.ch/the-three-levels-of-spec-driven-development-and-where-the-ai-unified-process-sits/
61. engwithai.substack: Birgitta Boeckeler profile - confirms martinfowler.com SDD article - engwithai.substack.com/p/birgitta-boekeler-is-bringing-structure (original martinfowler.com URL UNVERIFIED - not directly fetched)
62. specdd/specdd repo - .sdd colocated specs - github.com/specdd/specdd
63. Cline memory-bank docs - hierarchical markdown memory - github.com/cline/cline (memory-bank.mdx)
64. roo-code-memory-bank repo - decisionLog, mode rules - github.com/GreatScottyMac/roo-code-memory-bank/
65. Meetless: Memory Bank explained - method mechanics - research.meetless.ai/methods/memory-bank
66. Aider: Specifying coding conventions - CONVENTIONS.md pattern - aider.chat/docs/usage/conventions.html
67. Yellhorn MCP intro - issues-as-planning-boards - blog.connectly.ai/say-goodbye-to-lost-ai-agents-introducing-yellhorn-mcp-b564d4f27d26
68. InformationWeek: How SDD reshapes dev - senior-engineer spec behavior - informationweek.com/devops/how-spec-driven-development-is-reshaping-software-development
69. Augment Code: What SDD gets wrong - spec rot, agents execute stale specs - augmentcode.com/blog/what-spec-driven-development-gets-wrong
70. Sibylline: The Problems with SDD - specs-as-suggestions, 70-90% impl - sibylline.dev/articles/2026-01-28-problems-with-spec-driven-development/
71. ianhxu agentic-engineering-field-study: 04-sdd - size mismatch, review burden, illusory control, MDD - github.com/ianhxu/agentic-engineering-field-study/blob/main/04-spec-driven-development.md
72. Manorrock/Vidocq: Spec Kit Learnings real-world - agent drift audit, verifiable-constraints rule - manorrock.com/blog/2026/07/29/spec_kit_sdd_in_practice.html
73. jlevy/speculate: lessons_in_spec_coding - slop acceleration, trivial tests - github.com/jlevy/speculate/blob/main/about/lessons_in_spec_coding.md
74. arXiv 2602.00180: SDD From Code to Contract - 3 rigor levels - arxiv.org/html/2602.00180v1
75. productbuilder.net SDD 2026 guide - level adoption reality (most teams spec-first) - productbuilder.net/learn/spec-driven-development
76. Tessl registry: tessl-labs/spec-driven-development tile - skills/rules inventory - tessl.io/registry/tessl-labs/spec-driven-development
77. Local: .devin/plans/2026-08-31-prd-vertical-slice-example.md - bundle plan format - repo file
78. Local: .devin/ARCHITECTURE_MANIFEST.md - constitution-equivalent - repo file
79. Local: .devin/ledgers/grilling-frontier.md - OUTCOME/CHECK/EXPECT/EVIDENCE format - repo file
80. Local: skills/ listing + .devin/adr/README.md - skill inventory, ADR convention - repo

**Gaps:** Bockeler's original martinfowler.com SDD article URL not directly verified (secondary at 59-61); no controlled quantitative productivity study beyond InfoQ's review study - most outcome claims are practitioner field reports.
