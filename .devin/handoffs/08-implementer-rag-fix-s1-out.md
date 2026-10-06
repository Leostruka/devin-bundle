# Handoff - 08-implementer-rag-fix-s1

## Status

DONE

## Edits

- `skills/rag/reference/eval-and-failures.md` (S1): removed the fixed
  "30+ pairs minimum" floor. Golden set is now described as sized to the
  corpus: cover each distinct intent plus paraphrase and adversarial
  cases, grown over time from real failures. No numeric threshold, no
  new citation. Golden-set-first teaching retained.
- `skills/rag/SKILL.md` (S2): tier-entry sentence now reads "verify the
  target Python actually ships FTS5 compiled in - it is a build-time,
  platform-dependent option - before relying on `bm25()` (C36)".
  One-line-class edit; no restructure.
- `manifest.json`: updated only the `export_hash` of
  `scripts/validate-tool-args.py` to
  `3EF5EE5B42E279CEBEF2B20FD41E3198FFBDB54FE1F5A68BE59CCC6340B5EC86`,
  computed as `hashlib.sha256(open(path,'rb').read()).hexdigest().upper()`
  per audit.py lines 301-303.

## VF results (run by implementer)

- VF1: `grep -n "30+" skills/rag/reference/eval-and-failures.md`
  -> no match (exit 1). Removed, not reframed.
- VF2: `python scripts/validate-skill-format.py skills/` -> 68 passing,
  0 failing; rag PASS.
- VF3: Python scan for U+2014 over `skills/rag/` -> no occurrences
  (grep -P unsupported in this locale; equivalent Python check used).
- VF4: `python audit.py` -> Errors: 0, Warnings: 15. Audit prints
  "OK manifest script hashes match"; the
  "manifest script hash mismatch: validate-tool-args.py" warning is gone.
  Remaining warnings are pre-existing live-vs-bundle drift unrelated to
  this contract.

## Boundaries

No other files touched; no other manifest fields changed; no em-dashes
introduced.
