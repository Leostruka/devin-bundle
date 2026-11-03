# Plan: reels-survey adoption, orchestrated implementation (2026-11-03)

Input artifact: `.devin/research/2026-11-03-instagram-reels-survey.md`
Orchestration mode: `project-orchestrator`. Contracts under `.devin/handoffs/`,
ledger `.devin/ledgers/reels-adoption.md`, all state in files.

## Task ledger

Scope: 5 bundle items ranked 1-5 in the survey + 1 external backlog.
Non-goals: MERIDIAN implementation (external repo), MoneyPrinterTurbo vendoring,
replacing `voicebox` backend, changing AGENTS.md rule numbering.

Bundle consistency rules that every contract must satisfy:
- `manifest.json` skill/script counts + hashes; README + `.devin/docs/TOOLS-MAP.md`
  counts stay in sync (`python audit.py` == 0 errors).
- Skills need `name:` + description + "Use when" frontmatter.
- New `scripts/*.py` need `if __name__ == "__main__":` guard.
- No em-dash prose violations (`stop-guard.py` scans untracked files).
- `python -m pytest -q` (testpaths) green before any push; main is protected,
  so ship via branch + PR, never direct push.
- No AI signatures; no unmasked secrets.

## Phase G3: delegation contracts

Budget: <=3 concurrent subagents; ~15 turns declared per contract (cap 25).

### C1: `lean-code` skill (Ponytail port) | `implementer`
- Lane: worktree `.worktrees/lean-code`, branch `skill/lean-code`
- Inputs: survey section 3a; source `github.com/DietrichGebert/ponytail` (MIT,
  fetch SKILL.md, port with attribution line)
- Output: `skills/lean-code/SKILL.md` (decision ladder, never-cut guardrails,
  one-test-for-risky-logic); `manifest.json` entry (156); README/TOOLS-MAP
  count bump if the counter demands
- VFs: `python audit.py` == 0 err; `pytest -q tests/validation/test_skill_format_passes.py`
- NOT-list: no AGENTS.md edits, no new commands/scripts yet (skill only)

### C2: vendor `security-audit` (Cloudflare, MIT) | `implementer`
- Lane: worktree `.worktrees/sec-audit-cf`, branch `skill/security-audit-cf`
- Decision gate first: name `security-audit-cf` vs fold into existing
  `security-audit`. Read our SKILL.md, default to distinct name (survey 3b)
- Output: `skills/security-audit-cf/` (SKILL.md + ledgers/validators incl.
  the two `.cjs` scripts); manifest entry; license note in frontmatter
- VFs: audit 0 err; `node validate-findings.cjs --help` or syntax-check;
  skill-format test green
- NOT-list: don't rewrite existing `security-audit`; no Node deps added

### C3: VoiceStudio OpenAI-compat path | `implementer`
- Lane: worktree `.worktrees/voicestudio-path`, branch `feat/voicestudio-path`
- Output: `extensions/voicebox/wrapper.py` gains `--backend voicestudio`
  (or `VB_BACKEND=voicestudio`) targeting `127.0.0.1:3900`
  `/v1/audio/speech` (OpenAI shape); same safety contract (loopback-only,
  whitelisted actions, bounded bodies); `tts` SKILL.md documents backend
  switch + AGPL/non-commercial engine caveat
- VFs: `python extensions/voicebox/wrapper.py doctor` vs unreachable backend
  -> `status: missing`; unit tests in `tests/test_voicebox_wrapper.py` green
- NOT-list: don't remove jamiepine/voicebox path; no model downloads

### C4: JXL codec in media-tools | `implementer`
- Lane: worktree `.worktrees/jxl`, branch `feat/media-tools-jxl`
- Output: `extensions/media-tools` JXL decode/encode via `cjxl`/`djxl`
  (bootstrap fetch in the `extensions/asr` style: explicit, never silent);
  `identify` reports JXL; graceful `missing` when binaries absent
- VFs: round-trip png->jxl->png on a fixture; existing media-tools tests green
- NOT-list: no Pillow plugin dep; don't wire ROI encoding yet (follow-up)

### C5: `shorts-factory` skill (MPT-equivalent assembly) | `implementer`
- Lane: worktree `.worktrees/shorts-factory`, branch `skill/shorts-factory`
- Output: `skills/shorts-factory/SKILL.md` orchestrating existing pieces:
  script (agent) -> narration (`tts`) -> alignment (`asr`) -> scene plan
  -> render (`remotion-render`/`animation-direction`) -> ffmpeg composite;
  plus `extensions/stock-footage` thin fetcher (Pexels/Pixabay API key in
  env, plain HTTP, typed JSON errors). Footage fetch is the only new runtime.
- VFs: dry-run pipeline on a sample topic produces scene plan JSON;
  skill-format + audit green; no silent network calls without key
- NOT-list: no auto-publish (separate decision, needs creds + ToS review);
  no `seen.txt` batch daemon in v1

### C6: MERIDIAN backlog transfer | `researcher` (read-only)
- Output: `.devin/research/2026-11-03-meridian-altdata-backlog.md`:
  structured backlog for `leostruka/MERIDIAN` covering alt-data source
  registry (Sentinel-2/ESA, Planet, ADS-B, AIS), car-count CV baseline
  sketch, tank-shadow volumetrics approach, signal->backtest harness design
- VFs: artifact exists, cites survey section 4 + public source list
- NOT-list: no code, no new repos created

## Gates

- Per-contract: VFs above + `qa-ci` verify before lane merges.
- Final gate: `python audit.py` == 0 errors; `python -m pytest -q` green;
  manifest counts == disk; one PR per contract (or grouped C1+C2).
- Sequence: C1, C2, C3 can fan out (independent files). C4 independent.
  C5 last, since it touches the shared `extensions/` area and wants C3's
  backend path as a narration option. C6 anytime (read-only).

## Risks

- Phantom editor observed 2026-11-02 (uncommitted-tree reverts + a
  print-muting edit). Mitigate: commit early per contract, worktree lanes,
  verify `git status` before dispatch.
- VoiceStudio AGPL/non-commercial engine: document, don't bundle weights.
- Pexels/Pixabay APIs need user keys: skill must fail with a typed hint,
  never fabricate footage.
- CF skill Node validators: audit-time only; bundle stays stdlib-first.
