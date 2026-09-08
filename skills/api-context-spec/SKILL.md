---
name: api-context-spec
description: Use when generating or maintaining OpenAPI specs as context for AI agents. Ensures API contracts are explicit, versioned, and machine-readable.
---

# API Context Spec

Generates and maintains OpenAPI specs as context for AI agents. Ensures API contracts are explicit, versioned, and machine-readable so agents can reason about endpoints without reading implementation code.

## When to use

- When designing or reviewing an API.
- When the API contract is not documented or is outdated.
- When an AI agent needs to understand the API surface without reading code.
- When generating client SDKs or contract tests.

## What to include

1. **Endpoints.** Paths, methods, parameters, request/response schemas.
2. **Authentication.** Auth type, required headers, token format.
3. **Error responses.** Status codes, error schemas, retry semantics.
4. **Versioning.** API version, deprecation policy, migration path.
5. **Rate limits.** Requests per second, burst limits, backoff strategy.

## Process

```
Design or review API
  → Generate or update OpenAPI spec
  → Validate spec against implementation
  → Use spec as context for AI agents
  → Keep spec in version control
```

## Example

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found
```

## Anti-patterns

- No API spec or an outdated spec.
- Spec written in prose instead of OpenAPI.
- Spec not versioned or not in version control.
- Agents reading implementation code instead of the spec.

## Cross-skills

- `api-design` — designs the API that this spec documents.
- `planning-pipeline` — uses the spec as context for tickets.
- `implement` — uses the spec as the contract to implement.
- `verification-before-completion` — verifies the spec is up to date.
