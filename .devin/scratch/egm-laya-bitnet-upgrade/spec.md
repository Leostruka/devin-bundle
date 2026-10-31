# egm-laya-bitnet-upgrade (spec)

## Runtime rollout: active implementation scope

The user now requests implementation of the previously pending capabilities.
This section supersedes documentation-only boundaries for this new task;
the delivery and self-improvement sections below record earlier phases.

- JEV: executable 25% assistance threshold, lexical manifest picker,
  rg-to-Laya batches of at most 20 and top-K, seven-question review gate,
  explicit doc-to-test contracts and safe DOM recommendation picker.
- OpenUI: actual local parser, bounded streaming state and escaped HTML
  renderer with native controls. Preserve existing JSON/external CLI paths.
- Camera: actual low-poly scene, camera track, MP4, per-frame metadata and
  verified media-tools handoff. No external Katana/Seedance submission.
- Local inference: executable BitNet adapter, backend-specific offloading
  configuration/execution and frozen held-out batch runner, including an
  optional TPU entry point usable on supported hardware.
- Isolated pinned dependencies, runtime binaries and model downloads are
  approved. No global installs, live configuration overwrite, cloud jobs,
  proprietary uploads, EGM repository installation, commits or pushes.
- Critical guard policy, stdlib-only scripts, deterministic fallback,
  closed suggestion/abstain semantics and calibration gates stay intact.

Acceptance: regression RED/GREEN evidence, controller rechecks, independent
Goldfish review, full and held-out tests, audit and exporter dry-run. Real
CLI/render/inference smoke evidence must be distinguished from mocked unit
tests. Hardware-specific execution must not be claimed without that hardware.
The token target is a measured benchmark, not a promised universal saving.

## Delivery status (original documentation phase - historical)

Historical record: documentation delivered first; the accepted ingestion
scope was documentation and specs, not implementing these proposed engines.
The active rollout scope above supersedes this boundary for the runtime
lanes below. This file retains user stories; they are not claims of
end-to-end external-service acceptance.

## Runtime acceptance (current)

| Capability | Current evidence | Remaining gate |
|---|---|---|
| Goldfish | Protocol + profiles; fresh reviewer exercised in self-improvement | Repeated task-level quality evaluation |
| drift-audit | Existing `skills/drift-report/SKILL.md`; workflow alias only | No separate reporter is required |
| Laya JEV rollout | `scripts/compact-gate.py` (eval_floor 0.25), `scripts/skill-picker.py` in the `user-prompt.py` chain, `laya-tools/explore.py` (batches of 20, top-K), `review_gate.py`, `doc_coverage.py`, `computer-use/cu_dom_picker.py` (mode override can only lower the calibrated effective mode; exact-match before daemon). Doc contracts shipped: `.devin/validation-contracts.json` + `tests/validation/test_jev_runtime_contracts.py` (11 tests) | `profile.json` mode is `off` - calibration (G5) and `shadow`/`assist` adoption pending; `review-risk-v1` not yet in `profiles` |
| OpenUI | `craft-bridge/ui_dsl.py` v1 parser/StreamParser/render_html (non-modal `<dialog open>` + `method="dialog"`, `role="progressbar"` bar); measured ratio 0.5654 vs minified JSON (`benchmark-results.json`); browser smoke relocated to `devin-cache/openui-browser` (pytest 1 pass) | ~50% token target NOT met on fixture; no `ops_map.json` entry; no external renderer verified; not a universal savings claim |
| Katana | `blender-operator/camera_blocking.py` + presets; `media-tools/playblast_ingest.py`; controller smoke `.devin/scratch/egm-smoke-controller/shot.*` (h264 480x270, 24fps, 24 frames + camera.json + handoff.json); earlier `.devin/scratch/egm-smoke-l4/` kept as historical evidence | No external Katana/Seedance submission (descriptor `external_call: false`) |
| BitNet / TPU | `ai-tools/bitnet_adapter.py` (UTF-8 capture, `_clean_output` framing strip, native-only binary on Windows), `offload_plan.py`, `heldout_batch.py` (verified bytes bound at load), `vllm_tpu_runner.py` (`run_tpu_batch` via `LLM.generate`; `serve` forced 127.0.0.1). Real native run: `devin-cache/egm-runtime-install/cli_proof2.json` `ok:true` but semantically wrong completion. Runtime caches outside repo under `devin-cache/`; old `scratch/egm-runtime-install/smoke.json` timeout is historical | Model quality NOT established; CPU latency unmeasured; held-out quality eval (G5); no TPU hardware tested; no offload kernel measured; no cloud jobs submitted |

Contract tests validate boundaries only. They cannot establish inference
quality, latency, token savings or MP4 output; smoke artifacts above are
the runtime evidence that exists.

## Self-improvement correction scope

The original delivery above was documentation-only. This follow-up also
repairs a reproduced audit defect; it does not implement the runtime backlog.

- `audit.py`: share newline-tolerant manifest comparison for agent/script
  text files. Accept raw, LF and CRLF representations; still report changed
  content. This is inventory consistency, not executable integrity attestation.
- `manifest.json`: restore chief-of-staff's committed LF digest. Exporters
  remain unchanged; comparisons accept either LF or CRLF exported digests.
- `tests/validation/test_egm_upgrade_contract.py`: nine documentation cases
  plus sixteen hash cases (agent/script, checkout LF/CRLF, export LF/CRLF,
  unchanged/changed content). Fixtures do not modify production files.
- Existing guards, policy, packages, live installation and held-out sources
  are out of scope. Changes remain local, without commit or push.

Acceptance: documentation contracts pass, all sixteen hash cases preserve
content-change detection, existing held-out and full suites pass, audit
reports zero errors/warnings, and exporter dry-run succeeds. No inference
quality, video output, latency or token-savings claim follows from these tests.

## Intent

Land four workstreams from the 2026-10-31 source ingestion: (a) EGM Goldfish
Review protocol plus `drift-audit`, (b) JEV operational patterns in Laya,
(c) OpenUI Lang style line-based DSL for streamed HUDs and interactive
grilling forms in `craft-bridge`/`.devin/rts/`, (d) Higgsfield Katana style
camera-blocking export for `blender-operator`/`media-tools`. Doc-level
updates to `LAYA_MASTER_ARCHITECTURE.md` §12 and `MODEL-GUIDE.md` are already
landed this session; this spec covers the remaining build work.

## Problem Statement

- Spec review today embeds the implementer's rationale in context, anchoring
  the reviewer. No `zoom-out` first check exists as an enforced step.
- No `drift-audit` command exists; doc-vs-disk divergences are found by hand.
- The proposed line-based DSL targets half the tokens of equivalent JSON.
  This is an acceptance target, not a measured saving.
- Video pipelines (Katana / Seedance) need controlled camera blocking;
  `blender-operator` has no low-poly blocking or playblast export path.

## Solution

Vertical tickets, each gated. Protocol and DSL design land first; anything
touching `extensions/` keeps the stdlib-only / fail-closed invariants and
ships behind flags.

## User Stories

1. As the orchestrator, I want Goldfish review dispatches, so that spec reviews are unanchored and cheaper.
2. As the maintainer, I want `drift-audit` output, so that stale docs surface as a table instead of silent rot.
3. As the agent, I want a line-based UI DSL, so that streamed HUDs/forms cost half the tokens of nested JSON.
4. As the media pipeline, I want camera-blocking playblasts with metadata, so that Katana-style video gen gets precise camera intent.
5. As the Laya operator, I want the JEV patterns implemented per §12, so that compaction, skill picking, explore, and review triage stay cheap.

## Estimated size (lines)

~450-650 across 6 tickets; each ticket <= ~200.

## Input / Output boundaries

- Goldfish dispatch: brief file (`spec.md` path + diff command) -> reviewer
  subagent -> verdict block per `.devin/sdd/goldfish-review.md`.
- `drift-audit`: use `skills/drift-report/SKILL.md` and its
  `.devin/<YYYY-MM-DD>_DRIFT_REPORT.md` artifact; read-only.
- OpenUI Lang: `.devin/rts/openui-lang.md` grammar + `craft-bridge` renderer
  adapter prerequisite: verify a real receiving renderer before proposing
  an `ops_map.json` entry. No DSL operation is shipped.
- Katana blocking: `blender-operator` low-poly scene + camera track ->
  playblast MP4 + `camera.json` metadata -> `media-tools` handoff.

## Implementation Decisions

- Living: `.devin/sdd/goldfish-review.md` (landed), `drift-audit` spec +
  reporter script proposal, `.devin/rts/openui-lang.md`, craft-bridge DSL op,
  blender blocking helper, media-tools handoff note.
- Disposable: drift reports under `.devin/notes/`, playblast outputs in temp.
- No new deps for `scripts/`; craft-bridge/blender extensions may declare
  their own pinned deps as today.

## Testing Decisions

Current doc contracts: `tests/validation/test_egm_upgrade_contract.py`
checks Goldfish handoff, drift-report reuse, canonical camera references,
balanced DSL examples, runtime/proposal distinction and fail-closed guards.

Runtime gates status: parser/renderer round-trip and the fixture token
benchmark are done (ratio 0.5654; the ~50% target was not met on the
fixture); the real playblast + camera metadata smoke exists
(`.devin/scratch/egm-smoke-controller/`). Still pending: Laya
calibration/latency (G5), held-out decision-quality evaluation, and any
hardware-specific benchmark. Passing documentation tests does not satisfy
the pending gates.

## Out of Scope

EGM repo installation, BitNet integration into hooks or daemon, TPU job
automation, any credentialed scraping, changes to `hooks.v1.json` matchers.
