# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- CI path filter: docs-only PRs skip test/rust/install matrices via `changes` job (#487)
- push-gate: budgeted deferral — held-out always, mapped tests get remaining ~50s budget, overflow defers to required CI by name (#484)
- ship-metrics: DORA lead-time log `.devin/metrics/ships.jsonl` + report (#486)
- push-gate: `audit.py` root-file scoping slimmed to fast audit check (#484)
- api-bridge `--backend acp`: warm ACP process — real incremental SSE deltas + real token usage (#489)

- api-bridge extension (#478, #479, #480, #481, #482, #483): OpenAI-compatible local API over `devin -p` — `/v1/chat/completions` + `/v1/models` on loopback/LAN (token-required off-loopback); isolated workdir per request; E2E-verified translation ("bridge" -> "ponte"). v0.2: model validation, error taxonomy (400/502/504), estimated usage; v0.3: `--concurrency` semaphore, CORS preflight, `x-ignored-params`, self-describing `GET /`, `devin`-alias fix, deep `/health` (503 on missing backend).
- skill `devin-integrate` (#490): embed-Devin-anything playbook — direction matrix, transport ladder, verified surface inventory, contract checklist (origin: Busy Bar reel evaluation).
- push-gate docs-only risk tier (#484): pushes whose changed paths are all doc surfaces (`*.md`, docs/, .devin content dirs) skip the full suite — the suite now exceeds the outer hook budget (~150s), so a mid-run kill never wrote the green cache and every push ran cold; cheap checks (secrets, test deletions) still run on every push.
- state snapshot wave update + final (#475, #477).

- dead-code removal + `# public-api` def-line convention + install-ledger rendered-currency/artifact exclusion (#473); state snapshot wave update (#475).
- push-gate green cache (#476): verified-green verdict cached per HEAD+tree fingerprint in .git/push-green.json; repeat pushes on an unchanged surface skip the ~150s suite phase.

- simplify-scan unreferenced_def restricted to module top-level defs + `@pytest.fixture` exclusion (#471): findings 30 -> 13.
- install-ledger `.devin/` remap (#472): live `docs/`, `docs/plans/`, `docs/templates/` now compare against `.devin/docs`, `.devin/plans`, `.devin/templates` sources; corpus index covers remapped docs. False Outdated drift 75 -> 0.
- dead-code removal: `find_binary` (bitnet_adapter), `_search_csv` compat shim (design-intelligence), `SECURITY_ATTRIBUTES` (probe_spawnpty), unused test helpers (`_channel_pair`, `_spawn_ok`, `_evs`, `_lines_with`). Scan unreferenced_def 9 -> 6 (remaining = dispatch stubs/public API).
- fail-soft annotation wave (#469): all 103 unannotated `except: pass` sites across system-control/computer-use/laya/gcal/design-intelligence + hooks/scripts/tests annotated with `# fail-soft:` reason; scan except_pass 103 -> 0.
- silent-error-review `overflow_path` adoption (#470): PostToolUse truncated results carry `tool_response.overflow_path` to the complete output (field verified empirically on 3000.12.43); hook now scans full file <=8 MB so tail errors are caught; finding snippets prefer error lines.
- pulse frontier fix (#461): `**Status:**`/`**Blocked by:**` bold-colon forms now parsed; frontier consumes `status_vocab` canonical statuses + archived-effort exclusion. Phantom claimable backlog 168 -> 0; issue 04-jev triaged resolved.
- simplify-scan sibling-reraise pass (#466): `except X: raise` sibling marks `except: pass` as intentional fail-open. except_pass findings 110 -> 103.
- handoff skill adopts acp-summarizer schema (#460): Overview / Key Details & Breadcrumbs / Current State; breadcrumbs = re-readable paths.
- margin evidence for laya media-intent (#463, #431 item 5): runner-up recapture on frozen heldouts; margin gate rejected (error inside correct band).
- ACP session modes + client fs-gateway documented (#464): ask/plan modes delegate fs reads to client; silent deadlock if capability undeclared.
- simplify-scan precision pass (#459): TODO/FIXME/HACK/XXX markers restricted to comment text; annotated `except: pass` fail-open suppressed; pytest `test_*`/`Test*` defs no longer counted unreferenced. Scan noise 2612 -> 149 actionable items.

- laya worker emits `raw_runner_up_probability` alongside `raw_top_probability` from `distribution` or `probabilities` keys (#458, feeds #431 item 5): held-out margin evidence showed confident-wrong failure (mi-h14 margin 0.9365), so margin gating was rejected as an activation discriminator.

- devin-cli alignment 3000.12.28 -> 3000.12.43 (#457): acp server agent-types (summarizer/review/codemap) + --cloud relay, DEVIN_MODEL/DEVIN_REFUSAL_FALLBACK env, desktop/forward/migrate/setup/uninstall commands, cloud drs blueprints. Eval issues #453-#456 filed for acp-review/codemap/summarizer/drs.

- reels-7/yt-batch2 eval batch (#434-#451, milestone 14; PR #452): 28 unique links deep-dived (transcripts + captions + 7 researcher waves) -> survey + 18 eval issues. Executed same-day: `scripts/rules-coverage.py` NL-rule->control audit (#439, 74.3% coverage, all security rules backed), `task-brief.py --require-done-when` + SKILL.md orchestrator re-verify contract (#438), `scripts/pulse.py` rts-intents drainer -> afk-loop frontier (#434).

- **Reels-7/YouTube eval batch closeout (#434-#451)**: 18 research-driven eval issues resolved - 11 shipped, 7 documented decisions.
  - `scripts/done-evaluator.py` (#437): writer-is-not-the-grader gate - deterministic contradiction scan (test-run state, unchecked acceptance, admitted skips) + `--emit-brief` for separate-tier grading; wired into `skills/afk-loop` verification step.
  - `scripts/subagent-trace.py` (#435): per-dispatch trace JSONL + `.devin/subagent-abort/<id>` kill channel; contract in `skills/dispatching-parallel-agents`.
  - `scripts/simplify-scan.py` (#447): rot scan (TODO/FIXME, oversized, unreferenced defs, except:pass); audit check [40] skills-debt staleness (#449).
  - `scripts/graph-query.py` (#442): graph-before-grep retrieval fusing code-graph FTS + memory cues; spike evidence 5/5 top-2 vs grep-OR 11-248 unranked hits.
  - `extensions/ai-tools/weight_patch.py` (#440): activation-guided weight patching PoC - contrast direction extraction, planted-defect repair on down_proj, honest negative control.
  - `extensions/ai-tools/dory_sweep.py` (#441): Dory1.0-4B loop sweep on laya heldout - k={1,2,4} table, flat 0.688 skill-pick / 0.438-0.562 issue-cat at 20-110x latency, defer verdict; requires dory-enabled llama.cpp fork (PR ggml-org/llama.cpp#30306).
  - `skills/impeccable` (#445/#446): state x motion coverage matrix + converge-by-gate bounded iteration (gate=lint+waivers, N=3, plateau/distill kill-switch).
  - `skills/lgpd-questionnaire` (#448): compliance questionnaire skeleton - data inventory, legal basis, subject rights, breach response.
  - `.devin/docs/DEVICE-AUTOMATION-LANE.md` (#451): 4 access classes (HTTP API > structured > GUI > bridge), device sketches, 6 safety boundaries.
  - Eval docs: `.devin/evals/{graphify-query,design-state-motion,design-iteration-loop,raea-vs-remotion,lgpd-questionnaire,jev-cloud-tier,busybar-integration}/` - raea = verified Rust+Bevy Remotion alternative (hybrid recommendation); Jev = verified TypeSafe AI decision API (spike deferred); Busy Bar = verified busylib HTTP device (spec + `extensions/busybar/push.py` skeleton).

- **decision-queue.py (#436)**: stop-hook module + CLI recording human-blocking stops to `.devin/decisions.jsonl` (fail-open); `roadmap-board.py` surfaces `pending_decisions` count in JSON and Markdown board output. `stop-guard.py` `_hookrun` chain updated. Closes the "agent stopped for a decision overnight" blind spot.

## [3.20.0] - 2026-11-09

- check-ai-signature.py: git author/committer identity is now checked, not just the commit message. `git -c user.name=<AI>`, `-c user.email=<bot>`, `--author=`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*` env vars and `git config user.*` with AI service identities (devin/claude/copilot/gemini/etc., `[bot]` emails) are blocked; human identity overrides stay allowed. Commit gate widened: `git -c ... commit` / `git -C dir commit` now reach the message check (adjacent "git commit" substring previously required). AGENTS.md Rule 2 + constraint-pinning updated: an AI identity is never the commit fallback. New held-out `test_check_ai_signature_identity.py` (17 cases incl. the incident command) + 2 consolidated-guard cases.

- swe-2-flash family integration (5 gaps closed): `bundle-models.json` now carries `free_until`/`free_tier_permanent` on all six swe-2/flash ids (`swe-2-*` free until 2026-11-30, flash until 2026-12-04T18:00:00Z, only `swe-2-flash-medium` permanent) plus `fast_role_model: swe-2-flash-high`. `context-pressure.py` resolves `role: fast` with `BUNDLE_FAST_MODEL` override and now honors `BUNDLE_{DEFAULT,MAX,MEDIUM,DEFAULT_SUBAGENT}_MODEL` env parity. Recipes: `audit` and `implement` route `preferred_model_role: fast`. Agent repins: bounded execution (`implementer`, `debugger`, `qa-ci`, `data-analyst`, `art-director`, `performance-engineer`) -> `swe-2-flash-high`; mechanical volume (`copywriter`, `sentinel`, `chief-of-staff`, `issue-tracker`, `triage-labels`) -> `swe-2-flash-medium`; judgment/exploration stays `swe-2-max`. `config.json` gains `preferred_family_models["swe-2-flash"]` and `agent.model`/`default_parent_model` move to `swe-2-max` (parent default; `is_default_parent` flag moved in registry). Docs: MODEL-GUIDE/TOOLS-MAP/SKILL-TIERS/README carry exact free-window dates and the post-2026-11-30 FREE-ONLY decision matrix. prompt-compiler: `swe-2-flash` family added to embedded fallback, self-test asserts, FIELD_PROMPTS/docstring examples, and new `knowledge_bases/swe-2-flash.json` (bounded-execution prompt rules) - `--list-models` now shows swe-2 + swe-2-flash. New `test_model_pin_contract.py` validation + held-out `test_swe2_flash_contract.py` gap checks.

- devin-cli alignment 3000.12.17 -> 3000.12.28: latest promoted build confirmed via `static.devin.ai/cli/current/manifest.json`; public changelog ends at 12.17 so the delta was probed on the binary. New documented capabilities: `devin sandbox` subcommand (`sandbox setup` prints platform prereqs - WSL-2 constraint unchanged on Windows), `--respect-workspace-trust` flag (non-interactive `-p` fails in untrusted dirs without it), manual `irm` update path on Windows. `validated_cli_version` bumped in bundle-identity.json + README; doctor 3/3, compat tests 6/6, audit 0/0.

- laya checkpoint vendored + activation proposal completed: english checkpoint (convaiinnovations/laya rev 7b928d82) copied from HF cache to `.devin/laya/models/english/` (gitignored, ~843MB) - re-hashes to identical artifact_sha256 54f69565... and live-verified end-to-end (load_engine digest check + warm_engine + real media-intent prediction: stylize_video @ 0.996). Proposal JSON now carries the concrete path; #431 items 1-4 fully pre-staged, items 5-7 remain deliberate.

- laya worker warmup fix (deadline_exceeded root cause): frozen manifests showed 20 deadline misses, 16 at case index 0 - first-request cold CPU latency (~>1s) eats the 1000ms deadline_ms budget while steady state is ~200ms. New `laya_worker.warm_engine()` runs one throwaway prediction before serving, wired into both entry points (`serve-stdio` main and `layad serve_socket`); diag reports warmup ms. Live-verified: post-warmup first request returns suggestion instead of deadline_exceeded abstention. Residual misses on large dynamic candidate sets documented in rollout issue 04. +2 tests.

- audit check [39] stdio utf-8 decode + 4 script fixes: files reading text-mode `sys.stdin` (JSON-lines workers, piped-content hooks) decode with the Windows locale codepage unless pinned - same mojibake/lone-surrogate class as the laya worker bug. Check flags `sys.stdin.read/readline` and `for line in sys.stdin` without `reconfigure`/`pin_stdio_utf8` (binary `sys.stdin.buffer` exempt). First run caught 4 un-pinned sites now fixed with the established `reconfigure(encoding="utf-8", errors="replace")` block: `scripts/context-budget.py`, `scripts/context-pressure.py`, `scripts/file-size-guard.py`, `scripts/design-lint-gate.py` (the two JSON-payload hooks were the real exposure). Live copies synced, ledger + manifest export_hash refreshed. Summary now reads "ALL 39 CHECKS".

- laya held-out sweep complete: issue-category-v1 held-out 0.833/0.75 (beats run01's 0.684; compressed confidences 0.11-0.76 leave room for a real calibration map - solid 2nd-tier triage); media-preset-v1 held-out 1.000/0.3125 (perfect precision, poetic phrasings abstain - conservative-suggester only). Every evaluated profile now carries held-out evidence.

- laya held-out corrections: knowledge-label-v1 held-out (16 fresh spans) acc 0.000/cov 0.0625 - run02 perfect-precision was small-sample artifact, DOWNGRADED not viable; skill-pick-v1 held-out (16 fresh goals, post-UTF8-fix) acc 0.667/cov 0.375, combined 46-case evidence 0.826 decided acc with gate-rejectable errors - borderline viable second-tier. media-intent-v1 remains the only strong assist candidate.

- stdio UTF-8 sweep (same cp1252 class as the laya fix): pinned `reconfigure(encoding="utf-8", errors="replace")` on stdin/stdout in `computer-use/mcp_server.py` (MCP JSON-RPC - spec mandates UTF-8), `computer-use/cu_session.py` worker_main (JSON-lines worker), `craft-bridge/ui_dsl.py`, `scrape-tools/parse.py`, `ai-tools/prompt_compiler.py` (piped-content readers matching their file-path utf-8 siblings), and `laya-tools/review_gate.py` via `dc.pin_stdio_utf8()`. Non-ASCII piped input no longer mojibakes; non-ASCII JSON output no longer fails to encode on Windows.

- laya worker UTF-8 stdio fix (root-caused engine_error:TypeError): worker sys.stdin/stdout used Windows locale cp1252 while all clients write UTF-8 - non-ASCII request text became mojibake with lone surrogates the Rust tokenizer rejects. Explains skill-pick-v1's 25 deterministic per-case TypeErrors (previously misreported as transient) and silently degraded filebool-v1's 7 non-ASCII cases. New `decision_contract.pin_stdio_utf8()` called from `laya_worker.main()` + `laya_cli.main()`; layad was already UTF-8-clean. Recaptures: skill-pick-v1 acc 0.882/cov 0.567 (corrupted run showed 1.000/0.133 - "extreme abstention" was a bug artifact; now borderline viable, second-tier behind media-intent-v1, one high-conf wrong on overlapping skills); filebool-v1 0.500/0.500 (yes-collapse persists, verdict unchanged). Production decision_client path equally affected - any non-ASCII state errored. +2 tests.

- laya media-intent-v1 held-out batch 2 + fit_calibration.py: +20 fresh cases (acc 0.929 decided, adopted@0.9 13/13). Combined held-out (40 cases never in fit): adopted 23, correct 22 -> 0.9565; sole wrong adoption remains the complaint->stylize_video class. New `extensions/laya-tools/fit_calibration.py` fits platt + PAVA-isotonic table maps on frozen manifests and scores adoption curves on separate held-out manifests (7 tests). Bake-off: isotonic table 0.9583 best structural candidate, all maps within Wilson noise, none separates wrong adoptions - residual risk is a model limitation needing consumer-side guard, not calibration. Activation checklist tracked in issue #431; mode stays off/shadow.

- laya calibration campaign COMPLETE - all 14 profiles evaluated (~250 frozen cases, real worker): media-intent-v1 only viable assist candidate (0.966 decided acc; held-out adopted 0.90 - shadow-only); media-preset-v1 0.875 borderline; issue-category-v1 0.684 best fixed-label; knowledge-label-v1 1.000/0.25 perfect-precision-low-recall; skill-pick-v1 1.000/0.133 extreme abstention + transient engine_error:TypeError (superseded - encoding bug, corrected 0.882/0.567); ui-target-v1 0.714 with dangerous __none__ commits; cmd-risk-v1 0.231 unsafe direction; compact-item/boundary/gate + review-risk 0/0 abstention on trajectory/structured state. Contract fixes: compact-item + knowledge-label dict-labels (bare-list criteria defect), laya-guard empty-goal dead lane. Assist OFF everywhere.

- laya media-intent-v1 calibration x3 + first viable assist candidate: run01 acc 1.000/cov 0.813, run02 acc 0.938/cov 0.667 (28/29 decided correct) - intents are distinct workflow destinations on natural-language state, the checkpoint's strength. Platt fit (a=23.1982,b=-13.1611,thr 0.9) gave 27/29 adopted at 1.000 on same-data; HELD-OUT run03 (20 fresh cases) dropped to adopted 9/10 (0.90) - fit was optimistic, one complaint misread as stylize_video at conf 0.945. Verdict: only viable assist candidate, shadow-only pending more held-out evidence + non-saturating map + deliberate activation steps. NOT enabled.

- laya knowledge-label-v1 criteria fix + calibration: third instance of the bare-list-criteria defect - ontology jargon (`entity`/`concept`/...) produced content-free criteria and the model confidently abstained 16/16 (p 0.47-0.99). Converted to dict-labels with ontology glosses (candidate ids unchanged, `ONTOLOGY` now frozenset of dict keys). Run02: accuracy 1.000 on 4 decided / coverage 0.25 - perfect precision, conservative recall, safe failure direction (abstain leaves span unlabelled). First high-precision assist candidate shape; still requires the standard calibration block, NOT enabled.

- laya cmd-risk-v1 calibration + laya-guard dead-lane fix: guard sent `"goal": ""` which the contract rejects (`state_goal_invalid`) - every production request abstained since authoring; goal now carries the classification intent. Post-fix eval (20 cases): acc 0.231 / cov 0.65 with disqualifying severity under-classification (irreversible->mutating, id_rsa->mutating, git push->benign). Deterministic feats vector remains authoritative; assist stays gated.

- laya review-risk-v1 calibration + state-modality finding: 16 cases over the exact review_gate hint-JSON shape -> 16/16 abstain, coverage 0.0. Root cause is state modality, not labels: structured flag-JSON/digest state is opaque to the semantic matcher while prose state decides. Across all 7 evaluated profiles only issue-category-v1 (0.684) approaches viability; assist gate stays closed.

- laya <=3-label calibration sweep + compact-item-v1 criteria fix: evaluated the three remaining low-cardinality profiles (52 cases, real worker, frozen manifests). compact-item-v1 exposed a contract defect - plain-list labels produced content-free criteria (`{"keep":"keep"}`) and the model abstained 20/20; converted to dict-labels matching the sibling-profile pattern (candidate ids/requests unchanged, no calibration existed to invalidate). Post-fix accuracy still 0.125 (keep-attractor). filebool-v1 acc 0.444 with yes-collapse (all 9 suggestions "yes"). compact-boundary-v1 abstained 16/16 (trajectory reasoning beyond checkpoint). Meta-finding across all 6 evaluated profiles: only issue-category-v1 (0.684, surface-feature triage) approaches viability - assist gate stays closed. Artifacts: `.devin/evals/laya/{compact-item-v1,filebool-v1,compact-boundary-v1}/`; rollout issue 04 updated.

- asr/bootstrap.py supply-chain hardening (matches jxl_bootstrap pattern): sha256 pins for the whisper.cpp v1.7.6 Windows binary (GitHub release asset digest) and ggml-tiny/base/small models (HF LFS oid via paths-info API). Unpinned --model values now refused with `unpinned_model` instead of fetching unverified bytes. Cached artifacts are hash-verified: matching model/binary marker skips re-download, corrupt cache auto-refetches. Existing _cache contents verified MATCH against the pins. +5 tests (13 total).

- scripts/ sweep + audit scope extension: checks [36]/[37]/[38] now scan `scripts/` alongside `extensions/` via shared `_scan_py_files()` generator. Found + fixed: check-tools renderer determinism check had no timeout (hung renderer = hung audit; now 120s with clean FAIL), dep-audit + dep-audit-gate `text=True` calls missing utf-8 pins (cp1252 on pip-audit/npm output). Manifest export_hash refreshed for the 3 touched scripts.

- file-I/O decode sweep + audit check [38]: Path.read_text()/write_text() and text-mode open() without an encoding pin now flagged by audit (same cp1252 class as [37], for file content). Fixed 8 sites: cu_qmp_backend/cu_env_daemon heartbeat pair, abliterator safetensors index read, heldout_batch --out write, blender state json.load/dump, code-graph selftest fixtures, guest worker boot_id read. ASCII-guaranteed sites (ensure_ascii JSON, kernel boot_id) pinned anyway for convention uniformity. Summary now reads "ALL 38 CHECKS".

- subprocess timeout + decode sweep round 2: AST scan found the last `subprocess.run` calls without `timeout=` - harness-tree selftest helper (timeout=60, matching code-graph), taskkill calls in cu_browser `_kill_pid` and cu_taskrunner stop (timeout=10, best-effort kill). Also 4 `text=True` calls the earlier count-based sweep missed (blender --version probe, remotion npm install + render, ppisp_runner) now pin `encoding="utf-8", errors="replace"`. audit.py check [37] rewritten AST-precise (per-call text=True without encoding= kwarg) after the count heuristic proved it could mask per-call gaps.

- audit.py check [37] subprocess utf-8 decode: warns when a file has more `text=True` subprocess calls than `encoding=` pins (the cp1252 regression class fixed this session); warning-level heuristic. Summary now reads "ALL 37 CHECKS".

- audit.py check [36] CLI exit-code contract: AST-scans extensions/ mains for the `print(json.dumps(envelope))` + bare `return 0` shape that let `{"ok": false}` exit 0 (the bug class fixed in 9 mains this session); warning-level, skips ok-aware/can-fail/sys.exit paths. Summary now reads "ALL 36 CHECKS".

- CLI exit-code contract sweep: 9 mains emitted `{"ok": false}` envelopes but always exited 0 - scripts/CI could not detect failure. Fixed: composite, plan_check (the pre-render gate), render, transcribe, verdict (judge+build-ref), eval_set, photo_qc, ppisp_runner, craft-bridge. Also: plan_check now rejects non-finite fps/duration/sync_range/props (NaN/Infinity/bool slipped through - `fps:"30"` crashed the validator itself); composite refuses `--out` overwrite (ffmpeg -y), catches bad-fit ValueError, exits non-zero on failure. 6 new tests.

- Windows cp1252 decode sweep: every first-party `text=True` subprocess call now passes `encoding="utf-8", errors="replace"` (21 call sites across extensions/: asr, remotion-render, craft-bridge, laya-tools x4, media-tools x2, computer-use x5, agent-reach, rea-ops, rz-ops, offsec-tools, hyperframes, blender-operator, code-graph). On Windows, `text=True` alone decodes with the locale codepage - UTF-8 output containing non-ASCII (PT-BR filenames, accented window titles, JSON envelopes) could mojibake or crash on cp1252-undefined bytes. Matches the pattern already used in cu_agent_desktop/mcp_server/offsec-tools; one test fake signature updated.

- code-graph selftest: `run()` helper now has a 60s timeout (was unbounded - a hung sibling script would hang the self-test forever); verified live `selftest: PASS`.

- diagram-tools plantuml renderer hardening: server moved to https (was plaintext http - MITM could inject scriptable SVG); response body capped at 32 MiB (was unbounded read); explicit `-o` refuses to overwrite an existing file (default derived `<src>.<fmt>` stays overwritable for idempotent re-renders); 4 new tests.
- mesh-utils meshops: `clean` now checks src exists (was the only command missing it - missing file crashed with a traceback instead of typed `{"ok": false}`); `convert`/`clean` refuse to overwrite an existing dst; 3 new tests.

- hyperframes render arg parsing: a flag value starting with `--` (e.g. `--fps --output x`) is now rejected as "flag missing value" instead of silently consuming the next flag as the value; 1 new test.

- voicebox generate `--out` overwrite guard: refuses to truncate an existing file and fails before the synthesis call (both voicebox and voicestudio backends); 1 new test.

- stock-footage fetch hardening: `--out` now refuses to overwrite an existing file (was silent truncation of any path); non-dict JSON API responses return typed `bad_json:not_an_object` instead of crashing with AttributeError outside the envelope; 2 new tests.

- image-forensics held-out harness + first real-data eval (ISSUE_02 step 4 partial): `eval_set.py` runs verdict.judge over labeled --real/--synth dirs and reports per-class verdict distribution, decided accuracy, and coverage (thresholds stay CLI inputs - calibration and held-out never share constants); `ref_error` bucket separates shape-mismatched images from inconclusive. First real run (webcam JPEG ref vs held-out frames + Remotion-render synth): real 3/3 correct, but synth JPEGs false-positive at default PCE_REAL=50 (scores 130-187) - ref residual dominated by shared JPEG quantization signature, documented in `.devin/research/2026-11-09-if-heldout-eval.md` + SKILL.md JPEG-domain caveat; 4 new tests. Eval artifacts (personal camera frames) gitignored under `.devin/scratch/if-eval/`.

- asr transcribe local-video fix: `fetch_audio` passed any existing local file straight to whisper.cpp, which demuxes wav/mp3 only - mp4/mov/mkv inputs returned `ok:true` with empty segments (silent failure, reproduced live on a narrated mp4). Non-{wav,mp3} local files are now extracted to 16kHz mono wav via ffmpeg (`FFMPEG_EXE` override, clear error when ffmpeg absent); URLs still go through yt-dlp. 4 new tests.

- plan_check visual-prop contract: the pre-gate validator checked timing/overlap/readability but not `visual.props` against the template's prop types - a `counter` beat with `{value: 1}` instead of `{to: 1}` passed the gate then crashed Remotion mid-render (frame 375, cryptic interpolate TypeError). `VISUAL_PROPS` now mirrors PlanComposition.tsx (kinetic_text.text, diagram_nodes.nodes[].label, counter.to, pan_zoom.src; bool rejected as number); unknown visual types still fall back to KineticText; SKILL.md mapping table now documents the props contract; 6 new tests.

- animation-direction narrated-clip e2e: full pipeline proven end to end - SAPI-generated narration + testsrc -> narrated.mp4 -> transcribe (8 segments) -> plan synced to real timestamps -> plan_check -> Remotion render (822 frames) -> composite.py -> final-narrated.mp4 with narration audio preserved. Artifacts in `.devin/scratch/anim-e2e/`.

- animation-direction composite step (ISSUE_04 step 6): `extensions/remotion-render/composite.py` - ffmpeg overlay of a rendered plan onto the source video; narration-first audio (source track wins, `--mix` amixes overlay audio in, silent source falls back to overlay track), `--fit frame|contain` (frame = exact-cover for alpha .mov renders, contain = AR-fit PiP/lower-third with `--pos x:y`), duration-mismatch warnings (overlay shorter -> last frame holds, longer -> trimmed by -shortest), ffprobe-based stream/dims validation, FFPROBE_EXE/FFMPEG_EXE overrides; live-verified with lavfi-generated src+overlay -> h264/aac mp4, overlay confirmed in output pixels; 11 new tests (30 total pipeline tests); SKILL.md step 6 + Files updated.

- site changelog entry count honesty: `collect_changelog` counted only `- **bold**` bullets (9 shown for Unreleased vs 90 actual) - now counts all top-level bullets.

- site issue ledger archived-effort parity (follow-up to #406/#407): `status_vocab` gains `effort_archived`/`archived_efforts` (moved from roadmap-board, single source); `site/build.py collect_issues` now skips ARCHIVED efforts - site was counting all 20 archived efforts (190 issues/184 resolved) while the board showed 97; both surfaces now agree (97 issues, 4 groups); roadmap-board keeps `archived_efforts` alias; 1 new test.

- agent-desktop Backend contract integration (issue #429): `DesktopBackend` in `cu_agent_desktop.py` adapts the CLI wrapper to the `cu_backend` contract - `capabilities()`/`observe()`/`dispatch({"op",...})`/`release_all()`/`close()`; option A tree-native chosen (observe returns `{"tree","meta"}`, documented divergence from the `(img,meta)` frame contract - frame consumers must not receive it); `cu_backend.open_backend` accepts target kinds `desktop`/`agent-desktop` (no env_id needed); live-verified observe on WindowsTerminal; 5 new tests (16 total).

- asr PT-BR transcription quality (issue #430): `_model_path` resolves `ggml-*.bin` filenames + `medium`/`large` aliases (previously only base/small/tiny); `parse_lang_detection` extracts whisper.cpp auto-detect lang+confidence from stderr into `detected_lang`/`lang_confidence` output fields; `warnings[]` flags `lang_mismatch` (--lang vs detected) and `low_lang_confidence` (<0.5); docstring guidance: non-EN speech needs small+ model and/or explicit `--lang`; 2 new tests.

- review-hardening batch over gcal/caldav/oauth/dep-audit/roadmap (PR #422 review): wrapper rejects `--flag=value` on boolean flags (`--confirm=false` can no longer slip a write past the confirm gate); Google events URLs percent-encode calendar_id (`#`, `?`, `@` safe); CalDAV requires https except loopback, refuses cross-origin/insecure redirects so Basic auth never leaves the origin, ETag lookup case-insensitive, well-known discovery probes the RFC 6764 host-root path, event_ics folds content lines to <=75 octets per RFC 5545; oauth_setup matches `[gcal]` as a real TOML table header (not substring), TOML-escapes written values, creates credentials.toml 0600 from creation, and only completes the callback on code/error params; dep-audit honors `--root`/`--max-seconds` in any argv position; roadmap-board archived-effort detection anchored to a Status field (prose "ARCHIVED" no longer archives) and blocker refs strip prose tails; 8 new regression tests.

- agent-desktop CLI backend module (issue #427): `extensions/computer-use/cu_agent_desktop.py` - list-form subprocess wrapper over `agent-desktop` (snapshot/find/click/type/set-value/select/get/state/press/focus/scroll/screenshot + observe-act-verify `verify()`); UTF-8 stdout decode fix for Windows cp1252; real CLI signatures verified against `agent-desktop --help`; documented in USAGE.md as wrapper, not yet a `cu_backend.Backend`; 11 tests.

- rehearsal-gate pattern for visual artifacts (issue #428): docs capture the StageShow-derived pattern - visual/UI deliverables get a rehearsal step (render -> inspect -> fix loop) before being marked done; applied to skill docs.

- macro goal rollup (issue #420): `.devin/goals/*.md` files (Status/Horizon/Objective + Efforts:/Issues:/Refs: link sets, same tolerant field syntax) roll up read-only in roadmap-board - `goals[]` in --json + `## Goals` coverage table in markdown; coverage = done/linked over resolvable local issues, unresolved tokens reported not scored, Refs: traceability-only; format doc `.devin/goals/README.md` + first real goal `dev-org-ladder-2026-11` (#346 umbrella, live coverage 71/71); 2 tests.

- micro focus-session tracker (issue #419): `scripts/focus.py start|stop|report|status` - append-only JSONL ledger `.devin/ledgers/focus.jsonl` (gitignored, metrics.jsonl pattern); sessions pair start->stop FIFO with stale-close on unclosed start; report aggregates focus minutes per day and per issue + `--json` + `--day` filter; refuses double-start, offline stdlib-only; documented in agents/issue-tracker.md; audit manual_scripts + counts 44->45 synced; 6 tests.

- micro timeboxing fields (issue #418): issues accept `estimate_min:`/`actual_min:` frontmatter (bold/dash variants tolerated); roadmap-board exposes both per issue + capacity `est_open_min` rollup (open issues only) + markdown "Est min" column; agents/issue-tracker.md documents the convention (roteiro task `minutes` <- estimate_min); first real use: egm-laya 04-laya-jev-rollout estimate_min=120; 1 test.

- roadmap-board parser corrections + effort archiving (issues #402 #406): status/priority fields now parse `- **Status**: x`, `**Status:** x` and plain forms (bold residue previously left issues falsely open - live board corrected 190->97 issues, done 184); archived-effort mechanism - scratch/<effort>/README.md `Status: ARCHIVED` excludes that effort's issues from the live board, reported as summary.archived_efforts/archived_issues + markdown note; sweep archived 17 dead efforts (audit-r1..r6, reels-2..5, computer-use-staged-upgrades, agentcraft-rts(+v2), general-audit, 3d_sources, cu-perception, cu-realtime) covering 93 resolved issues; site/build.py field regex aligned to same bold-status variants; live frontier now 5 claimable + 1 egm-laya open; 2 new tests.

- _hookrun resilience (issue #408): metrics.jsonl rotates at 512KB keeping newest half (was unbounded - 10k lines/2.2MB observed); per-script timings_ms in hookrun metric + stderr warning over 5s; docstring documents the non-blocking sub-script contract (outer hook timeout is the only hang bound); 2 tests.

- dep-audit gate coverage + hook-budget fix (issue #404): INSTALL_RE now matches `python -m pip`, `pipx`, `uv pip`, `poetry/pipenv/conda/mamba`, `gem install`, `bundle install`, `mix deps.get`, `dotnet add/tool install/restore`, `composer global require` - ruby/elixir/dotnet install commands previously never triggered the gate; dep-audit.py gains `--max-seconds` total-scan budget (_Deadline caps each scanner subprocess to remaining wall time, exhausted ecosystems skipped 'budget-exhausted'); gate calls with --max-seconds 28 + hard timeout 32 under the 35s hook budget (was 300s - could never finish, orphaned mid-scan); 28 new tests.

- PS5.1-safe export/install (issue #412): export.ps1 Get-FileHash256 switched to .NET SHA256 (parity with install.ps1) removing the Get-FileHash cmdlet dependency that dies on broken PS5.1 module sets; both scripts preflight core cmdlets and exit 1 with a clear message before touching anything; verified `export.ps1 -DryRun` + `install.ps1 -DryRun` complete on Windows PowerShell 5.1.26100.

- roadmap status vocabulary unification (issues #402 #403 #405 #407): new scripts/status_vocab.py - single source of truth for done/terminal/non-actionable/in-flight consumed by both roadmap-board.py and site/build.py; DONE gains implemented/landed/complete, CLOSED_EXTRA gains wontfix/archived, TERMINAL_PREFIXES covers superseded-*; is_claimable() excludes terminal + blocked/needs-*/on-hold + in-flight so non-actionable statuses no longer appear frontier-ready; site heading match tightened to exact-line (`## Done when` no longer resolves); roadmap-board blocker refs strip markdown residue (`**`, backticks, brackets - `_` preserved for MILESTONE_2_XX keys) and prose-none forms (`None - can start...`); numeric-prefix refs (`blocked_by: 01`) resolve within the same effort group only, surfaced as `via: group-prefix`; capacity() re-bucketed - blocked now means open-and-not-claimable (markdown column renamed "Not ready"); live run: 190 issues, done 96, open 94, frontier 85; manifest script_count 43->44, README/TOOLS-MAP synced, live scripts + install-ledger resynced; 6 new tests (14 total in test_roadmap_board.py). Covers #402 #403 #405 #407.

- gcal hardening batch (issues #395 #396 #397 #398 #409 #411 #413): wrapper argv normalization (`--flag=value` split, unknown `--*` rejected, missing values error instead of silent defaults); apply validates schedule blocks (dict + start/end) on both Google and CalDAV paths - no more AttributeError tracebacks; plan.pack validates tasks/slots upfront (name str, minutes int>0, priority int, ISO parseable, end>start) rejecting whole input with all errors listed - negative minutes can no longer create inverted events outside free slots; ics_busy rewritten - TZID honored via zoneinfo (tzdata optional, unresolved TZID warns+assumes UTC), all-day VEVENTs now informational `all_day` like the api path (never full-day busy), RRULE counted as `recurring_events` + hint (not expanded, stdlib-only); oauth_setup gains state + PKCE S256, --timeout (default 900s), clean token-exchange errors, credentials.toml chmod 600; roteiro skill documents ics limitations; 10 new/updated tests.

- roadmap-board capacity/WIP view (issue #417, #346 meso layer): capacity() per-effort open/ready/blocked/in_flight + totals + frontier + --wip-limit over-flag; markdown gains ## Capacity table; --json emits capacity block; in-flight statuses excluded from claimable ready; live run 190 issues, frontier 95, edge-audit holds 61; 3 tests. Covers #417.

- gcal live write path verified end-to-end + all-day fix: gcal.free_busy now uses events.list per calendar (singleEvents, paginated) instead of the freeBusy endpoint - timed events only block slots; all-day events surface as informational `all_day` in free-busy output (rent reminders/holidays no longer zero out a planning day); transparent + cancelled excluded; wrapper apply unwraps the `{roteiro:{schedule}}` envelope emitted by `plan` (previously crashed on wrapper-produced files); oauth_setup.py gains --force (replace [gcal] section) and requests `calendar.calendars` scope so AGdevin can be created via calendars.insert; first real run 2026-11-08: OAuth consent -> free-busy api -> plan -> apply --confirm -> AGdevin created + 4 events confirmed. Covers #346.

- CalDAV backend for the calendar extension (issue #346 agenda path): extensions/gcal/caldav.py - stdlib PROPFIND discovery (well-known + base fallback), calendar-home-set, calendar list, calendar-query REPORT free/busy (TRANSP:TRANSPARENT excluded via ics_busy update), MKCALENDAR find-or-create, PUT .ics event writes; creds via BUNDLE_CALDAV_URL/USER/PASSWORD or credentials.toml [caldav] (app passwords - iCloud/Fastmail/Nextcloud/Radicale, no OAuth); wrapper.py `--caldav` flag routes free-busy/plan/add/apply with same --confirm gate + AGdevin default; `--ics-url` fetches remote iCal feeds (Google secret-iCal read path); doctor reports both backends; roteiro skill updated; 13 tests incl. fake-server e2e. Covers #346.

- roadmap-board.py (issue #346 macro layer): stdlib parser over `.devin/issues/*.md` + `.devin/scratch/*/issues/*.md` - extracts title/status/priority/blocked-by/blocks, renders Markdown board per effort + frontier-ready list + burndown counts, `--json` model; milestone alias map (M2_XX/ISSUE_NN); manifest/script_count 42->43; README/TOOLS-MAP synced; 5 tests. Covers #346 macro end. (#394)

- office specialists wave (M2_15): 4 new agent profiles closing skill-without-agent gaps - data-analyst (swe-2-max, SQL-first + viz), sre (swe-2-max, incident/deploy-verify/postmortem), ux-researcher (swe-2-max, heuristic/journey/a11y evidence), performance-engineer (swe-2-medium, measured before/after only); VALID_PROFILES +4; manifest agent_count 17->21; README/TOOLS-MAP synced; gap analysis `.devin/research/2026-11-07-office-gap-analysis.md`. Covers M2_15. (#392, #393)

- reels batch-5 wave-2 (R5-03..08): frontend-design gains dashboard-grid spring-reflow note (moxen.cl/recursos/parrilla verified) + style-taxonomy pointer (filtercoffee.dev field guide, Option A - no vendored list); agent-reach SKILL.md "Curated source candidates" (airesearches feed candidate-unverified 403, AI-Weekly-News GitHub archive, AI Research YT); eval notes `.devin/research/craft-anything-eval.md` (track, do not adopt) + `wici-one-eval.md` (track hw, inferssd deferred); INDEX.md evals row; batch-4 survey SLEEP row cross-links parthknowsai DfZuDIUOGJZ + arXiv:2606.03979. Covers R5-03..R5-08. (#390)

- reels batch-5 survey + issues: 11 Instagram links deep-reviewed (3 batch-4 overlap); transcripts via local ASR; survey `.devin/research/2026-11-07-reels-batch5-survey.md`; issues `.devin/scratch/reels-5/issues/R5-01..08` + map + plan. Highlights: dep-audit scanner gap (matheusgomes), upload-trust UX checklist (kairozmind/designmotionhq), craft-anything + WiCi One + SLEEP evals. (#388)

- adequacao Devin CLI 3000.11.234 -> 3000.12.17: `validated_cli_version` bump; new capabilities section in DEVIN-CLI-COMPATIBILITY.md (/vim, model pinning, permission_mode, `devin mcp list --json`, ContextInput hooks, PostToolUse truncated-output path, UserPromptSubmit-on-handoff); TOOLS-MAP hook-fields + REPL/CLI rows + models table (adds swe-2-flash row); README version sync. (#388)

- dep-audit + PostToolUse gate (reels-5 R5-01): scripts/dep-audit.py - ecosystem detection (py/node/rust/go/php/ruby/elixir) + scanner dispatch (pip-audit/npm audit/cargo audit/osv-scanner), JSON contract, never installs, missing scanners reported as skipped; scripts/dep-audit-gate.py - PostToolUse(^exec$) install-command pre-filter, scanner-presence check, [DEP-AUDIT] additionalContext on findings, fail-open; hooks.v1.json registered (timeout 35); manifest/script_count 40->42; README/TOOLS-MAP/HOOKS-PIPELINE synced; 10 tests. Covers R5-01. (#389)

- ISSUE_06+07 closed (were already shipped): `skills/learn-mode` verified against vibe-wise upstream re-read (no deltas; SessionStart restore hook deferred to project-memory per spec); `grilling` Cross-skills gains pedagogical-counterpart line; ISSUE_07 port matrix confirmed complete (.devin/research/pocock_port_matrix.md, #96). Issues marked resolved. (#385)

- AGdevin isolation calendar: gcal writes default to dedicated AGdevin calendar - gcal.py list/find/create_calendar + ensure_calendar + resolve_calendar (summary-name -> find-or-create; 'primary' or raw id passthrough); add/apply resolve post-confirm and report calendar_created; roteiro skill + APP.md + README updated; 4 tests. (#387)

- gcal event write: extensions/gcal gains write path - gcal.py event_payload + create_event (events.insert, calendar.events scope); wrapper.py `add` (single event) + `apply` (roteiro batch) both gated by --confirm (preview-only "confirm-required" without it, API never called); apply reports created/failed per block; doctor hint notes scope; roteiro skill + agenda-roteiro APP write contract; README/TOOLS-MAP synced; 5 tests. (#386)

- orchestrator prompts v4 (M2_14): .devin/orchestrator_prompts_v3.md (content v4) - TEAM pattern 1 architect + <=3 workers with declared guards (silent->FAIL, kill@20min, nudge-then-pause, 20-round cap, pause-free); queue-vs-steer semantics; 03_Art_Director direction contract (5FQ + direction-approved.md + frontend-rules); schema_version 3 preserved; 5 tests. Covers M2_14, #383.

- design-lint gate hook (M2_05): scripts/design-lint-gate.py PostToolUse(write|edit) - 12 inline slop rules (no extension import), [DESIGN-LINT] via additionalContext, fail-open, UI-ext + path filters; hooks.v1.json registered (timeout 10); manifest/script_count 39->40; README/TOOLS-MAP/HOOKS-PIPELINE synced; 7 tests. Covers M2_05, #382.

- impeccable skill upgrade (M2_03): 24-command sync verified vs upstream SKILL.src.md @c3bb418 (added craft+generate); PRODUCT.md spec (10 fixed sections + schema-1 marker + no-invented-claims); DESIGN.md spec (normative YAML frontmatter + 7 fixed sections); huashu direction protocol (sec0 fact-verify->product-facts.md, 5FQ->search.py domains, 6->3+3 gate->direction-approved.md verbatim exemptions); muscle wiring (audit/critique run design_lint.py first; colorize/typeset/layout query search.py --domain; React stacks consult frontend-rules; [DESIGN-LINT] gate noted). 7 contract tests. Covers M2_03, #381.

- design_lint deterministic linter (M2_02): rules_registry.py ported from impeccable antipatterns.json @c3bb418 (62 rules, upstream now Rust crates not .mjs); checks.py implements ALL 46 static-scope rules (html.parser + CSS regex; 12 browser + 4 designsys marked skipped); design_lint.py CLI (--json/--list-rules/--ignore, exit 0/1/2); look_ledger.py reskin detection (fonts+palette+skeleton hash); seeded fixtures + 9 tests. Covers M2_02, #380.

- design brain upgrades (M2_04): creative-engineering gains retrieval step-0 (search.py --domain style before archetype .md) + 5 Form Questions->corpus dial map + frontend-rules pointer for React/Next/RN; art-director deep_analysis answers 5FQ, requires direction-approved.md evidence (3 real + 3 alt, verbatim exemptions), cites vendored frontend-rules on React stacks; v3 contract intact; 5 contract tests. Covers M2_04, #379.

- extensions/design-intelligence (M2_01): local BM25 design engine vendored from ui-ux-pro-max-skill @b7d5353 (MIT); search.py --domain/--stack/--design-system/--persist with auto-domain detect + runner-up; corpus 12 domain CSVs + 22 stack CSVs (34/34 schema-valid) + 139 vendored vercel frontend-rules .md + aesthetics alias; validate_csv.py; 11 tests. Covers M2_01, #377.

- extensions/harness-tree (M2_09): SurfaceSpec devin c1..c8 (specs.py); tree.py read/validate/diff/apply + tree_hash, omitted-is-inherited, RESERVED refuse-in-apply, utf-8 stdout; ns.py .devin/runs/<ts>-<seed>/ snapshot+resume (gitignored); first-wins dedupe for c4 paths under c6; 9 tests; 566 in-spec files validate clean. Covers M2_09, #375.

- self-improvement PPC discipline (M2_08): INV/DOM candidate classes + probe-on-same-task contrast evidence + earlier-only retention; refine log fields class/probe_evidence/contrast; validate-refinement-evidence.py anti-leakage check (future/self ref-id citation = suspect); harness-reference row; 3 tests. Covers M2_08, #373.

- extensions/code-graph (M2_10): stdlib SQLite FTS5 structural index (camel/snake tokens, mtime+sha1 incremental); index.py/query.py/detect_changes.py/selftest.py; 1035 files/5964 symbols indexed on bundle corpus; routing doc updates (orchestrator_prompts_v2 + skill-discovery, [GRAPH-DOWN] fallback); 5 tests. Covers M2_10, #371.

- tools.json multi-CLI render contract (M2_07): root tools.json (devin enabled; gemini/claude/codex disabled placeholders), scripts/check-tools.py (schema + byte-identical render gate; devin render 3471B deterministic), audit check 35, devin-config doc, 8 tests; 39 scripts. Covers M2_07, #369.

- install drift ledger (M2_06): scripts/install-ledger.py record-all/record/reconcile/status; .devin/install-ledger/{installs,corpus-index}.json (gitignored runtime data); 5-state reconcile (Current/Outdated/Modified/Removed/Foreign); backup_if_differs stdlib; installers now record-all post-install and ABORT on backup failure (was: silent continue); audit check 34 Ledger; 7 tests; 38 scripts. Covers M2_06, #367, #368.

- changelog refs for M2_11 hooks wave. Covers #364, #365.

- skills/camera-blocking (181 skills): brain for the shipped blender-operator presets; prompt template with hard location map + t=Ns beats; scroll-bound hero scaffold. Covers M2_13, #364.

- token-saver hooks (M2_11): token-saver.py (output-mode presets on change only), git-diff-stat.py (diff footer for caveman/lean), rl-resume-detect.py (rate-limit -> .devin/rts/intents resume intent); data/output-modes.json; 13 tests; 37 scripts / 24 internal hook modules. Covers #363, M2_11.

- atlas status fix: parenthetical '(research done)' no longer counts items as resolved (roadmap shows honest 0/21). Covers #362.

- atlas issues board gains 'roadmap' group from .devin/issues (macro ISSUE_*/MILESTONE_* items, 21 items/6 resolved); _issue_items refactor + Status ' · ' separator normalization. Covers #360.

- stale test-deletion approval marker removed (per-push semantics, record kept in history/PR). Covers #343, #347, #358.

- test-deletion gate hardened: approval marker must NAME each removed test/path (scoped, not blanket); _approval_text helper + 3 gate tests; approval file format documented. Covers #356, #357.

- agenda-roteiro (issue #345): extensions/gcal (free/busy API + --ics dev mode, urllib OAuth refresh, no deps) + plan.py roteiro packer + skills/roteiro (180 skills) + agenda-roteiro app dogfood. Covers #345, #348; README/TOOLS-MAP gcal rows + 180 count fix. Covers #345, #348, #349, #350, #351, #352, #353, #354, #355.

- reels batch-4: swe-2-flash model entry + MODEL-GUIDE fast-lane note (free until 2026-11-30); frontend-design micro-interactions spec; animation-direction direction grammar; ARCHETYPE-MAP harness-differentiator note; de-slop codebase mode; criador-de-devin-app skill (179 skills); 8 issues resolved. Covers #338, #339.
- batch-4 follow-up evals: OpenViking + Google Artemis identified and evaluated (R3-02 waitlist resolved); SLEEP framework coverage note; 2 issues resolved. Covers #340.
- atlas apps section: .devin/apps/*/APP.md rendered as cards + modal + REPL (cd/ls/open apps, key 0); ls scripts object-name fix. Covers #341, #342.
- atlas section parity test: SECTIONS vs view-* vs build.py data keys; pre-existing issues/changelog view order fixed. Covers #344.


- review pass: context-hygiene table split fixed, atlas q-key/modal-close logic fixed (q now types when no modal), VALID_PROFILES + README, build.py JSON-in-script hardening, file-size-guard handle, bundle-models newline, boot agent-count consistency. Covers #337.

- sentinel: report dir renamed to .devin/scratch/sentinel/ for consistency; hooks doc parity test (#336).

- tests: hooks-pipeline doc parity test (entry points + inner modules). Covers #335.

- changelog: coverage refs for atlas REPL fix and hooks arithmetic PRs. Covers #330, #334.

- docs: hooks arithmetic corrected (11 entry points / 6 consolidated / 21 inner modules), HOOKS-PIPELINE adds file-size-guard row. Covers #333.

- SKILL-TIERS: honest scope note (curated subset, manifest.json = full index) + 14 high-use rows (afk-loop, autonomous-gates, context-folding, de-slop, lean-code, tdd, etc). Covers #332.

- reels batch-3: 10 saved reels enumerated via computer-use, 9 transcribed, survey + evals docs; ai-tools watchlist + Dia/Bonside-2. Covers #331.

- site: REPL terminal sticky-footer fix (input no longer scrolls out of view as scrollback grows), Escape blurs input restoring key shortcuts, q no longer leaks into type-anywhere, all printable chars reach the terminal, scrollback capped at 200 lines. Fixes #329. Covers #328.

- README + site meta: stale agent/skill counts corrected to 17 profiles / 178 skills. Covers #327.
- manifest: sentinel original_path mojibake (bell char) fixed.

### Added

- ARCHETYPE-MAP: alvim job-apply drafter/reviewer chain cited in the Grower/Maintainer transit note (R2-02 adopted-as-note). Covers #321.
- validate-tool-args: repo-reviewer added to VALID_PROFILES; profile parity test now covers .devin/agents project profiles. Covers #322, #323.
- SKILL-TIERS: project-local section indexes verify-atlas + rts-* skills under .devin/skills. Covers #324, #325.
- agents: watchdog renamed to sentinel (dispatch-probed; avoids name collision with chief-of-staff SysAdmin watchdog + layad _idle_watchdog). Covers #326.

### Added

- README section 8: Atlas publico - describes the Pages site, issue board, and REPL so the public face is discoverable from the repo front door. Covers #318.

### Added

- MODEL-GUIDE: profile-registry lifecycle note - agents installed mid-session fail `run_subagent` until session restart (verified: watchdog today, chief-of-staff/researcher spawned fine). Covers #317.

### Added

- SKILL-TIERS.md: 11 rows for the reels-2 and round-2/3/4 skills (web-perf-checklist, big-file-refactor, cli-adapter, correct, blast-radius, arena, benchmark-checklist, technical-writing, create/maintain-verification-skill) so the discovery path covers them.

### Added

- `ai-tools` local-model watchlist entry: nvidia/personaplex-7b (full-duplex S2S, gated weights, GPU-gated) - closes the R2-08 adopted-as-note.

### Fixed

- audit.py check 32 (merge coverage): refs for merges younger than 24h now WARN instead of ERROR - every merge no longer makes the tree red until a changelog-ref PR lands; stale missing refs still fail. Covers #319, #320.

### Fixed

- README extensions table: 8 -> 24 rows, covers every directory under extensions/ (asr, voicebox, offsec-tools, blender-operator, comfyui-operator, craft-bridge, laya-compactor and 9 more were undocumented).

### Fixed

- TOOLS-MAP.md subagent counts stale (13 -> 17 disk profiles, table gained chief-of-staff + watchdog rows, .devin/agents note clarified to 4 profiles + README) - covers #316.

### Fixed

- `sc_process._reap_posix_group`: `killpg(pgid, 0)` can transiently raise EPERM on macOS while a killed group is reaped - the probe now falls through to the ps membership check instead of reporting `tree_cleanup=False` for an actually-dead tree (CI flake root cause, macos py3.11/py3.14) (#315); deepened: the verification loop now runs unconditionally and is the sole source of the flag - signal-send OSErrors can no longer falsify cleanup.

### Fixed

- `validate-tool-args.py` VALID_PROFILES: `chief-of-staff` and `watchdog` were missing, making both agents undispatchable through `run_subagent`; added `tests/validation/test_profile_parity.py` pinning disk agents to the validator set (#315). Also documents #314.

### Fixed

- Atlas issue board: issues whose resolution is declared via `## Done`/`## Shipped`/`## Landed` sections now count as resolved (egm-laya 3/4 -> 4/4); egm issue 02 status normalized to `resolved`.

### Added

- Atlas `~/issues` board: build.py scans `.devin/scratch/*/issues/` into the site data (144 issues, 143 resolved across 12 ledgers), new view + styles in app.js/index.html/style.css (#313).

### Added

- Reels-2 wave 4: `verify-atlas` dogfooded verification skill (R2-06), MERIDIAN backlog corroborating source (R2-15, #313). All 15 reels-2 issues resolved.

### Added

- Deflake macOS CI: longer process-tree reap window + socket connect retry in camera-blocking test.

### Added

- Reels-2 wave 3: `file-size-guard.py` PostToolUse hook (R2-13, 34 scripts), ai-tools HF-name decoder (R2-10), ARCHETYPE-MAP doc (R2-14), consolidated eval notes (R2-02/03/07/08/12, #313).

### Added

- `cli-adapter` skill (R2-01): build-a-CLI protocol for tools with no MCP, citing agent-reach wrapper contract (R2-01, #311). 178 skills.

### Added

- **GitHub Pages atlas** (#301): `site/build.py` + `site/src/` generate a static terminal-style explorer (CRT phosphor aesthetic, typed boot with real stats, grep-filterable skill explorer, agent gallery, hooks pipeline, ADR/docs reader with mermaid, changelog timeline, Ctrl+K palette); `.github/workflows/pages.yml` deploys `site/dist` via SHA-pinned official actions on pushes touching site inputs. Live at https://leostruka.github.io/devin-bundle/, linked from the README atlas badge (#302).
- **Atlas logo swap** (#303): hero ASCII logo alternates DEVIN BUNDLE / LEOSTRUKA every 5s through a character-scramble transition; respects `prefers-reduced-motion`.
- **blast-radius skill** (#309): vendored + adapted from pstack (MIT); proves the one safety fact of a risky-looking change by running real code, with a certainty ladder and subagent fan-out per angle.
- **Verification-skill generator pair** (#309): vendored + adapted from pstack (MIT): `create-verification-skill` (generates `.devin/skills/verify-<app>` with launch/doctor/drive/evidence sections + seeded feature map, proven end-to-end before handover) and `maintain-verification-skill` (per-feature source fan-out + live driving pass, three invariants, clean/changed/blocked outcome). With `blast-radius`, skills 172 to 175.
- **arena skill** (#307): vendored + adapted from pstack (MIT); N parallel candidates at one task via background subagents with isolated outputs, cross-judge, base pick, hand-graft, verify. Model-family seat logic collapsed to per-seat angle stances under the free-model policy. Skills 171 to 172.
- **Atlas REPL** (#308): footer prompt is a real input: `cd`/`ls`/`cat`/`open`/`grep`/`doctor`/`install`/`version`/`pwd`/`history`/`clear`/`:q`, Tab-completion, Up/Down history, type-anywhere focus, prompt path tracks the section. Closer to devin-cli terminal feel.
- **Backlog round-1 skills** (#304): vendored + adapted from pstack (MIT): `benchmark-checklist` (vet measured numbers: limiter, tuning, reproduction, e2e relevance), `correct` (kill repeated agent mistake classes at the highest enforcement level), `technical-writing` (Diataxis + Google style + STE + Global English for docs/PRs). Skills 168 to 171.

### Fixed

- **Push gate race fix** (#309): validation and held-out now run sequentially in `check-push-green.py`: held-out mutation tests rewrite `scripts/*.py` in place, and a concurrent validation audit could read a half-mutated script (the recurring `constraint-pinning.py line 104` SyntaxError flake).

- **Push gate made feasible** (#299): `check-push-green.py` now treats `tests/validation` + `tests/held-out` as the main check when both exist (Rule 15 contract, concurrent, `MAIN_TIMEOUT` env `BUNDLE_PUSH_GATE_TIMEOUT` default 250s); full suite stays in CI. Spawned pytest no longer inherits `DEVIN_PROJECT_DIR` (cwd isolation for hook-script tests). `audit.py` `render_norm` collapses resolved `python(w).exe` interpreter paths to `python` for the hooks-render comparison.

### Added

- `web-perf-checklist` + `big-file-refactor` skills, `watchdog` agent, `advisor_role_model` in bundle-models, ultrathink/advisor + compact-early docs (reels-2 wave 1-2 partial, R2-04/05/09/11, #311). 177 skills.

### Added

- Reels batch-2 survey: 16 Instagram reels transcribed via `extensions/asr` (whisper.cpp local), decoded against the 175-skill bundle; 15 systematic issues + execution plan + map under `.devin/scratch/reels-2/` (#310). 4 P2 adopts (web-perf-checklist, big-file-refactor, watchdog/ultrathink, advisor routing), backlog evals for game-dev/voice/alt-data lanes.


## [3.19.0] - 2026-11-04

### Added

- **Edge-to-edge workspace audit corpus** (#297): 68 verified issues under `.devin/scratch/edge-audit/` (spec + map + issues) covering optimization, UX, code, organization, investigative cycles, traceability, metrics, adaptability, best practices, devin-cli limitations with workaround tradeoffs, documentation, diagrams, business logic, algorithm translation, applied rules, rationale, ADR, versioning.
- **Subsystem docs and ADRs**: `.devin/docs/HOOKS-PIPELINE.md`, `MEMORY-PIPELINE.md`, `INSTALL-PARITY.md`, `DRIFT-LEDGER.md`, `BUSINESS-LOGIC.md` (rules R1-R19 with code anchors); ADRs 005-008 (hooks.v1.json single-source, hook consolidation, scratch issue tracker, vendored-skill policy); mermaid diagrams under `.devin/docs/diagrams/` (hook event flow, thermos dual-lane, de-slop sequence, export cycle); CONTRIBUTING gained a Releasing section and README an English quick-start.
- **Reels-adoption skill wave** (#293): `lean-code` (Ponytail minimal-code port, MIT), `security-audit-cf` (vendored Cloudflare security-audit, MIT, renamed to avoid collision), `shorts-factory` (shorts pipeline composing tts/asr/remotion/ffmpeg) + `extensions/stock-footage` Pexels/Pixabay fetcher (env-key gated, typed JSON); `extensions/voicebox` gained a `--backend voicestudio` OpenAI-compatible path at 127.0.0.1:3900 (voicebox path unchanged); `extensions/media-tools` gained JPEG XL codec `jxl.py` + `jxl_bootstrap.py` (pinned sha256-verified libjxl).
- **Forensic testkit** (#294): `forensic-debugging` (escalation-tier debugging protocol: mandatory trace ledger, invariant map, hypothesis falsification table, three-axis bisection, probe lattice, root-cause proof) and `edge-coverage` (suite-construction standard: mandatory Edge Inventory driving every test; input/state/error/concurrency/oracle matrices; coverage reported by inventory) with cross-references from `debugging`, `edge-cases`, `testing`.
- **Quality-skills wave** (#295; cursor/plugins MIT vendors, adapted to Devin `run_subagent`): `thermo-nuclear-code-quality-review`, `thermo-nuclear-review`, `thermos` (dual-lane parallel review orchestrator) + `agents/thermo-nuclear-*-subagent.md` profiles; `unslop` (AI-tell cleanup for prose); `typescript-best-practices` (principle refs inlined); `vercel-react-best-practices` (Vercel rulebook, 70 rules); `no-comments` (port: comment-sicko rubric via `reviewer` profile); `de-slop` (composite simplification pass sequencing lean-code/no-comments/unslop/thermo per diff). `VALID_PROFILES` extended to 20.

### Changed

- **Hook rendering resolves a real interpreter** (edge-audit 26/42): `render-user-hooks.py` emits hook commands with the detected Python (`sys.executable`/python3/python/py chain) and install.sh passes a Windows-native `cygpath -w` home on Git Bash, so `fail_closed` hooks no longer block on POSIX-shaped paths.
- **install.sh POSIX/macOS hardening** (edge-audit 03,04,05,09,11,16): hasher detection (`sha256sum`/`shasum -a 256`/`openssl dgst`, hard-fail if none), portable `tail -c +4` BOM strip, recursive `backup_file`, `ast.parse` validation instead of `py_compile`, single `PY` resolution for all python calls.
- **Export masking parity** (edge-audit 06,07,36): shared `mask_json_file` reaches ps1-vocabulary parity (session/cookie/jwt/dsn/connection_string/org_id/user_id/email, `env` blocks masked wholesale), fail-closed when no python3 for masking, masked-mcp placeholders install under `--force`.
- **Gate scripts fail closed correctly** (edge-audit 61-68): `check-push-green` distinguishes no-framework vs unrun-framework, `git push` matcher no longer substring-bypassable, AI-signature scan covers untracked files, `architecture-gate` comment escape closed, `silent-error-review` gaps fixed, metrics sink persisted to `.devin/ledgers/metrics.jsonl` via `_hookrun.emit_metric`.
- **Audit checks tightened** (edge-audit 10,70,71): dead duplicate-rule check removed, rule-count check reads bodies not index aliases, purpose-vs-description comparison no longer truncated-prefix-only.
- **Test infrastructure** (edge-audit 78,79,83): `norecursedirs = held-out` keeps held-out out of default `pytest` while explicit targeting still works; zero-coverage hook scripts gained edge tests; real 30-60s sleeper processes replaced with short controllable ones.
- **Organization** (edge-audit 17,23,24,25): mcp_config ownership contract documented (root = install artifact, `.devin/` = repo runtime), scratch loose files filed under `probes/`/`gate-scripts/`/`prompt-specs/`/`notes/`/`tools/` subdirs with README rules, skill-overlap reconciliation table recorded in issue 23.
- **Live config export sync** (#289): manifest re-synced to real live inventory (skill_count 101 -> 155, sorted, `export_hash`/`exported_at` metadata); `config.json` `agent.model` normalized to `swe-2-high` per `data/bundle-models.json`; `export.{ps1,sh}` stages a filtered explicit path list (`git add -- "${existing_paths[@]}"`) instead of atomic adds that silently failed on missing paths, surfaces add/commit/push failures, and runs the CI pytest suite (`testpaths=tests`) instead of sweeping `extensions/` integration tests that hard-fail without a live QEMU env.

### Fixed

- **`blender_server` unauthenticated localhost exec** (edge-audit 76): nonce required on `exec`/`shutdown` via `hmac.compare_digest`; nonce no longer echoed in responses; delivered via owner-only (0o600) per-port nonce file.
- **`cu_taskrunner` trace_id path traversal** (edge-audit 77): `^[0-9a-f]{12}$` + realpath containment enforced in `_trace_dir` and the `_exec` CLI; `stop()` can no longer write or kill outside the store.
- **`scrape.py` SSRF allowlist** (edge-audit 82): `check_url_allowed` enforces http/https only, resolves hostnames, rejects private/loopback/link-local/reserved ranges; `--allow-private` opt-out.
- **`cu_env_daemon` token exposure** (edge-audit 81): `env_dir` chmod 0o700; `ready.json` and guest-caps written via `_write_private` (0o600).
- **install.sh credential handling** (edge-audit 01,18,19,80): `credentials.toml` gated behind `--restore-secrets` (opt-in parity with ps1), `chmod 600` on credentials and mcp copies, lossy sed merge fallback removed (merge skipped loudly without jq), usage text corrected.
- **install.sh config merge** (edge-audit 02,12): jq deep-merge `.[0] * .[1]` keeps local keys; masked mcp placeholders install under `--force`.
- **export.ps1/install.ps1** (edge-audit 08,20,27,35,41): `Get-FolderHash` detects pure renames (relpath + hash lines), `__pycache__`/`*.pyc` excluded from all copies, render-hooks output no longer swallowed, AGENTS.md case-variant dedup on all filesystems, extension `.deps.sha256` markers with fail-soft revalidation.
- **install.sh extra hardening** (edge-audit 38,40): `devin --version` vs `validated_cli_version` install-time notice, `record_skip` + `.install-receipt.json` for partial installs.
- **`cu_taskrunner.py` status race** (#289): per-writer status tmp files; shared `status.json.tmp` raced `stop()` vs `_exec()` producing corrupt trailing bytes (caught by `test_cli_surface`).


## [3.18.0] - 2026-11-03

### Fixed

- **`install.sh` Windows split-brain** (#269): on MINGW/MSYS/CYGWIN the installer now targets `%APPDATA%/devin` (where the CLI actually reads) instead of `~/.config/devin`; `audit.py` prefers `%APPDATA%` on Windows and warns when both dirs exist. Previous bash installs had written a shadow config that drift checks validated as "live".
- **Exporter secret masking and pre-push gate** (#268): `export.sh`/`export.ps1` now mask by key-name (`token|secret|api[_-]?key|password|auth|credential|private|pat`, e.g. `GITHUB_PAT`, `Authorization`, `client_secret`) and embedded URL userinfo; TOML masking tracks multiline openers (`[`, `"""`, `'''`) so continuation lines no longer leak; the pre-push `audit.py`/`pytest` gate now runs inside the bundle root (it previously validated the caller's cwd, where `audit.py` walks `.`, silently broken); `git add -A` replaced with export-owned paths; paths passed via `sys.argv` instead of shell interpolation; bundle-only/stale export entries now reported.
- **Installer/skill robustness** (#264): unreadable-file guards, `ppisp` subprocess timeout, empty extension directory skip in `install.sh` (parity added to `install.ps1` in #269).
- **`comfyui-operator` hardening** (#263): loopback-only server URL and download path sanitization.
- **Typed-error hardening** (#262, #255, #254): `plan_check`, ASR bootstrap, `sc_bench`, custom presets, laya-compactor pairing/reduction accounting.
- **`asr` Windows discovery** (#256): whisper binary/model discovery fixed on Windows.
- **Unexpanded placeholders** (#272): `{{VALIDATED_CLI_VERSION}}` in `ask-bundle` (never substituted by any pipeline) now references `validated_cli_version`; `data/bundle-identity.json` filled with real values (`Leostruka/devin-bundle`, 2026); `blender-operator` POSIX `ps` call gained `timeout=15` parity.
- **Unbounded subprocess calls** (#274): `timeout=15` added to the PowerShell CIM query in `extensions/computer-use/probes/probe_spawnpty.py`; `timeout=60` added to CLI subprocess calls in `extensions/media-tools/tests/{test_cli,test_export}.py`.
- **Phantom recipe tool** (#275): `data/recipes.json` `explore` listed `glob` (premise corrected in #284: `glob` is a real tool, but recipes should not demand mode-absent tools); it capped the recipe tool score at 0.75 in `context-pressure.py`. Removed; regression test validates every recipe tool against the canonical CLI tool set.
- **False architecture boundary + missing enforcement** (#278): `.devin/ARCHITECTURE_MANIFEST.md` claimed hook scripts never import from `extensions/`, but `laya-guard.py` intentionally does (dynamic, fail-open); manifest corrected to "no third-party pip deps" with the laya exception documented; new `test_scripts_import_boundary` test enforces stdlib/sibling/exception imports across `scripts/*.py`.
- **POSIX reap verification flake** (#280): `_reap_posix_group` group-absence deadline widened 5s -> 15s; SIGKILL-to-launchd-reap latency on loaded macOS CI runners exceeded 5s, producing transient false `tree_cleanup` results (`test_spawn_timeout_cleans_tree` failed 3x).
- **Phantom tool in skill frontmatter** (#282): `observability-quality` `allowed-tools` listed `glob` (premise corrected in #284) corrected to `find_file_by_name`; new `test_skill_allowed_tools_exist` enforces canonical tool names across all SKILL.md frontmatter.
- **`glob` tool misclassified as phantom** (#284): `glob` is a real CLI tool (`validate-tool-args` checker + TOOLS-MAP); the session toolset is mode-dependent and not canonical. #282's premise corrected: `observability-quality` restored to `glob` + `find_file_by_name`; `VALID_TOOLS` expanded to the canonical 28-tool set; allowed-tools test now covers YAML-list form and `agents/` + `.devin/agents/` profiles.
- **Orphaned extension requirements** (#287): `playwright` (craft-bridge), `opencv-python-headless` and `piexif` (image-forensics) were declared but never imported; `ppisp-prep` gained the missing `requirements.txt` (numpy, pillow) for its hard deps; new `test_extension_declared_deps_used` enforces declared->used per extension.
- **`agent-reach` wrapper desync from upstream CLI**: wrapper forwarded channels as subcommands (`agent-reach youtube ...`), a grammar agent-reach 0.1.0 never shipped; every documented call exited 2 and `doctor` reported `degraded` probing a nonexistent `--version`. Wrapper now translates `<channel>[.<command>]` to `get <target> --json`, `doctor` proxies `doctor --json` per-channel status, whitelist narrowed to the real upstream index (`youtube`, `rss`; `auth:none`), and SKILL.md/manifest purpose synced (previous docs claimed phantom github/bilibili/v2ex/web channels).

### Added

- **`test_extension_used_deps_declared`** (#288): the reverse direction of the R20 check is now enforced — module-scope third-party imports in `extensions/` must be covered by that extension's `requirements*.txt`; AST-based (function-scope lazy imports exempt), extensions-internal module roots exempt, documented `bpy`/`mathutils` host-provided allowlist for Blender's embedded interpreter; the R20 orphan check was upgraded from regex to AST.
- **`agentic-rag` vectorless/tree-index retrieval** (#266): architecture selector gained `long structured docs -> PageIndex-style` with honest costs (LLM call per hop, index build time, stale-tree versioning); gate/escalation unchanged.
- **`brag` portfolio-site beat order** (#267): storyboard template for portfolio/personal-site inputs (hero -> work -> recognition -> process -> values -> CTA) from real-site reel re-analysis.
- **`stuck-detect` deterministic advisory** (#260): token-economizer subset hook.
- **Ponytail minimal-diff checklist** (#258): Goldfish zoom-out review step.
- **EGM runtime rollout** (#253): JEV routing, OpenUI runtime, camera blocking, BitNet/offloading adapters, TPU held-out scaffolding + 12-issue audit hardening.

### Changed

- **MODEL-GUIDE**: Avalon AMD MoE fork evaluated-not-adopted with 4-question benchmark-reading checklist (#265); LFM3 local-audio family entry (#259).
- **`dispatching-parallel-agents`** (#277): DeepSeek super-agent eval evidence added; task-queue interruption inverts the sub-delegation bias (neutral prompt 0/5, delegate-first 4/5, median 20.4->13.8 min) plus Cooper Bench co-edit cost (~30% lower success).
- **`audit.py` check 32** (#281): `[Unreleased]` merge coverage now enforced; merge PRs since the released tag without `#NNN` refs in `[Unreleased]` fail the audit (`docs(changelog)` PRs exempt).
- **`audit.py` pycache check robustness** (#285): check 11 `git ls-files` pathspec replaced by Python-side `'__pycache__' in path` filter, matching tracked caches at any depth.

### Documentation

- Source analyses: NCM coarse-to-fine (#261), FreeMyTv Claude-Code-on-TV (#257), batch sources incl. DeltaDB/TradingAgents/Kimi K3/Openjutsu (#265), TSF Lesson 1 (#271), GG Coder demo (#276), all notes-only, no portable implementation; Nx-style lib boundaries applied internally as a real enforcement fix (#278); R8 issue answers (#270); review-pattern capture and drift reconciliation (#252).

## [3.17.0] - 2026-10-30

### Added

- **10 skills ported and adapted from the parallel Fingertech Devin install** (`\\192.168.1.67` survey): `powershell-safe`, `shell-safe`, `edge-cases`, `dead-wire`, `github-actions`, `webhooks`, `typescript-node`, `binary-triage`, `ghidra`, and `dma` (with `tools/` stdlib recon/probe suite, artifacts path adapted to `.devin/scratch/dma/`). Cascades rewired to bundle skills (`testing`, `security`, `web-probe`, `re-binary`, `debugging`, `research`, `git-workflows`). Skill count 91 -> 101.

## [3.16.0] - 2026-10-30

### Changed

- **Devin CLI 3000.11.234 alignment**: `data/bundle-identity.json` and `README.md` now validate against `3000.11.234` (installed `92c83011d113`). Added `3000.11.234` capability table in `.devin/docs/DEVIN-CLI-COMPATIBILITY.md` and synced `.devin/docs/TOOLS-MAP.md` (`--verbosity`/`DEVIN_VERBOSITY`, hook stdin `session_id` + `prompt_id`, `PreToolUse` `hookSpecificOutput.updatedInput`, `keymap` `-`-separated key-spec validation, `devin desktop`, and `agent.verbosity: 3` alignment note).
- **`agentic-rag` skill production guardrails**: added architecture selector (<200k prompt-cache vs. linear RAG+reranker vs. agentic RAG), 3-context separation table (verbatim recent turns vs. `kind=conversation` user memory vs. `kind=document` corpus so document examples are never attributed to the caller), iron rules against silent rerank/gate fallback (`RERANKING_FAILED` / stage verification) and streamed request deadlines (`CancellationTokenSource` + reasoning `gen_token_budget`), and `hit@1`/`hit@3`/`MRR` + split `p50`/`p95` latency metrics in Gate G5.
- **`ai-tools` skill expanded with Reasoning & Domain Model Post-Training Playbook**: added evidence-backed method selector (Self-Consistency `arXiv:2203.11171` / `arXiv:2408.03314`, SFT Reasoning Distillation `s1K`/DeepSeek-R1 `arXiv:2501.12948` / `arXiv:2501.19393` for `<7B` models, RLVR with GRPO/DAPO `arXiv:2402.03300` / `arXiv:2411.15124` / `arXiv:2503.14476` for `>=7B` models), 4-gate implementation route (Verifier -> Inference Baseline -> Distillation -> RLVR), and iron rules against unverified self-refinement (`arXiv:2310.01798`), format-reward hacking, and zero-variance group collapse.

## [3.15.0] - 2026-10-28

### Added

- **`brag-slim` skill** (#244): single-file `/brag` variant vendored from latent-spaces/brag v0.5.0. No bundled assets; builds the launch video with tools already on the machine and supports website-URL input with prompt-injection hardening (fetched content treated as data, never instructions). Full `skills/brag/` synced to upstream 0.5.0: Opus 5.5 dispatch to `/brag-slim`, bundled `slim.md`, refreshed cue-analysis deps. Manifest, README and TOOLS-MAP synced to 91 skills.

### Fixed

- **Stale composition-skill references in vendored `/brag`** (#245): the delegation pointed at HeyGen domain skills absent from the bundle. Composition guidance now uses `skills/hyperframes` + `extensions/hyperframes/wrapper.py` for the CLI contract and `skills/animation-direction` for motion and beat-to-visual mapping. HeyGen skills stay optional when their plugin is installed; audio-reactive extraction documents a local ffmpeg/librosa fallback, and `.claude` paths were replaced with Devin install paths.

## [3.14.0] - 2026-10-27

### Added

- **`drift-report` skill** (#242): port of `egm-drift-report` (google/elephant-goldfish-model, Apache-2.0). Detects design-doc-vs-code drift: missing features, incomplete models, logic shortcuts, architectural divergence. Report-only output `<YYYY-MM-DD>_DRIFT_REPORT.md`; complements `spec-consistency.py` (plan-file internals) with doc-to-code fidelity.

### Fixed

- **Audit drift warnings** (#241): `render_norm()` now normalizes `pythonw` -> `python` (false-positive hooks live-vs-render after the pythonw renderer in #232); `manifest.json` `export_hash` re-synced for 10 scripts + 2 agents stale since #234/#236/#240; README version badge synced with manifest.

## [3.13.0] - 2026-10-27

### Added

- **`agentic-rag` skill** (#237): implementation playbook for evidence-gated agentic RAG products (retrieve -> decision-gate -> answer-or-escalate). Multimodal per-page index (text chunks + page PNG), decision-model answerability thresholds in DB, human-review ticket loop with save-to-knowledge re-indexing. Stack-agnostic slots; decision-model slot is free-first with **Laya multilingual** (Apache-2.0, self-host) as reference, Kev/Jeeves/Strands Decider/open-weight d1-3B as swaps, Jev/hosted d1 as paid options.

### Fixed

- **Windows console popups** (#238): every console-subsystem child spawned from the console-less runtime allocated a visible conhost window. Hook renderer emits `pythonw` on Windows (#232); all `subprocess` call sites in hook scripts (#234) and across extensions (#236, 29+ sites) pass `CREATE_NO_WINDOW` via getattr fallback (POSIX no-op).
- **CU toast identity** (#239): Windows notifications now show `Cu-Talk` instead of `devin-computer-use`; MCP protocol name unchanged.

## [3.12.0] - 2026-10-27

### Added

- **External-repo integration suite** (Stackademic top-10 analysis, #224, #226, #227, #228, #229): 10 repos evaluated against the bundle; 5 landed as skills/wrappers, 4 already covered (`brag`, `grilling`/`tdd`/`implement`/`triage`, `rea-ops`, `scrape-tools`), 1 rejected (VoiceStudio: AGPL + desktop GUI).
- **`frontend-design` skill** (#224): port of anthropics/skills `frontend-design` (Apache-2.0); aesthetic direction up front, pairs with `impeccable`.
- **`career-ops` skill** (#229): port of santifer/career-ops workflow modes (MIT); public-board scan, fit scoring, CV tailoring, tracker under `.devin/scratch/career-ops/`; agent never submits applications.
- **`hyperframes` extension + skill** (#226): governed wrapper (`extensions/hyperframes/wrapper.py`) for `npx hyperframes` HTML-to-MP4 rendering, whitelisted `doctor`/`init`/`render`; HTML-native alternative to `remotion-render`.
- **`agent-reach` extension + skill** (#227): governed wrapper for the `agent-reach` JSON CLI, limited to credential-free channels (`github`, `youtube`, `bilibili`, `v2ex`, `web`); cookie channels rejected per bundle credential policy.
- **`tts` skill + `voicebox` wrapper** (#228): local TTS via the voicebox FastAPI backend (`127.0.0.1:17493`, urllib-only client); completes the local narration pipeline `tts -> asr -> animation-direction`.
- Contract tests for the three wrappers (25 tests, no network).

## [3.11.1] - 2026-10-27

### Fixed

- **`manifest.json` version sync**: bumped `3.10.0` -> `3.11.1` so the release workflow's version gate passes. The `v3.11.0` tag shipped without the manifest bump and its release run failed at `Verify tag ancestry and version sync`; tags `v*` are immutable, so the fix lands as this patch release. All `3.11.0` content ships unchanged in `v3.11.1`.

## [3.11.0] - 2026-10-27

### Changed

- **Devin CLI 3000.11.228 alignment**: `data/bundle-identity.json` and README now validate against `3000.11.228` (installed `053434014dbd`; delta covers `3000.11.205` + `3000.11.228`). New capability table in `.devin/docs/DEVIN-CLI-COMPATIBILITY.md`; `TOOLS-MAP.md` gains `/rename`, `/confetti`, `/hooks`, `devin models` and the new hook fields; `/loop` + `agent.model_mixture` removal noted (bundle unaffected: `scheduled-turns` uses `devin -p`).

### Added

- **`fail_closed: true` on PreToolUse guards** (`hooks.v1.json`): verified empirically that an exit-1 hook lets `exec` through without the flag and blocks it with `Blocked: a required PreToolUse hook failed`. Ships on `pre-exec-guard.py` and `pre-write-guard.py` so a broken gate fails secure; observer hooks stay fail-open.
- **`read_config_from.cloud: false`** (`config.json`): keeps Devin Cloud MCP servers and personal plugins out of the validated surface, matching the existing `read_config_from` policy; organization-required plugins still load.

## [3.10.0] - 2026-10-24

### Added

- **agent-rts LORE.md: DevinCraft, A Cronica da Oficina** (`extensions/agent-rts/LORE.md`, #213): 7-section pt-BR tale mapping the 11 canonical buildings, 15 hero classes, fog, contested tiles, Wonder Age, War Council and the player beyond the mist; extension-local `ARCHITECTURE_MANIFEST.md` for the architecture gate.
- **agent-rts 50-loop WC3 polish pass** (#214): combat (hit flash, death dissolve+pool, damage vignette, camera shake, under-attack ping+horn, hero-fallen alert, +xp floaters), control (Tab subgroups, contextual r-click, ESC disarm, control groups, formation spiral, hover ring), world (soft fog + reveal peel, void edge, instanced doodads, cloud shadows, critters, contested decals, gold piles, day/night with sun/moon/dial, night windows), meta (rally line+flag, waypoint posts, production bars, decision beacon, quest+age banners, per-class barks, ambient pad, favicon). Matrix: 51 DONE, 1 GAPPED, 4 BLOCKED-BY-CANON.

### Fixed

- **agent-rts fog of war leaks + army vision** (#208, #209): marks/plots/gold/decals/smoke/dust/sparks/server FX/meteor trails no longer render inside unexplored shroud; `puff(x,y,z)` honored its z argument (all smoke compressed to the north edge); own troops never vanish and carry a sight halo via a separate fog overlay plane repainted per unit-tile change; path trail counter-rotated so waypoints anchor to the map instead of spinning with facing.
- **agent-rts camera rebuild** (#210): pan/zoom write directly to the camera (no ~150ms spring lag), rotation only via Insert/Delete/MMB-drag, RMB never rotates (fixes smart-order collision), rotated-pan sign error fixed.
- **agent-rts HUD regression** (#211): banner skin scoped to `#banner` (was stacking portrait/feed/roster/toasts at top-center), inventory runes render readable values, feed dedups consecutive repeats, camera rescue snaps instead of gliding from the void, `window.__rts` debug handle.
- **UTF-8 decoding on Windows pipes** (#212): `collectors._run` and `check-ai-signature` decode subprocess output as UTF-8 with replace (was cp1252: ticket mojibake `frÃ¡geis`, hook crash on UTF-8 diffs).
- **computer-use record flake** (#118): `_record` accepts injected `_now`/`_sleep`; pacing tests run on a deterministic FakeClock instead of racing a loaded CI scheduler.

## [3.9.0] - 2026-10-24

### Added

- **M2 NEXTGEN milestone planning suite** (`.devin/research/MILESTONE_NEXTGEN_MATRIX.md`, `.devin/issues/MILESTONE_2_*.md`, #203 #204 #205): deep technical ingestion of 10 reference sources (google-research/harness2, vercel-labs/agent-skills, nextlevelbuilder/ui-ux-pro-max-skill, alchaincyf/huashu-design, pbakaus/impeccable, msitarzewski/agency-agents{,-app}, DeusData/codebase-memory-mcp, stablyai/orca, and 2 video workflows covering Blender camera-blocking and PandaCode token-saver UX), each verified against primary sources and classified as UPGRADE_EXISTING / NEW_EXTENSION / NEW_SKILL / HOOK_INTEGRATION against the current bundle. The matrix specifies a unified design suite (one muscle `extensions/design-intelligence/` = BM25 engine + CSV corpus + ~62-rule deterministic linter + vercel frontend-rules + aesthetics re-index; brain upgrades in-place on `skills/impeccable`, `skills/creative-engineering`, `agents/art-director.md`; zero new design skills), a tripartite code-read routing rule (rg / code-graph pattern-port / semble / ask_laya_glob) with codebase-memory-mcp adoption gated on a held-out token benchmark, PPC self-improvement upgrades with anti-leakage lessons retention, installs drift ledger (5-state SHA reconcile + backup-before-overwrite), agent-rts opt-in dispatch lane, token-saver output modes, and a Blender camera-blocking pipeline. Ships the executable backlog: 14 DAG-ordered local issues `MILESTONE_2_01..14` with declared blocking edges and per-issue gates. Corrections verified during recon: drift states are five (adds Removed), cbm token-savings claim did not reproduce in independent benchmarking, and the `platform/gemini-argus` branch is absent so multi-CLI render targets ship disabled.

## [3.8.0] - 2026-10-24

### Added

- **agent-rts DevinCraft 3D PBR RTS/Tycoon orchestrator extension** (`extensions/agent-rts/`, `skills/agent-rts-commander/`, #200): `server.py` is a stdlib HTTP+WebSocket daemon on port 8798 (`AGENT_RTS_PORT`) sharing `.devin/rts/` state with `rtsd` (zero protocol drift); `collectors.py` reports real repo telemetry (git branch/dirty/worktrees, `gh issue list`, prompt-compiler queue, ledgers, context gas, supply); `world_bridge.py` reuses `rtsd/world.py` event-sourced semantics without mutation; `bootstrap.py` provisions the extension `.venv`; `selftest.py` gates boot, snapshot schema, WS handshake, static/vendor assets, intent writes, allowlisted `/cmd`, decisions, event log, and score. `web/` ships a vendored Three.js PBR client (14 modules): RTS camera pan/zoom/rotate, click+box selection, grid pathing with steering, spring-damper UI, procedural particles (blue design / green code / purple research / red bugs), tilt-shift post pass, SSAO hooks, dual live-switchable themes (Medieval RTS vs Office Tycoon) plus `#theme=` deep links, HUD topbar with real gold/ctx/gas/supply/dirty counters, ticket rail from real GitHub issues, decision modal, minimap, and `#booterr` on-page error surface. Inbound WS `order` writes intent files for the orchestrator (never auto-executed); `/cmd` allowlist: `forge_ticket` -> `prompt_compiler.py --draft`, `laya_guard` -> `laya_cli.py predict --preset guard`, `compact_hint`, `refresh_repo`. `.devin/research/AGENT_RTS_GAME_DESIGN.md` documents the mechanic-to-CLI mapping, WS protocol, ECS FSM, and PBR pipeline.
- **agency pipeline: asset-driven agentic DAG, orchestrator prompts v3 & 07_Chief_of_Staff (Goose) profile** (`.devin/orchestrator_prompts_v2.md`, `agents/`, `.devin/research/ssp_ai_orchestrators.md`, #201): the 7-persona pipeline moves from linear `cat << 'EOF'` chaining to an asset-driven DAG modeled on ssp.sh data-orchestration patterns (assets as materialization targets, deterministic skeleton + stochastic nodes). Front-matter schema_version 3 adds `upstream_hashes` (file@sha8), `status: DRAFT|APPROVED|BLOCKED`, and `rework_cycle`; the 04->02 bounded feedback loop routes `04_BLOCKERS.md` diffs to the Tech Lead with a 2-cycle cap then operator escalation; Laya `router`/`guard` presets classify node transitions without spending main-model tokens; write protocol uses per-write `AGENCY_EOF_NN_<ts>` delimiters plus a base64 fallback; tooling bounds (`semble --limit 20`, docling verify, conditional Shannon read) are explicit. `agents/chief-of-staff.md` adds the seventh profile: an out-of-critical-path SysAdmin watchdog with a whitelisted AUTO-FIX set and `NOMINAL|DEGRADED|ESCALATE` verdicts; the six existing profiles gained v3 contracts without identity or model changes. `manifest.json` `agent_count` 13->14.

- **rtsd optional WebGL 3D render path with Canvas painter fallback** (`extensions/rtsd/web/`, #194): `engine3d.js` adds `Engine3D`, a real depth-tested WebGL1/2 renderer that subclasses the `Engine` camera/input/picking/clamp/minimap math 1:1 - per-frame CPU vertex emission into a single streamed buffer draws lambert-lit terrain quads (water sunken `z=-5` with animated color waves, bridges `z=+1.5`), deco cones/cylinders for trees and rocks, stacked `emitBox`/`emitCone`/`emitCyl` volumetric buildings per `bid` (Keep corner towers, runeforge chimney), unit cylinders + box heads with bob, GL_LINES ellipse selection rings + Flaming Weapons buff rings, point-sprite fx, and 160-line rain/storm streaks; the existing `#cv` canvas becomes a transparent 2D HUD overlay (names, HP/mana bars, barks, P/G/A/F status badges, waypoint flags, order marks, armed preview, pings, night dim). `app.js` selects the backend via `?renderer=webgl` or persisted `localStorage.rtsd.renderer` (Game Menu `Renderer:` toggle, default `canvas`) with `Engine3D.supported()` detection; isometric office mode and no-GL environments always fall back to the Canvas painter. `sw.js` bumps cache to `rtsd-v6` and adds `engine3d.js` to the app shell; `index.html` loads it after `engine.js`; `engine.js` exports the constructor as `Engine._ctor`; `selftest.py` asserts `/js/engine3d.js` is served and loaded after `engine.js`.
- **rtsd Devin CLI gamification loop: commander XP/rank, quest milestones, minted trophy artifacts & `GET /trophies`** (`extensions/rtsd/`, #195): `world.py` adds `_progression()` deriving commander XP from real session actions (gates passed x10, quests done x50, skill casts x5, heroes deployed x25, achievements unlocked x100) across 10 rank tiers (Recruit -> Legendary Commander) with perk labels bound to real mechanics; `q["milestone"]` exposes each quest's real milestone (effort dir); `_mint_trophies()` writes deterministic SVG shield badges + markdown citations to `.devin/rts/trophies/` on achievement unlock. `rtsd.py` adds `GET /trophies` (list) and `GET /trophies/<id>.svg` (badge artifact). `app.js` renders the Commander Rank crest + XP progress bar + XP breakdown in the Game Menu and marks minted trophies in the Hall of Glory.
- **rtsd Micro & Command Layer: armed-order path preview, loop destination marks, unit status badges, spell cooldowns, Focus-Fire order & action feedback** (`extensions/rtsd/web/`, #193): `engine.js` renders live dashed path preview from every selected unit to the cursor plus a pulsing target ring while a targeted order is armed (`st.armed`), chained destination marks for client-side loops (`st.orderMarks`: patrol pennants, gather gold-mine diamond + Keep flag, attack/focus crosshair X), per-unit order status chips (P/G/A/F) and a flickering Flaming Weapons buff ring. `app.js` adds the Focus-Fire order (`F` hotkey + card button, quest-POI snap), cast/ability/special cooldowns with countdown overlays (`.cd`), `.fired` gold flash on the last issued command, inspector status/buff chips (`PATROLLING`/`GATHERING`/`ASSAULT`/`FOCUS FIRE`/`FLAMING WEAPONS`), and a 400ms cooldown tick loop that keeps the card counting down. `index.html` adds `.cd`/`.fired` styles.
- **rtsd True Office Tycoon Mode (Game Dev Tycoon / Cafe Mania style: staff roster, needs, desks, sprint loop & upgrade cards)** (`extensions/rtsd/`, #192): `world.py` adds `_office_state()` exposing `office` in snapshot with staff roster (energy, coffee, needs, desk assignment, task, XP/level), departments by lane, sprint progress and upgrade cards. `index.html` adds `Office` side panel and `#officePanel` overlay; `app.js` renders staff cards, needs badges, energy/HP bars, sprint progress bar and upgrade list.
- **rtsd Age of Mythology: Retold 5 Ages progression, Divine Favor, Reusable God Powers bar (`#godbar`) & BANG!-style unit collision pushing** (`extensions/rtsd/`, #190): `world.py` adds `_age_and_favor()` computing the 5 Ages (`I. Archaic -> II. Classical -> III. Heroic -> IV. Mythic -> V. Wonder Age`), Minor God patrons, `resources.favor`, and 4 reusable God Powers (`Vision`, `Restoration`, `Flaming Weapons`, `Meteor Storm`). `index.html` and `app.js` add the top-bar Age Crest (`#ageBtn`), `FAVOR` resource pod, top-center `#godbar` with escalating Favor costs and cooldowns, 3D God Power VFX, and pairwise BANG!-engine unit collision separation in `stepMotion(dt)`.
- **rtsd continuous river channels & unidirectional downstream water flow** (`extensions/rtsd/web/js/engine.js`, #188): replaces per-tile circular water `arc`/`ellipse` rings and circular `(sin(wph1), cos(wph1))` wave orbits with continuous connected river strokes (`strokeWaterPass` with `lineCap = "round"` for sandy bank, shallow water, and deep channel) and unidirectional downstream current streaks (`pFlow = (now / 2200 + seed) % 1` modulated by a `sin(pFlow * PI)` fade-in/fade-out envelope so ripples glide strictly forward without ever reversing or orbiting).
- **rtsd stateful `dt`-integrated weather particle engine & soft volumetric clouds** (`extensions/rtsd/web/js/engine.js`, #186): fixes the `now * wind.vx(now)` phase-whipping bug in `_windVec`, water waves, and `_weatherPass` by separating steady `baseStr`/`baseVx`/`baseVy` from instantaneous gust sway and integrating persistent cloud, leaf, rain, and snow particles by frame `dt` (`p.x += vx * dt`). Replaces hard-edged `ctx.ellipse` cloud/fog ovals with multi-stop radial gradients (`createRadialGradient`) and disables outdoor weather particles inside indoor Office Mode.
- **rtsd strict camera map clamping in Battlefield & Office Isometric modes** (`extensions/rtsd/web/js/engine.js`, `extensions/rtsd/web/js/app.js`, #184): binds `eng.map = state.map` / `st.tiles` so `clampCam()` and canvas click handlers no longer early-return on `if (!this.map) return;`. Enforces minimum zoom `zMinBf` / `zMinIso` so the viewport never exceeds the map span, removes the `+-40px` out-of-bounds margin in Battlefield mode, and clamps isometric diamond coordinates `U = 2*cam.y + cam.x` and `V = 2*cam.y - cam.x` so all 4 screen corners stay strictly within `0 <= wx <= mw` and `0 <= wy <= mh`.
- **rtsd complete UI/UX & multi-theme HUD overhaul (Battlefield Race themes vs Corporate Office OS theme, Resource Bar & Inspector Cards)** (`extensions/rtsd/web/`, #182): `index.html` and `app.js` introduce reactive theme/faction CSS variables (`body[data-theme="battlefield|office"]` and `body[data-race="human|orc|elf|undead"]`), switching the HUD between ornate faction-tuned RTS frames (`human` royal gold/navy, `orc` crimson iron, `elf` silver/violet, `undead` blight green/obsidian) and a sleek Modern Corporate OS slate/cyan dashboard in Office Mode. Replaces the raw `#res` text line with 4 structured Resource Pods (`GOLD/BUDGET`, `LUMBER/CONTEXT`, `SUPPLY/STAFF`, `UPKEEP/BURN`), declutters the top header toolbar, upgrades `#portrait` into a structured Unit Dossier Card with named Kit Tool Pills and clickable Spell Chips, and upgrades Quest Log entries into visual cards with gate progress bars (`qbar`).
- **rtsd complete 3D Isometric Office Mode overhaul (3D furniture, glass boardroom, server racks, dual-monitor desks & tech dev rigs)** (`extensions/rtsd/web/js/engine.js`, #180): replaces medieval castle/knight fallbacks in Office Mode (`this.iso`) with zoned 3D Tech Startup HQ flooring (oak hardwood boardroom, acoustic carpet tile grid, concrete cable-tray corridors, recessed liquid-cooling data trenches, indoor potted Monstera plants & robot vacuums), `_drawOfficeBuilding3D` constructing 11 3D office structures (`Meeting Room` glass boardroom with walnut table, 6 swivel chairs & 65" presentation display, `Onboarding Desk` L-counter with dual monitors & MacBook boxes, `Break Room` espresso bar with steaming espresso machine & stainless fridge, `Bookshelf` wall, 3x 42U `Server Racks` with blinking LEDs, commercial `Printer` ejecting paper sheets, magnetic glass `Whiteboard`, soundproof Framery `Phone Booth`, smart `Vending Kiosk`, 5-gallon `Water Cooler` with rising bubbles & sofa, and 3-column `Kanban Wall`), and `_drawOfficeUnit3D` rendering 3D Software Engineers in hoodies/blazers with lanyards, smart glasses, headsets + boom mics, laptops/coffee mugs, and 3D dual-monitor sit-stand workstations with live IDE code & typing animations.
- **rtsd Campaigns (Map DAG Lines + Review & Merge), Scheduled Loops (`/loops`), Integrated Terminal (`Ctrl+T`), Ambient Music & War Advisor** (`extensions/rtsd/`, #178): `engine.js` draws Campaign DAG dependency lines (`q.deps`) between Quest POIs on the 3D map; `rtsd.py` adds `GET/POST /loops` (`create`, `trigger`, `stop` persisted in `.devin/rts/loops.json`) and `POST /terminal` (loopback admin shell execution, 403 for spectators/replay); `index.html` and `app.js` add the `Campaign/Loops` Side Panel tab, `Ctrl+T` Multi-Tab Integrated Terminal drawer (`#termdrawer`), `#musicBtn` procedural modal soundtrack, and `#tutBtn` 5-step interactive War Advisor tutorial.
- **rtsd Collectible Skill Scrolls on Map + Achievements (Hall of Glory & Trophy Card 600x315 PNG)** (`extensions/rtsd/`, #176): `world.py` adds `_scrolls()` (5 deterministic collectible Skill Scrolls placed on the map from real `skills/` entries) and `_achievements()` (12 tiered achievements across `Discovery`, `Mastery`, and `Secret` in `Common`, `Uncommon`, `Rare`, and `Legendary` rarities evaluated from real session metrics). `engine.js` and `app.js` render 3D floating golden Skill Scrolls with rotating rune rings on the map and gold dots on the minimap, add 1-click Scroll casting, and add the Hall of Glory gallery with `downloadTrophyCard()` exporting `600x315` PNG Trophy Cards.
- **rtsd Race Faction Skins (`Human`, `Orc`, `Elf`, `Undead`) + Fog Toggle (`V`), Territory Heatmap (`H`), War Table (`` ` ``) & Hotkeys** (`extensions/rtsd/web/js/`, #174): `theme.js` adds 4 persisted Race Faction Skins (`human`, `orc`, `elf`, `undead`) transforming terrain grass/water/road palettes and 3D structure materials/roofs. `engine.js` and `app.js` add `V` Fog of War toggle (`state.noFog`), `H` Territory Activity Heatmap (`state.heatmap`), `` ` `` War Table overlay (`state.warTable`), `Y`/`N` War Council quick-approval, and `F9`/`F12`/`Enter` panel hotkeys.
- **rtsd Side Panel Explorer, Git Codex & Worktree Manager + `@file` autocomplete & Voice Input** (`extensions/rtsd/`, #172): `rtsd.py` adds `GET /files` (bounded project file tree with extension badges `PY/JS/TS/MD/JSON/RS/GO/SH/HTML/CSS/IMG`), `GET /git` (`git status` changes labeled `altered`/`newly scribed`/`sealed`/`destroyed`, `git worktree list`, branches, stashes, recent commits), `GET /git/diff?path=<rel>` (path-confined unified diff or file preview), and `POST /git` (safe Stash Manager `stash_push`/`stash_apply`/`stash_pop`/`stash_drop`). `index.html` and `app.js` add Side Panel tabs (`Quests/Econ | Git Codex | Files`), `@file` autocomplete in the `#msg` composer alongside unit names, and `#micBtn` Web Speech API (`SpeechRecognition`) voice transcription with auto-send on silence.
- **rtsd real 3D perspective engine, 3D heightmap terrain, 3D volumetric buildings & 14-joint 3D skeletal animations** (`extensions/rtsd/web/js/engine.js`, #170): replaces the flat top-down orthographic projection and vertical-bobbing 2D sprites with a tilted 3D RTS perspective camera (`PITCH = 0.74`, vertical Z elevation `-wz * 0.88`, and exact 3D ground-plane inverse in `toWorld` / `toScreen`), 3D elevated Citadel plateaus with stone retaining walls, sunken riverbanks, 3D arched timber/stone bridges, and 3D multi-tier conical swaying trees (`_cyl3D` + `_cone3D`). Adds `_drawBuilding3D` (`_box3D`, `_cyl3D`, `_cone3D`, `_roofPrism3D`) constructing all 11 structures in 3D `(wx, wy, wz)` space (Citadel Keep with 4 cylindrical corner towers, Garrison Fortress, 2-story Timber Inn, Arcane Sanctum with 3-axis gyroscope rings, Guard Spire, Blacksmith Foundry with animated 3D trip-hammer, Waygate Portal, Market Pavilion, Ziggurat Altar with 3D winged statue, Pantheon), and upgrades `_drawUnitLive` to a 14-joint 3D articulated skeletal rig (`Rig3D`) with smooth 3D facing yaw (`atan2(dy, dx)`), Z-sorted limbs, and 8 keyframed 3D animations (`Idle`, `LookAround`, `Flourish`, `Walk`, `Attack`, `Gather`, `Wave`, `Dance`).
- **rtsd procedural WebAudio DSP sound engine with Karplus-Strong, FM metallic clashes & theme-aware foley** (`extensions/rtsd/web/js/app.js`, #165): replaces basic single-oscillator beeps with a real-time WebAudio DSP synthesizer (`_getNoise` pink-weighted noise buffer, `_fm` inharmonic FM metallic partials, `_noise` biquad-filtered noise bursts, `_pluck` Karplus-Strong plucked string synthesis, and `syncAmbience` dual-filter continuous wind/rain soundscape tracking live `weather.wind_kph` and `weather.condition`). Adds distinct per-class and per-structure acoustic signatures (Runeforge anvil clang, Tavern lute chord, Altar cathedral choir triad, Marketplace coin chime, Portal void hum, Library crystal shimmer) and automatic Office Mode foley switching (mechanical key clacks, printer stepper whir, espresso steamer hiss, water-cooler bubble glug).
- **rtsd HUD architecture, F10 game menu, 4x3 QWER command card with vector icons & 6-slot inventory** (`extensions/rtsd/web/`, #164): `index.html`, `app.js`, and `engine.js` upgrade the bottom console to a competitive 4x3 (`Q W E R / A S D F / Z X C V`) Command Card with custom inline SVG vector icons (`ICON_SVG`) and an anchored WC3 Command Tooltip (`#cardtip`), add a WC3 6-Slot Runed Inventory Grid (`#invgrid`) and beveled HP/MP/XP progress bars (`#pbarHp`, `#pbarMp`, `#pbarXp`) beside the animated 3D portrait, add minimap filter toggles (`all`, `units`, `bld`) plus an isometric camera frustum polygon on the minimap in Office mode, and add the `F10` Game Menu modal (`#gamemenu`) featuring a full local weather forecast inspector and 1-click weather mode overrides.
- **rtsd 3D volumetric modeling, seamless terrain splatting, cast shadows & skeletal/Verlet physics** (`extensions/rtsd/web/js/`, #163): `theme.js` adds 3D PBR-inspired volumetric shading helpers (`_cylGrad`, `_sphereGrad`, `_roof3D` with sunlit West vs shadowed East slopes and shingle courses) and Ambient Occlusion contact shadows across all 11 structures and 22 unit/hero classes at `96x96` raster resolution. `engine.js` adds `_ensureTerrainCanvas` (offscreen organic biome splatting, stone-paved Keep courtyards, soft-edged wheel-rutted dirt roads, and sandy riverbanks), 2-wave Gerstner water superposition with specular glints, directional ground cast shadows, 4-node Verlet cloth capes trailing unit velocity and wind, 2-bone articulated leg stride kinematics, and ranged arrow/arcane projectiles during combat.
- **rtsd HUD, mechanics & gameplay overhaul + procedural soundscape** (`extensions/rtsd/web/`, #159): `index.html` and `app.js` add the WC3 Top-Left Hero Roster Bar (`#herobar`, click to select, double-click to center), AoE3 Top-Right Building Quick-Select Strip (`#bldbar`), live local Weather HUD orb (`#wxBtn`, showing city, temperature, condition, wind speed/direction, and 6h forecast tooltip, click to cycle weather modes), animated 3D-style Portrait canvas (`#portcv`), collapsible `Comms`/`Quests` drawers (`#togFeed`/`#togSide`), and floating hover tooltips (`#tooltip`). War Council (`#council`) no longer traps the viewport on expired decisions and gains a close button (`#councilClose`). The 3x4 Command Card (`#cmdcard`) adds icons, hotkey badges, `Gather` (`G`), and Building Commands when a structure is selected (1-click hero class recruitment at Barracks/Tavern, Town Bell, Rally, Tech Tree, Victory Score). Gameplay loops in `stepMotion` execute continuous Patrol (`P`), Gold/Lumber Gather hauling (`G` or right-click gold vein), Quest/Camp combat engagement (`A`), and visual AoE Spell effects (`pushFx`) backed by expanded procedural WebAudio SFX (`select_hero`, `select_bld`, `attack`, `gather`, `spell`, `thunder`, `bird`).
- **rtsd WC3/AoE3 unit, hero & building modeling + autonomous life** (`extensions/rtsd/web/js/`, #158): `theme.js` replaces basic disc/triangle/keep primitives with multi-part procedural silhouettes for all 22 unit/hero classes (pauldrons, class headgear, shields, broadswords/staves/bows/hammers, team trim) and all 11 structures (`town-hall` Keep with twin towers and oak gate, `barracks` with battlements and crossed spears, `tavern` with timber frame, chimney, and barrels, `library` with azure dome and lancet windows, `watchtower` spire, `runeforge` with glowing furnace and anvil, `vault`, `portal` with void vortex, `marketplace` with striped awnings, `altar` with winged statue, `trophy-hall` pantheon) plus `Theme.drawPortrait` for live animated portraits. `engine.js` adds `_drawBuildingAnim` (wind-flapping banners, drifting chimney/forge smoke, rising forge sparks, orbiting arcane rings, portal vortex, sacred braziers, watchtower beacon) and `_drawUnitLive` (WC3 Hero Glow, rotating Aura rune rings, wind-reactive flowing capes, striding boots + footstep dust puffs, `Stand - 1/2/3` look-around and weapon flourish fidgets, social nods between nearby idle allies, worker gold/timber hauling, and active combat/spell FX).
- **rtsd live local weather + wind physics + WC3/AoE3 terrain engine** (`extensions/rtsd/`, #157): `rtsd.py` adds `GET /weather`, `POST /weather` (mode cycling across `live`, `clear`, `overcast`, `rain`, `storm`, `snow`, `fog`, `windy`), and `snapshot.weather` backed by IP geolocation (`geojs.io`/`ipwho.is`) and Open-Meteo current + hourly forecasts cached in `.devin/rts/weather.json`. `sw.js` bypasses cache for `/weather`. `engine.js` and `theme.js` compute a unified wind vector (`wind_kph`, `wind_gust_kph`, `wind_deg`) that drives water wave crests, shoreline foam, swaying multi-layer forest trees, falling leaves, bending grass/reeds, cloud shadows, slanted rain/snow/fog particles, and storm lightning; terrain synthesis adds cobblestone Keep plazas, dirt roads connecting capitals and plots, river/lake channels with wooden bridges at road crossings, wandering critters, and dynamic Line-of-Sight vision around all allied buildings and units.
- **rtsd post-review audit fixes** (`extensions/rtsd/`, #155): resolved all 9 Spec and Standards findings from the v3.8.0 milestone review - `_apply_hook` now accepts `type == "hook.posttooluse"` alongside `hook == "PostToolUse"` for gold/burn/activity accounting; isometric wheel zoom projects `(p.x, p.y)` before updating `cam.x`/`cam.y`; `sw.js` bypasses cache for `/buildings`, `/score`, `/sessions`, and `/replay`; Marketplace merges `mcp_config.json`/`.devin/mcp_config.json` with `bundle-integrations.json` and reports tool counts; hero completion triggers `barkLine(cls, 2)` and minions group around their summoner hero; non-shift orders replace unconsumed orders (`stop` and debriefs mark orders consumed), waypoint lines chain `unit -> wp1 -> wp2`, and motion glides through queued waypoints in FIFO order; Office mode shows `OFFICE_BLD.label` in the building inspector, gathers idle heroes by the water cooler, and flashes printer fire on `runeforge` during breaches; `list_sessions()` caches replayed worlds by `(mtime, size)` and the Web UI Victory Screen renders Match History from `/sessions`; `<700px` mobile/PWA view gains `#mtabs` (`map | quests/econ | comms | orders`).
- **rtsd polish pass: animations, ambient life, day/night, guide card** (`extensions/rtsd/`, #136): unit animation states - heroes glide across the map toward their latest live order coordinate (display position eased per frame at a fixed walk speed, walk-bounce while moving) and drift back to their home tile when the queue empties; work-loop hammering while `status_live == "running"`, slow idle fidget otherwise; existing fade-outs kept for deaths/despawns. Ambient life (purely cosmetic, hash-seeded): birds crossing the battlefield sky plus drifting fog wisps, dust motes in the office theme; worker peasants still scurry on real hook firings. Day/night cycle: `world.started` (first event ts, replay-safe) anchors a 600s WC3-style day/dusk/night/dawn cycle; when enabled the map dims and building windows glow - toggled by the N key or the `day/night:` header button, persisted in `rtsd.daynight`, zero render cost while off. Hotkey audit + legend: the `?` guide card now lists every implemented binding - A attack-target, H hold, P patrol, `.` idle-worker cycle, F1-F4 camera bookmarks (Ctrl+Fn saves), plus the existing groups/Tab/SPACE/ESC/T/K/M/-/= set - an entity glossary, mode switches and mouse/command references (A took over from left-pan; arrows/edge/WSD still pan). Performance: procedural sprites are rasterized once per entry into offscreen canvases and blitted with `drawImage`, cutting per-frame path+text work for every unit/building/worker/fade.
- **rtsd replay + spectator + score screen** (`extensions/rtsd/`, #135): `rtsd.py --replay <events.jsonl>` runs a playback daemon that rebuilds the session deterministically through the same `World.apply` path; `GET /replay` reports `{total,index,playing,speed,done}` and `POST /replay` accepts `play`/`pause`/`seek` + `speed` (UI presets 1x/2x/4x, scrub slider = jump-to-event); each applied event broadcasts the identical upsert shape a live event produces, seeks rebuild via `World.replay` + a snapshot broadcast, and every other POST is denied server-side (403). Spectator mode: `--remote` now mints a second read-only token alongside the admin token (printed as a spectator URL, both stored operator-side in `.devin/rts/remote.json`); any client presenting it, loopback included, is scoped `client_role: "spectator"` in the snapshot and every POST returns 403, not just hidden in the UI - the web client additionally hides the command input/card under the spectator body class. Match history: `GET /sessions` walks `.devin/rts/` for every event log (`events.jsonl` plus archived copies like `sessions/*.jsonl`) and replays each through `World` for real per-session stats (events, agents, quests done/total, gates, tokens, duration). Score screen: `World.score()` aggregates quests/gates/heroes-by-xp/tokens/calls/duration over the same snapshot path, served at `GET /score`, shown as a victory-screen modal (auto-opens at end of a replay via a `score` WS frame) and as the TUI `/score` command. `tui.py` is now the command console: `--replay <file>` spawns the replay daemon and connects, `--spectate --token <t>` blocks `/intent`/`/answer` locally on top of server enforcement, and `/history` `/replay` `/play` `/pause` `/speed` `/seek` round out the console commands.
- **rtsd office mode: isometric theme** (`extensions/rtsd/web/js/`, #134): the office palette is now a true isometric presentation over the same world data. The engine centralizes projection in `toScreen`/`toWorld`: under `theme.iso` every world point maps through `(x - y, (x + y) / 2)` before the camera, and picking (`pickUnit`/`pickBuilding`/`unitsInBox`/`unitsInView`), order targeting, quest drops and pings all funnel through the same transform so the sprite you see is the sprite you click. Floor tiles render as iso diamonds (visible range derived by unprojecting the screen corners); camera clamp uses the projected map bounds; toggling re-centers on the same world point so the view never jumps. Office reskin table (GDD 3.2) covers all 11 buildings with interior glyphs + flavor labels: meeting room (town-hall), onboarding desk (barracks), break room (tavern), bookshelf (library), server rack (watchtower), printer (runeforge), whiteboard (vault), phone booth (portal), supply cabinet (marketplace), water cooler (altar), kanban wall (trophy-hall). Furniture and ambient life drawn from real positions only: desks under heroes with a typing bob while `status_live == "running"`, shared bench under minions, meeting table and water cooler at the town-hall plot, kanban walls behind quest markers. Decision summons: while a decision is pending, each hero gets a dashed walk line and a ghost sprite lerping toward a meeting-table slot (real unit positions, picking and selection untouched). Theme choice persists in localStorage (`rtsd.theme`). Minimap stays a top-down world overview (viewport rect skipped under iso).
- **rtsd alert system** (`extensions/rtsd/` + `web/`, #133): multi-tier alerts, all wired to real events. `world.breaches` in the snapshot lists every ledger with a failed gate, resolved to its territory (region named after the ledger, else the region holding a linked issue file's tile, else root) with the failed gate ids - so a wall breach keeps pulsing red across map and minimap until every gate in the ledger passes, and polling PWA/remote clients see the same alarm state without push infra. Snapshot diffs fire a new-breach alarm (horn, breach banner naming ledger+gates, fail ping at the region capital, `breach` feed line) and a `breach sealed` line when it clears. Procedural WebAudio signatures per tier (no asset files): council two-note sting on `decision.created`, low falling sawtooth horn on gate-fail/breach, soft sine blip on spawn pings, detuned-square clash on contested tiles, dual-triangle warn on upkeep escalations, quiet ack tick elsewhere. Sound controls: `snd:` header button / M key toggles mute, -/= set volume, both persisted in localStorage (`rtsd.snd`/`rtsd.vol`). Browser Notification API is opt-in via the `notify:` header button (permission-gated, graceful on deny/unsupported, fires only while the tab is hidden) for council calls, breaches and upkeep escalations. The alert stack orders by severity: red breach chips (`!region`, click = jump to the breached capital) outrank decision chips. TUI `/feed` prints `[ALERT decision]`/`[ALERT gate-fail]` lines for `decision.created` upserts and fail hints/debrief lines, and the hello snapshot now reports pending decisions plus active breaches.
- **rtsd tech tree + spellbook** (`extensions/rtsd/` + `web/`, #132): the K-key overlay renders the real skill economy. `world.tech` groups every `skills/<name>/` directory into the six GDD schools (Command/War/Lore/Craft/Creation/Summoning, plus `Unsorted` for skills the GDD table does not place) with a `path` back to its `SKILL.md`; `hook.posttooluse` events with `tool == "skill"` record casts in the event-sourced `world.skill_casts` ledger so cast spells glow with a count and never-cast skills render grey (availability + usage, never fake progression). Each hero carries a `spellbook` = the real skills literally named in its profile sheet (`agents/<profile>.md`), shown on the portrait, as `*skill` cast slots on the command card, and clickable in the overlay for the selected hero; casting posts a real `order` intent `{order:"cast", skill}` for `rts-intents.py`. Armory: `tech.armory` lists model tiers from `data/bundle-models.json` with the live subagent pin from `config.json agent.subagent_model` (falling back to the registry default); hero `model` now honors the profile's own `model:` frontmatter pin and `tier` is derived from that model's registry effort (medium=Footman, high=Commander, max=Knight), TOOLS-MAP as fallback. Library doctrines: `tech.doctrines` rates the 8 RAG chunking strategies (fixed/recursive/document/semantic/LLM/agentic/late/hierarchical) - `in_use` is set only when a real artifact proves it (cue-anchored whole-note retrieval in `scripts/memory-retrieval.py`/`memory-post-edit.py` over `.devin/memory/` notes marks `document`; `MOC.md` marks `hierarchical`), everything else shows not-in-use with empty evidence. Skill casts also emit `spell` feed lines and a spell ping on the library site, and `GET /buildings/library` returns `spellbook`/`doctrines`/`armory`.
- **rtsd economy HUD** (`extensions/rtsd/` + `web/`, #131): the top bar now reports a real income rate - `world.gold_log` records every PostToolUse event's est tokens (output chars / `CHARS_PER_TOKEN` + the same 200/call overhead used for gold, all replayed from `events.jsonl`) so `resources.income_min` is the trailing-60s token rate and `resources.income_last5` feeds a trend-bars sparkline in the new side Economy pane. That pane also shows the context window size and warn/crit/clear thresholds straight from `data/context-budget.json` (`resources.thresholds`) plus the supply split (`supply_heroes` / `supply_minions`). Per-hero economy: each unit's `burn` is the est token spend attributed to its event lane, and `turns_left` estimates remaining turns as (mana % of model window) / avg burn per call on that lane; heroes with no heartbeat report `null`, never a guess. Upkeep tier warnings: the HUD diffs successive snapshots and a tier crossing fires within one tick - econ feed line, res-bar flash animation, tone, and a minimap ping on the town hall (escalations only); upkeep itself stays derived from real context-pressure thresholds.
- **rtsd quest system** (`extensions/rtsd/` + `web/`, #130): the scratch-issue DAG is now a real WC3-style quest log. `world._quests` resolves dependency tokens to actual issue ids (short prefixes like `01` and GitHub-style `#120` both resolve; prose tokens stay visible in the chain text but do not block), recognizes the local `resolved` status, and enriches every side quest with `kind` (main/side), `done`/`failed`, `ledger` (per-issue ledger wins, else the effort ledger), gate tallies (`gates.pass/fail/total`), and `assignees` (heroes whose latest order carries the issue ref). Quest assignment: dragging a quest row onto a hero on the map or command-card/right-click Attack on a quest marker posts the same real `order` intent with the issue ref; the assigned hero's HP/xp/loot then track the issue's ledger gates and passed-gate `EVIDENCE` lines drop into the hero inventory tagged with the quest ref (WoW-style grid on portrait click, green-bordered quest loot). Map markers are state-aware: open `!` gold, blocked `?` greyed, failed `!` red until retried, done `*` rewards stamp. Comms feed gains `quest` lines: event-sourced `Quest accepted: <issue> -> <hero>` on assignment plus snapshot-derived `Objective complete (n/m)` / `Quest complete - reward: <ledger> ledger GREEN` / `Quest failed` lines (computed, never appended to `self.feed`, so replay stays pure). Quest log UI splits MAIN QUEST (latest `goal` intent) from SIDE QUESTS, greys blocked rows with the `a <- b` dependency chain, shows gate progress and assignee names; click a row to jump the camera to its marker.
- **rtsd war council** (`extensions/rtsd/` + `web/`, #129): `hook.permissionrequest` events now project into real pending decisions - the daemon writes `.devin/rts/decisions/<id>.json` in the exact shape `scripts/rts-decision.py --create` produces and appends a `decision.created` event (feed line names the requesting hero, gold minimap ping at town-hall). A decision poller in the tick also rings the bell for pending files created out-of-band (`rts-decision.py --create`), deduped via the event-sourced `world.dec_seen`. UI: pending decisions surface as a war-council modal showing the question, the requesting hero's portrait, council options with the last option marked as the deny-safe timeout default, and the rest of the queue stacked beneath; a header alert stack shows an `alerts:N` badge plus a flashing hero chip per pending decision (click pulls it to the chamber). Notification tiers per GDD: decision = modal + sound + gold ping, gate-fail = red breach banner + ping, info = feed only. Decisions stale past their `timeout` render as timed-out/deny-applied (fail-closed, matching `rts-decision.py --wait` semantics) and never re-alarm. Answers still flow through `POST /decisions/<id>/answer` writing the `.response` file `--wait` consumes; re-answer (409) and out-of-range choice (400) unchanged. Polling clients (PWA/remote) pick up new pending decisions via the snapshot diff the same way WS clients do.
- **rtsd comms feed** (`extensions/rtsd/world.py` + `rtsd.py` + `web/`, #128): the left Comms panel is now in-fiction radio chatter generated inside `World.apply` from real event payloads - hero deployments and debriefs (`read_subagent` returns report done/failed plus test counts parsed from the output), file-touch position updates naming the real path, war-council calls, order/goal/spawn intents, steering messages, raven deliveries, and agent status reports. Scrollback is event-sourced: `world.feed` rebuilds byte-identically from `events.jsonl` replay, and upsert broadcasts carry the new line (`feed` key) so live clients append without a refetch. A comms poller in the rtsd tick turns out-of-band surfaces into real events: new `.devin/mailboxes/*/inbox/msg-*.json` files append `mail.deposit` (deduped via `world.mail_seen`) and changed `status.json` notes append `agent.note`. Mailbox deposits fly a raven animation from sender to recipient on the canvas (arced path, flapping glyph, dotted trail) via a `hint` of kind `raven`. Feed UI: per-kind and per-class filter chips, click a line to select the speaking unit and jump the camera. `@unit text` in the command input resolves unit names (Knight-4) to the real agent id before posting the `message` intent for `rts-intents.py` mailbox delivery; plain text remains a goal intent.
- **rtsd orders queue** (`extensions/rtsd/world.py` + `web/js/`, #127): shift-click orders enqueue onto each hero's order queue (one `order` intent file per order, queue order preserved); queued waypoints render on the canvas as numbered flags with a dashed path from the unit, ghost (translucent) while the intent file is `pending` and solid once `rts-intents.py` surfaces it (queued/acknowledged/consumed state is overlaid at snapshot time from the real intent files). Right-click on the world canvas is a context order: snaps to quest POIs (attack with issue ref), buildings (garrison), or ground (move); with a building selected it sets that building's rally point (watchtower rally carries the target territory as alert channel). Barracks rally applies to the next spawned hero's lane server-side in `World._spawn_hero`. New `world.idle` snapshot list feeds an `idle:N` bottom-bar button that cycles and centers idle/stale heroes with no active order. Portrait panel shows the selected hero's live order queue.
- **rtsd selection + command card** (`extensions/rtsd/web/`, #126): box-drag multi-select with on-canvas rectangle overlay, shift-click toggle-add, double-click select-all-of-class-in-viewport, and Tab subgroup cycling. Control groups: Ctrl+0-9 assign, 0-9 recall, double-tap centers the camera on the group centroid; live group pips sit between portrait and card. Bottom-right command card (3-col grid) is generated per selected hero: Move/Stop/Hold/Patrol/Attack shared orders plus a per-class special (Far Seer Reveal, Knight Build, Cleric Verify, Ranger Track) and the full kit vocabulary (Cartography/Write/March/Farsight/Envoy/Parley/Camp) rendered enabled or disabled from the unit's real `kit` (agents/*.md allowed-tools). Move/Attack/Reveal arm a target mode resolved by the next map click; Attack snaps to quest POIs and embeds the issue ref in the intent. Every button posts a real `order` intent to `.devin/rts/intents/` via `POST /intent`; multi-select restricts to shared orders (move/stop) with one intent per unit; minimap right-click now orders the whole selection.
- **rtsd unit model** (`extensions/rtsd/world.py` + `web/js/`, #125): hero units now carry class identity derived from real profile data - `kit` (ability names mapped from the profile's actual allowed-tools in `agents/*.md`, `March` downgraded to `Verify` for read-only profiles, `Cartography` squire fallback) and `tier` (Footman/Knight parsed from the model column in `.devin/docs/TOOLS-MAP.md`). Hook firings become visible worker peasants that scurry between the last destination and the tool's building site (or the touched file's region capital), interpolated client-side off the server clock. Units bark: selecting shows the agent's real heartbeat `status.json` note when present, else a GDD class line; order intents show the ack line; done debriefs show the done line. Portraits show class, profile, tier, level badge, HP/mana, kit chips, and ledger loot. Failed heroes keep red outlines and fade out; low mana flashes the mana bar.
- **rtsd minimap + camera integration** (`extensions/rtsd/`, #124): every upsert broadcast now carries a world-derived `hint` (`{kind, xy}`) - file touches ping their tile (or `contested` once a second lane has touched it), spawns ping the hero's lane capital, failed debriefs ping red, `decision.created` pings gold at town-hall. The client keeps a ping queue: expanding rings on the main canvas, blinking blips on the minimap (click ping = jump camera), and SPACE cycles the last 8 alerts Warcraft-style. Minimap now draws building squares, ping blips, and per-lane territory tint (region `owner` = dominant lane). Minimap right-click issues a real `order` intent (`POST /intent`, kind whitelist extended) for the selected unit.
- **rtsd buildings** (`extensions/rtsd/world.py` + `rtsd.py` + `web/js/app.js`, #123): the 11 GDD structures are pinned to fixed map plots (affinity regions - town-hall/watchtower at `root`, library/trophy-hall at `.devin`, barracks/tavern at `agents`, runeforge at `scripts`, vault at `docs`, portal/marketplace at `extensions`, altar at `tests`; deterministic round-robin fallback when a region or plot is missing). New `GET /buildings/<id>` returns live per-building state: town-hall (goal, quest tallies, worker counts, pending decisions), barracks (hero-class table + pending spawn intents), tavern (real roster from `agents/` + `.devin/agents/` with model tiers parsed from TOOLS-MAP), library (actual `.devin/memory/` entries), watchtower (ledger pass/fail/pending + heartbeat count), runeforge (prompt/forge scripts on disk), vault (`git log --oneline -10`), portal (remote listener port/ttl/token-set), marketplace (`data/bundle-integrations.json` MCP servers), altar (failed heroes), trophy-hall (ledger evidence loot). Buildings are clickable on the map; the inspector offers real actions only - barracks class picker seeds `/spawn <profile>` intents, altar revive re-issues a spawn intent.
- **rtsd world map** (`extensions/rtsd/world.py`, #122): authoritative server-side tilemap; top-level dirs become named territories (weighted-Voronoi around deterministic ring capitals, bigger dirs = bigger territory), 2 fixed BFME-style build plots per region, per-tile fog of war (shroud/explored/lit; file-touch events light a 3x3 patch that re-dims after 180s, home territory starts explored), contested tiles when >1 lane touches a file, and POIs (quest markers from issue files, gold nodes from largest files, creep camps on untouched dirs). Layout persists to `.devin/rts/map.json` keyed by region signature and regenerates when top-level dirs change; fog demotions ride the 2s tick broadcast (`_map.fog` deltas). Renderer consumes the server map (`tile_region`/`fog`/`mark`/`pois`); client Voronoi is now demo-mode fallback only.
- **rtsd renderer v2** (`extensions/rtsd/web/`, #121): canvas-2D tilemap engine (`js/engine.js`) with camera pan/zoom (WASD, arrows, edge-pan, wheel-to-cursor, alt-drag), minimap canvas with viewport rect + click-to-jump, theme system (`js/theme.js`: battlefield + office palettes/glyphs with a sprite-sheet contract so real art drops in without code changes), and a rewired `js/app.js` consuming the v2 world snapshot (unit positions via deterministic hash placement, region Voronoi tilemap, contested-region tinting, war-council modal, `?bench` mode + live fps meter). OFFLINE DEMO mode when the daemon is unreachable. rtsd now serves any safe path under `web/` (traversal-guarded) so JS modules load; sw.js bumped to `rtsd-v2` caching the new shell.
- **rtsd world engine** (`extensions/rtsd/world.py`, #120): event-sourced v2 world model next to the v1 projection: units (heroes per GDD class table, exec-shell minions with TTL, hook-firing workers), 11 GDD buildings with activity counters, resources (gold=est tokens, lumber=context %, supply=live heroes, upkeep tiers from `data/context-budget.json`), quests (scratch-issue DAG + `/goal` main quest), map regions with reveal/contested tracking. All time-derived state computed at `snapshot(now)` so `events.jsonl` replay is byte-identical; daemon replays the log at startup; 2s tick thread broadcasts status deltas (running->idle->stale decay, minion expiry). `/snapshot` gains `v:2` + `world` key; v1 keys unchanged.
- **AgentCraft RTS v2 GDD** (`.devin/scratch/agentcraft-rts-v2/gdd.md`, #119): metaphor bible for the v3.8.0 RTS milestone; entity mapping tables covering all bundle surfaces (13+2+4 agent profiles as hero classes, 83 skills as spells in 6 schools, 35 scripts as workers, 22 extensions as allied arsenal, 28 runtime tools, 8 hook events), mechanics mapping (HP/mana/supply/gold/lumber/upkeep/fog/quests/loot/barks to real data sources), dual-mode spec (battlefield + office themes on one engine), desktop + PWA layout wireframes, programmer-art direction, per-class voice lines, and binding honesty rules.

## [3.7.0] - 2026-10-18

### Added

- **`extensions/rtsd` RTS overlay**: local state daemon projecting ephemeral `run_subagent` activity into a live RTS-style view (AgentCraft-inspired heroes/quest board/decision podium/evidence panel). Python stdlib only — HTTP + hand-rolled RFC 6455 WebSocket (snapshot + upserts), fleet/ledger/intent/decision file projections under `.devin/rts/`, canvas-2D web UI, PWA (manifest + service worker + mobile tabs), stdlib TUI client (`/status /agents /decisions /answer /feed`), `--remote MIN` LAN listener with per-session token + TTL deny-safe expiry + auth audit events.
- **RTS bridges in `scripts/`**: `rts-emit.py` (fail-open lifecycle event tap wired into the `_hookrun` chains), `rts-intents.py` (UserPromptSubmit surfacing of pending UI intents + mailbox deposits with traversal guards), `rts-decision.py` (create/wait bridge for the podium, fail-closed on timeout).
- **Heartbeat clause** in `skills/project-orchestrator/templates/delegation-contract.md`: workers write `.devin/rts/agents/<Contract ID>/status.json` per milestone; rtsd attaches heartbeat to the hero by contract-id.

### Fixed

- `extensions/computer-use` scoped channels: `_scoped_mouse`/`_scoped_type` gated on `cm.get_profile()` which resolves env + persisted profile file — an ambient `human`/`smooth` preference silently blocked every scoped dispatch (exit 2) even without `--profile`. Gate now fires only on an explicit `--profile human/smooth` flag, matching `cu_scope.resolve_channel`. Fixes `test_cu_scope_boundaries` (3) + `test_uia_has_no_key_concept`.
- `audit.py`: compile step wrote bytecode (`py_compile`) then warned about the `__pycache__` dirs it created itself — an always-firing warning. Compile now uses the `compile()` builtin (no writes); the `__pycache__` check matches its stated intent (tracked files via `git ls-files`).
- `devin-session-launcher.ps1`: session picker now lists only sessions of the current directory. `Get-DevinSessionData` discards a shared `DEVIN_N_SESSIONS_FILE` cache whose entries all belong to another `working_directory` (multi-project mode: parent cache is cwd-scoped to the parent) and refetches live; `Start-DevinSession` filters parsed sessions by `working_directory` as a safety net. 2 new Pester tests (26 total).

### Changed

- **Devin CLI alignment `3000.11.92`**: `validated_cli_version` bumped from `3000.11.1`; new `3000.11.92` capability-decision table in `DEVIN-CLI-COMPATIBILITY.md` covering `3000.11.3`→`3000.11.92`. Adopted `agent.subagent_model: swe-2-max` in `config.json` (verified empirically: `subagent_explore` ran on SWE-2 Max with the key vs parent-inherited SWE-2 High without). Documented `PreCompact`/`PostCompact` events, `/goal`, steering, `/billing`, `Alt+Enter` session model pick, `devin connect`/`cloud drs`, plugin `platforms`/`PLUGIN_ROOT`/`PLUGIN_DATA`, `sandbox.excluded.allow`, and rules/`read_config_from` hardening fixes.
- `TOOLS-MAP.md`: new commands (`/goal`, `/billing`, `Alt+Enter`, `devin connect`, `devin cloud drs`); unused hook events list now includes `PreCompact`/`PostCompact`.
- Plan: `.devin/plans/2026-10-15-adequacao-devin-cli-3000.11.92.md`.

## [3.5.0] - 2026-10-10

### Added

- **`laya-compactor` Smart Window pruning** (`extensions/laya-compactor/`): per-item transcript compaction through the resident Laya worker — `compact-item-v1` keep/truncate/drop decision profile (suggestion-only), tool_use/tool_result pair integrity, orphan-risk abort, reduction-floor fallback returning the original transcript.
- **`image-forensics` extension + skill** (`extensions/image-forensics/`): metadata inspection + PRNU residual/PCE scoring emitting `real_capture`/`synthetic`/`inconclusive` verdicts with confidence; abstains on weak residual or recompression.
- **`craft-bridge` extension** (`extensions/craft-bridge/`): uniform dispatch over the verified storytold suite (filmcraft, photocraft, vectorcraft, wordcraft, pdfcraft, gridcraft, deckcraft, cadcraft, lightcraft, soundcraft — Apache-2.0; spark MIT), cross-engine scene manifest, ops matrix, and a static `spark-view` gsplat preview page.
- **`animation-direction` pipeline**: local ASR timestamped transcript (`extensions/asr/`), motion scene manifest with mandatory approval gate (`extensions/remotion-render/plan_check.py` validates timing/overlap/read-time/budget), Remotion rendering + FFmpeg compositing.
- **`ppisp-prep` extension** (`extensions/ppisp-prep/`): photometric QC (exposure/WB/vignetting variance) emitting go/correct/recapture, wrapping NVIDIA PPISP upstream rather than reimplementing.
- **`learn-mode` skill**: opt-in learning-first collaboration adapted from `nykooi1/vibe-wise` — user owns design decisions, agent explains concepts, waits for approval before implementing, explains the diff.
- **Pocock upstream ports** (`mattpocock/skills` @49dd158): `skills/pr` (visual Summary + Evidence + Merge Danger), `skills/retro` (session retrospective feeding `continuous-improvement`), `skills/setup-pre-commit` adopted into the repo; 22 skills verified already covered, 12 skipped with reasons in `.devin/research/pocock_port_matrix.md`.
- **`computer-use` screen recording** (`extensions/computer-use/record.py`): duration-based capture to mp4/webm via streamed ffmpeg rawvideo pipe (honest exit-2 when ffmpeg is absent) or animated webp/gif via the bundled Pillow dep; every run also writes a reservoir-sampled contact-sheet PNG that agents can `read` directly. Absolute-deadline pacing reports `dropped`/`fps_actual`; `--env` records isolated guests via `backend.observe()`.
- **`project-bootstrap` rule templates** — `templates/domain-rules.md` (glob-scoped to domain paths, for business rules) and `templates/devin-config-rules.md` (scoped to `.devin/**`, teaches bundle conventions). Frontmatter format verified on CLI 3000.11.1 (`trigger: glob`, `globs:` YAML sequence).
- **`prompt_compiler.py` Golden Template refactor** — the script no longer guesses: it validates and assembles a strict spec (`effort`, `persona`, `goal`, `context`, `acceptance[]`, `in_scope[]`, `out_scope[]`, `phases[]`) drafted by the agent. Effort/persona are semantic agent decisions (language-agnostic); `--draft <file|->`/`--spec` input; `recommended_model` resolves family+effort via `bundle-models.json` deterministically. `prompt-compiler` skill rewritten around the agent-as-Prompt-Engineer flow.
- **Pester suite for the devin-N launcher** (`tests/pester/`): AST-based `Import-DevinFunctions` loads real functions from `devin-N.ps1`/`devin-session-launcher.ps1` without executing the interactive wizard; 24 tests cover fuzzy matching, quote escaping, EncodedCommand round-trip, runspace spinner (incl. `$Ctx` argument passing and nested-hashtable integrity), shared `devin ls` cache and path-suggestion TTL.
- **ADR 004** (`.devin/adr/004-tui-manual-devin-launcher.md`): records the decision to keep the manual TUI in the devin launcher (Terminal.Gui v2 API churn and pwsh gaps; ConsoleGuiTools archived).
- **`devin-N` README section** documenting the multi-instance launcher usage.

### Changed

- **Devin CLI alignment `3000.11.1`**: `validated_cli_version` bumped from `3000.10.27`; new `3000.11.x` capability-decision table in `DEVIN-CLI-COMPATIBILITY.md` covering `3000.10.31`→`3000.11.1` (recursive `.devin/rules/` discovery, `allowed-tools` write grant, subagent always-on rule inheritance, cloud commands, `otel` block, `Exec` deny precedence). All verified empirically on the installed CLI.
- `.devin/rules/README.md` moved to `.devin/docs/RULES-DIRECTORY.md` — recursive rule discovery listed it as a `manual` rule.
- Duplicate `3000.10.x capabilities` / `read_config_from` sections in `DEVIN-CLI-COMPATIBILITY.md` consolidated.
- `TOOLS-MAP.md` documents the `3000.11.1` cloud commands (`--cloud`, `/handoff`, `/pickup`, `ssh`).

### Fixed

- `install.ps1`/`install.sh` now create the `.venv` for `scrape-tools` (previously `computer-use` only) - the skill's documented interpreter path was never provisioned.
- `manifest.json` `export_hash` drift for `memory-stop.py`/`spec-consistency.py` corrected.
- **`devin-N.ps1` audit remediation** (13 confirmed defects): original branch restored in every mode incl. multi-run non-worktree children; `git status --porcelain` gate before any `worktree remove --force` with dirty-file listing and confirm; stale-worktree sweep scoped to the launching session via `worktree lock` + `.session-<pid>` markers; single-quote escaping in `Get-InstanceCommand` and uniform `-EncodedCommand`; `status --porcelain --untracked-files=no` in the pull gate covers staged changes; branch-list `-like` patterns escaped via `[WildcardPattern]`; impossible `[Nova branch]` sentinel replaces collidable `devin-new`; `$windowSize` initialized before the key-drain loop; dead `'0'` shortcut branch removed; `NaoGitRepo` template gained its `{0}` placeholder; top-level `param()` accepts `%*` args with a warning instead of silently ignoring them.
- **`Invoke-WithSpinner` now uses a `[powershell]::Create()` runspace** instead of `Start-Job`: no child pwsh process, no CliXml degradation (nested hashtables survive), `$Ctx` hashtable parameter passing replaces `$using:`; all 9 call sites updated.
- **Windows Terminal window targeting without process-diff**: new windows are spawned with `wt -w <unique-id>`, children set a `[Console]::Title` marker, hwnd is resolved via `EnumWindows` title match, and cleanup sends `WM_CLOSE` only to windows created by the session (no more `Stop-Process` on foreign `WindowsTerminal` processes).
- **UX/perf**: dependency preflight (`git`/`devin` fail-fast, `gh` warnings); single `%(upstream:track)` call for ahead/behind (per-branch `rev-list` only as fallback); spinner around serial `gh` metadata calls; 500ms TTL cache for path suggestions; `devin ls` shared with children via `DEVIN_N_SESSIONS_FILE`; `TreatControlCAsInput` in the path editor; 3s fixed sleep replaced by a bounded child-liveness probe; `Esc` on the summary screen reconfigures any project; launcher literals centralized in `$LM`.
- **Empty `catch {}` blocks** removed across both scripts (now log via `Write-Verbose`).

## [3.4.0] - 2026-09-21

### Added

- **`teach` skill** — stateful tutoring engine with ZPD-strict gating and state integrity checks.
- **`prompt compiler` + `/prompt` skill** — compile rough intent into structured prompts (`ai-tools`).
- **`diagram-tools` extension + `architecture-diagrams` skill** — PlantUML serverless renderer.
- **`media-tools` skill** — routes the visual-FX extension (grainrad parity).
- **`laya-tools` extension + `implement-laya` skill** — wrapper for the laya decision engine; bilingual EN/PT routing.
- **`spline-operator` extension + `operate-spline` skill** — Spline MCP bridge control (`ws://127.0.0.1:19692`), 36 tools, daemon keeper, `3d_load_skill` protocol.
- **`creative-engineering` skill + aesthetics KB** — 15 visual archetypes under `extensions/media-tools/knowledge_bases/aesthetics/` (CRT, receipt, depth-map, blob, datamosh, 1-bit dither, night-vision, brutalism, PC-98, wired-cyber-UI, constructivism, Y2K, PSX, risograph, vaporwave) with math/algorithm + Python + Web implementations per archetype.
- **`creative_tooooools.json`** — scraped tooooools.app catalog (16 tools) + refreshable stdlib scraper `update_tooooools_db.py`.
- **`NOTICE.md`** — third-party attributions (impeccable Apache-2.0 chain, MIT/conceptual sources, runtime deps).
- **Release automation CI** — tag-push workflow verifying manifest/CHANGELOG sync.

### Changed

- **Ecosystem alignment refactor** — routing sharpened (ask-bundle/planning/intake/execution/memory boundaries), 8 cross-skill wires added, `obsidian-workflow` split 70KB→3.3KB index + 4 deferred `modes/`, loose scripts moved to `scripts/`.
- README/LICENSE placeholders rendered for the concrete repo identity.

### Fixed

- `validate_mermaid.py` canonical path resolution (fell back to global path).
- Manifest mojibake (`â€”`/`→` double-encoding) reverted to UTF-8.
- `test_recv_collects` macOS flake — root-caused: bare `recv_from` raced the drain thread; now polls with `wait=`.

## [3.3.0] - 2026-09-20

### Added

- **`system-control` extension** — authorized OS-level control: typed contract v1, deny-wins policy with one-shot request-bound confirmations, bounded argv-only execution, persistent owned sessions (loopback JSONL daemon), resumable event streams, root-bound hash-verified file ops, native Windows (Job Objects/SCM/WMI), Linux (procfs/pidfd) and macOS (ps/kqueue) adapters, opt-in privileged broker seam (JEA/polkit templates), benchmark harness (decision: stay_python), thin skill router + USAGE docs.
- **`scan` skill** — goal-driven codebase investigation via Plan→Shard→Map→Reduce orchestration (`/scan` equivalent).
- **`ai-tools` extension** — offline-first ML tooling with abliterator PoC.
- **`brag` skill** — launch-video generation via Hyperframes.
- **`media-tools`** — grainrad.com parity: 15 effects, pipeline, presets, animated io.
- **`computer-use` terminal control** — bound read/control for WT/conhost/mintty, WinPTY PTY spawn via pywinpty, sentinel-gated exec.
- **`computer-use` browser** — bound-browser observation + full-fidelity event daemon (network, dialogs, HAR-lite).
- **`computer-use` mintty OCR** — text read via Windows.Media.Ocr (winrt).
- `computer-use` action profiles, observation contracts, dual-engine browser client.

### Changed

- **Bundle slim** — hooks 22→9 bindings, skills 83→48, AGENTS.md 18→11 KB, native Devin CLI capabilities adopted.
- Layout refactor — `docs/` dissolved into `.devin/`; plugin manifest dropped.
- README — skill groups deduplicated, counts fixed, extensions layer documented.
- `context-hygiene` — code-minification caution note (real but completion-scoped).
- Registry trimmed to SWE-2-only models.

### Fixed

- `computer-use` — phantom context menus from emergency_release; SM_SWAPBUTTON button translation; JSON stdout guard; UIA segfault.
- `devin-N` — orphan worktree dirs and reserved-name files; worktree branches preserved and re-attached; strict-mode sessions tolerated.

## [3.1.1] - 2026-09-08

### Fixed

- Resolved all remaining minor audit findings from `AUDIT_REPORT.md` in seven batches (lotes 1-7).
- `audit.py`: 32/32 checks pass, 0 errors.
- `python -m pytest -q`: 289 tests pass.
- Live installation synchronized with bundle after all changes.

## [3.1.0] - 2026-09-06

### Added

- **6 new skills** for governance, security, and cost control:
  - `ontology-validator` — validate structured knowledge and ontology integrity.
  - `task-sizer` — estimate and calibrate task scope before dispatching.
  - `secure-defaults-check` — pre-commit/pre-push security defaults verification.
  - `agent-cost-guard` — guardrails for token and parallel-tool cost.
  - `intention-capture` — capture and pin user intent before implementation.
  - `api-context-spec` — design and validate API context contracts.
- Validated task-adaptive harness recipes, durable session logging, MCP code-mode routing, model-interface preflight, bidirectional patch verification, temporal regression checks, and prompt-bloat quality gates.
- Validation coverage for Leo's orchestration contract.

### Changed

- **`leo` skill**: promoted from session-start router to the bundle's universal orchestrator, with direct routing to `wayfinder` and specialist domains, multi-skill composition, and control returning to Leo until verified completion.
- Live bundle installation and audit now validate all 32 checks with no warnings.

## [2.9.0] - 2026-09-01

### Added

- **7 Matt Pocock AI Coding workshop plans**: skills, plans and ledgers for context-workflow, grill-me, prd-to-issues, afk-loop, tdd-feedback, deep-modules, and push-pull-review.
  - `context-window-hygiene` + `scripts/context-budget.py`: added `SMART_ZONE_TOKENS` (100k), `--simulate`, and explicit `clear` over `compact` nudge.
  - `grilling`: assertive questions, one recommendation alongside every question, and `shared design concept` PRD export.
  - `planning-pipeline` and `writing-plans`: PRD as destination document, declared modules and interfaces, tracer-bullet vertical slices, and prototype/disposable asset lifecycle.
  - `afk-loop`: new skill for unattended TDD over local Markdown issues in isolated worktrees.
  - `tdd`: RED→verify RED→GREEN→verify GREEN→REFLECT→REFACTOR contract, anti-cheat reflection, and `Feedback Loops Are the Quality Ceiling`.
  - `improve-codebase-architecture`: Ousterhout deep vs shallow module heuristics and five deepening refactor moves.
  - `code-review`, `receiving-code-review`, `impeccable`: push/pull pattern distinction with Sand Castle as mental model, no Docker dependency.
- **`afk-loop` skill** — Prompt/workflow for an unattended agent that consumes local Markdown issue files under `.devin/scratch/<feature>/issues/*.md`, uses TDD in an isolated git worktree, and picks the next ready issue autonomously from a DAG of blocking relationships. Stops when no ready issues remain or on blockers; does not commit/push to `main` without human confirmation and does not require Docker.
- **`youtube-fetcher` skill** — Devin-native, stdlib-first, network-free adapter for turning a YouTube URL and provider/fixture caption/metadata JSON into raw, timestamped transcript + metadata Markdown under `.devin/notes/youtube/`. Strict host allowlist for URL validation, input/output size limits, symlink containment, duplicate preservation, and handoff to `structured-knowledge-extraction`. Conceptually adapted from JimmySadek/youtube-fetcher-to-markdown (MIT); no code copied.
- **`leo` skill** — `/leo` session-start skill that injects bundle operating rules, skill discovery, tool verification, telegraphic output, subagent/model routing, and a clear priority hierarchy. Replaces the playbook experiment.

### Changed

- **README.md**: complete rewrite explaining the full ecosystem (rules, skills, agents, tools, hooks, context, memory) and operational flows (idea → ship, AFK loop, deep modules, push/pull review). Updated counts and badges.
- **manifest.json**: version `2.8.1` → `2.9.0`, skill count `75` → `76` with `afk-loop`.
- **docs/TOOLS-MAP.md**, **docs/DEVIN-CLI-COMPATIBILITY.md**: skill count updated to `76`.

## [2.8.1] - 2026-08-29

### Fixed

- **README.md**: corrected rule count (19 → 20), script count in Mermaid (13 → 17), added `context-pressure.py` and `SessionEnd`/`memory-stop.py` rows, clarified `credentials.toml` as generated.
- **docs/TOOLS-MAP.md**: added `context-pressure.py` (PostToolUse) and `SessionEnd`/`memory-stop.py` rows; updated rule count (19 → 20); corrected claim that `SessionEnd` was unused.
- **docs/SKILL-TIERS.md**: added `youtube-fetcher` to Data tier.
- **CONTRIBUTING.md**: corrected hook exit code (1 → 2) for block.
- **SECURITY.md**: updated `post-compaction-reminder.py` → `constraint-pinning.py` and `refine` skill → `primeagent-reference` Refine mode.
- **hooks.v1.json** (root + `.devin/`): synchronized with `config.json` hooks; uses `python scripts/*.py` paths and lists all 8 lifecycle events.
- **manifest.json**: synchronized `impeccable` purpose with `SKILL.md` description.

### Changed

- **12 skills**: removed YAML quote wrapping from `description` frontmatter so `validate-skill-format.py` scores 100 (`a11y-audit`, `api-design`, `cost-optimization`, `database`, `deploy`, `docker`, `e2e-testing`, `i18n`, `impeccable`, `legacy-refactor`, `performance`, `security-audit`).

## [2.8.0] - 2026-08-28

### Added

- **11 new skills for modern agent coverage**:
  - `deploy` — deploy, release, rollback, and smoke-test workflows.
  - `security-audit` — defensive SAST, dependency CVE, and secret-leak scanning.
  - `performance` — profiling, benchmarking, and bottleneck optimization.
  - `a11y-audit` — WCAG, keyboard, screen-reader, and contrast checks.
  - `api-design` — REST/OpenAPI design and contract testing.
  - `database` — schema design, migrations, query review, and indexing.
  - `e2e-testing` — Playwright/Selenium/Cypress critical-journey tests.
  - `cost-optimization` — token, cache, model routing, and MCP cost reduction.
  - `docker` — container build, run, compose, and image scanning.
  - `i18n` — internationalization, pluralization, LTR/RTL, and formatting.
  - `legacy-refactor` — strangler-fig, seams, and incremental modernization.

### Changed

- **manifest.json**: version 2.7.0 → 2.8.0, 71 skill entries.
- **README.md**: skills badge 60 → 71, version badge 2.7.0 → 2.8.0, summary and Mermaid diagram updated.
- **docs/TOOLS-MAP.md**: skills count 60 → 71.
- **docs/SKILL-TIERS.md**: new "Infra / Quality / Release" tier with the 11 new skills.

## [2.7.0] - 2026-08-27

### Added

- **project-setup skill**: FASE 0 deep research + 10-step setup loop for bootstrapping `.devin/` configuration in projects.
- **Cross-skill wiring**: `context7`, `deep-mode`, and `research` wired into 35+ skills where library docs, unfamiliar code, or primary-source investigation is needed.
- **Engineering skill integration in `project-setup`**: Passo 4.5 now explicitly runs `grilling`, `domain-modeling`, `project-memory`, `triage`, and `planning-pipeline` to populate the project's knowledge base before work begins.

### Changed

- **Agent-produced artifact paths**: `docs/specs/` → `.devin/specs/`, `docs/plans/` → `.devin/plans/`, `docs/obsidian/` → `.devin/obsidian/` (with legacy fallback) in `grilling`, `writing-plans`, `dispatching-parallel-agents`, `code-review`, and `obsidian-workflow`.
- **manifest.json**, **README.md**, **audit.py**: version bumped to 2.7.0.

## [2.6.0] - 2026-08-27

### Added

- **project-memory skill**: captures project-specific knowledge as plain-text
  Markdown notes under `.devin/memory/`, with user approval, cue-anchored
  frontmatter, and Obsidian-compatible wikilinks.
- **Memory helper scripts**: `capture-memory.py`, `query-memory.py`, and
  `audit-memory.py` for note lifecycle and link/orphan validation.
- **Cue-anchored memory hooks** (arXiv:2607.20972, arXiv:2608.15008):
  - `memory-retrieval.py` on `UserPromptSubmit` (keyword cues)
  - `memory-post-edit.py` on `PostToolUse` `write`/`edit` (path cues)
  - `memory-post-exec.py` on `PostToolUse` `exec` (symbol/keyword cues)
  - `memory-stop.py` on `Stop` (session review nudge)
- **Rule 21**: "Don't think through uncertainty — research or ask".

### Changed

- `manifest.json`, `README.md`, `docs/TOOLS-MAP.md`, `audit.py`: updated
  script counts to 17, hook script counts to 15.
- `docs/MODEL-GUIDE.md`: added arXiv:2607.20972 and arXiv:2608.15008 to the
  source verification table.

## [2.5.3] - 2026-08-26

### Fixed

- `audit.py`: removed hardcoded version and badge checks, using manifest and runtime counts.

## [2.5.2] - 2026-08-26

### Added (iter 8.5 — continuous improvement + mermaid + cleanup)

- **continuous-improvement skill**: FASE 0 deep research + 10-step self-improvement
  loop based on Constitutional AI, RISE, Six-Step Reframing, and held-out
  validation. Enforces the full directive and prevents skipped steps.
- **PermissionRequest and SessionEnd hook events**: added to `config.json` and
  `hooks.v1.json` to match all 8 Devin CLI lifecycle events. Audit check [30]
  prevents future drift.
- **Mermaid architecture diagram in README.md**: replaced ASCII diagram with
  a `flowchart TB` Mermaid block, validated by `validate-mermaid.py`.

### Changed

- **README.md and SKILL-TIERS.md**: skill count 49 → 50, added
  `continuous-improvement` to skill inventory and tier list.
- **scripts/validate-skill-format.py**: default scan now includes bundle root
  `skills/` as the source of truth, plus project `.devin/skills/` and global
  installs.
- **TOOLS-MAP.md and audit.py**: updated skill count checks 49 → 50.

### Removed

- **ci-logs.zip**, `__pycache__/`, `.pytest_cache/`: cleaned project junk.

### Added (iter 8.1 — CLI replicas of cloud-only features)

- **deep-mode skill**: replicates Ask Devin's Deep Mode (`!deep` in
  Slack/Teams) for the CLI. Multi-pass agentic search (broad sweep ->
  deep read -> cross-file synthesis -> architecture map) with
  mandatory file:line citations. Sources: docs.devin.ai/work-with-devin/ask-devin,
  docs.devin.ai/integrations/slack, cognition.ai/blog/new-self-serve-plans-for-devin.
- **data-analyst skill**: replicates Devin cloud's Data Analyst Agent
  (DANA) for the CLI. SQL-first exploration via MCP data sources,
  schema discovery + caching, query formulation, analysis, and
  matplotlib/seaborn-style visualizations. Read-only by design.
  Sources: docs.devin.ai/work-with-devin/data-analyst,
  docs.devin.ai/use-cases/gallery/dana-slack-data-analyst,
  docs.devin.ai/release-notes/2025.
- **playbook skill**: replicates Devin cloud's Playbook feature for
  the CLI. Structured prompt template (Procedure, Specifications,
  Advice, Forbidden Actions, Required from User), local library
  (`.devin/playbooks/*.devin.md`), macro approximation, create-from-
  session workflow. Sources: docs.devin.ai/product-guides/creating-playbooks,
  docs.devin.ai/product-guides/using-playbooks,
  docs.devin.ai/work-with-devin/advanced-capabilities.
- **obsidian-workflow skill enhanced**: 4 new steps (17-20) complementing
  existing rigor to match DeepWiki cloud. Effort levels (low/medium/high)
  in `wiki-config.json` controlling depth. Deep Research pass (Step 18)
  — architecture critique, anti-patterns, optimization opportunities,
  senior-reviewer-level analysis. TechDebt page (Step 19, `11-TechDebt.md`)
  — cited issues, numbered (AP-001/OPT-001), categorized. Conversational
  Q&A (Step 20) — `deep-mode` skill integration for multi-pass search
  over wiki with double citations (wiki + source). Backward compatible:
  absent `effort` defaults to `high` (existing behavior). Sources:
  docs.devin.ai/work-with-devin/deepwiki, cognition.com/blog/deepwiki,
  marktechpost.com/2025/04/27/devin-ai-introduces-deepwiki.
- **obsidian-workflow validators**: 2 new scripts + 1 updated.
  `validate_wiki_content.py` (9 content rigor checks: source path:line
  format, min 5 sources per page, Sources: footers, overview links to
  all root pages, function ## Links, source columns in tables, TechDebt
  content, architecture critique, effort valid). `find_orphan_pages.py`
  (graph orphan detection — referenced in checklist but did not exist).
  `validate_wiki_structure.py` updated with 3 new checks (effort valid,
  TechDebt exists, arch critique section). SKILL.md updated with
  validation scripts table and content rigor checklist item.
- **manifest.json scripts list**: added `scripts` array (was missing —
  `script_count: 12` but no list). 12 .py + 1 .js entry. audit.py check
  [9b] validates consistency (count match, disk existence). Check count
  23 -> 24.
- **Counts updated**: 46 -> 49 skills in README.md (summary, diagram,
  tree, badge), TOOLS-MAP.md, SKILL-TIERS.md (3 new entries in
  Pesquisa/Data/Planejamento sections), manifest.json (3 entries +
  skill_count 46->49), audit.py (checks [9] and [18]).

### Fixed (iter 8.3 — self-improvement loop: hook FP/FN fixes + audit hardening)

- **destructive-gate.py commit message parsing**: strip_commit_message()
  now extracts only the command portion before `-m`/`-F`/`--message`,
  preventing the gate from blocking descriptive commit messages that
  mention gate names. (ref-030)
- **check-ai-signature.py self-detection skip**: write/edit to
  check-ai-signature.py or validate-skill-format.py was blocked because
  the detector code contains the signature patterns. Added self-detection
  skip. Also fixed exec handler to extract `-m` message. (ref-031)
- **silent-error-review.py false positives**: bare exception-name regex
  matched past-tense fix descriptions ("the fix resolved the KeyError").
  Fixed: require colon after exception name or Traceback/raise prefix.
  (ref-032)
- **validate-refinement-evidence.py tool-call patterns**: flagged
  ref-002 as PHANTOM despite evidence containing write/edit/exec. Added
  write|edit|exec to REPRODUCIBLE_PATTERNS regex. (ref-033)
- **check-ai-signature.py allowed contexts**: "AI-assisted tooling"
  blocked descriptive documentation. Added ALLOWED_CONTEXTS denylist for
  AI-assisted tooling/development/review and AI-generated content/images.
  (ref-034)
- **behavioral-nudge.py syntax error**: muted print left multi-line dict
  literal active, causing SyntaxError. Restored print call. (ref-035)
- **constraint-pinning.py empty main()**: main() was `pass` with no
  `__main__` guard — hook never wrote markers or re-injected constraints.
  Restored full implementation. (ref-036)
- **check-push-green.py empty main()**: main() was `pass` — hook never
  blocked any git push. Restored full implementation with stdin parse,
  PreToolUse/exec/git-push checks, test runner, held-out gap. (ref-037)
- **check-push-green.py gap check investigation**: empty tests/validation/
  makes gap check dead code (val_passed=False never blocks). No code
  change — test infrastructure gap. (ref-038, investigated)
- **.gitignore .pytest_cache**: added .pytest_cache/ to .gitignore
  (was not ignored despite internal .gitignore). (ref-039)
- **audit.py __main__ guard check**: added check [2b] to detect hook
  scripts missing `if __name__ == "__main__"` guard. Would have caught
  iters 4-6 bugs. Updated check count 24->25. (ref-040)
- **check-ai-signature.py multi-context strip**: check_text with two
  allowed contexts returned True (blocked) because loop stripped one
  context at a time. Fixed: strip ALL contexts cumulatively, then check.
  (ref-041)
- **destructive-gate.py SQL false positives**: SQL_DESTRUCTIVE regex
  matched echo/grep/cat commands containing keywords. Added SQL_CLIENTS
  regex — gate now requires both SQL_DESTRUCTIVE and SQL_CLIENTS. (ref-042)
- **destructive-gate.py WinRM false negatives**: Remove-Item with path
  before flags, or no target, was not blocked. Added WIN_RM_RE_PATH_FIRST
  and WIN_RM_RE_NOTARGET patterns. (ref-043)
- **validate-skill-format.py AI signature false positives**: flagged
  descriptive contexts inconsistently with check-ai-signature.py. Added
  AI_ALLOWED_CONTEXTS tuple matching check-ai-signature.py. (ref-044)
- **destructive-gate.py force-with-lease**: GIT_FORCE_PUSH blocked
  `--force-with-lease` (safe alternative). Removed from alternation,
  added negative lookahead. (ref-045)
- **check-ai-signature.py .bak file filtering**: substring match
  filtered .bak variants as self-files. Replaced with regex matching
  exact filename at end of git diff path. (ref-046)
- **silent-error-review.py warning+error lines**: signal_lines stripped
  entire lines containing warning keywords, causing false negatives when
  a line had both warning AND error indicators. Fixed: only strip if
  noise without error. (ref-047)

### Fixed (iter 8.4 — continuous improvement directive: data integrity + gap check activation)

- **refinements.log.jsonl duplicate IDs**: 48 entries had 30 unique IDs
  (16 duplicates) — rollback-by-ID was ambiguous. Renumbered all entries
  sequentially ref-001 to ref-048. (ref-048, LOOP 1)
- **audit.py refinement ID uniqueness check**: added check [25] to
  detect duplicate IDs in refinements.log.jsonl. Prevents recurrence.
  Check count 25->26. (ref-048, LOOP 2)
- **tests/validation/ populated**: 4 infrastructure smoke tests added
  (audit passes, skill-format passes, refinement-evidence valid).
  Activates check-push-green.py gap check (was dead code with empty
  validation/). Rule 16 reward hacking guard now operational. (ref-048,
  LOOP 3)
- **manifest.json stale purposes**: diagnosing-bugs and primeagent-
  reference had outdated purpose fields vs SKILL.md descriptions. Synced
  to current frontmatter. (ref-048, LOOP 4)
- **audit.py manifest/SKILL.md sync check**: added check [26] to detect
  stale manifest purposes vs SKILL.md descriptions. Prevents recurrence.
  Check count 26->27. (ref-048, LOOP 4)

### Fixed (iter 8.2 — self-improvement loop: stale refs + model info + encoding)

- **dispatching-parallel-agents model info**: skill table said
  implementer/debugger use "parent" model, but `agents/implementer.md`
  and `agents/debugger.md` pin `model: swe-1-7`. Updated table and
  Model Selection section to reflect SWE-1.7 (free, 262K) as default
  for implementers. Source: cognition.com/blog/swe-1-7.
- **subagent-router stale model info**: 5 agent profiles had stale
  SWE-1.6/$ cost info. Updated all to SWE-1.7 (262K, FREE), added
  `subagent_explore` PAID warning, fixed 4 references to pruned
  `subagent-driven-development` skill.
- **Agent profiles AgentCARD**: added bottleneck role awareness to
  all 5 profiles (architect=planner for debugging, reviewer=reviewer
  for doc analysis, researcher=executor for research). Source:
  arXiv:2606.20629.
- **MODEL-GUIDE.md benchmarks**: added SWE-1.7 vs GLM-5.2 comparison
  table (FrontierCode 42.3% vs 24.5%, Terminal-Bench 81.5% vs 81.0%,
  SWE-Bench 77.8% vs 74.5%) and 10-task routing matrix. Source:
  cognition.com/blog/swe-1-7.
- **render-graphs.js stale ref**: example used `subagent-driven-
  development` (deleted in iter 8.0). Replaced with `obsidian-
  workflow` (only skill with Mermaid diagrams).
- **obsidian-workflow validators rename**: 3 scripts had stale
  `obsidian-project-docs` in docstrings/argparse (skill renamed to
  obsidian-workflow in iter 8.0). Fixed to "Obsidian codebase wiki".
- **primeagent-reference adaptation status**: SKILL.md said "9/9
  features adapted" but 2 were pruned (session-checkpoint, heartbeat).
  Fixed to "7/9 adapted, 2 pruned" — consistent with README bullets.
- **README adaptation status**: 2 stale "9/9 features" references
  (lines 262, 288) contradicted own bullet list ("2 pruned") and
  primeagent-reference skill. Fixed to "7/9 adapted (2 pruned)".
- **install.ps1/export.ps1 encoding**: PowerShell 5.x read UTF-8
  files without BOM as Windows-1252, causing parser errors on
  em-dashes. Added UTF-8 BOM (EF BB BF) to both .ps1 files.
- **CHANGELOG missing iter 8.2**: Unreleased section had iter 8.1
  and 8.0 but was missing 9 refinements (ref-011 to ref-019) from
  subsequent sessions. Added iter 8.2 Fixed section.
- **TOOLS-MAP missing hook entry**: hooks table missing
  `behavioral-nudge.py` (UserPromptSubmit) — added in commit bfef22b
  but not documented. Added row.
- **README hooks table missing 2 entries**: missing `validate-
  mermaid.py` (PreToolUse write/edit) and `behavioral-nudge.py`
  (UserPromptSubmit). Added 2 rows to match hooks.v1.json.
- **SKILL-TIERS stale token counts**: 3 skills updated after
  2026-08-20 measurement had stale counts: primeagent-reference
  7876→10091 (28% off), obsidian-workflow 14798→17435 (18% off),
  dispatching-parallel-agents 9710→10065 (3.7% off). Updated counts
  + measurement date to 2026-08-22.
- **manifest.json vague purpose fields**: planning-pipeline and
  obsidian-workflow both had the identical string "merged planning/
  obsidian pipeline" as their purpose — two different skills with the
  same description. Fixed to their real SKILL.md frontmatter
  descriptions (spec/tickets/questionnaire; Obsidian 4 modes).
- **SKILL-TIERS 4 more stale token counts**: writing-plans 1746→1704,
  executing-plans 551→535, wayfinder 2936→2938, playbook 2400→1496
  (60% off — playbook SKILL.md was rewritten shorter in iter 8.1).
  Updated 4 counts in the planning/decision domain rows.
- **Planning flow unification (grilling vs ask-matt)**: grilling
  SKILL.md mandated writing-plans as its ONLY terminal state ("Do NOT
  invoke any other implementation skill"), but ask-matt SKILL.md
  routed grilling → planning-pipeline (Spec) → planning-pipeline
  (Tickets) → implement without mentioning writing-plans. Unified:
  grilling now offers both exits (planning-pipeline/Tickets canonical,
  writing-plans alternative for single-session detailed plans);
  ask-matt now mentions writing-plans → executing-plans as alternative
  to Tickets → implement; writing-plans now documents its input
  sources and positions itself vs Tickets mode. Updated 3 token
  counts (grilling 2511→2656, writing-plans 1704→1785, ask-matt
  2893→3037). Synced 3 skills to live.

### Fixed (iter 8.0 — doc count consistency + hook events accuracy + legacy cleanup)

- **Deleted 3 legacy skill dirs**: obsidian-project-docs (consolidado em
  obsidian-workflow), subagent-driven-development (consolidado em
  dispatching-parallel-agents), systematic-debugging (consolidado em
  diagnosing-bugs). Reduzido 49→46 skills. README "Merged from" table
  mantida como histórico de consolidação.
- **TOOLS-MAP.md stale counts**: "46 skills" → "49 skills" → "46 skills"
  (legacy cleanup), "11 scripts" → "12 scripts", "6 eventos" → "8 eventos",
  "25 ativas + 2 modo-dependentes" → "26 ativas + 2 modo-dependentes"
  (28 total), "19/27" → "19/28", "8 excluídas" → "9 excluídas".
  Verified against disk and docs.devin.ai/cli/extensibility/hooks/overview
  (8 events). Bundle uses 6 of 8; PermissionRequest and SessionEnd
  documented as available but unused.
- **README.md stale counts**: diagram "46 skills" → "49 skills" →
  "46 skills", "6 events" → "8 events"; hooks header "6 events" →
  "8 events"; install summary "6 hook events" → "8 hook events";
  badge skills-49 → skills-46.
- **SKILL-TIERS.md**: typo double period `PAGO)..` → `PAGO).`.
- **manifest.json**: removed 3 legacy skill entries, skill_count 49→46,
  tool_count 27→28.
- **audit.py check [24]**: new check verifies TOOLS-MAP.md and README.md
  counts match disk reality (skills, scripts, hook events, tools, excluded).
  Prevents future stale-count regressions.
- **validate-refinement-evidence.py**: added PowerShell cmdlet patterns
  (Select-String, Get-ChildItem, etc.) to REPRODUCIBLE_PATTERNS — fixes
  false phantom-guardrail flag on Windows-documented refinements.
- **Sources**: docs.devin.ai/cli/extensibility/hooks/overview (8 events),
  docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks (event details),
  Get-ChildItem skills/scripts (disk counts).

### Changed (iter 7.3 — política de modelos CONDICIONAL)

- **Política alterada de FREE-ONLY para CONDICIONAL**: modelos pagos agora
  são permitidos para subagents **quando o parent está em modelo pago**
  (usuário fez `/model opus`, `/model sonnet`, etc.). Quando o parent está
  em modelo FREE (default `glm-5-2`), subagents DEVEM ser FREE.
- **Caso 1 (Parent FREE)**: FREE-ONLY mantido. `subagent_explore` (SWE-1.6
  pago), `swe` alias (SWE-1.7 Lightning pago) e todos os modelos pagos
  proibidos para subagents.
- **Caso 2 (Parent PAGO)**: `subagent_explore` (SWE-1.6, $0.5/$2.5) é
  permitido — mais barato que o parent. `subagent_general` herda o modelo
  pago do parent. Custom profiles com `model: swe-1-7` continuam FREE
  (preferir quando possível).
- **Arquivos atualizados**: `AGENTS.md` Rule 20, `MODEL-GUIDE.md` (novo
  protocolo condicional com 2 casos), `TOOLS-MAP.md`, e 5 skills
  (`dispatching-parallel-agents`, `primeagent-reference`, `context-folding`,
  `obsidian-workflow`, `self-extend`) — todas as annotations "NUNCA usar
  `subagent_explore`" agora dizem "NUNCA usar quando parent é FREE".

### Fixed (iter 7.1 — `subagent_explore` PAGO bug)

- **BUG CRÍTICO DE CUSTO (iter 7.1)**: o profile built-in `subagent_explore`
  roda no **default subagent model (SWE-1.6, PAGO $0.5/$2.5 MTok)**. Não há
  override local — apenas enterprise settings podem mudar isso. O system
  prompt do Devin CLI recomenda `subagent_explore` para read-only exploration,
  então qualquer dispatch desse profile incorre em custo.
- **Solução**: adicionada regra em `AGENTS.md` (Rule 20) e `MODEL-GUIDE.md`
  proibindo `subagent_explore`. Direcionado para o profile customizado
  `researcher` (`agents/researcher.md`, pin `model: swe-1-7`, gratuito, 262K)
  que tem as mesmas capacidades read-only.
- **Skills corrigidas**: 5 skills (`dispatching-parallel-agents`,
  `primeagent-reference`, `context-folding`, `obsidian-workflow`,
  `self-extend`) tinham 10 referências ativas a `subagent_explore` como
  recomendação de uso. Todas substituídas por `researcher` com annotation
  "NOT `subagent_explore` — PAID SWE-1.6".
- **Fonte**: docs.devin.ai/cli/subagents — "subagent_explore: The default
  subagent model — a fast, cheap model (SWE-1.6 by default)".

### Changed (iter 7.0 — FREE-ONLY policy enforcement)

- **Protocolo de escalada pago REMOVIDO**: `MODEL-GUIDE.md` tinha um
  protocolo de 6 níveis que recomendava GLM-5.2 Max ($0.7/$2.2),
  DeepSeek V4 Flash ($0.14/$0.28), Opus ($5/$25) e GPT-5.4 ($2.5/$15)
  como fallbacks. Substituído por protocolo FREE-ONLY: se GLM-5.2 High +
  SWE-1.7 fan-out falharem, parar e reportar ao usuário — nunca escalar
  para pago.
- **AGENTS.md Rule 20**: "Só usar como fallback após 3+ tentativas
  documentadas" → "🚫 NUNCA usar modelos pagos. Se falharem, parar e
  reportar ao usuário."
- **Skills corrigidas**: `dispatching-parallel-agents`, `primeagent-reference`
  e `self-extend` recomendavam `sonnet` (pago, $2/$10) e `SWE-1.6` (pago,
  $0.5/$2.5) para subagent profiles. Corrigido para `SWE-1.7` (gratuito,
  262K) em todas as referências.
- **TOOLS-MAP.md**: tabela de aliases agora marca todos os modelos pagos
  com "**PAGO** — não usar" e adiciona `swe-1-7-medium` (gratuito) como
  alternativa.
- **Regra ABSOLUTA adicionada**: "NUNCA usar modelos pagos. Os modelos
  gratuitos (GLM-5.2 High + SWE-1.7) cobrem 100% dos casos."

## [2.5.1] - 2026-08-21

GLM-5.2 High + SWE-1.7 optimization. 9 iterations, all changes verified against
primary sources (`devin models list`, docs.devin.ai, cognition.com, z.ai).

### Fixed (CRÍTICO — agents/ usando modelo PAGO em vez de gratuito)

- **BUG CRÍTICO DE CUSTO**: todos os 5 agents/ (architect, debugger,
  implementer, researcher, reviewer) usavam `model: swe` que é alias para
  `swe-1.7-lightning` (PAGO, $2.5/$12.5 MTok, 202K context). O modelo
  gratuito é `swe-1-7` (SWE-1.7 Max, 262K context, Free). Corrigido: todos
  os agents/ agora usam `model: swe-1-7`. Descoberto via `devin models list`.
- **Impacto**: cada subagent dispatch estava custando ~$2.5/$12.5 MTok
  desnecessariamente. O modelo gratuito tem MAIS contexto (262K vs 202K).
  Correção salva dinheiro E dá mais headroom de contexto.
- **SWE-1.7 context window** — corrigido de "200K/256K ambíguo" para
  definitivamente 262K. Verificado contra `devin models list` e fontes
  primárias (cognition.com/blog/swe-1-7, HuggingFace Kimi-K2.7-Code card).
- **BOM em agent files**: 4 de 5 agent files tinham BOM (EF BB BF) no início.
  BOM em YAML frontmatter pode impedir o parser de reconhecer `---`, fazendo
  `model: swe-1-7` ser ignorado — agent cairia para SWE-1.6 (PAGO). BOM
  removido. `install.ps1`/`install.sh` agora stripam BOM automaticamente.
- **`validate-mermaid.py` fail-closed → fail-open**: quando Node.js/mermaid
  indisponível, o hook bloqueava TODOS writes com mermaid. Corrigido para
  fail-open (consistente com os demais hooks do bundle).
- **`constraint-pinning.py` marker not session-scoped**: marker usava filename
  fixo sem session_id — sessions paralelas sobrescreviam markers um do outro.
  Corrigido: filename inclui session_id. SessionStart limpa markers stale.
- **`constraint-pinning.py` dead code removido**: `inject("PostCompaction")`
  era chamado mas PostCompaction não suporta `additionalContext` (per docs).
  Chamada removida; mecanismo correto é marker-based re-injection no
  UserPromptSubmit.
- **`refine-review-prompt.py` skill ref fixa**: referência a skill `refine`
  inexistente → `primeagent-reference` Refine mode.
- **`mermaid-parse-check.js` hardcoded paths**: paths machine-specific
  (`C:\Users\Fingertech\scoop\...`) → portable lookup (require.resolve,
  npm root -g, Linux paths, Windows fallback).
- **MODEL-GUIDE.md dados de GLM-4.6 atribuídos a GLM-5.2**: max output
  128K → 131,072. Custos $1.4/$4.4 removidos (GLM-5.2 High é gratuito).
- **24 broken skill references**: `subagent-driven-development`→`dispatching-parallel-agents`,
  `systematic-debugging`→`diagnosing-bugs`, `to-spec`→`planning-pipeline`,
  `find-skills`→`tool-and-skill-discovery`, `grill-with-docs`→`grilling`,
  `wiki-audit/audit.py`→`obsidian-workflow/scripts/audit.py` (11 skills).
- **`hooks.v1.json` `%APPDATA%` → `{{APPDATA}}`**: sintaxe Devin-native.
- **`audit.py` live_base stale**: `C:\Users\leand\...` → auto-detect
  (WSL/Linux/Windows).

### Added

- **Rule 20: Model-aware operation** — GLM-5.2 High (200K, gratuito, thinking,
  tool-use nativo) é primário; SWE-1.7 (262K, gratuito, self-compaction,
  1000 TPS) é subagent via `model: swe-1-7`. Non-pinned. Ver MODEL-GUIDE.md.
- **MODEL-GUIDE.md** — specs verificadas (GLM-5.2 + SWE-1.7), linhagem,
  estratégia de model pin, context budget, protocolo de escalada (6 níveis),
  reasoning effort guide, subagent vs compaction decision table.
- **TOOLS-MAP.md** — mapeamento completo do runtime: 27 ferramentas, 7
  subagentes, 6 eventos de hook, 11 scripts, configs, modos, modelos.
- **validate-tool-args.py**: 6 validators adicionados (`ask_user_question`,
  `browser_preview`, `close_browser_preview`, `todo_write`, `apply_patch`,
  `exit_plan_mode`). Matcher depois otimizado 28→19 tools (removidos 9 no-ops).
- **install.ps1/install.sh**: `strip_bom` (remove BOM de agent files) e
  `dedup_agents_md` (remove duplicatas lowercase em FS case-sensitive).
- **context-budget.py**: reporta share de 200K (GLM-5.2) e 262K (SWE-1.7).
- **SKILL-TIERS.md**: custos de tokens medidos (bytes÷4), modelos alvo,
  anti-patterns expandidos.

### Changed

- **`silent-error-review.py` scope narrowed (noise reduction)** — PostToolUse
  matcher de `""` (all tools) → `^(exec|mcp_call_tool)$`. ALTK scope
  (arXiv:2603.15473): "best suited for verbose/tabular responses". Regexes
  tightened (error requer colon, test-failures requer count > 0). Max 1
  finding por call. Addresses PR #1 review comment on hook noise.
- **`validate-tool-args.py` matcher narrowed (latency reduction)** — 28→19
  tools. Removidos 9 tools com checks triviais/no-ops. Zero perda de
  validação real. Saves ~9 Python process spawns per session.
- **SKILL-TIERS.md reescrito** — custos medidos em vez de estimativas.
- **README.md** — 8 inconsistências corrigidas (rules 18→19, skills 47→46,
  tools 15→28→19, events 4→6, scripts 4→11).

### Verified

- `devin models list` — primary source (swe-1-7 = Free/262K, swe alias = Lightning/$2.5/202K)
- docs.devin.ai/cli/subagents — default router = SWE-1.6
- docs.devin.ai/cli/models — short names resolve to latest
- cognition.com/blog/swe-1-7 — SWE-1.7 specs (Kimi K2.7 base, self-compaction, 1000 TPS)
- HuggingFace Kimi-K2.7-Code card — Context Length: 256K (262,144 tokens)
- z.ai/blog/glm-5.2 — GLM-5.2 specs (gratuito, 200K, 131K max output)

## [2.4.0] - 2026-08-18

### Added

- **Rule 19: Never read secrets or sensitive env vars** — new pinned
  governance rule. Never `read`, `cat`, `echo`, `print`, or output API keys,
  tokens, passwords, private keys, or `.env` secret values. Use them (pass to
  commands, reference by variable name) but never display their contents. If
  a key/env var is missing, empty, or doesn't behave as expected, say so
  without exposing the value. Pinned into `constraint-pinning.py` (survives
  compaction). Pinned set is now Rules 2, 5, 7, 12-19.
- **`context-window-hygiene` skill** — clear vs compact, MCP paranoia,
  lost-in-the-middle (arXiv:2307.03172).
- **`mcp-context-audit` skill + `mcp-context-audit.py` script** — estimates
  per-server tool-definition token cost; flags >15 tools/server and >5%
  window share.
- **`context-budget.py` script** — SessionStart hook that reports AGENTS.md
  token cost to stderr. Transparency without context bloat.
- **`SKILL-TIERS.md`** — skills categorized by domain with token costs
  (~1700 tok vs ~2094 for `skill list`).

### Pruned (orphaned/duplicated — no consumers)

- **`graphify` skill** — 9659 tok (a mais cara), sem `graphify-out/` em
  nenhum projeto ativo. CLI `graphify.exe` instalado mas sem uso pelo agente.
  Rule 6 (graphify trigger) removida do AGENTS.md. 47 → 46 skills.
- **`post-compaction-reminder.py`** — órfão (0 hooks), duplicado por
  `constraint-pinning.py` (superior: dinâmico, 9 regras pinned, em 3 hooks).
- **MCP `arxiv`** — 0 consumidores (grep por `mcp__arxiv` em skills/ vazio).
  `observability-quality` cita `arxiv.org/abs/...` (URL de paper), não o MCP.
- **`heartbeat` skill** — emulação PrimeAgent que não fita Devin CLI
  (single-process, sem daemon). OS scheduler + script launches nova sessão
  não funciona no runtime atual.
- **`session-checkpoint` skill** — mesma razão. Emulação daemon-backed
  reattach não funciona em single-process.

### Consolidated (overlaps merged with mode selectors — content preserved)

- **`grilling`** ← `grill-me` + `grill-with-docs` (wrappers de 5-6 linhas
  que só redirecionavam). Modos: Default, Stateless, With-docs.
- **`diagnosing-bugs`** ← `systematic-debugging`. Pipeline unificado de
  6 fases. Arquivos de suporte (`root-cause-tracing.md`,
  `defense-in-depth.md`, `condition-based-waiting.md`) movidos para
  `diagnosing-bugs/`.
- **`tool-and-skill-discovery`** ← `find-skills`. Discovery + install/evaluate
  em uma skill.
- **`dispatching-parallel-agents`** ← `subagent-driven-development`. Dispatch
  geral + modo plan execution. Scripts e prompts de suporte movidos.
- **`planning-pipeline`** ← `to-spec` + `to-tickets` + `to-questionnaire`.
  Modos: Spec, Tickets, Questionnaire.
- **`obsidian-workflow`** ← `obsidian-project-docs` + `vault-organizer` +
  `wiki-audit` + `memory-bridge`. Modos: Build, Reorganize, Audit,
  Cross-session. Templates, references e scripts movidos.
- **`primeagent-reference`** ← `a2a-mailbox` + `refine` + `subagent-router`.
  Modos: Reference Card, A2A Messaging, Refine, Subagent Router.

### Fixed

- **`hooks.v1.json` leftover no global** — arquivo user-level com paths
  `%APPDATA%` literais não expandidos causava `validate-mermaid.py` e outros
  hooks a falhar com `[Errno 2] No such file or directory`. O Devin CLI lia
  o arquivo (não deveria — user-level hooks vão em `config.json` desde
  v2.2.1). Arquivo deletado do global.
- **`audit.py` rule detector false positive** — `6. **` era detectado como
  substring de `16. **`, inflando a contagem de regras. Ancorado com `\n`
  prefix para matching start-of-line.

### Changed

- **62 → 46 skills** (-16, 26% redução). Mesma cobertura funcional, menos
  namespace bloat, menos manutenção.
- **17 → 18 rules** (Rule 6 removida, Rule 19 adicionada). Regras pinned:
  2, 5, 7, 12-19.
- **12 → 11 scripts** (remoção de `post-compaction-reminder.py`).
- **2 → 1 MCP** (remoção de `arxiv`).
- **AGENTS.md enxugado**: 25KB → 18.5KB (~6263 → ~4614 tok). Non-pinned rules
  comprimidas para one-liners referenciando skills.
- **`constraint-pinning.py`** — Rule 19 adicionada ao `PINNED_CONSTRAINTS`
  e `key_phrases`.
- **`agents/researcher.md`** — removida referência a `graphify` (query mode).
- **`obsidian-workflow/SKILL.md`** — 9 referências a `graphify` substituídas
  por `ls`/`tree`/`git ls-files`.
- **Version 2.3.0 → 2.4.0** (manifest). README badges, counts, skill tables
  atualizados. SKILL-TIERS.md reescrito com 46 skills.
- **`audit.py`** — contagens e listas de sync atualizadas para 46 skills,
  11 scripts, 18 rules, v2.4.0.

## [2.3.0] - 2026-08-18

### Added (context window management — from "Context Windows Explained for Coding Agents", Matt Pocock)

- **Rule 18: Keep the context window lean** — new pinned governance rule.
  Context window = input + output tokens (hard-capped); lost-in-the-middle
  deprioritizes the middle of long chats; default to `clear` over `compact`;
  keep rules files small; audit MCP servers before adding; bigger window ≠
  better retrieval. Pinned into `constraint-pinning.py` (survives compaction).
- **`context-window-hygiene` skill** — practical user-facing hygiene: clear vs
  compact, lean rules, MCP paranoia, subagent context savings, model selection
  heuristic. Backed by lost-in-the-middle (arXiv:2307.03172).
- **`mcp-context-audit` skill + `mcp-context-audit.py` script** — estimates
  per-server tool-definition token cost; flags >15 tools/server (selection
  accuracy degrades, arXiv:2606.30317) and >5% window share. `--config` static
  mode + `--tools` measured mode (fed from `mcp_list_tools`).
- **`context-budget.py` script** — SessionStart hook that reports the AGENTS.md
  token cost to stderr. Transparency analogous to Claude Code's `/context`,
  without adding context bloat (stderr only). Warns at ≥10% of a 200k window.

### Changed

- **AGENTS.md enxugado: 25KB → 18KB (~6263 → ~4546 tokens).** Non-pinned rules
  compressed to terse one-liners referencing skills; pinned rules (2, 5, 7,
  12-18) keep full detail. Reduces lost-in-the-middle tax on every session.
- **`constraint-pinning.py`** — Rule 18 added to `PINNED_CONSTRAINTS` and
  `key_phrases`; pinned set is now Rules 2, 5, 7, 12-18.
- **`config.json` / `hooks.v1.json`** — `context-budget.py` added to
  SessionStart alongside `constraint-pinning.py`.
- **Version 2.2.5 → 2.3.0** (manifest). README badges, counts, rules table,
  hooks table, and skill listing updated (62 skills, 18 rules, 12 scripts).
- **`audit.py`** — hardcoded expectations updated to the true counts
  (62 skills, 18 rules, 12 scripts, version 2.3.0); new skills added to the
  live-vs-bundle sync list.
- **`SKILL-TIERS.md`** — novo arquivo de discovery rápido. Skills
  categorizadas por domínio de uso (núcleo, docs, programação, debug, git,
  jira, obsidian, planejamento, pesquisa, meta, setup, artefatos de pesquisa,
  outros) com custo em tokens e quando invocar. ~1500 tok vs ~2094 tok de
  `skill list`. Referenciado em AGENTS.md Rule 4 e README.

## [2.2.3] - 2026-08-15

### Fixed (coverage gaps vs official tool list)

- **validate-tool-args.py missing 7 tools** — the official docs list
  `get_output`, `write_to_process`, `kill_shell`, `skill`, `request_scope`,
  `mcp_list_tools`, `mcp_list_servers` as available tool names. The validator
  had no checks for them, so calls with missing required args (e.g. `get_output`
  without `shell_id`) passed silently. Added validators for all 7.
- **validate-tool-args.py early-exit on empty tool_input** — `if not tool_input`
  treated `{}` as falsy and exited before validating. Tools like `get_output`
  and `kill_shell` that require args but received `{}` were allowed. Fixed:
  only skip on non-dict input, not empty dict.
- **researcher.md model: swe** — `swe` is not a documented model value.
  Changed to `sonnet` (documented in the subagent profiles example).
- **researcher.md BOM** — UTF-8 BOM (EF BB BF) removed.
- **Matcher expanded** — config.json and hooks.v1.json matchers now include
  the 7 newly-validated tool names.

## [2.2.2] - 2026-08-15

### Fixed (critical — hook commands used %APPDATA% which is not expanded)

- **`%APPDATA%` is not expanded in hook commands** — the hook shell does not run
  through cmd.exe, so `%APPDATA%` stays literal and the path becomes
  `D:\...\%APPDATA%\devin\scripts\...` (No such file or directory). All hooks failed
  to find their scripts. Live config.json now uses absolute paths
  (`C:/Users/leand/AppData/Roaming/devin/scripts/...`).
- **Bundle uses `{{APPDATA}}` placeholder** — portable across users/machines.
  `install.ps1` expands `{{APPDATA}}` to `$env:APPDATA` (forward slashes) during
  merge. `export.ps1` normalizes absolute APPDATA paths back to `{{APPDATA}}`.
- **audit.py** — regex now matches `scripts/` and `scripts\`; warns on `%APPDATA%`;
  normalizes `{{APPDATA}}` vs absolute path before comparing live vs bundle hooks.

## [2.2.1] - 2026-08-15

### Fixed (critical — hooks at wrong location)

- **hooks.v1.json is not a valid user-level location** — the docs
  ([Where Hooks Live](https://docs.devin.ai/cli/extensibility/hooks/overview#where-hooks-live))
  list `hooks.v1.json` only under project-level (`.devin/hooks.v1.json`). At user-level,
  hooks must be in `config.json` under the `"hooks"` key. The standalone `hooks.v1.json`
  at `%APPDATA%\devin\` was silently ignored. Hooks are now merged into `config.json`.
- **mcp_config.json BOM** — file had UTF-8 BOM (EF BB BF), removed.
- **mcp_config.json undocumented fields** — `arxiv` server had `transport: stdio` (not
  documented for stdio servers; transport is inferred from `command`) and a `note` field
  (not in the schema). Both removed.
- **refine-review-prompt.py exit code** — printed `{"decision":"block"}` but exited with
  0 instead of 2. Changed to exit 2 for consistency with all other blocking scripts.
- **export.ps1 / install.ps1 / audit.py** — updated to read/write hooks from `config.json`
  instead of standalone `hooks.v1.json`. The bundle keeps `hooks.v1.json` for project-level
  use (`.devin/hooks.v1.json`).

## [2.2.0] - 2026-08-15

### Fixed (critical — hooks were non-functional)

Verified every hook script against the official Devin CLI hook contract
([Lifecycle Hooks](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks),
[Overview](https://docs.devin.ai/cli/extensibility/hooks/overview)). Nine defects
made the hooks silently no-op:

- **`tool` → `tool_name`** — every script read `data["tool"]`, which does not exist in the payload. All tool checks always saw an empty string and never fired. Affected all 9 scripts.
- **Exit code 1 → 2** — blocking requires exit code **2**; exit 1 is "error, logged but doesn't block". Every block was being ignored. Affected 7 scripts.
- **`tool_response` schema** — real shape is `{success, output, error}`, not `{exit_code, stderr, results, content, matches}`. `silent-error-review.py` never detected anything.
- **`Stop` payload** — has `stop_hook_active`, not `event`. `check-ai-signature.py` and `refine-review-prompt.py` exited early on every Stop event.
- **`PostCompaction` cannot inject context** — only `UserPromptSubmit`, `SessionStart`, and `PostToolUse` support `hookSpecificOutput.additionalContext`. Constraint Pinning was rewritten as a three-event flow: detect at PostCompaction → marker → re-inject at UserPromptSubmit.
- **Unanchored matchers** — `"read"` also matched `notebook_read`, `read_subagent`, and `mcp_read_resource`; `"write"` also matched `write_to_process`. Matchers are now anchored regexes (`^exec$`, `^(write|edit)$`, explicit tool list).
- **Missing `decision`/`reason` output** — blocks now return `{"decision":"block","reason":...}` so the agent receives an actionable explanation instead of a bare non-zero exit.
- **`hook_event_name` dispatch** — multi-event scripts now dispatch on `hook_event_name` instead of guessing from absent fields.
- **Stop-hook loop risk** — `refine-review-prompt.py` now honours `stop_hook_active` and consumes its marker before blocking, so it can block at most once.

Also fixed: `DEVIN_PROJECT_DIR` is now used for the project root; `rm -rf` target
parsing rewritten (whitelist by path prefix, handles multiple targets and shell
operators); `validate-skill-format.py` no longer false-positives on the prose word
"task (" and now joins folded multi-line YAML frontmatter values.

### Removed

- **`post-compaction-reminder.py`** — printed a reminder to stdout on `PostCompaction`, an event that cannot inject context, so it never reached the agent. Superseded by `constraint-pinning.py`.

### Added
- **Rule 14:** Constraint Pinning survives compaction — governance constraints re-injected after compaction with hash verification (arXiv:2606.22528v2)
- **Rule 15:** Refinement evidence must be reproducible — phantom guardrails occur in 25% of self-improvement runs (arXiv:2607.13083)
- **Rule 16:** Self-improvement loops produce 47-74% illusory gains — validate with held-out tests (ICLR 2026 Workshop)
- **5 new scripts:**
  - `destructive-gate.py` — PreToolUse hook blocking `rm -rf /`, `git push --force` without `--dry-run`, `DROP TABLE`, `chmod -R 777 /` (arXiv:2607.07405, KDD 2026 Workshop)
  - `silent-error-review.py` — PostToolUse hook flagging `success:true` responses that carry error indicators, empty reads, or no-match searches (ALTK, ACM CAIS 2026)
  - `constraint-pinning.py` — three-event Constraint Pinning across PostCompaction / UserPromptSubmit / SessionStart (arXiv:2606.22528v2)
  - `validate-tool-args.py` — PreToolUse hook validating paths, regexes, URLs, and subagent profiles for 15 tools (ALTK SPARC, ACM CAIS 2026)
  - `validate-refinement-evidence.py` — manual-run script checking `refinements.log.jsonl` for phantom guardrails
  - `validate-skill-format.py` — manual-run script scoring SKILL.md against the 8-point quality checklist
- **arxiv MCP server** — Domain-Specific Adapter pattern, 14 tools, for Rule 12 enforcement (arXiv:2606.30317 evaluation)
- **3 new hook events wired** — `PostToolUse` (silent error detection), `UserPromptSubmit` and `SessionStart` (Constraint Pinning re-injection and marker cleanup)
- **Held-out gap check** in `check-push-green.py` — blocks push when validation passes but held-out fails
- **MCP evaluation criteria** in Rule 13 — 5 patterns, 4 anti-patterns, tool count < 10-15 (arXiv:2606.30317)
- **Dynamic Subagent Construction (AOrchestra 4-tuple)** documented in `self-extend` skill (ICML 2026, arXiv:2602.03786)
- **Role Bottleneck Awareness (AgentCARD)** in `subagent-router` skill (arXiv:2606.20629)
- **Phantom Guardrail Check** in `refine` skill Step 1 (arXiv:2607.13083)
- **Elaborate Stagnation Check** in `refine` skill outcome tracking (arXiv:2607.25152)
- **Interaction-Centric Failure Dimension** in `diagnosing-bugs` skill (arXiv:2607.28802)
- **VRR-Stop stopping criterion** in `systematic-debugging` skill (arXiv:2607.17641)

### Changed
- `hooks.v1.json` — 3 to 6 events, 4 to 7 hook scripts, anchored regex matchers
- `AGENTS.md` — expanded from 13 to 16 rules, added MCP evaluation criteria to Rule 13
- `check-push-green.py` — added held-out gap measurement (Rule 16), skips `--dry-run` pushes
- `check-ai-signature.py` — Stop event now scans unstaged changes in addition to staged
- `README.md` — updated counts (16 rules, 6 events, 7 hook scripts, 2 manual-run scripts), added rules 14-16, documented the hook contract
- `audit.py` — expectations updated to 16 rules / 9 scripts / version 2.2.0

## [2.1.0] - 2026-08-15

### Added
- **Rule 13:** Devin CLI is not a security sandbox — guardrails for untrusted code, MCP servers, skills, and reward hacking
- **7 new skills** from verified PrimeAgent/RLM research:
  - `context-folding` — RLM-style context folding (arXiv:2512.24601), depth=1 only
  - `refine` — Continual Harness self-improvement (arXiv:2605.09998) with auto-trigger, outcome tracking, reward hacking guard
  - `autonomous-gates` — bounded autonomous mode with quality gates
  - `a2a-mailbox` — file-based A2A messaging emulating PrimeAgent's `agent_message.send()`
  - `session-checkpoint` — structured checkpoint for cross-session continuation
  - `heartbeat` — OS-scheduled re-entry via Task Scheduler/cron
  - `primeagent-reference` — reference card of 9/9 adapted features with verified sources
- **`refine-review-prompt.py`** Stop hook for auto-refinement prompts
- **LICENSE** (MIT)
- **SECURITY.md** — security policy documenting guardrails and limitations
- **CONTRIBUTING.md** — contribution guide with skill/rule/hook standards
- **CHANGELOG.md** — this file
- **.github/workflows/ci.yml** — CI: validate JSON + Python + skill frontmatter on push/PR
- **.github/ISSUE_TEMPLATE/** — bug report and feature request templates
- **.github/PULL_REQUEST_TEMPLATE.md** — PR template
- **Rule 12 clause:** "Don't trust ANY subagent return without verification" — subagent returns are leads, not answers

### Changed
- `post-compaction-reminder.py` — now re-primes rules 7-10 (verification, Rule 12, Rule 13) in addition to 1-6
- `check-push-green.py` — added .NET detection (`.sln`/`.csproj`) + `dotnet test`
- `manifest.json` — synced with disk (was missing 9 skills)
- `README.md` — major rewrite: badges, quick start, prerequisites, troubleshooting, bilingual sections, updated counts
- `.gitignore` — expanded with common temp files

### Fixed
- `post-compaction-reminder.py` was missing rules 10-13 — after compaction, verification and security rules were not re-primed
- `check-push-green.py` did not detect .NET projects — C#/F#/VB.NET pushes were not blocked by failing tests
- `manifest.json` was missing 9 skills (jira, observability-quality, context-folding, refine, autonomous-gates, primeagent-reference, a2a-mailbox, session-checkpoint, heartbeat)
- `refine` skill was not autonomous — added auto-trigger (Stop hook + `.refine-pending` marker), outcome tracking (`refinements.log.jsonl`), rollback by ID

### PrimeAgent/RLM Adaptation Status
- **9/9 features adapted** (3 direct, 3 emulated, 1 partial, 2 guardrails)
- All claims verified against primary sources (arXiv, GitHub, PrimeAgent blog, ARC Prize leaderboard)
- 2 errors in source video corrected (GPT-V → GPT-5, Opus-V → Opus 5)

## [2.0.0] - 2026-08-13

### Added
- Rule 12: Maximum precision, zero tolerance for partial verification
- Rule 11: Never fail from failures
- Cross-platform installer (Windows + Linux/macOS)
- Auto-discover skills export (not limited to manifest)
- Secrets masking in export (config.json, mcp_config.json, credentials.toml)
- 5 subagent profiles (architect, debugger, implementer, researcher, reviewer)
- Hooks: check-ai-signature, check-push-green, post-compaction-reminder
- 45 skills (unified, adapted, and original)

### Changed
- Rules framed as negative constraints (evidence: arXiv:2604.11088)
- Post-compaction re-priming (evidence: arXiv:2605.10039 — 5.6% compliance decay per step)

## [1.0.0] - 2026-08-11

### Added
- Initial bundle: AGENTS.md (10 rules), skills, config, hooks, scripts
- Windows installer (install.ps1) and exporter (export.ps1)
