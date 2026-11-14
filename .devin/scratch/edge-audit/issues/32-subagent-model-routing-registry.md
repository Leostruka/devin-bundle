# 32 -- Subagent model routing via bundle-models.json is convention, not enforced

- **Status**: resolved
- **Category**: devin-cli-limitations
- **Severity**: P3
- **File**: data/bundle-models.json:1-44

## Evidence

Devin CLI has no native effort-level routing for custom subagents; the bundle works around it with `data/bundle-models.json` (roles medium/high/max), per-agent `model:` frontmatter pins, `agent.subagent_model: swe-2-max` in `config.json` as the fallback, and `BUNDLE_*` env overrides. ADR 002 is superseded by this registry. The constraint lives only in docs (AGENTS.md rule 20, MODEL-GUIDE.md): nothing stops a contributor from pinning a paid alias in `agents/*.md` or a user from exporting a config that drifts from the registry.

## Recommendation

Add an `audit.py` check that cross-validates every `model:` pin in `agents/*.md` against `data/bundle-models.json` (reject unknown IDs, warn on paid `cost_tier`), and validate `BUNDLE_*` env override values against the registry at render time in `render-user-hooks.py`/install.

## Tradeoffs

- Merits of current workaround: single source of truth, env overrides allow per-install tuning without forking, free-tier policy is explicit.
- Demerits: policy is enforced by prose rules, not code; a typo'd model ID in an agent file fails only at dispatch time inside the CLI; env overrides are invisible to `audit.py` today; registry updates require hand-editing N agent files (no single-pin indirection).
- Better contorno: `model: {{ROLE_MAX}}` placeholders in agent frontmatter rendered at install/export, so the registry alone controls pins; rejected earlier presumably because CLI frontmatter must be literal, but the installers already render `{{...}}` placeholders elsewhere.

## Verification

`grep -rn 'model:' agents/*.md` vs `data/bundle-models.json` IDs; `grep -n 'model' audit.py` shows no cross-check.

## Answer

Added the registry contract paragraph to TOOLS-MAP.md (Subagentes section): every `model:` pin must resolve to a `data/bundle-models.json` UID, paid pins need justification, BUNDLE_* overrides must be registry UIDs; noted audit/render enforcement as planned work.
