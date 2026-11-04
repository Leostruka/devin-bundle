# 33 -- No native skill versioning: manifest export_hash is the only version signal

- **Status**: open
- **Category**: devin-cli-limitations
- **Severity**: P3
- **File**: manifest.json

## Evidence

Devin CLI skills (`skills/<name>/SKILL.md`) carry no version field the runtime honors. The bundle works around this with `manifest.json` (`version` at bundle level, `export_hash` per skill) plus the global CHANGELOG. There is no per-skill semver: a user cannot tell whether the installed `drift-report` skill is older or newer than the bundle's copy except by hashing files, and `audit.py` compares live-vs-bundle by hash equality only (audit.py:518-527), which flags any local edit as "drift" without version semantics.

## Recommendation

Add an optional `version:` (or `x-bundle-version`) key to SKILL.md frontmatter, populated at export, and teach `audit.py`/the planned install ledger to report older/newer/equal instead of bare hash mismatch.

## Tradeoffs

- Merits of current workaround: hash comparison is simple, catches any divergence, no CLI dependency.
- Demerits: hash equality is binary; a formatting-only change and a behavior change look identical; "live != bundle" warnings cannot distinguish user customization from stale install; no upgrade path semantics (no way to say "safe to overwrite").
- Better contorno: plugin distribution (`devin plugins install`) has native versioning since non-semver versions load (COMPATIBILITY.md:169), but was rejected because plugin hooks are fail-open; frontmatter version keeps the installer path while gaining ordering.

## Verification

`grep -n 'version' skills/*/SKILL.md` returns nothing; `grep -n 'export_hash' manifest.json` shows hash-only tracking.
