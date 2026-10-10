# GATES: red-team capability (REA adaptation + domain research)

Spec: `.devin/scratch/optimized_ready.md` | Branch: `feat/red-team-capability`

## Fase 1 — research + proposed architecture (stops for approval)

- [x] G1: REA analysis exists with required sections
  CHECK: test -f .devin/research/rea-analysis.md && grep -c "^##" .devin/research/rea-analysis.md
  EXPECT: file exists; sections cover architecture, tool catalog, Hopper/Ghidra bridges, investigation/evidence model, port-vs-reimplement
  EVIDENCE: 8 `##` sections; covers monorepo layout, 126-tool catalog, provider bridges, evidence model, CLI-wrap decision (npx verified: `rea-agents@latest` 4.1.0, `doctor --json` ok on host)

- [x] G2: coverage matrix exists with >=20 cited sources per domain
  CHECK: test -f .devin/research/red-team-domains.md && grep -c "http" .devin/research/red-team-domains.md
  EXPECT: file exists; >=20 sources/domain x 6 domains; every source has URL + type; critical claims marked cross-validated
  EVIDENCE: 143 http lines; per-domain counts RE=22 Web=22 Net=26 WiFi=25 FW=27 Mob=21; types doc/paper/std/forum; `xv` cross-validation markers; section 9.1 WSL/Docker tiers

- [x] G3: proposed architecture lists skills/extensions/profiles + routing
  CHECK: grep -l "routing" .devin/research/rea-analysis.md .devin/research/red-team-domains.md
  EXPECT: architecture section present, approved by user before Fase 2
  EVIDENCE: routing section in rea-analysis.md; architecture presented in-thread (skills x7, extensions x2, agent, tests); user replied "aprovado"

## Fase 2 — implementation (post-approval)

- [x] G4: new skills follow bundle convention
  CHECK: python scripts/validate-skill-format.py skills/<new-skill>/SKILL.md
  EXPECT: PASS per skill; SKILL.md <=~10KB; 'Use when' frontmatter; reference/ for detail
  EVIDENCE: `python scripts/validate-skill-format.py` -> Total: 198  Passing: 198  Failing: 0 (7 new skills included, triggers: [user, model])

- [x] G5: extensions follow wrapper.py pattern
  CHECK: py_compile on each new extensions/<name>/wrapper.py; lazy deps; no new runtime
  EXPECT: compiles; deps installed on demand only
  EVIDENCE: `python -m py_compile extensions/rea-ops/wrapper.py extensions/offsec-tools/wrapper.py` exit 0; stdlib-only; lazy `shutil.which` discovery; smoke: `capabilities` -> 30 tools, contract_violation on missing window/roe, `doctor` -> wsl: available, docker: unavailable (daemon off), tools honest `unknown`

- [x] G6: scope contract on every offensive skill/extension
  CHECK: grep for target/window/ROE fields in each new SKILL.md + wrapper contract
  EXPECT: all present; no auth disclaimers; destructive actions require explicit confirmation; no credential harvesting
  EVIDENCE: test_red_team_skills.py asserts contract fields + Boundaries in all 7; wrappers enforce require_contract (exit 2) and requires_confirmation (exit 3) gates; catalog contains no credential-harvesting tools; `run --tool nmap` without --confirm -> `requires_confirmation` observed

## Fase 3 — gates

- [x] G7: contract tests green
  CHECK: python -m pytest tests/validation -q
  EXPECT: 0 failures; one contract test per new skill
  EVIDENCE: 234 passed in 38.57s (test_red_team_skills.py: 10/10); interim failures fixed: U+2014/U+2192 chars purged (ASCII-clean verified), TOOLS-MAP count 68->75

- [x] G8: install.ps1 covers new components
  CHECK: powershell -File install.ps1 -DryRun
  EXPECT: exit 0; new components covered or install.ps1 updated
  EVIDENCE: exit 0; DryRun lists `would install` for red-team, re-binary, web-probe, net-probe, wireless-probe, firmware-probe, mobile-probe, agents/red-team-lead.md, extensions/rea-ops, extensions/offsec-tools via generic enumeration; install.ps1 untouched

- [x] G9: audit clean
  CHECK: python audit.py
  EXPECT: 0 errors
  EVIDENCE: `python audit.py` -> Errors: 0, Warnings: 1 (pre-existing __pycache__ listing only); manifest synced (skill_count 75, agent_count 7, export_hash sha256 per component); README counts updated (badge skills-75, 7 perfis); git diff --check: 0 issues; sig/secret scans clean

## Incident 2026-10-09 — free-tier rate-limit burn + apparent freeze

Evidence: CLI log `%APPDATA%\devin\cli\logs\devin_20261008-230609_8388.log`,
session `plural-woolen` in `cli\sessions.db`.

- 5,006 message nodes / ~9.8 MB chat churn in one session; 0 `run_subagent`
  tool calls — bulk burn was main-context work (813 `grep` calls) on
  swe-2-max (free tier).
- Kill shot: `skill` invoke on frontmatter `agent:`/`subagent:` skills
  dispatches a real autonomous subagent. A batched invoke spawned `debugger`
  (debugging skill) which ran unrequested work (em-dash sweep on
  rea-analysis.md) and consumed the remaining quota; the `research` invoke
  then failed at the rate-limit wall. 14 skills carry this frontmatter.
- 03:45-04:38 UTC: upstream HTTP 502/EOF storm; nested retries (5x stream
  x 3x control-loop) resend full context per attempt. ~50 min of silent
  retrying = perceived freeze.
- 04:38-04:41 UTC: `Reached free model rate limit`; 3 session/prompt calls
  exhausted retries -> turn died mid-Fase-1 (red-team-domains.md not written).
- Foreign rules injection: `.devin/scratch/rea-repo/AGENTS.md` lazy-loaded
  into any session touching the clone (~6KB of REA/Turborepo rules) and
  caused system-prefix churn (MessageChain cache busts 02:08, 03:27).

Fixes applied:
- `rea-repo/AGENTS.md` renamed to `AGENTS.upstream.md` (content preserved;
  rules loader matches filename exactly).
- Stripped `agent: debugger` from `debugging` (repo + installed),
  `diagnosing-bugs`, `debug-ci-failures` (installed). Invoke now loads
  guidance in-context; explicit `run_subagent profile=debugger` unchanged.
- `skill-discovery` (repo + installed): batched-invoke rule now warns that
  `agent:`/`subagent:` frontmatter = real subagent spawn; max one per task.
- `validate-tool-args.py` unwired by design since e6f69e3 (bundle-slim);
  not restored.

Not locally fixable: CLI-internal retry policy and free-tier quota are
server/binary-side. Mitigation is workload shaping, below.

Resume plan for G2 (batched to fit free tier):
- One domain per session/batch; web_search triage first, deep fetch only
  for accepted sources; <=3 sequential `researcher` subagents (never
  subagent_explore); append sources to `red-team-domains.md` incrementally
  so a rate-limit stop loses at most one batch.
- Do not clone foreign repos inside `.devin/` — keep them outside the
  workspace or strip their AGENTS.md/rules files on arrival.
