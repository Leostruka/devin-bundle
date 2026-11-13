---
name: device-repurpose
description: Use when repurposing an existing device (TV, Kindle, iPad, AC, router, printer, embedded board) into agent-driven use — strip vendor services, deploy a custom controller/UI, verify. Encodes the recon -> strip -> redeploy -> verify pipeline on top of firmware-probe, devin-integrate, and computer-use ADB.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, write, edit, exec, webfetch, web_search]
---

# device-repurpose

Repurpose a device the user already owns into something better —
verified real-world pattern (cleanyourtv, coolbar AC controller, iPad
wall panels, dictation-mic builds, EEVblog 121GW firmware RE). The one
trait every real case shared: **the agent had a way to check its own
work.** No verification path, no repurpose.

## Stage 1 — recon (read-only, always first)

Enumerate every interface before touching anything:

| Surface | Probing |
|---|---|
| Web admin | `webfetch` the device's admin UI / API docs; port scan if on LAN |
| ADB / Android | `extensions/computer-use/cu_adb_backend.py` (already drives Android) |
| Firmware | `firmware-probe` skill — image extraction, SBOM, config review (read-only) |
| Serial/UART | document pins + baud; capture boot log first |

Deliverable: an interface map file listing what was found, which write
paths exist, and the recovery path if a write bricks the device.

## Stage 2 — strip

Remove vendor telemetry/ads/bloat only through interfaces confirmed in
stage 1. Prefer disabling over deleting; keep a restore note for every
change.

## Stage 3 — redeploy

Pick the embed surface per `devin-integrate`'s transport ladder
(file ledger < subprocess < HTTP < stdio JSON-RPC < WebSocket). For
displays: build the replacement UI/controller as a minimal app first —
the device is a host, not the dev machine.

## Stage 4 — verify (gate, not suggestion)

Define the observable success check BEFORE stage 3 (ping endpoint,
screenshot hash via computer-use, serial banner, UI element present).
Loop until the check passes or the recovery path triggers. A repurpose
without a verification loop is an anecdote, not a deliverable.

## Anti-sources — do NOT codify

Astroturfed/promotional cases (fact-checked, 17/31 of the source list
real): WiFi-router-8x-speedup, DJI security drone, BlackBerry terminal,
Airbnb hidden-camera sweep. Use verified anchors only.

## Boundaries

- Every destructive write (flash, partition, vendor partition wipe)
  requires explicit per-action user confirmation.
- Root/jailbreak actions void warranties — state that once, proceed on
  the user's authorization.
- Own devices and the user's own network only.
