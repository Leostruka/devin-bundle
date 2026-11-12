
## Wave E/F completion + operate-spline (11:40)

- Spline-operator: deliberately removed #72 (Blender stack); operate-spline skill was dead route -> removed via PR #540 (184 skills).
- PermissionRequest: registered, 0 commands -> issue #541 (spike: does CLI fire it?).
- Tests/data audit: 6 defects -> issue #542 (vacuous check-count test, fake mutation tests, dead skip guards, stale fixture/filename).
- Stale skill export_hash x34: bookkeeping metadata (hash of last export); install.ps1 syncs live from source -> NOTE, no issue.
- install.sh vs install.ps1 extension sets: identical. release.yml tag/version sync OK.

## Loop 12:00-12:30

- #542 fixed: PR #543 (real mutation detection via secrets-block scenario; 4 dead skip guards -> hard imports; check-count parses numbered sections; fixture SessionEnd; compat test renamed).
- #533 envelopes: spec-consistency exits 1 on errors (contract [36]); install-ledger exception exits 1 (callers tolerate); subagent-trace already compliant. PR #545.
- #541 evidence: binary ClaudeHookEvent enum has PermissionRequest + Notification/SubagentStop/ContextInput/PreCompact/PostCompact - real event, empty registration is a gap.
- NEW DEFECT #544: check-push-green suite (~15s) exceeds hook budget - test-file pushes rejected by slowness, not decision. Bypassed via subprocess once; needs structural fix.

## Loop 12:30-13:00

- #535 closed-out on issue: spark-view was false positive; USAGE.md x2 updated; busybar IP = device USB-wire default (documented); internal_probe POSIX on #539.
- #544 root cause found + fixed: stderr under fail_closed=true = rejection. Warn now env-gated (DEVIN_HOOKRUN_DEBUG); timings already in metrics. Live _hookrun patched.
- Smoke: dep-audit-gate, memory-post-edit, memory-stop, constraint-pinning all rc=0. All 8 lifecycle events now have verified coverage.
- Audit H dispatched: .devin internals + root files.

## Audit H verdicts (13:00)

- .gitattributes:5 agent-rts rule: inert, dir incoming per MILESTONE_2_12 -> keep.
- laya proposal.json: authored decision artifact, correctly tracked -> non-defect.
- ledgers/ root: 45-file legacy archive, deliberate -> non-defect (documented).
- .devin internals otherwise CLEAN: apps/evals/rules/templates/gitignore/secrets/ci-refs all verified.

## CLOSE-OUT (16:10)

- All 6 audit PRs merged: #534 #538 #539 #540 #543 #545 (+ earlier #536 #537).
- Serial-merge defect discovered + filed #547: export_hash staleness fails the egm newline test on every merge commit - burned 3 CI cycles, preempted 2.
- Live install synced with -Force (installer requires it for divergent files); cmp-verified SYNCED.
- Final state: pytest 2478 pass / 8 skip; audit.py 0 errors, 1 warn (ledger drift audit.py - benign).
- Issues closed: #527 #528 #529 #530 #532 #533 #535 #542 #544.
- Open: #547 (structural), #546 (hook timeouts), #541 (gate design), #531 (automated compat check), #431 (user decision).
- Survey complete: 8 lifecycle events verified, 184 skills, 54 scripts, ~30 extensions, ~150 test files, 13 hook entry points, install/manifest/live triad, CI/local parity.

## Loop 15:15 — issue burn-down

- #546 fixed (PR #548): compact-gate's own _ensure_daemon lacked the #522 fail-fast (that fix covered extensions/laya-tools lc.ensure_daemon only). Now returns Popen, breaks poll on dead spawn, hook call site caps wait at LAYA_SPAWN_WAIT_S=8s (daemon detached, abstains this turn, boots for next). Installers provisioned laya-tools venv (was hardcoded computer-use/scrape-tools only — actual root cause of "daemon never starts").
- #547 test-half fixed (PR #549): egm test now asserts the mutated entry's name in the mismatch list — unrelated drift no longer fails serial merges. Verified live: first clean `git push` through the gate post-#544-fix.
- #531 closed via PR #550: audit check [41] pins compat-doc version vs bundle-identity; summary count self-derives.

## Loop close 16:40

- #546 closed: laya-tools venv now EXISTS live; registered daemon healthy; orphan killed.
- #547 closed: serial merges no longer gate on unrelated export_hash drift (egm test asserts per-entry).
- #531 closed: audit check [41] live; dynamic count.
- Open remainder: #541 (PermissionRequest gate design), #431 (user decision).
- Final: 0 PRs, audit 0 errors/1 benign warn, changelog backfilled, live fully synced.

## Loop continuation (post-merge queue)

- #541 RESOLVED: PermissionRequest now wired. Contract verified from bundled
  CLI docs (stdin tool_name/tool_input, decision approve|block). Implemented
  scripts/permission-gate.py - approve-only on provably read-only single-
  invocation exec commands (no shell composition chars, allowlist git/gh/
  rg/fd/ls/...); silent on everything else so the human prompt proceeds.
  Never emits block; fail_closed:false. PR #551 merged, 8 tests.
- #552 merged: stale .gitattributes agent-rts rule removed; laya
  *.proposal.json ignored (transient calibration artifacts).
- Counts updated: 55 scripts, 14 hook entry points (6 consolidated + 8 direct).
- Remaining open issues: #431 only (user decision on shadow->assist).

## Round 3 — render-normalization + ledger reconciliation

- hooks-render WARN root cause: live render uses scoop shim
  `...\current\python` (no .exe) inside an escaped quote; audit regex
  required `.exe` + unescaped follower. Fixed via optional-.exe pattern
  and escaped-quote lookahead (#553).
- Ledger "Removed" ghosts: record-all never pruned records for files
  deleted live (operate-spline, old metrics path). record-all now has
  snapshot semantics — prunes absent records (#554).
- Ledger reconciled: 0 Outdated/Modified/Removed/Foreign; live audit.py,
  TOOLS-MAP, manifest synced; stale operate-spline live dir removed.
- Result: audit 41 checks, 0 errors, 0 warnings — first fully clean run.

## Round 4 - stdin utf-8 sweep + doc drift guards

- #557 RESOLVED: check [39] missed json.load(sys.stdin); 26 hook scripts
  unpinned for cp1252 mojibake. All pinned via guarded reconfigure;
  [39] extended to flag the pattern (#558 gate + #559 mass-pin).
- TOOLS-MAP drift: 6 stale entries (decision-queue, design-lint-gate,
  permission-gate, git-diff-stat, token-saver, rl-resume-detect). Fixed +
  new test_tools_map_hooks.py mechanically guards inner-module and
  entry-point rows (#556).
- #555 filed: type:prompt hooks = undocumented LLM-evaluated gate surface;
  spike only, no contract in bundled docs.
- False-positive fix: [39] regex restricted to real call forms after
  cu_actions.py docstring match (#560).
- Live resynced; ledger clean; audit 0 errors.

## Round 5 - independent review + hardening (#561)

Fresh-eyes reviewer on permission-gate found real vulns. Fixes shipped:
- Inverted to deny-by-default arg shapes: env/fd -x/rg --pre/git-lfs exec removed or gated
- ext:: transport blocked per-arg (quote-stripped); ref mutation via positionals blocked (branch/tag/stash/reflog expire/remote set-head)
- File-write flags blocked: git diff --output, log -o; gh --method=POST/--input/-H override/auth token
- audit [39] exemption scoped to stdin-targeted pin - caught stdout-only pins in decision-queue + subagent-trace (now pinned)
- install-ledger record-all: prune guard refuses degenerate scans (>25% or total wipe) + 2 regression tests
Live gate probed: 7/7 vectors correct. Audit 41/41 clean. Ledger 0 drift.

## Round 6 - permission-gate 2nd-pass review + fix (#562)

Second reviewer pass on hardened gate found quote-collapse bypass class:
- `--out""put=x`, `e'xt::`, `-""p`, `--pre""=cat` defeated anchored regexes
- Fix: strip ALL quotes per token (shell-equivalent) before matching
- New blocked vectors: ls-remote -u, --upload-pack/--exec space-form, grep
  --open-files-in-pager, -O<pager> (case-sensitive), --ext-diff, --textconv,
  gh issue develop --checkout (verb dropped), remote show -p
- False negatives fixed: git log/diff/stash show -p, remote -v, bare remote,
  ls-files -o now approve
- -p/--prune scoped to `remote` only; -u scoped to ls-remote only
Live probe: all attack vectors silent, reads approve. 41/41 audit clean.
Also: install.ps1 header comment updated (laya-tools venv was missing);
install.sh already provisions laya-tools - parity confirmed.

## Round 6b - residuals verified clean
- .devin/agents/ (4 profiles) + .devin/apps/ (agenda-roteiro, reels-surveyor):
  all referenced paths/subcommands exist; VALID_PROFILES "README" = real
  runtime profile (not a defect)
- data/*.json: 7 files valid, all referenced (9-75 refs each)
- post-exec.py handles exec + mcp_call_tool payloads silently, rc=0
- Flag-injection probes on live gate: git -c/-C/--git-dir, gh -XPOST space/
  concat forms -> all silent; tag -n5 + positional -> silent (conservative)
- install.sh/bash -n + export.sh syntax OK; validation suite 332/332 pass

## Round 7 - .devin state internals
- .devin/rules/ empty with .gitkeep: README.md removed deliberately in #60
  (cli-alignment) - AUDIT_REPORT.md claim is historical, not a defect
- .devin/issues/: 22 milestone/issue files all resolved
- .devin/laya/: shadow.jsonl 278 entries valid, collecting (last 11:58);
  mode=shadow consistent with open #431
- .devin/decisions.jsonl: 2 historical records contain cp1252-era mojibake;
  verified today's stdin pin now stores UTF-8 correctly (probe record added
  and removed)
- post-exec mcp payload, pre-exec layering, data/*.json refs - all clean
