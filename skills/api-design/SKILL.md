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
4. **Specify input/output/behavior.** Every endpoint or operation must declare its input schema, output schema, and observable behavior. A spec that lacks input/output is incomplete.
5. **Write the contract.** Produce an OpenAPI spec (or proto file) and validate it with tools. The spec is the primary context for the agent; keep it in sync with the code.
6. **Add tests.** Contract, serialization, and happy/unhappy paths.
7. **Document.** Keep spec and docs in sync.

## Output rule

- Deliver a spec file, examples, and a test command.
- Verify spec is valid with `swagger-codegen` or similar if available.
- Include the OpenAPI spec (or equivalent) as context for implementation; the agent works from the spec, not from memory.
