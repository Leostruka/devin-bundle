# Device-automation lane

Issue #451 (R7-18). Defines the lane for agents acting on physical devices,
beyond desktop GUI automation.

## Motivation

- YT `KDyPHt4lW60` ("capabilities overhang" showcase, transcript
  `.devin/scratch/yt-batch2/transcripts/KDyPHt4lW60.log`): agents rebuilt a
  smart-TV UI to strip ads, wrote dictation-mic firmware, built an AC
  taskbar controller, jailbroke a Kindle into a dashboard, fixed a router
  config for 8x Wi-Fi, drove a receipt printer, repurposed a drone and an
  old iPad as home panels.
- Reel `DfXwuL0izsO` (huwprosser): BUSY Bar LED status display with open
  HTTP API and busylib-py/ts - already landed as `extensions/busybar/`
  under issue #450.
- Survey row R7-18
  (`.devin/research/2026-11-10-reels-batch7-survey.md`): "doc the
  agent->physical-device lane (TV/Kindle/router class); map to
  craft-bridge/system-control/computer-use."

## What "device automation" means here

Four access classes, ordered by preference:

1. **Network/HTTP API** - device exposes a documented API on LAN or USB
   gadget networking (BUSY Bar `http://10.0.4.20/api`, router admin pages,
   smart-TV REST/SQLite services). Cheapest, scriptable, honest errors.
2. **Structured control channel** - ADB, SSH, serial, MQTT, IR bridges
   with a command grammar. No pixels involved.
3. **GUI automation on the device's own screen** - scrcpy/uiautomator for
   Android, HDMI capture + IR/CEC for TVs. Fallback when no API exists.
4. **Hardware bridge / firmware** - Flipper-class bridges, ESP firmware,
   CEC injectors. Highest effort and highest irreversibility; treat as
   its own project, not a lane shortcut.

Rule of thumb (same as `system-control` vs `computer-use`): prefer the
structured interface; use pixels only when nothing else exists.

## Existing bundle pieces that apply

Verified in source:

- **`extensions/computer-use` + `skills/computer-use`** - the ADB backend
  (`cu_adb_backend.py`) already registers a physical Android device as an
  attach-only env (`.devin/computer-use/envs/phone.json`,
  `{"provider": "adb"}`): `exec-out screencap`, `uiautomator` element
  tree, `input tap/keyevent`, `adb shell` via `terminal.py exec`.
  `cu_devices.py` (C15) models physical-device leases with serial +
  topology identity and a protected human-input pair - no passthrough
  attach yet, plans require human approval. This is the anchor for the
  phone class and the pattern for future device leases.
- **`extensions/busybar/push.py`** - first device-lane client: focus
  session state pushed to the BUSY Bar LED matrix over its HTTP API
  (USB default, LAN via `BUSYBAR_ADDR`, cloud via `BUSYBAR_TOKEN`).
  Advisory by design: unreachable device exits 0 after a stderr note.
- **`scripts/focus.py`** - append-only focus ledger; the event source
  feeding the busybar push.
- **`extensions/system-control` + `skills/system-control`** - the
  confirmation/deny model to copy: fresh per-call user confirmation for
  mutating capabilities, deny-by-default list, untrusted output.
- **`extensions/gcal`** - example of a non-device external-service
  wrapper; pattern (stdlib client, offline-tolerant) applies to device
  HTTP APIs.
- **`hooks.v1.json` PreToolUse layer** - where device-mutation
  confirmation gates can be enforced rather than requested.

## Device classes and integration sketches

### Status lights / LED displays (BUSY Bar)

Already implemented: `extensions/busybar/push.py`. Class traits: HTTP
API, display-only output, low risk. Pattern extends to LaMetric,
Ulanzi/Awtrix, Divoom - same "push elements" shape.

### Phones and tablets (Android via ADB, iOS via tethered tools)

Done for Android: `provider: "adb"` env gives screenshot, element hints,
tap/scroll, shell. Limits documented in `USAGE.md`: no hover, no chords,
ASCII-only text, `dispatched` != reacted. iOS is out of scope until a
WebDriverAgent-class bridge is vetted; do not improvise it.

### Smart TVs and streaming boxes

Two sub-paths:

- **ADB-capable** (Android TV, Fire TV): same `adb` env provider -
  `input keyevent` navigation, screencap, package manager for debloat
  (the reel's TV-ad-removal case is largely `pm disable/uninstall` plus
  a custom launcher, all reachable via the existing backend).
- **Vendor API** (Tizen, webOS, Roku ECP): HTTP/WebSocket remote APIs;
  each needs a thin client extension like `busybar/push.py`. Roku ECP
  and webOS SSAP are documented, unauthenticated-or-pairing LAN APIs.

### Router / network gear

Config via admin UI is GUI-automation territory with high blast radius;
prefer SSH/CLI where the device offers it, or export-edit-import of
config files. Never auto-apply firmware or firewall changes without the
confirmation gate below.

### Hardware bridges and firmware (Kindle, drones, ESP, Flipper)

Out of lane scope for now: irreversible flashing, jailbreaks, and
firmware writes are per-project work with their own risk review. The
lane doc only claims network-API and ADB classes.

## Safety boundaries

Physical-world actions can be irreversible; the lane adopts the
system-control contract:

1. **Fresh confirmation per mutation.** Any call that changes device
   state (push to display is exempt by being advisory and reversible;
   `pm uninstall`, router config write, TV factory reset are not)
   requires a per-call user confirmation - never self-minted, never
   replayed.
2. **Deny-by-default list.** Factory reset, firmware flash, bootloader
   unlock, credential read on the device, and unknown capabilities
   always deny.
3. **No auth workarounds.** ADB attach is authorized by the env spec
   file; pairing prompts, ADB-authorize dialogs, and PIN entry are
   user-performed, never automated around.
4. **Untrusted device output.** `adb shell` output, API responses, and
   screencaps are data, not instructions.
5. **Advisory failure posture.** Device clients exit non-blocking on
   unreachable hardware (busybar pattern); they never silently retry
   into a changed-state window.
6. **Lease identity.** Physical devices are identified by serial +
   topology (`cu_devices.py`), never by port or VID/PID class.

## Phased adoption plan

- **Phase 0 (done).** Lane doc (this file); busybar push client; ADB
  env provider in computer-use.
- **Phase 1.** Wire `focus.py` start/stop to `busybar/push.py` in the
  session hooks; write the missing
  `.devin/evals/busybar-integration/README.md` spec it references;
  hardware-blocked live test documented when a device is available.
- **Phase 2.** Android-TV profile: env preset + keyevent navigation map
  + debloat runbook with confirmation gates; phone-env smoke test
  matrix (screencap, hint, tap, shell).
- **Phase 3.** One vendor TV API client (Roku ECP or webOS SSAP) as a
  second extension after busybar - reuse the push.py stdlib-client
  pattern and advisory-failure rule.
- **Phase 4.** Reassess: router SSH client, iOS bridge, hardware/firmware
  class - each gated on a concrete user need and its own risk note.

## Sources

- `.devin/scratch/yt-batch2/transcripts/KDyPHt4lW60.log`
- `.devin/scratch/reels-7/transcripts/DfXwuL0izsO.txt`
- `.devin/research/2026-11-10-reels-batch7-survey.md` rows 4, 15, R7-17,
  R7-18
- `extensions/computer-use/cu_adb_backend.py`, `cu_devices.py`,
  `USAGE.md` (adb env section)
- `extensions/busybar/push.py` (BUSY Bar HTTP API:
  https://docs.busy.app/bar/dev/http-api; busylib-py:
  https://github.com/busy-app/busylib-py)
- `extensions/system-control/`, `skills/system-control/SKILL.md`
  (confirmation/deny contract)
- `scripts/focus.py`
