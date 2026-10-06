# Handoff - 04-implementer-docs-index-language (OUT)

- **Status**: DONE_WITH_CONCERNS
- **Date**: 2026-10-05

## Files modified (all inside contract list)

| File | Change |
|---|---|
| `.devin/docs/SKILL-TIERS.md` | Rewritten in English; same headers/structure; all 68 top-level `skills/` dirs now indexed (the 14 missing added: ai3d-gen, architecture-diagrams, creative-engineering, fact-check, humanizer, implement-laya, media-tools, mesh-utils, operate-blender, operate-godot, prompt-compiler, project-orchestrator, scrape-tools, social-midia with its 8 nested children noted); `scan` tok filled with measured 936 (3745 bytes/4); new-row tok values measured bytes/4; existing rows kept; `{{BUNDLE_*}}` placeholders and model table preserved |
| `.devin/docs/MODEL-GUIDE.md` | Translated pt-BR to EN; content unchanged |
| `.devin/docs/3D-STACK-INSTALL.md` | Translated to EN and genericized: machine-state table became a generic component checklist; `C:\Program Files\Blender...` and `~/ComfyUI` replaced by `<comfyui-dir>` placeholder and generic instructions; machine-specific limits section rewritten as generic checks (no user paths) |
| `skills/self-improvement/modes/improvement-loop.md:165` | Stray pt line translated to EN (rest of file untouched per contract scope) |
| `skills/{ai3d-gen,mesh-utils,operate-blender,operate-godot}/SKILL.md` | Added `triggers: [user, model]` after `description:` in frontmatter, matching convention |

## VF results (run locally)

- **VF1** PASS (with caveat) - all 67 contract-relevant top-level dirs have a `` `name` `` row; the 68th dir, `skills/rag/` (untracked, contract 07 in-flight), has NO row per the explicit boundary. A naive substring check passes `rag` only via `brag`; an exact-name check would flag it - expected and contract-mandated.
- **VF2** PASS - spot grep `quando|para|com |uso` on the 3 docs: only English-word substring hits (`parallel`, `separate`, `github.com`, `com ` inside "becomes/com" none in prose). No pt-BR prose remains.
- **VF3** PASS - no `C:\Users`, `C:\Program Files`, `~/ComfyUI` literals in 3D-STACK-INSTALL.
- **VF4** PASS - `triggers:` present in all 4 named skills' frontmatter (verified via grep, line 4 each).
- **VF5** FAIL (external causes) - `python audit.py` exit 0 but SUMMARY: **10 errors, 16 warnings**. All 10 errors trace to files owned by other contracts:
  - `skills/rag/` exists on disk (untracked, contract 07 work-in-progress) -> manifest mismatch, `skill_count declared=67 actual=68`, `disk_only={'rag'}`, README count/badge errors expecting 68.
  - TOOLS-MAP.md staleness errors (skills/scripts/hook/tool counts) - file owned by contract 03, currently modified in worktree.
  - None of the 10 errors reference files in this contract's list. Re-running audit after contracts 03/07 land should clear them.
  - Warnings (16) are install-drift (`live != bundle`) + `__pycache__` noise; my 4 edited skills appear in `live != bundle`, expected until reinstall.

## Concerns

1. **VF5 red at handoff time** - caused by parallel contract work (`skills/rag/` dir + TOOLS-MAP in flight), not by this contract's edits. Recommend orchestrator re-run VF5 after contracts 03 and 07 merge.
2. SKILL-TIERS grew to ~3600 tok (was ~3500): the "~1700 tok" claim is aspirational header text kept verbatim; full coverage of 68 skills is incompatible with 1700 tok. Flagging as spec tension, not improvised - VF1 (coverage) was prioritized per contract.
3. `improvement-loop.md` remains largely pt-BR except line 165 - contract scoped to that single line; whole-file translation would exceed the file list boundary.
4. Em-dashes (U+2014) removed from all authored content per project gate (`scripts/no-em-dash.py` exists).

## Boundaries respected

- TOOLS-MAP.md, manifest.json, CHANGELOG.md, AGENTS.md, `skills/scan/`, `skills/mcp-governance/` untouched.
- No `rag` row added to SKILL-TIERS (boundary; see VF1 caveat above).
