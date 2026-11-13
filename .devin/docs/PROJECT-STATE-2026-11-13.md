# Project State - 2026-11-13 (improvement-loop snapshot)

## Position

Main `42743f8`+ (origin synced). Bundle `v3.21.0` released and tagged.
Live install: 1449/1449 files Current, 0 drift. audit.py 50/50, 0
errors, 0 warnings. pytest 2589 pass / 7 skip.

## Batch-9 research (3 links deep-dived)

- caleb.is-a.dev repo list -> `.devin/research/resource-index.md`: 14
  high-signal repos mapped to bundle areas (#589, PR #592).
- Meshy image-to-3D API verified real (task lifecycle, Bearer key,
  base64 input); verdict BACKLOG - ai3d-gen stays local-first, hosted
  path only on explicit opt-in (#590).
- Astryx agent-facing CLI contract evaluated; covered patterns
  documented, gaps shipped as the envelope-v2 arc (#591 -> #593-#609).

## Envelope v2 (issue #593 + #604, 11 waves, PRs #594-#609)

Every agent-facing JSON CLI now emits `api_version: 2` +
`meta.answered_by {bundle, wrapper}`; bundle version resolves from the
nearest ancestor `manifest.json` with a `"name"` marker, honest `""`
on malformed/missing manifests. 86 deterministic subprocess probes in
`tests/test_envelope_contract_v2.py`.

Waves: 11 dedicated wrappers -> scrape-tools/asr + `code-graph
--envelope` opt-in -> full computer-use surface (23 files) ->
skill-referenced extension CLIs (24) -> remaining extensions +
graph-query -> laya-tools sub-tools + scripts tools -> final
dict-JSON emitters (roadmap-board, ship-metrics, rules-coverage).
Out-of-scope documented: hook-protocol payloads, bare arrays,
system-control SCHEMA_VERSION, busybar.

Probe/CI-found crash fixes (8): metadata.py, plan_check.py
(argv IndexError), look_ledger.py, ns.py resume, fit_calibration.py,
capture_eval.py (unreadable input), api-bridge doctor + models
(silent death on missing devin via `_devin_path` sys.exit to stderr).

## Also landed

- `install-ledger` MANAGED_FILES now tracks root artifacts (audit.py,
  manifest.json, mcp_config.json) - caught live manifest stale at
  3.20.0 post-release (the provenance field paid for itself
  immediately).
- `stock-footage search --detail brief|compact|full` (#598).
- manifest.json `skills\a` mojibake un-mangled (arena original_path);
  byte-scan: 0 remaining control chars.
- 5 reels-2/reels-4 transcripts losslessly recoded from double-encoded
  cp1252 mojibake.
- `pbdump.py` argv guard (last unguarded sys.argv[1] in
  extensions/scripts).
- Reference-integrity sweep: 575 path refs across skills/.devin docs,
  0 real dead links; hooks.v1.json 14/14 resolve.

## Process notes

- Stacked-PR trap learned: `--delete-branch` on a base branch
  auto-closes the next PR in the stack (#606 closed unmerged,
  content carried by #607). Retarget BEFORE deleting bases.
- `open()` default encoding on Windows is cp1252: writing manifest.json
  via plain json.dump corrupted em-dashes; always `encoding='utf-8'` +
  `ensure_ascii=False`.
- The pre-push gate runs scoped pytest - resolve merge conflicts in
  separate steps, never chain resolve+push.

## Open

- #431 - laya shadow->assist decision (awaits user).
- #565 - intentional tracking items (deny-by-default residues).
