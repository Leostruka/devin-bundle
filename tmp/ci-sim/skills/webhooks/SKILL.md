---
name: webhooks
description: Use when building or debugging endpoints that receive third-party callbacks (payments, GitHub, ERP). Webhook receiver discipline - signature verification, idempotency by event id, fast acknowledge with background processing, replay protection.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, write, edit, exec]
---

# Webhooks

A webhook endpoint is a public endpoint receiving POSTs from third parties: without verified signatures anyone injects events; without idempotency retries duplicate effects.

## When to use

- Creating an endpoint that receives webhooks (payment, GitHub, ERP).
- Debugging duplicated or lost events.
- Reviewing an existing callback endpoint.

## Hard rules

**Event authentication**

- ALWAYS verify the provider signature (payload HMAC with the secret, or the provider's own mechanism). Never trust the payload.
- Constant-time signature comparison (`hash_equals`): normal comparison leaks timing.
- Secret outside the code (secrets/env) with a rotation procedure.

**Idempotency and retry**

- Same event_id processed twice = effect once: store processed event_ids (table with unique constraint) and ignore duplicates.
- Respond 2xx fast (ack) and process later in a queue. Never process synchronously with the provider timeout on your neck.
- Events arrive out of order: process by state, do not assume arrival order.

**Validation and surface**

- Validate payload schema before using: a missing field is a malformed event, not a crash.
- Event-type whitelist; unknown type = ignore and log, never explode.
- Replay: acceptance window based on the provider timestamp.

**Operations**

- Structured log keyed by event_id (debug correlation).
- Queue with its own retry and dead-letter (DLQ).
- Monitor received vs processed; alert if the queue backs up.

## Flow

1. New webhook: define event_id + signature verification BEFORE the handler.
2. Provider test event: validate signature and end-to-end processing.
3. Test a real duplicate: send the same event 2x and confirm single effect.
4. Test replay/lag: an old event must not corrupt state.

## Anti-patterns

- Synchronous processing in the request (provider timeout = lost event and infinite retry).
- Accepting a payload without signature "because the provider is trustworthy".
- No event_id: duplicate becomes double effect (2x charge).
- Empty catch on malformed events: invisibly lost data.
- Webhook secret in code/commits.

## Cascade

- `security`: webhook secret handling and rotation, public endpoint surface.
- `debugging`: duplicated/lost event investigation.
