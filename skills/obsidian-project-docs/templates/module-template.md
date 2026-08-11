---
title: "{{MODULE_NAME}}"
module: "{{MODULE_NAME}}"
project: "{{PROJECT_NAME}}"
parent: 04-Modules
tags:
  - module
  - {{PROJECT_TAG}}
---

# {{MODULE_NAME}}

## Purpose
_One sentence: what problem does this module solve?_

## Source
- `source: path/to/module/file.ext:line`

## Interface
_What a caller must know: public functions, classes, types, invariants, ordering, errors, config._

## Implementation notes
_Design choices, internal structure, key algorithms._

## Dependencies
- Internal: _[[Modules/OtherModule]]_
- External: _see [[06-Dependencies]]_

## Tests
- _Unit tests:_ `source: tests/module.test.ext:1`
- _Integration tests:_ `source: tests/module.integration.test.ext:1`

## ADRs and decisions
_Link to relevant ADRs in [[09-Decisions]]._

## Open questions
> [!question]
> _List unresolved questions._
