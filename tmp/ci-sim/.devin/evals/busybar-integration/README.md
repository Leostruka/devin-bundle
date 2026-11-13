# Eval: focus.py -> Busy Bar status push (busylib)

Issue: #450. Status: spec + stdlib skeleton
(`extensions/busybar/push.py`). Hardware-blocked for live verification.

Source reel: instagram huwprosser/reel/DfXwuL0izsO
(`.devin/scratch/reels-7/transcripts/DfXwuL0izsO.txt`) -- unboxing /
brainstorm reel; hardware specs it lists (72x16 RGB front matrix,
mono OLED back, star/pause switch, scroll wheel, 5-position dial,
Wi-Fi 6, BT, USB-C, light sensor, speaker, replaceable 18650 battery,
built by Flipper Devices) are corroborated by official docs.

## What Busy Bar / busylib is (verified)

Busy Bar is a physical LED status display + Pomodoro timer by Busy
(built by Flipper Devices), sold at busy.app. It ships an open HTTP
API and official client libraries.

Verified from primary sources:

- Docs: https://docs.busy.app/bar/dev and
  https://docs.busy.app/bar/dev/http-api
- API surface: full device control -- display draw (text/images on
  both displays, brightness), audio upload/play, file/asset
  management, input simulation, real-time state over WebSocket.
- Connectivity and auth:

  | Connection | Base URL | Auth |
  |---|---|---|
  | USB | `http://10.0.4.20/api` | none |
  | Wi-Fi LAN | `http://<device-ip>/api` | required |
  | Internet | `https://api.busy.app/busybar` | Bearer token from https://cloud.busy.app/api-tokens |

- busylib-py: https://github.com/busy-app/busylib-py (MIT, PyPI
  `busylib`). `BusyBar("10.0.4.20")` context manager;
  `bb.display_draw(types.DisplayElements(application_name=...,
  elements=[types.TextElement(id=..., type="text", x=..., y=...,
  text=..., font="small", display=types.DisplayName.FRONT)]))`;
  `bb.display_clear(application_name=...)`.
- busylib-ts: https://github.com/busy-app/busylib-ts
  (`@busy-app/busy-lib`) -- `BusyBar` HTTP client, `StateStream`
  WebSocket state, `ScreenRenderer` WebGL2 preview.
- Displays: FRONT 72x16 RGB LED matrix (~16M colors); BACK 160x80
  mono OLED, 16 gray shades. Fonts: tiny, small, normal, condensed,
  bold, large, extra_large, global.
  Source: https://busy-app.github.io/busylib-py/guides/displays/

## Bundle integration contract

State emitter: `scripts/focus.py` -- pomodoro-style session tracker
writing append-only events to `.devin/ledgers/focus.jsonl`
(`{"event": "start"|"stop", "issue": ..., "effort": ..., "t": ...}`).

Mapping:

| focus state | Busy Bar display |
|---|---|
| `start` (open session) | front: `FOCUS <issue>` + elapsed mm:ss, red LED accent |
| `stop` (no open session) | clear app elements / front: `FREE` |
| open > effort budget | front: `WRAP UP` (optional phase) |

Push points (no changes to focus.py needed -- a watcher can poll the
ledger, or callers invoke push.py after `focus start|stop`):

1. `python extensions/busybar/push.py start --issue KEY` -- draw status.
2. `python extensions/busybar/push.py stop` -- clear.
3. `python extensions/busybar/push.py refresh` -- re-read ledger, update
   elapsed (call from `scripts/pulse.py` or a cron tick).

Device discovery: USB path is deterministic (`10.0.4.20` fixed,
no auth) -- preferred default. LAN needs the device's IP; discovery is
out of scope for the skeleton -- take `--addr` / `BUSYBAR_ADDR` env.
Cloud path needs `BUSYBAR_TOKEN`.

## Implementation sketch

`extensions/busybar/push.py` (landed, stdlib-only):

- POST `<addr>/api/display/draw` with
  `{"elements": {"application_name": "devin-focus", "elements":
  [{"id": "status", "type": "text", "x": 2, "y": 4, "text": "FOCUS #450",
  "font": "small", "display": "FRONT"}]}}`.
- POST `<addr>/api/display/clear` with
  `{"application_name": "devin-focus"}` on stop.
- Auth: none over USB; `Authorization: Bearer $BUSYBAR_TOKEN` when addr
  is the cloud proxy.
- Fails soft: unreachable device -> stderr note + exit 0 (status push
  is advisory, never blocks a session event).

Alternatively `pip install busylib` and use the typed client -- same
calls (`BusyBar(addr) as bb`, `bb.display_draw(...)`,
`bb.display_clear(application_name=...)`) with less hand-rolled JSON.
The stdlib skeleton avoids a dependency for what is two HTTP calls.

## Recommendation: SPEC + SKELETON (adopt-if-hardware)

The spec is verified real, the device API is genuinely open (USB path
needs no auth and no cloud account), and the integration surface is
tiny -- two endpoints. Skeleton landed; a `pip install busylib` variant
is documented above if richer use (audio cues, input reading,
WebSocket state stream) is ever wanted.

Hardware-blocked: no live test possible without the device. If a Busy
Bar is ever on the desk, wire `push.py refresh` into the pulse tick and
`start`/`stop` into the focus workflow; total remaining work <1h.
