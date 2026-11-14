# audit-r6 -- issue map

Sixth audit round. Scope: never-audited surfaces -- 17 hook scripts
(constraint-pinning, context-budget, check-ai-signature,
destructive-gate, gh-pr-assignee, memory-post-exec, no-em-dash,
pre-exec-guard, pre-write-guard, render-user-hooks, session-start,
silent-error-review, spec-consistency, user-prompt,
validate-refinement-evidence, validate-skill-format), 28 skill
scripts (memory-management, obsidian-workflow, dma tools,
dispatching-parallel-agents, context-hygiene, devin-config,
youtube-fetcher, wizard, grilling), 9 unaudited extensions
(diagram-tools, hyperframes, image-forensics, mesh-utils, offsec-tools,
ppisp-prep, rea-ops, rz-ops, spline-operator), install.sh
extensions loop.

| # | File | Defect | Severity | Status |
|---|------|--------|----------|--------|
| 01 | scripts/memory-post-exec.py | unguarded load_note kills hook on non-UTF8 note | P2 | resolved |
| 02 | extensions/ppisp-prep/ppisp_runner.py | subprocess no timeout, OSError uncaught | P2 | resolved |
| 03 | skills obsidian-workflow x3 + audit-memory.py | unguarded per-file open aborts scan | P3 | resolved |
| 04 | skills/dma/tools/jwt_tool.py | malformed token traceback, not die() | P3 | resolved |
| 05 | install.sh | empty extension dirs copied + reported installed | P3 | resolved |

## Scanned, clean

- 0-try scripts pre-exec-guard/session-start/user-prompt/
  render-user-hooks are thin _hookrun dispatchers -- correct by
  contract. pre-write-guard stdin-guarded.
- silent-error-review: stdin guarded, output str-normalized.
- compact-gate taskkill has timeout=10 + OSError/SubprocessError catch.
- query-memory.py guards per-file reads already.
- agent-reach/hyperframes/offsec-tools/rea-ops/rz-ops wrappers:
  subprocess list-form, TimeoutExpired + FileNotFoundError caught.
- diagram-tools plantuml: urllib timeout=30, broad except -> _fail.
- mesh-utils, image-forensics/verdict, laya eval_decisions,
  remotion-render/render: typed _fail or guarded json.loads.
- transcribe.py: whisper subprocess timeout=600, CalledProcessError
  handled.
- Parked: render-user-hooks --merge missing-arg IndexError (installer
  always passes CFG; manual misuse only). capture-memory --file
  missing-file traceback (explicit single-arg dev tool).
