---
name: ontology-validator
description: Use when validating tool outputs or data against a domain ontology or structured knowledge base. Ensures entities, types, and relations are consistent before side effects.
triggers: [user, model]
---

# Ontology Validator

Validates that tool outputs and data changes are consistent with a domain ontology or structured knowledge base. Complements Pydantic (schema/type checking) with domain-level reasonableness.

## When to use

- After a tool returns a result that will drive a side effect (write, DB insert, API call).
- When the system has a `knowledge.json` or similar structured knowledge base.
- When entity types, statuses, or relationships must be enforced.
- When duplicate operations must be prevented.

## Core rule

> **Pydantic at the door, ontology at the ledger.**

- **Pydantic** (or equivalent) validates types and required fields at the boundary.
- **Ontology** validates domain-level reasonableness: valid statuses, entity types, disjoint relationships, no duplicates.

## What to check

1. **Entity type consistency.** Is the returned entity type valid for this domain?
2. **Status validity.** Is the status value allowed (e.g., `pending`, `in_progress`, `completed`)?
3. **Relationship validity.** Does the relation type make sense (e.g., `contains`, `depends_on`)?
4. **Duplicate prevention.** Would this operation create a duplicate entity or relation?
5. **Disjointness.** Are two entities that should be disjoint being treated as the same?

## Process

```
Tool returns result
  → Pydantic/schema check (types, required fields)
  → Ontology check (entity type, status, relation, duplicates)
  → If both pass: proceed to side effect
  → If either fails: return to model or human for correction
```

## Example

```python
# Pydantic validates the shape
class Ticket(BaseModel):
    id: str
    status: Literal["pending", "in_progress", "completed"]

# Ontology validates the domain
if ticket.status == "completed" and ticket.depends_on_open():
    raise ValueError("Cannot complete ticket with open dependencies")
```

## Anti-patterns

- Trusting tool output without domain validation.
- Treating Pydantic as sufficient for domain rules.
- Skipping duplicate checks when creating entities.
- Assuming all relations are valid because the schema allows them.

## Cross-skills

- `verification-before-completion` — use as final gate before claiming done.
- `structured-knowledge-extraction` — provides `knowledge.json` for ontology checks.
- `security-audit` — ontology can flag insecure states (e.g., `status: public` on a secret).
