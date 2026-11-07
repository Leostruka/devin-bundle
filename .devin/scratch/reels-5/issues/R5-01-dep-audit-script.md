# dep-audit: dependency vulnerability scanner (script + optional hook)

status: ready-for-agent
priority: P2
source: reels batch-5 survey (.devin/research/2026-11-07-reels-batch5-survey.md), matheusgomes DcUOPkPzorX

## Evidence

PT transcript (`.devin/scratch/reels-5/transcripts/DcUOPkPzorX.pt.json`): matheusgomes (~529K IG, vibe-coding educator, github.com/soumatheusgomes) describes a Python script with no LLM/token cost that scans project dependencies for known vulnerabilities on every library update/install. It caught a production library whose submodules were vulnerable. His point: agents (Claude/GPT) cannot tell whether a dependency is vulnerable, so a deterministic scanner must run outside the model.

Bundle gap verified: `security-audit`/`security` skills cover dependency CVEs only as a manual checklist line; no script/extension/hook automates it (grep for pip-audit/osv/npm audit/cargo audit across skills+scripts+extensions = docs mentions only).

## Task

Add a deterministic dep-audit capability:

1. `scripts/dep-audit.py` (stdlib-first wrapper): detect ecosystem(s) in cwd: `requirements*.txt`/`pyproject.toml` -> `pip-audit` or OSV-Scanner; `package.json`+lock -> `npm audit --json`; `Cargo.toml`+lock -> `cargo audit`; `go.mod` -> `govulncheck` if present. Graceful `ok:false`+hint when the underlying scanner is not installed (never silent install, same contract as `extensions/asr/transcribe.py`). Aggregate JSON output `{ok, ecosystems, findings:[{pkg, vuln, severity, fix}]}`.
2. Wire optional PostToolUse hook in `hooks.v1.json` on `^exec$`: only when command matches package-install patterns (`pip install`, `npm install/i`, `pnpm add`, `cargo add`, `uv add`, `poetry add`) via a cheap regex pre-filter in a small `scripts/dep-audit-gate.py`, fail-open, `[DEP-AUDIT]` warning via additionalContext on findings. Keep timeout small.
3. Document in `skills/security-audit/SKILL.md` checklist (point at the script) + `docs/TOOLS-MAP.md` + README script count if scripts are counted there.
4. Tests under `tests/` for detection + JSON contract with stubbed scanners (no network).

## Acceptance

- [ ] `python scripts/dep-audit.py` on a fixture project returns structured findings without network when scanners absent
- [ ] hook fires only on install-like commands; fail-open on error
- [ ] `python audit.py` + `python -m pytest` green
