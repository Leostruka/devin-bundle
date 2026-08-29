---
name: api-design
description: Use when the user wants to design, review, or document an API. Covers REST, OpenAPI, versioning, error models, contract testing, and authentication.
triggers: [user, model]
---

# API Design

Design and review HTTP/gRPC/GraphQL APIs with contracts and tests.

## When to use

- New endpoint or service is needed.
- Reviewing an existing API for consistency.
- Generating or updating OpenAPI specs.
- Adding contract tests.

## Core protocol

1. **Collect constraints.** Consumers, auth, rate limits, error handling, versioning.
2. **Choose style.** REST, gRPC, GraphQL, or hybrid based on use case.
3. **Design endpoints.** Nouns as resources, consistent paths, status codes, error model.
4. **Write the contract.** OpenAPI or proto file; validate with tools.
5. **Add tests.** Contract, serialization, and happy/unhappy paths.
6. **Document.** Keep spec and docs in sync.

## See also

- `codebase-design` — module and seam architecture.
- `api-design` — contract-first HTTP/gRPC/GraphQL API design.

## Output rule

- Deliver a spec file, examples, and a test command.
- Verify spec is valid with `swagger-codegen` or similar if available.
