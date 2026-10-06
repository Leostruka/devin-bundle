# Handoff: 03-implementer-docs-accuracy - implementer report

- **Status**: DONE_WITH_CONCERNS
- **Contract**: `.devin/handoffs/03-implementer-docs-accuracy.md`

## Findings fixed

| Finding | File(s) | Change |
|---|---|---|
| DOC-001 | `.devin/docs/TOOLS-MAP.md` | Removed the false "19/28 validator + hook matcher" claim and per-tool matcher column. Tools table now documents the validator checks implemented in `validate-tool-args.py` (19 CHECKS) and states honestly that only `exec`/`write`/`edit`/`notebook_edit` payloads reach it via the consolidated guards; checks for the other 15 tools (incl. `run_subagent`) exist but are not wired. Hooks table rewritten to match `hooks.v1.json` reality: 2 PreToolUse matchers (`^exec$` → pre-exec-guard.py chaining destructive-gate/architecture-gate/check-ai-signature/check-push-green/validate-tool-args/no-em-dash; `^(write|edit|notebook_edit)$` → pre-write-guard.py chaining architecture-gate + validate-tool-args + no-em-dash always, check-ai-signature + validate-mermaid for write\|edit), plus the consolidated post-exec/user-prompt/session-start/stop-guard/memory-post-edit/memory-stop/constraint-pinning entry points with their in-process gate lists. PermissionRequest listed as declared-but-unused. |
| DOC-002 | `scripts/validate-tool-args.py` | Added `"qa-ci"` and `"repo-reviewer"` to VALID_PROFILES (now 12 names). |
| DOC-006 | `.devin/CONTEXT.md`, `.devin/ARCHITECTURE_MANIFEST.md` | `docs/plans/` → `.devin/plans/` (CONTEXT.md:88); `docs/` layout row → `.devin/docs/` (manifest §6). No other dead `docs/` pointers found in either file. |
| DOC-008 | `.devin/docs/TOOLS-MAP.md` | Subagent table now lists all 8 profiles (added `qa-ci`); "(7 perfis)" heading → "8 profiles"; VALID_PROFILES caption corrected to 12 names with a note that the check is implemented but not wired. |
| DOC-010 | `.devin/docs/TOOLS-MAP.md` | Single measured figure: AGENTS.md = 11,534 bytes → ~2883 tok (1.10% of 262K). Other doc figures re-measured the same way (SKILL-TIERS ~3610, MODEL-GUIDE ~3820, TOOLS-MAP ~3432). Divergent claims deleted (file rewritten). |
| DOC-011 | `skills/mcp-governance/SKILL.md` | Personal-name citation replaced with neutral "Context-window management for coding agents" (conference talk). |
| DOC-012 | `skills/scan/SKILL.md` | Removed `(or subagent_explore)`; dispatch line now points at `researcher` only. |
| DOC-013 | `CHANGELOG.md` | `C:\Users\Fingertech` → `<user-path>`; `C:\Users\leand`, `C:/Users/leand` → `<user-path>`; "Matt Pocock" (x2) → `<contributor>`. Technical meaning preserved. |
| DOC-017 | `AGENTS.md` | Added a one-line note after the rule index: numbering gaps (e.g. no Rule 6) retained for reference stability; rules are never renumbered. No renumbering done. |
| DOC-018 | `.devin/docs/TOOLS-MAP.md` | AGENTS.md config row now says "28 index entries (20 rule bodies + 8 merged aliases)" instead of "20 regras"; skills row notes `afk-loop` is a mode of `execution`, not a separate skill. (The `afk-loop`-as-skill reference in `.devin/docs/DEVIN-CLI-COMPATIBILITY.md:57` is outside this contract's file list.) |
| DOC-004 (partial, in-scope file) | `.devin/docs/TOOLS-MAP.md` | File rewritten entirely in English per ADR-005. No em-dashes in written content. |

## Verification (VFs)

- VF1: `python -c "...qa-ci/repo-reviewer in validate-tool-args.py"` → **True**
- VF2: no `19/28` claim, no false per-tool matcher table, `qa-ci` in subagent table (lines 59, 79), file in English → **PASS**
- VF3: `grep -n "docs/plans" .devin/CONTEXT.md .devin/ARCHITECTURE_MANIFEST.md` → **no matches**
- VF4: `grep -n "subagent_explore" skills/scan/SKILL.md` → **no matches**
- VF5: `grep -nE "C:\\Users|leand|Fingertech|Pocock" CHANGELOG.md` → **no matches**
- VF6: `python audit.py` → **8 errors (see concerns)**; `pytest -q` →
  **1573 passed, 4 failed, 4 skipped (181s)**. Failures:
  `test_audit_passes.py` x3 (same audit.py errors above) and
  `test_consolidated_hooks.py::test_stop_guard_passes_clean` (stop-guard's
  no-em-dash gate blocks on untracked `.devin/adr/004-rag-skill-tier-model.md`,
  another contract's file; my own diffs add zero U+2014, verified via
  `git diff -U0` scanned for added U+2014 → 0 hits).

## Concerns

1. **audit.py still reports 8 errors, none fixable inside this contract's file list:**
   - 5 pre-existing cross-contract drift: `Manifest mismatch`, `manifest skill_count mismatch`, `README count wrong: 68 skills`, `README skills badge wrong (expected skills-68)`, `README.md diagram skills count stale` - all caused by the untracked `skills/rag/` dir from a parallel contract (disk = 68 skills, manifest/README still say 67). Owned by the rag contract / orchestrator resync.
   - 3 stale audit checks asserting Portuguese literals in TOOLS-MAP: `expected 8 eventos`, `expected 28 in TOOLS-MAP` (requires `28 ferramentas` or the false `19/28` claim), `expected 9 in TOOLS-MAP` (requires `9 excluídas`). These checks encode the pre-ADR-005 pt-BR text and the false DOC-001 claim itself - they cannot be satisfied without un-fixing DOC-001/DOC-004. `audit.py` check-24 strings need updating (audit.py is not in this contract's file list). ESCALATE: orchestrator should realign audit.py checks 732-737 to the English TOOLS-MAP (e.g. "8 events", drop the 19/28 and "9 excluídas" literals).
2. **Audit nuance noted while editing:** `validate-tool-args.py` is not entirely unwired - the consolidated guards invoke it for `exec`/`write`/`edit`/`notebook_edit` payloads; its other 15 CHECKS (incl. `run_subagent` profile validation) never run because no matcher routes those tools. TOOLS-MAP now says exactly this ("available, mostly not wired").
3. AGENTS.md byte size grew with the DOC-017 note; the ~2883 tok figure in TOOLS-MAP is measured post-edit.

## Out of scope (not touched)

`manifest.json`, `.devin/docs/SKILL-TIERS.md`, `MODEL-GUIDE.md`, `3D-STACK-INSTALL.md`, `skills/rag/`, `audit.py`, hooks files, DEVIN-CLI-COMPATIBILITY.md (carries the DOC-018 `afk-loop` stale name at :57 - flagged for whichever contract owns it).
