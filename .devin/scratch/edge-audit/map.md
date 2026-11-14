# Edge audit - issue map

Total: 68 issues | P1: 6 | P2: 36 | P3: 26

| # | Issue | Category | Severity | Status |
|---|-------|----------|----------|--------|
| 01 | [install.sh installs unmasked credentials.toml without --restore-secrets](issues/01-install-sh-credentials-without-flag.md) | code-optimization | P1 | open |
| 02 | [install.sh config merge discards every local key except org_id](issues/02-install-sh-config-merge-drops-local-keys.md) | code-optimization | P2 | open |
| 03 | [sha256sum absent on stock macOS makes hashing silently no-op](issues/03-sha256sum-missing-on-macos.md) | code-optimization | P1 | open |
| 04 | [strip_bom uses GNU sed -i syntax, fails on macOS (set -e aborts)](issues/04-sed-i-gnu-syntax-breaks-macos.md) | code-optimization | P2 | open |
| 05 | [--backup silently does nothing for directories (skills, docs, extensions)](issues/05-backup-silent-noop-for-directories.md) | code-optimization | P2 | open |
| 06 | [export.sh masks only org_id; ps1 masks all secret-named keys and credentialed URLs](issues/06-export-sh-config-masking-weaker-than-ps1.md) | code-optimization | P2 | open |
| 07 | [export.sh without python3 exports secrets unmasked or aborts mid-run](issues/07-export-sh-python3-missing-unmasked-copy.md) | code-optimization | P1 | open |
| 08 | [export.ps1 Get-FolderHash hashes contents only; renames go undetected](issues/08-export-ps1-folder-hash-ignores-filenames.md) | code-optimization | P2 | open |
| 09 | [export.sh validation py_compile writes __pycache__ into bundle scripts/](issues/09-export-sh-pycompile-dirties-scripts.md) | optimization | P3 | open |
| 10 | [audit.py duplicate-rule detection is dead code](issues/10-audit-py-duplicate-rule-check-dead.md) | code-optimization | P3 | open |
| 11 | [export.sh validation calls `python` while masking required `python3`](issues/11-export-sh-python-vs-python3-inconsistency.md) | code-optimization | P3 | open |
| 12 | [masked mcp_config.json: ps1 -Force installs it, sh never does](issues/12-install-sh-mcp-masked-force-drift.md) | code-optimization | P3 | open |
| 16 | [Git Bash install renders hook commands with POSIX paths Windows python cannot open](issues/16-git-bash-hooks-posix-paths.md) | user-experience | P2 | open |
| 17 | [Two identical mcp_config.json files with ambiguous authority](issues/17-duplicate-mcp-config.md) | organization | P3 | open |
| 18 | [install.sh sed fallback merge loses devin.org_id](issues/18-sed-merge-loses-devin-org-id.md) | user-experience | P2 | open |
| 19 | [--restore-secrets flag promises more than it does](issues/19-restore-secrets-flag-misleading.md) | user-experience | P3 | open |
| 20 | [__pycache__ trees inside skills/ and scripts/ are shipped to install targets](issues/20-pycache-shipped-in-skills.md) | organization | P3 | open |
| 21 | [SKILL-TIERS.md ships unrendered {{BUNDLE_*_MODEL}} placeholders](issues/21-skill-tiers-unrendered-placeholders.md) | organization | P3 | open |
| 22 | [README is Portuguese-only and quick-start defaults to -Force](issues/22-readme-pt-only-force-default.md) | user-experience | P3 | open |
| 23 | [Near-duplicate skills create ambiguous discovery](issues/23-overlapping-skill-pairs.md) | organization | P3 | open |
| 24 | [.devin/scratch contains 163 tracked files including one-off probes and gate scripts](issues/24-scratch-tracked-clutter.md) | organization | P3 | open |
| 25 | [Root directory mixes distribution artifacts with personal launchers and debris](issues/25-root-stray-artifacts.md) | organization | P3 | open |
| 26 | [Hooks assume `python` on PATH; POSIX installs with only python3 break or lock the agent](issues/26-hooks-assume-python-on-path.md) | user-experience | P2 | open |
| 27 | [install.ps1 swallows render-user-hooks.py output, leaving a reason-free warning](issues/27-render-hooks-output-swallowed.md) | user-experience | P3 | open |
| 31 | [Hook event coverage gap: PreCompact/PostCompact unwired, dual PostCompaction contract](issues/31-hook-event-coverage-gap.md) | devin-cli-limitations | P3 | open |
| 32 | [Subagent model routing via bundle-models.json is convention, not enforced](issues/32-subagent-model-routing-registry.md) | devin-cli-limitations | P3 | open |
| 33 | [No native skill versioning: manifest export_hash is the only version signal](issues/33-no-skill-versioning.md) | devin-cli-limitations | P3 | open |
| 34 | [Per-skill/agent tool sandboxing limited to validate-tool-args plus allowed-tools frontmatter](issues/34-tool-sandboxing-limits.md) | devin-cli-limitations | P2 | open |
| 35 | [AGENTS.md case-variant duplication: install-time dedup only, CLI bug unfixed](issues/35-agents-md-case-dup.md) | devin-cli-limitations | P3 | open |
| 36 | [Export secret masking is regex-based: org_id and token patterns can leak](issues/36-export-masking-regex.md) | devin-cli-limitations | P2 | open |
| 37 | [Windows/POSIX dual-script parity burden across install and export](issues/37-dual-script-parity.md) | adaptability | P2 | open |
| 38 | [CLI version drift: adequacao plans are manual, no runtime version check](issues/38-cli-version-drift-no-runtime-check.md) | adaptability | P2 | open |
| 39 | [Live-vs-bundle drift detection is hash-pair only, ledger planned but absent](issues/39-live-bundle-drift-partial.md) | adaptability | P2 | open |
| 40 | [Partial installs: warn-and-continue leaves degraded installs with no record or rollback](issues/40-partial-install-no-rollback.md) | adaptability | P2 | open |
| 41 | [Missing extension deps: venvs built at install, never re-validated at use time](issues/41-extension-deps-no-runtime-check.md) | adaptability | P2 | open |
| 42 | [Python version spread (3.11/3.14) with unversioned `python` hook invocations and fail_closed guards](issues/42-python-version-spread-unversioned-hook-calls.md) | adaptability | P1 | open |
| 46 | [TOOLS-MAP hook table describes pre-consolidation wiring](issues/46-tools-map-hook-table-stale.md) | documentation | P2 | open |
| 47 | [DEVIN-CLI-COMPATIBILITY verified versions lag validated CLI](issues/47-cli-compat-verified-version-lag.md) | documentation | P3 | open |
| 48 | [_hookrun aggregation layer has no documentation](issues/48-hookrun-aggregator-undocumented.md) | documentation | P2 | open |
| 49 | [Memory hook pipeline (retrieval/scoring/storage) undocumented](issues/49-memory-pipeline-undocumented.md) | documentation | P2 | open |
| 50 | [No diagram of hook event flow and decision merge](issues/50-no-hook-event-flow-diagram.md) | diagrams | P2 | open |
| 51 | [Composite pipelines (thermos dual-lane, de-slop sequence) lack diagrams](issues/51-composite-skill-pipelines-no-diagrams.md) | diagrams | P3 | open |
| 52 | [No ADR for hooks.v1.json as single source over config.json.hooks](issues/52-adr-hooks-v1-single-source.md) | adr | P2 | open |
| 53 | [No ADR for hook consolidation into aggregator scripts](issues/53-adr-hook-consolidation.md) | adr | P2 | open |
| 54 | [No ADR for .devin/scratch file-based issue tracker over GitHub Issues](issues/54-adr-scratch-issue-tracker.md) | adr | P3 | open |
| 55 | [No ADR for vendored/external skill adoption policy](issues/55-adr-vendored-skill-policy.md) | adr | P3 | open |
| 56 | [Release/tag procedure exists only in release.yml, not documented](issues/56-release-process-undocumented.md) | versioning | P2 | open |
| 57 | [CHANGELOG vs EXECUTION_CHANGELOG duality; PR refs unresolvable locally](issues/57-changelog-duality-and-pr-linkage.md) | traceability | P3 | open |
| 61 | [check-push-green fails open on timeout, error, and missing framework](issues/61-check-push-green-fails-open.md) | applied-rules | P1 | open |
| 62 | [git push detection is a brittle substring match](issues/62-git-push-matcher-bypass.md) | applied-rules | P2 | open |
| 63 | [Partially masked credentials.toml passes the secrets gate](issues/63-masked-secrets-partial-check.md) | applied-rules | P2 | open |
| 64 | [AI-signature Stop scan never sees untracked files](issues/64-ai-signature-misses-untracked.md) | applied-rules | P2 | open |
| 65 | [architecture-gate exec escape is a comment-level bypass](issues/65-arch-gate-comment-escape.md) | applied-rules | P2 | open |
| 66 | [Rules 25, 27, and the Rule 15 log have no enforcement mechanism](issues/66-convention-only-rules.md) | applied-rules | P2 | open |
| 67 | [Metrics are written to stderr and never read; no per-skill or hook telemetry exists](issues/67-metrics-never-persisted.md) | metrics | P2 | open |
| 68 | [silent-error-review can drop a real failure line and never closes the loop](issues/68-silent-error-review-gaps.md) | investigative-cycles | P2 | open |
| 69 | [afk-loop resolution status is self-certified by the agent](issues/69-afk-loop-self-certifies.md) | investigative-cycles | P3 | open |
| 70 | [audit rule-count check matches the index, not the rule bodies](issues/70-audit-rule-count-index-only.md) | algorithm-translation | P2 | open |
| 71 | [audit check 26 compares only the first 60 chars, and only for "Use when" skills](issues/71-audit-26-prefix-only.md) | algorithm-translation | P2 | open |
| 72 | [Bundle business rules exist only as implicit code, no domain document](issues/72-business-logic-undocumented.md) | business-logic | P2 | open |
| 76 | [blender_server nonce check is optional and nonce is leaked in every response](issues/76-blender-server-nonce-optional-and-leaked.md) | security | P1 | open |
| 77 | [cu_taskrunner trace_id used unvalidated in path join (traversal)](issues/77-cu-taskrunner-trace-id-path-traversal.md) | security | P2 | open |
| 78 | [held-out and validation tests are collected by the default pytest run](issues/78-held-out-tests-collected-by-default-pytest-run.md) | test-coverage | P2 | open |
| 79 | [five hook/utility scripts have zero test coverage](issues/79-untested-hook-scripts-zero-coverage.md) | test-coverage | P2 | open |
| 80 | [install.sh copies credentials.toml and mcp_config.json with default permissions](issues/80-install-sh-credentials-copied-without-mode-restriction.md) | security | P2 | open |
| 81 | [cu_env_daemon TCP auth token written to ready.json with default file perms](issues/81-cu-env-daemon-token-in-ready-json-default-perms.md) | security | P3 | open |
| 82 | [scrape.py fetches arbitrary URLs with no scheme/host allowlist](issues/82-scrape-py-no-scheme-host-allowlist-ssrf.md) | security | P3 | open |
| 83 | [tests spawn real processes with multi-second sleeps and taskkill](issues/83-tests-spawn-real-long-sleep-processes.md) | test-coverage | P3 | open |
