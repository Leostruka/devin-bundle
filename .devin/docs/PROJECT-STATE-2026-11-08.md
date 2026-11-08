# Project State - 2026-11-08 (surfaces -> deep)

Branch `fix/gcal-validation-ics` (PR #422). Repo = versioned source of a Devin
CLI bundle; live config at `%APPDATA%\devin` is the installed copy. Sync via
`install-ledger.py record` + file copy; `export.ps1 -DryRun` verifies the
8-step distribution pipeline.

## 1. Install / identity plane

- `data/bundle-identity.json` pins `validated_cli_version` (now `3000.12.28`).
- `install.ps1`/`install.sh` distribute: skills, agents, hooks, scripts,
  config.json merge. `install-ledger.py` snapshots file hashes into
  `data/install-ledger.json`; `audit.py` warns on drift.
- `check-tools.py` (deterministic, no network) + `export.ps1` 8/8 verify the
  artifact set. Live `devin doctor`: 26 custom subagent profiles, OTEL off.

## 2. Governance plane (hooks + audit)

- ~45 hook/guard scripts in `scripts/` wired via `hooks.v1.json` +
  user-config merge: PreToolUse guards (destructive-gate, architecture-gate,
  pre-write-guard, laya-guard), PostToolUse (post-exec, memory-post-exec,
  silent-error-review), UserPromptSubmit (constraint-pinning, skill-picker,
  user-prompt), Stop/SessionEnd (stop-guard, memory-stop, check-push-green),
  SessionStart (session-start), PreCompact/PostCompact (compact-gate).
- `audit.py` = 39 sequential checks covering manifest/hash consistency,
  skill format, ledger drift, plus the new regression classes:
  - [36] ok-envelope mains must exit non-zero on `{"ok": false}`.
  - [37] AST-precise `subprocess text=True` must pin `encoding=`/`errors=`.
  - [38] text-mode file I/O (`open`/`read_text`/`write_text`) must pin utf-8.
  - [39] text-mode `sys.stdin` reads must reconfigure utf-8/replace.
- `global_rules.md` codifies the same conventions for new code.
- CI `ci.yml` gates: py_compile sweep, `check-ai-signature.py`,
  skill-format validation, `git diff --check` (whitespace), pytest matrix
  (3 OS x 2 py), installer matrix, rust workspace. Known gate classes fixed
  this week: AI-signature false positives in eval JSONs (reword data),
  `.ics` CRLF (now `.gitattributes` `eol=crlf whitespace=cr-at-eol`).

## 3. Issue / tracking plane

- Local issues: `.devin/issues/ISSUE_*.md` + `.devin/scratch/` DAG issues;
  vocabulary in `.devin/agents/triage-labels.md`.
- `roadmap-board.py` renders the issue DAG per effort + capacity/WIP view
  (#417). Capacity report: ~190 issues total, frontier ~95.
- GitHub issues are the tracking source for the self-improvement loop
  (#395-#430 wave: gcal hardening, status vocab, write-path, OAuth,
  PowerShell preflight, reel/YouTube evaluations, Laya campaign).
  This week 26 verified-done issues were closed; open remainder: #346
  (umbrella) and #431 (Laya activation checklist).

## 4. Calendar / planning plane (the #346 ladder)

- `extensions/gcal/` wrapper + `gcal.py`: OAuth (installed-app flow,
  credentials in live config only), dedicated `AGdevin` calendar,
  free/busy reads, roteiro apply with `--confirm` gate, typed errors.
- `.devin/apps/agenda-roteiro/APP.md` = the micro->macro compose layer:
  day roteiros (`.devin/scratch/dev-org-ladder/*.md/.ics`), week route
  written to GCal (10 events, `[week]` prefix, 0 failures).
- Weekly route: Mon GCal/ICS/OAuth; Tue write-path + status vocab; Wed
  scratch hygiene/PowerShell preflight/PR closeout; Thu YouTube batch +
  evals + ladder scoping; Fri buffer/spillover.
- Free-time protocol: gaps consumed by explore->research->file-issues.

## 5. Laya decision engine (deep)

- `extensions/laya-tools/`: `layad.py` resident daemon (authenticated
  socket), `laya_worker.py` stdio JSON-lines worker, `decision_client.py`
  (utf-8/replace line-buffered pipes), `decision_contract.py` (closed-world
  request validation: profile/mode/state-key blocklist, finite numerics,
  size caps), `capture_eval.py`/`eval_decisions.py`/`fit_calibration.py`
  (frozen-manifest capture, scoring, platt+isotonic-PAVA fits with separate
  held-out scoring).
- Fixes shipped: `pin_stdio_utf8()` (cp1252 mojibake -> surrogate tokenizer
  crashes), `warm_engine()` (first-request cold CPU >1s deadline_ms -> 16/20
  misses were idx-0 artifacts; residual misses on large dynamic candidate
  sets documented).
- Eval campaign complete: all 14 profiles have frozen + held-out evidence
  under `.devin/evals/laya/<profile>/`. Verdicts:
  - `media-intent-v1`: only strong candidate - 40 held-out, adopted@0.9
    22/23 = 0.9565, single wrong-adoption class documented.
  - `media-preset-v1`: 1.000 decided but 0.31 coverage (conservative).
  - `issue-category-v1`: 0.833 decided, confidence carries no signal.
  - `skill-pick-v1`: 0.826 combined; high-conf wrong picks on overlap.
  - `knowledge-label-v1`: downgraded to 0.000/0.0625 (small-sample artifact).
  - `ui-target-v1`: dangerous wrong-element commits - not viable.
  - `cmd-risk-v1`: under-classifies severity - not viable for a guard.
  - compact-* / review-risk / output-context / skill-family / filebool:
    abstain or below threshold (structured/trajectory state exceeds the
    checkpoint; accuracy decays with label cardinality).
- Meta-pattern: prose state + distinct intent labels engage; JSON digests,
  session trajectories, single-word labels do not. Calibration cannot fix
  semantic confusion.
- `profile.json` keeps `mode: off` everywhere; deterministic checks remain
  authoritative. #431 holds the 7-step activation checklist; items 1-4 are
  pre-staged (checkpoint vendored to `.devin/laya/models/english/` with
  matching sha256, proposal JSON, calibration map draft); items 5-7
  (mitigation, off->shadow->assist transition, held-out re-run) stay
  deliberate.

## 6. Extensions plane

- 28 extensions audited this week; hardening fixes pushed:
  stock-footage/voicebox/hyperframes (overwrite + arg-parse guards),
  plantuml (https + 32MiB cap + -o guard), meshops (exists-check + dst
  guards), code-graph selftest (subprocess timeout).
- Media pipeline verified end-to-end: asr transcribe -> scene plan v2 ->
  `plan_check` gate (now validates visual-prop contracts incl. bool/NaN/
  fps) -> remotion render -> `composite.py` overlay (ffmpeg, exit-code
  fixed) -> `final-narrated.mp4` artifact ffprobe-verified.
- `extensions/computer-use/` + `scrape-tools/` `.venv` dirs are runtime
  artifacts (gitignored, untracked).
- Encoding sweep applied across extension subprocess/file I/O sites.

## 7. Devin CLI compat

- `DEVIN-CLI-COMPATIBILITY.md` tracks per-version capability decisions.
- 12.17 -> 12.28: changelog unpublished; probed binary - `devin sandbox`
  subcommand (WSL-2-only on Windows, unchanged), `--respect-workspace-trust`
  (-p fails in untrusted dirs), manual `irm` update path. No config change
  required; doctor 3/3; compat tests 6/6.
- Plugins: none installed; bundle deliberately stays on installer path
  (plugin hooks are fail-open; bundle hooks are guardrails).

## 8. CI/CD

- Push cadence: audit + focused tests per change, full suite before push
  (~2350-2361 passed / 8 skipped across the week), `check-push-green.py`
  hook reruns validation+held-out (531 passed).
- PR #422 carries the gcal/status-vocab/laya/extension-hardening series;
  static gate fixed for signature false-positives + `.ics` CRLF + README
  trailing space.

## 9. Open frontier

- #346 umbrella: ladder delivered; closeout pending PR merge.
- #431: deliberate activation decision (mode stays `off`).
- ISSUE_02/05 held-out: blocked on fresh datasets.
- ISSUE_03 craft-bridge: blocked on storytold CLI installs.
- `edge-audit` effort (61 open issues) parked as next-week triage.
