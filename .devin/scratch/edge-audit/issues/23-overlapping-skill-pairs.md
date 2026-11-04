# 23 -- Near-duplicate skills create ambiguous discovery
- **Status**: resolved
- **Category**: organization
- **Severity**: P3
- **File**: skills/context-hygiene/SKILL.md, skills/context-window-hygiene/SKILL.md, skills/context-folding/SKILL.md, skills/memory-hygiene/SKILL.md, skills/memory-management/SKILL.md, skills/project-memory/SKILL.md, skills/brag/SKILL.md, skills/brag-slim/SKILL.md

## Evidence
Several skill pairs/triples have descriptions that trigger on the same user situations:

- `context-hygiene` ("context is growing large... deciding clear vs compact... >50k tokens") vs `context-window-hygiene` ("conversation is getting long and the agent seems to be forgetting... deciding whether to clear or compact") vs `context-folding` ("context is growing large (approaching model window limits)... compaction is losing critical information"). The first two describe the same triggers almost verbatim.
- `memory-hygiene` vs `memory-management`: both cover "auto-memory seems stale or preferences leak across tasks" and "deciding whether to persist knowledge in cross-session agent memory"; `memory-management` even self-describes its scope as "memory hygiene only".
- `brag` vs `brag-slim`: both claim the "/brag" phrase family; brag-slim's description includes a runtime negotiation rule ("If the /brag skill is also installed, let /brag handle those phrases") that only works if the dispatching agent reads both descriptions.

With 168 flat skills, lexical pickers (scripts/skill-picker.py) and SKILL-TIERS.md cannot reliably disambiguate; overlapping "Use when" clauses mean the wrong variant is chosen nondeterministically.

## Recommendation
Consolidate or add explicit routing: merge context-hygiene + context-window-hygiene (one appears to be a superset), rename memory-* to distinct verbs (e.g. `memory-capture` vs `memory-audit`), and state precedence for brag/brag-slim in the manifest purposes, not only inside SKILL.md bodies.

## Tradeoffs
Merits: deterministic selection, smaller token cost at discovery time. Demerits: renaming skills breaks `original_path` entries in manifest.json and any hooks/docs that reference current names.

## Verification
Compare `description:` frontmatter of the listed files; run scripts/skill-picker.py with prompts like "conversation getting long, agent forgetting instructions" and observe which candidate set it emits.

## Answer
No skills merged or removed (manifest `original_path` and hook/doc references make renames a larger decision). Reconciliation table of recommended actions:

| Pair / triple | Overlap | Recommended resolution |
|---|---|---|
| context-hygiene vs context-window-hygiene | Near-verbatim triggers ("forgetting earlier instructions", "clear vs compact") | Merge into `context-hygiene` (superset: also covers >50k docs and subagent fan-out); redirect context-window-hygiene |
| context-hygiene vs context-folding | Both trigger on "context growing large" | Keep both; sharpen boundary: folding = RLM-style recursive processing of long documents, hygiene = clear/compact/session budgeting. Differentiate `description:` fields |
| memory-hygiene vs memory-management | Same triggers verbatim; memory-management self-scopes to "memory hygiene only" | Merge into one skill (`memory-management`); rename survivor to a distinct verb per recommendation |
| project-memory vs memory-* | Partial: capture-side of memory | Keep `project-memory` as the capture/write skill; scope the merged memory skill to audit/staleness decisions only |
| brag vs brag-slim | Same "/brag" phrase family; precedence only inside SKILL.md body | Declare precedence in `manifest.json` `purpose` fields (brag-slim handles bare /brag when brag absent); or merge into brag with a slim mode |

Follow-up: apply merges in a dedicated lane (touches `manifest.json`, `SKILL-TIERS.md`, `scripts/skill-picker.py` results).
