---
name: database
description: "Use when the user wants to design, migrate, query, or optimize a database. Covers schema design, migrations, query review, indexing, and data integrity."
triggers: [user, model]
---

# Database

Database design, migrations, and query optimization.

## When to use

- New schema or migration is needed.
- Query is slow or returns wrong results.
- Data integrity or constraints must be added.
- Backup/restore or seeding is required.

## Core protocol

1. **Understand the model.** Read existing schema, migrations, and ORM config.
2. **Design or change schema.** Use migrations; never edit schema directly in production.
3. **Review queries.** Check indexes, N+1, transactions, and locks.
4. **Run migrations locally.** Verify roll-forward and roll-back.
5. **Validate data.** Seed, constraints, and referential integrity.
6. **Document.** Update migration log and schema docs.

## See also

- `data-analyst` — SQL-first data exploration and charts.
- `database` — schema design, migrations, and query optimization.

## Output rule

- After schema changes, run migration tests and a sample query plan.
- Commit migration files and update CHANGELOG.
