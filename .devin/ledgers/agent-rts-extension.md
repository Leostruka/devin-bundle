# GATES: extensions/agent-rts (DevinCraft 3D RTS orchestrator)

- [x] G1: design doc exists with mapping table + WS protocol + ECS FSM
  CHECK: test -f .devin/research/AGENT_RTS_GAME_DESIGN.md
  EXPECT: file exists, sections 0-12
  EVIDENCE: written this session

- [x] G2: backend boots + snapshot schema valid
  CHECK: python extensions/agent-rts/selftest.py
  EXPECT: all asserts pass, exit 0
  EVIDENCE: "14 checks, 0 failed" fresh re-run (boot, /health, /snapshot schema, WS hello+snapshot, index 200, js module 200, vendor three.js 200, /intent file, /cmd refresh_repo, /decisions 404, /event append, /score, no tracebacks)

- [x] G3: collectors return real repo data (branch, dirty, worktrees, issues-or-skip, gas, supply)
  CHECK: live boot --root . + GET /telemetry
  EXPECT: repo.* keys present, no tracebacks
  EVIDENCE: branch=milestone/v3.8.0, dirty=[3 real paths], worktrees=[1], issues=[13 GH issues w/ titles+ages+labels], gas/supply/forge/ledgers sections present

- [x] G4: 3D client loads + theme swap + order POST writes intent file
  CHECK: headless Chrome screenshot + live WS order
  EXPECT: scene renders, both themes distinct, intent file created
  EVIDENCE: medieval screenshot rendered (terrain+buildings+units+HUD+minimap+13 real GH issues); office theme rendered via #theme=office deep link (distinct office floor/desks, theme pill=office); zero boot errors (#booterr overlay absent); WS order -> ack ok -> .devin/rts/intents/i1792856078029.json written w/ kind=order (test file removed after check)

- [x] G5: skill registered + bundle gates green
  CHECK: python audit.py && python -m pytest -q
  EXPECT: 0 errors, tests pass
  EVIDENCE: skills/agent-rts-commander/SKILL.md created; manifest.json synced to 84 skills (name+purpose via .devin/notes/sync-skill-meta.py); audit.py "Errors: 0" (1 pre-existing warning: post-exec.py script hash, identical in HEAD); pytest "1685 passed, 4 skipped"
