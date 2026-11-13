---
name: drift-report
description: Use when checking whether design documents, READMEs, or specs still match the code they describe. Reads each document, locates the referenced source files, and reports only concrete divergences in a dated drift report. Detection only; does not fix code or docs.
triggers: [user, model]
---

# Drift Report (design vs code consistency)

## Overview

Adapted from `egm-drift-report` in google/elephant-goldfish-model
(Apache-2.0). Detects where the codebase diverged from or failed to
implement what design documents describe. Report-only: divergences are
evidence for a human decision or a follow-up task, never silently
repaired in the same pass.

Default targets when the user names none: `docs/` and `.devin/plans/`
in this bundle; in target projects, the directory of specs or READMEs
the user points at. `spec-consistency.py` covers plan-file internals
(checkboxes, declared refs); this skill covers doc-to-code fidelity.

## Procedure

1. **Check input**: require a directory of design documents or READMEs.
   If absent, ask the user to specify the target directory.
2. **List documents** in the directory; process them sequentially to
   keep tool output under control.
3. For EACH document:
   - **Contextualize**: read the document; extract intent, proposed
     changes, and specific filenames or symbols mentioned.
   - **Locate source**: find the referenced code via explicit paths,
     code search, or grep on the classes/functions/endpoints named. If
     the doc lacks links, tell the user to add them so future detection
     is cheaper.
   - **Verify**: read the current state of the source files with tools;
     never compare from memory.
   - **Detect drift**, looking specifically for:
     - Missing features: logic described in the doc but absent in code.
     - Incomplete models: dataclass/class/struct/proto fields the design
       specifies but the code lacks.
     - Logic shortcuts: hardcoded values where dynamic logic was planned.
     - Architectural divergence: implementation using different
       patterns or libraries than proposed.
   - **Filter**: report ONLY differences. When code matches the design,
     record "No drift detected" for that document.
4. **Report**: write findings to `<YYYY-MM-DD>_DRIFT_REPORT.md` in the
   project `.devin/` directory when it exists, else the design directory.
   Strict format per document:

   ```markdown
   ## <DESIGN_DOC_NAME>

   <bulleted list of specific divergences>
   or "No drift detected"
   ```

## Iron rules

1. Report-only. Never edit code or docs to close a drift found in the
   same pass; record it and stop.
2. Every claimed divergence cites the doc section and the code location
   actually read; no memory-based claims.
3. "No drift detected" is a first-class result, not a failure.
4. Be rigorous: a named object, field, or file absent from code is
   reportable drift; so is shipped logic unreferenced by any doc.
