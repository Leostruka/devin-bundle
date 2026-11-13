---
name: docker
description: Use when the user wants to build, run, compose, or deploy containers. Covers Dockerfiles, docker compose, images, volumes, networks, and basic Kubernetes manifests.
triggers: [user]
---

# Docker

Container build, run, and compose workflows.

## When to use

- Adding or fixing a Dockerfile.
- Running the stack with `docker compose`.
- Image is too large or has security issues.
- Need a basic Kubernetes manifest.
- Running a destructive or risky task that should be isolated from the host.

## Core protocol

1. **Read existing setup.** Dockerfile, compose files, .dockerignore.
2. **Build image.** `docker build -t <tag> .`
3. **Run container.** Verify ports, env vars, volumes.
4. **Optimize.** Multi-stage builds, layer caching, non-root user.
5. **Scan image.** Check for known CVEs if a scanner is available.
6. **Compose stack.** Bring up services and run integration tests.

## Dev container for destructive work

For tasks that could be destructive (file system, DB, network, credentials), run the agent inside a container or dev container rather than directly on the host:

- Build the project image with `docker build` or use an existing `.devcontainer`/`devcontainer.json`.
- Run the agent with the project mounted read-only or inside the container.
- This limits blast radius and prevents accidental host modification.

## See also

- `deploy` — release and rollback orchestration.
- `docker` — container build, run, and compose.

## Output rule

- After changes, run `docker build` and `docker compose up` (or `docker run`) and report status.
