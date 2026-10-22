#!/usr/bin/env python3
"""rtsd - RTS overlay daemon for the Devin bundle.

Local state daemon: ingests hook events, projects fleet/task/decision state
from .devin files plus an event-sourced v2 world (units/buildings/resources/
quests/map, world.py), serves snapshot+upserts over HTTP+WebSocket and the
web UI. A 2s tick recomputes time-derived state (heartbeat decay, idle,
minion TTL) and broadcasts deltas; replaying events.jsonl reproduces the
same world.

Endpoints (127.0.0.1 only):
  POST /event        append JSON event to .devin/rts/events.jsonl, broadcast
  GET  /snapshot     current projected state JSON
  GET  /health       {"ok": true}
  GET  /decisions    pending decisions list
  POST /decisions/<id>/answer  {"choice": ..., "text": ...} -> writes response file
  POST /intent       {"kind": "spawn|message|goal", ...} -> .devin/rts/intents/
  GET  /ws           WebSocket upgrade: hello -> snapshot, then upserts
  GET  /score        victory-screen aggregates (quests/gates/heroes/tokens)
  GET  /sessions     match history: every *.jsonl under .devin/rts + stats
  GET  /replay       replay status {total,index,playing,speed,done}
  POST /replay       playback control {action:play|pause|seek,index,speed}
  GET  /             web UI (web/index.html)

Replay mode: --replay <events.jsonl> rebuilds the session through the same
World.apply path; all mutating POSTs are denied (server-enforced) and only
/replay control is accepted. Spectator mode: --remote mints a second,
read-only token; connections presenting it get GETs but every POST is 403.

Stdlib only (bundle rule: no new deps). WS = minimal RFC 6455 implementation.
State root: <cwd>/.devin/rts/ unless --root is given.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as worldmod  # noqa: E402

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_PORT = 8797
TICK_S = 2.0
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def safe_name(s):
    return bool(SAFE_NAME.match(s or "")) and ".." not in s \
        and bool(str(s).lstrip("."))

STATE = {"root": None, "clients": [], "lock": threading.Lock(),
        # RLock: a permissionrequest append recursively appends its
        # decision.created event through the same locked path (#129)
        "write_lock": threading.RLock(), "token": None, "world": None,
        "spectator_token": None, "replay": None,
        "weather": None, "weather_ts": 0.0, "weather_mode": "live"}

_WMO_MAP = {
    0: ("clear", "Clear Sky"),
    1: ("clear", "Mainly Clear"),
    2: ("cloudy", "Partly Cloudy"),
    3: ("overcast", "Overcast"),
    45: ("fog", "Fog"),
    48: ("fog", "Rime Fog"),
    51: ("rain", "Light Drizzle"),
    53: ("rain", "Moderate Drizzle"),
    55: ("rain", "Dense Drizzle"),
    56: ("rain", "Freezing Drizzle"),
    57: ("rain", "Heavy Freezing Drizzle"),
    61: ("rain", "Slight Rain"),
    63: ("rain", "Moderate Rain"),
    65: ("rain", "Heavy Rain"),
    66: ("rain", "Freezing Rain"),
    67: ("rain", "Heavy Freezing Rain"),
    71: ("snow", "Slight Snow"),
    73: ("snow", "Moderate Snow"),
    75: ("snow", "Heavy Snow"),
    77: ("snow", "Snow Grains"),
    80: ("rain", "Rain Showers"),
    81: ("rain", "Heavy Showers"),
    82: ("storm", "Violent Showers"),
    85: ("snow", "Snow Showers"),
    86: ("snow", "Heavy Snow Showers"),
    95: ("storm", "Thunderstorm"),
    96: ("storm", "Thunderstorm + Hail"),
    99: ("storm", "Severe Thunderstorm"),
}

_WX_PRESETS = {
    "clear": {"condition": "clear", "label": "Clear Sky", "weather_code": 0,
              "cloud_pct": 10, "precip_mm": 0.0, "wind_kph": 12.0,
              "wind_gust_kph": 18.0, "wind_deg": 65},
    "overcast": {"condition": "overcast", "label": "Overcast",
                 "weather_code": 3, "cloud_pct": 95, "precip_mm": 0.0,
                 "wind_kph": 16.0, "wind_gust_kph": 28.0, "wind_deg": 75},
    "rain": {"condition": "rain", "label": "Moderate Rain",
             "weather_code": 63, "cloud_pct": 92, "precip_mm": 4.2,
             "wind_kph": 22.0, "wind_gust_kph": 38.0, "wind_deg": 110},
    "storm": {"condition": "storm", "label": "Thunderstorm",
              "weather_code": 95, "cloud_pct": 100, "precip_mm": 11.5,
              "wind_kph": 38.0, "wind_gust_kph": 64.0, "wind_deg": 135},
    "snow": {"condition": "snow", "label": "Moderate Snow",
             "weather_code": 73, "cloud_pct": 88, "precip_mm": 2.5,
             "wind_kph": 15.0, "wind_gust_kph": 26.0, "wind_deg": 200},
    "fog": {"condition": "fog", "label": "Dense Fog", "weather_code": 45,
            "cloud_pct": 85, "precip_mm": 0.0, "wind_kph": 6.0,
            "wind_gust_kph": 11.0, "wind_deg": 45},
    "windy": {"condition": "cloudy", "label": "Gale Winds",
              "weather_code": 2, "cloud_pct": 45, "precip_mm": 0.0,
              "wind_kph": 44.0, "wind_gust_kph": 72.0, "wind_deg": 80},
}


def _cardinal(deg):
    dirs = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
    return dirs[int(((float(deg or 0) + 11.25) % 360) / 22.5)]


def _http_get_json(url, timeout=2.5):
    req = urllib.request.Request(url, headers={"User-Agent": "rtsd/3.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def fetch_weather(force=False):
    """Fetch operator's local weather via IP geolocation + Open-Meteo (#157).
    Caches for 600s in memory and persists to .devin/rts/weather.json so
    offline sessions and unit tests never block or fail."""
    now = time.time()
    if not force and STATE.get("weather") and now - STATE["weather_ts"] < 600:
        return STATE["weather"]
    cache_path = os.path.join(state_dir(), "weather.json")
    cached = read_json(cache_path, None)
    if not force and cached and now - (cached.get("fetched_at") or 0) < 600:
        STATE["weather"] = cached
        STATE["weather_ts"] = cached.get("fetched_at", now)
        return cached
    city, region, country, lat, lon = "Curitiba", "Parana", "BR", -25.50, -49.29
    if cached:
        city = cached.get("city", city)
        region = cached.get("region", region)
        country = cached.get("country", country)
        lat = float(cached.get("lat", lat))
        lon = float(cached.get("lon", lon))
    if not os.environ.get("RTSD_NO_NET"):
        for gurl in ("https://get.geojs.io/v1/ip/geo.json",
                     "https://ipwho.is/"):
            try:
                g = _http_get_json(gurl, timeout=2.2)
                if g and g.get("latitude") is not None:
                    city = str(g.get("city") or city)
                    region = str(g.get("region") or region)
                    country = str(g.get("country_code") or g.get("country")
                                  or country)
                    lat = float(g["latitude"])
                    lon = float(g["longitude"])
                    break
            except Exception:
                continue
        try:
            murl = (
                "https://api.open-meteo.com/v1/forecast"
                "?latitude=%.4f&longitude=%.4f"
                "&current=temperature_2m,relative_humidity_2m,is_day,"
                "precipitation,rain,showers,snowfall,weather_code,"
                "cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
                "&hourly=temperature_2m,precipitation_probability,"
                "weather_code,wind_speed_10m&forecast_days=1&timezone=auto"
                % (lat, lon)
            )
            w = _http_get_json(murl, timeout=2.8)
            cur = (w or {}).get("current") or {}
            code = int(cur.get("weather_code", 0) or 0)
            cond, label = _WMO_MAP.get(code, ("cloudy", "Cloudy"))
            deg = float(cur.get("wind_direction_10m", 75) or 75)
            hr = (w or {}).get("hourly") or {}
            times = hr.get("time") or []
            temps = hr.get("temperature_2m") or []
            probs = hr.get("precipitation_probability") or []
            codes = hr.get("weather_code") or []
            winds = hr.get("wind_speed_10m") or []
            hourly = []
            for i in range(min(len(times), 24)):
                c_i = int(codes[i] if i < len(codes) else code)
                hourly.append({
                    "time": str(times[i])[-5:],
                    "temp_c": round(float(temps[i]), 1)
                    if i < len(temps) else 0.0,
                    "pop": int(probs[i]) if i < len(probs) else 0,
                    "condition": _WMO_MAP.get(c_i, ("cloudy", "Cloudy"))[0],
                    "wind_kph": round(float(winds[i]), 1)
                    if i < len(winds) else 0.0,
                })
            data = {
                "ok": True,
                "source": "open-meteo",
                "fetched_at": now,
                "city": city,
                "region": region,
                "country": country,
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "temp_c": round(float(cur.get("temperature_2m", 18.0)), 1),
                "humidity": int(cur.get("relative_humidity_2m", 70) or 70),
                "is_day": bool(cur.get("is_day", 1)),
                "weather_code": code,
                "condition": cond,
                "label": label,
                "cloud_pct": int(cur.get("cloud_cover", 40) or 40),
                "precip_mm": round(float(cur.get("precipitation", 0.0) or 0.0),
                                   2),
                "wind_kph": round(float(cur.get("wind_speed_10m", 12.0)
                                        or 12.0), 1),
                "wind_gust_kph": round(float(cur.get("wind_gusts_10m", 18.0)
                                             or 18.0), 1),
                "wind_deg": int(round(deg)),
                "wind_cardinal": _cardinal(deg),
                "hourly": hourly[:8],
            }
            STATE["weather"] = data
            STATE["weather_ts"] = now
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except OSError:
                pass
            return data
        except Exception:
            pass
    if cached:
        STATE["weather"] = cached
        STATE["weather_ts"] = now
        return cached
    fallback = {
        "ok": True, "source": "fallback", "fetched_at": now,
        "city": city, "region": region, "country": country,
        "lat": lat, "lon": lon, "temp_c": 18.0, "humidity": 72,
        "is_day": True, "weather_code": 2, "condition": "cloudy",
        "label": "Partly Cloudy", "cloud_pct": 45, "precip_mm": 0.0,
        "wind_kph": 14.0, "wind_gust_kph": 22.0, "wind_deg": 75,
        "wind_cardinal": "ENE", "hourly": [],
    }
    STATE["weather"] = fallback
    STATE["weather_ts"] = now
    return fallback


def weather_state(fetch_if_empty=False):
    base = STATE.get("weather")
    if base is None:
        if fetch_if_empty:
            base = fetch_weather()
        else:
            base = read_json(os.path.join(state_dir(), "weather.json"), None)
            if base:
                STATE["weather"] = base
                STATE["weather_ts"] = base.get("fetched_at", time.time())
            else:
                base = {
                    "ok": True, "source": "pending", "fetched_at": 0,
                    "city": "Local", "region": "", "country": "",
                    "lat": -25.50, "lon": -49.29, "temp_c": 18.0,
                    "humidity": 75, "is_day": True, "weather_code": 2,
                    "condition": "cloudy", "label": "Partly Cloudy",
                    "cloud_pct": 45, "precip_mm": 0.0, "wind_kph": 14.0,
                    "wind_gust_kph": 22.0, "wind_deg": 75,
                    "wind_cardinal": "ENE", "hourly": [],
                }
    out = dict(base)
    mode = STATE.get("weather_mode") or "live"
    out["mode"] = mode
    if mode in _WX_PRESETS:
        out.update(_WX_PRESETS[mode])
        out["wind_cardinal"] = _cardinal(out["wind_deg"])
    return out


def state_dir():
    d = os.path.join(STATE["root"], ".devin", "rts")
    for sub in ("", "decisions", "intents", "agents"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


def append_event(ev):
    if STATE["replay"] is not None:
        return  # replay mode: the log is immutable history, never append
    ev.setdefault("ts", time.time())
    path = os.path.join(state_dir(), "events.jsonl")
    with STATE["write_lock"]:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        project_fleet(ev)
        hint = line = None
        if STATE["world"] is not None:
            line = STATE["world"].apply(ev)
            hint = STATE["world"].event_hint(ev)
    broadcast({"type": "upsert", "event": ev, "hint": hint, "feed": line})
    if ev.get("type") == "hook.permissionrequest":
        _permission_decision(ev)


def _permission_decision(ev):
    """Project a PermissionRequest hook event into a real pending decision
    (#129): writes .devin/rts/decisions/<id>.json in the exact shape
    scripts/rts-decision.py --create produces (so --wait + the
    /decisions/<id>/answer endpoint resolve it, timeout -> last option =
    deny), then appends a decision.created event for feed/ping/upsert."""
    payload = ev.get("payload") or {}
    tool = ev.get("tool") or payload.get("tool_name") or "?"
    ti = payload.get("tool_input") or {}
    opts = payload.get("options") or payload.get("choices") \
        or ["allow", "deny"]
    if not isinstance(opts, list) or not opts:
        opts = ["allow", "deny"]
    opts = [str(o) for o in opts]
    summary = ti.get("command") or ti.get("file_path") \
        or ti.get("prompt") or json.dumps(ti, ensure_ascii=False)[:120]
    ddir = state_dir()
    base = int(ev.get("ts", time.time()) * 1000)
    n = 0
    while os.path.isfile(os.path.join(ddir, "decisions",
                                      "d%d.json" % (base + n))):
        n += 1  # same-ms requests stack, never silently merge
    did = "d%d" % (base + n)
    dpath = os.path.join(ddir, "decisions", did + ".json")
    d = {"id": did, "kind": "permission",
         "prompt": "%s: %s" % (tool, summary),
         "options": opts, "status": "pending",
         "created_at": ev.get("ts", time.time()),
         "timeout": payload.get("timeout", 120),
         "tool": str(tool),
         "requester": str(ev.get("session_id")
                          or ti.get("lane") or "")}
    with open(dpath, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    append_event({"type": "decision.created",
                  "payload": {"id": did, "kind": "permission",
                              "prompt": d["prompt"],
                              "options": opts,
                              "requester": d["requester"]}})


def _find_agent_id(resp):
    if isinstance(resp, dict):
        for k in ("agent_id", "id"):
            if k in resp:
                return str(resp[k])
        resp = json.dumps(resp)
    if isinstance(resp, str):
        m = re.search(r"agent_id[=:\s]+([0-9a-fA-F-]{6,})", resp)
        if m:
            return m.group(1)
    return None


def _resp_text(resp):
    if isinstance(resp, dict):
        resp = json.dumps(resp)
    return resp if isinstance(resp, str) else ""


def _default_model():
    cfg = read_json(os.path.join(STATE["root"], "data", "bundle-models.json"), {})
    return cfg.get("default_subagent_model", "swe-2-max")


def project_fleet(ev):
    """Project hook events into .devin/rts/fleet.json (single writer: rtsd)."""
    if ev.get("type") != "hook.posttooluse":
        return
    tool = ev.get("tool")
    payload = ev.get("payload") or {}
    ti = payload.get("tool_input") or {}
    resp = payload.get("tool_response", payload.get("result"))
    fleet_path = os.path.join(state_dir(), "fleet.json")
    fleet = read_json(fleet_path, {})
    changed = False
    if tool == "run_subagent":
        aid = _find_agent_id(resp) or "fg-%d" % int(ev["ts"] * 1000)
        running = bool(ti.get("is_background"))
        fleet[aid] = {
            "id": aid,
            "profile": ti.get("profile", "?"),
            "title": ti.get("title", ""),
            "task": (ti.get("task") or "")[:120],
            "model": _default_model(),
            "status": "running" if running else "done",
            "spawned_at": ev["ts"],
            "lane": ti.get("lane", ""),
        }
        changed = True
    elif tool == "read_subagent":
        aid = str(ti.get("agent_id", ""))
        if aid and aid in fleet:
            txt = _resp_text(resp)
            if "completed successfully" in txt or '"done"' in txt:
                fleet[aid]["status"] = "done"
            elif "failed" in txt.lower() or "error" in txt.lower():
                fleet[aid]["status"] = "failed"
            changed = True
    if changed:
        with open(fleet_path, "w", encoding="utf-8") as f:
            json.dump(fleet, f, ensure_ascii=False, indent=2)


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def scan_issues(root):
    return worldmod.scan_issues(root)


def scan_ledgers(root):
    """Parse .devin/ledgers/*.md into gate state lists.

    Checkbox convention: [x]=pass, [ ]=pending, [!]/[F]=fail.
    Indented CHECK/EXPECT/EVIDENCE lines attach to the last gate.
    """
    return worldmod.scan_ledgers(root)


def build_snapshot():
    root = STATE["root"]
    rts = state_dir()
    fleet = read_json(os.path.join(rts, "fleet.json"), {})
    decisions = []
    ddir = os.path.join(rts, "decisions")
    for fn in sorted(os.listdir(ddir)):
        d = read_json(os.path.join(ddir, fn), None)
        if d and d.get("status") == "pending":
            decisions.append(d)
    intents = []
    idir = os.path.join(rts, "intents")
    for fn in sorted(os.listdir(idir)):
        d = read_json(os.path.join(idir, fn), None)
        if d and d.get("status") == "pending":
            intents.append(d)
    agents = dict(fleet)
    adir = os.path.join(rts, "agents")
    for key in os.listdir(adir):
        hb = read_json(os.path.join(adir, key, "status.json"), None)
        if not hb:
            continue
        hb["dir"] = key
        if key in agents:
            agents[key]["heartbeat"] = hb
            continue
        # heartbeat keyed by contract/handle id: attach to the agent
        # whose dispatch text references it
        for a in agents.values():
            if key in (a.get("task") or "") or key in (a.get("title") or ""):
                a["heartbeat"] = hb
                break
    ledgers = scan_ledgers(root)
    ledger_ids = {l["id"] for l in ledgers}
    fail_ledgers = {l["id"] for l in ledgers
                    if any(g["state"] == "fail" for g in l["gates"])}
    tasks = scan_issues(root)
    for t in tasks:
        if t["effort"] in ledger_ids:
            t["ledger"] = t["effort"]
    for a in agents.values():
        if a.get("lane") in ledger_ids:
            a["ledger"] = a["lane"]
        if a.get("lane") in fail_ledgers:
            a["gate_fail"] = True
    snap = {
        "generated_at": time.time(),
        "agents": list(agents.values()),
        "tasks": tasks,
        "decisions": decisions,
        "intents": intents,
        "ledgers": ledgers,
    }
    if STATE["world"] is not None:
        snap["v"] = 2
        snap["world"] = STATE["world"].snapshot(snap["generated_at"])
    snap["weather"] = weather_state(fetch_if_empty=False)
    snap["mode"] = "replay" if STATE["replay"] is not None else "live"
    if STATE["replay"] is not None:
        snap["replay"] = replay_status()
    return snap


# --- #135 replay engine + match history ---------------------------------

def load_events(path):
    events = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return events


def replay_status():
    r = STATE["replay"]
    return {"path": r["path"], "total": len(r["events"]),
            "index": r["idx"], "playing": r["playing"],
            "speed": r["speed"],
            "done": r["idx"] >= len(r["events"])}


def replay_seek(idx):
    """Jump-to-event / scrub: deterministic rebuild via World.replay, then
    a full snapshot broadcast so every client resyncs at the new index."""
    r = STATE["replay"]
    idx = max(0, min(int(idx), len(r["events"])))
    with STATE["write_lock"]:
        STATE["world"] = worldmod.World.replay(
            STATE["root"], r["events"][:idx])
        r["idx"] = idx
        r["deadline"] = 0
    broadcast({"type": "snapshot", "snapshot": build_snapshot()})
    broadcast({"type": "replay", "replay": replay_status()})


def replay_control(body):
    r = STATE["replay"]
    if r is None:
        return None
    act = body.get("action")
    if act == "play":
        if r["idx"] >= len(r["events"]):
            replay_seek(0)                    # play at end = restart
        r["playing"] = True
        r["deadline"] = 0
    elif act == "pause":
        r["playing"] = False
    elif act == "seek":
        replay_seek(body.get("index") or 0)
    if "speed" in body:
        try:
            sp = float(body["speed"])
            if sp > 0:
                r["speed"] = sp
                r["deadline"] = 0
        except (TypeError, ValueError):
            pass
    broadcast({"type": "replay", "replay": replay_status()})
    return replay_status()


def replay_loop():
    """Applies recorded events on their original timeline scaled by
    speed (1x/2x/4x from the UI, any positive factor via API); each
    event goes through World.apply and broadcasts the same upsert a
    live event would. Inter-event gaps cap at 1s real time so sparse
    logs still play as a session, not a slideshow."""
    r = STATE["replay"]
    while True:
        time.sleep(0.02)
        if not r["playing"]:
            continue
        if r["idx"] >= len(r["events"]):
            r["playing"] = False
            broadcast({"type": "replay", "replay": replay_status()})
            # victory screen at end of tape
            broadcast({"type": "score",
                       "score": STATE["world"].score()})
            continue
        now = time.time()
        if now < (r.get("deadline") or 0):
            continue
        with STATE["write_lock"]:
            i = r["idx"]
            ev = r["events"][i]
            line = STATE["world"].apply(ev)
            hint = STATE["world"].event_hint(ev)
            r["idx"] = i + 1
        broadcast({"type": "upsert", "event": ev,
                   "hint": hint, "feed": line})
        if r["idx"] < len(r["events"]):
            nxt = r["events"][r["idx"]]
            dt = max(0.0, (nxt.get("ts") or 0) - (ev.get("ts") or 0))
            r["deadline"] = now + min(dt / max(r["speed"], 0.01), 1.0)
        else:
            r["deadline"] = 0


_SESS_CACHE = {}  # path -> (mtime, size, World, t0, t1, n_events)


def list_sessions():
    """Match history (#135): every event log under .devin/rts (the live
    events.jsonl plus archived copies, e.g. sessions/*.jsonl) replayed
    through World for its real per-session aggregates."""
    rts = os.path.join(STATE["root"], ".devin", "rts")
    out = []
    for dirpath, _dirs, files in os.walk(rts):
        for fn in sorted(files):
            if not fn.endswith(".jsonl"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
                key = (st.st_mtime_ns, st.st_size)
            except OSError:
                continue
            cached = _SESS_CACHE.get(p)
            if cached and cached[:2] == key:
                _, _, w, t0, t1, nev = cached
            else:
                evs = load_events(p)
                if not evs:
                    continue
                t0 = evs[0].get("ts") or 0
                t1 = evs[-1].get("ts") or t0
                w = worldmod.World.replay(STATE["root"], evs)
                nev = len(evs)
                _SESS_CACHE[p] = (key[0], key[1], w, t0, t1, nev)
            sc = w.score(now=t1)
            out.append({"id": os.path.relpath(p, rts),
                        "events": nev,
                        "started": t0, "ended": t1,
                        "duration_s": round(t1 - t0),
                        "agents": len(sc["heroes"]),
                        "quests_done": sc["quests_done"],
                        "quests_total": sc["quests_total"],
                        "gates_pass": sc["gates_pass"],
                        "gates_fail": sc["gates_fail"],
                        "tokens": sc["gold"],
                        "score": sc})
    out.sort(key=lambda s: s["started"])
    return out


_BADGE_MAP = {
    ".ts": "TS", ".tsx": "TS",
    ".js": "JS", ".jsx": "JS", ".mjs": "JS",
    ".css": "CSS", ".scss": "CSS", ".less": "CSS",
    ".json": "JSON", ".yaml": "JSON", ".yml": "JSON", ".toml": "JSON",
    ".md": "MD", ".mdx": "MD", ".txt": "MD",
    ".py": "PY",
    ".rs": "RS",
    ".go": "GO",
    ".sh": "SH", ".bash": "SH", ".zsh": "SH", ".ps1": "SH",
    ".html": "HTML", ".svg": "HTML",
    ".png": "IMG", ".jpg": "IMG", ".jpeg": "IMG", ".gif": "IMG", ".webp": "IMG",
}
_SKIP_WALK = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "target", "dist", "build", ".pytest_cache", ".mypy_cache"}


def list_project_files(root):
    """#172 File Explorer + @file autocomplete index."""
    files = []
    for base, dirs, fnames in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_WALK)
        for fn in sorted(fnames):
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            ext = os.path.splitext(fn)[1].lower()
            try:
                sz = os.path.getsize(p)
            except OSError:
                sz = 0
            files.append({
                "path": rel,
                "size": sz,
                "badge": _BADGE_MAP.get(ext, "FILE"),
            })
            if len(files) >= 500:
                break
        if len(files) >= 500:
            break
    return {"ok": True, "files": files}


def _git_run(root, args):
    try:
        r = subprocess.run(
            ["git"] + list(args), cwd=root,
            capture_output=True, text=True, timeout=3.0,
            encoding="utf-8", errors="replace")
        return r.returncode == 0, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return False, "", str(e)


def git_codex_state(root):
    """#172 Git Codex: status, worktrees, branches, stashes, commits."""
    ok_s, out_s, _ = _git_run(root, ["status", "--porcelain"])
    changes = []
    if ok_s:
        for line in out_s.splitlines():
            if len(line) < 4:
                continue
            xy = line[:2]
            rel = line[3:].strip().strip('"')
            if "->" in rel:
                rel = rel.split("->")[-1].strip()
            lbl = ("destroyed" if "D" in xy else
                   "newly scribed" if ("?" in xy or "A" in xy) else
                   "sealed" if xy[0] != " " and xy[1] == " " else
                   "altered")
            top = rel.split("/")[0] if "/" in rel else "."
            changes.append({"path": rel, "code": xy.strip(),
                            "label": lbl, "dir": top})
    ok_w, out_w, _ = _git_run(root, ["worktree", "list", "--porcelain"])
    worktrees = []
    if ok_w:
        cur = {}
        for line in out_w.splitlines():
            if not line.strip():
                if cur:
                    worktrees.append(cur)
                    cur = {}
            elif line.startswith("worktree "):
                cur["path"] = line[9:].strip()
            elif line.startswith("branch "):
                cur["branch"] = line[7:].strip().replace("refs/heads/", "")
            elif line.startswith("HEAD "):
                cur["head"] = line[5:].strip()[:8]
        if cur:
            worktrees.append(cur)
    ok_b, out_b, _ = _git_run(
        root, ["branch", "--format=%(refname:short)|%(HEAD)"])
    branches = []
    current_branch = ""
    if ok_b:
        for line in out_b.splitlines():
            if "|" in line:
                bname, head = line.split("|", 1)
                active = head.strip() == "*"
                if active:
                    current_branch = bname.strip()
                branches.append({"name": bname.strip(), "current": active})
    ok_st, out_st, _ = _git_run(root, ["stash", "list"])
    stashes = []
    if ok_st:
        for line in out_st.splitlines():
            if ":" in line:
                sid, desc = line.split(":", 1)
                stashes.append({"id": sid.strip(), "desc": desc.strip()})
    ok_lg, out_lg, _ = _git_run(
        root, ["log", "-n", "10", "--pretty=format:%h|%an|%ar|%s"])
    commits = []
    if ok_lg:
        for line in out_lg.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({"sha": parts[0], "author": parts[1],
                                "when": parts[2], "subject": parts[3]})
    return {
        "ok": True,
        "branch": current_branch,
        "changes": changes,
        "worktrees": worktrees,
        "branches": branches,
        "stashes": stashes,
        "commits": commits,
    }


def git_file_diff(root, rel_path):
    """#172 Safe per-file diff or file preview (confined to root)."""
    if not rel_path or ".." in rel_path.replace("\\", "/").split("/"):
        return {"error": "bad path"}
    ap = os.path.abspath(os.path.join(root, rel_path))
    rroot = os.path.abspath(root)
    if not ap.startswith(rroot + os.sep) and ap != rroot:
        return {"error": "path outside root"}
    ok, diff_out, _ = _git_run(root, ["diff", "HEAD", "--", rel_path])
    if ok and diff_out.strip():
        return {"ok": True, "path": rel_path, "diff": diff_out[:12000]}
    if os.path.isfile(ap):
        try:
            with open(ap, encoding="utf-8", errors="replace") as f:
                txt = f.read(8000)
            return {"ok": True, "path": rel_path, "diff": txt, "preview": True}
        except OSError:
            pass
    return {"ok": True, "path": rel_path, "diff": "(no changes)"}


def git_action(root, body):
    """#172 Safe Stash Manager actions (stash_push/apply/pop/drop)."""
    act = str(body.get("action") or "")
    ref = str(body.get("ref") or "stash@{0}")
    if not re.match(r"^stash@\{\d+\}$", ref):
        ref = "stash@{0}"
    if act == "stash_push":
        msg = re.sub(r"[^\w\s._-]", "", str(body.get("message") or "rtsd"))[:60]
        cmd = ["stash", "push", "-m", msg or "rtsd"]
        if body.get("untracked"):
            cmd.insert(2, "-u")
        ok, out, err = _git_run(root, cmd)
    elif act in ("stash_apply", "stash_pop", "stash_drop"):
        sub = act.split("_")[1]
        ok, out, err = _git_run(root, ["stash", sub, ref])
    else:
        return {"error": "bad git action"}
    return {"ok": ok, "output": (out or err).strip()[:400],
            "git": git_codex_state(root)}


def _loops_file():
    return os.path.join(state_dir(), "loops.json")


def loops_state():
    """#178 Scheduled Loops (Active Loops panel)."""
    items = read_json(_loops_file(), [])
    return {"ok": True, "loops": items if isinstance(items, list) else []}


def loops_action(body):
    """#178 Create, trigger, or stop a recurring agent loop."""
    act = str(body.get("action") or "create")
    items = loops_state()["loops"]
    if act == "create":
        lid = "loop-%d" % int(time.time() * 1000)
        lp = {
            "id": lid,
            "hero": str(body.get("hero") or "all"),
            "interval_m": int(body.get("interval_m") or 5),
            "prompt": str(body.get("prompt") or "Run status check")[:240],
            "iterations": 0,
            "active": True,
            "created_at": time.time(),
        }
        items.append(lp)
    elif act == "trigger":
        lid = str(body.get("id") or "")
        for lp in items:
            if lp.get("id") == lid:
                lp["iterations"] = int(lp.get("iterations") or 0) + 1
                lp["last_run"] = time.time()
                iid = "i%d" % int(time.time() * 1000)
                it = {"id": iid, "kind": "goal",
                      "text": "[Loop %s #%d] %s" % (
                          lid, lp["iterations"], lp.get("prompt", "")),
                      "status": "pending"}
                p = os.path.join(state_dir(), "intents", iid + ".json")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(it, f, ensure_ascii=False, indent=2)
                append_event({"type": "intent.created", "intent": it})
                break
    elif act == "stop":
        lid = str(body.get("id") or "")
        items = [lp for lp in items if lp.get("id") != lid]
    else:
        return {"error": "bad loop action"}
    with open(_loops_file(), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"ok": True, "loops": items}


def terminal_exec(root, body):
    """#178 Integrated Terminal command execution (loopback admin only)."""
    cmd = str(body.get("cmd") or "").strip()
    if not cmd:
        return {"error": "empty command"}
    try:
        r = subprocess.run(
            cmd, cwd=root, shell=True,
            capture_output=True, text=True, timeout=5.0,
            encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        return {"ok": True, "code": r.returncode,
                "output": out[:8000] or "(exit %d)" % r.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": 124, "output": "(timeout after 5s)"}
    except Exception as e:
        return {"ok": False, "code": 1, "output": str(e)}


# --- minimal WebSocket (RFC 6455, text frames only) ---

def ws_accept(key):
    return base64.b64encode(
        hashlib.sha1((key + WS_GUID).encode()).digest()).decode()


def ws_send(sock, payload):
    data = payload.encode() if isinstance(payload, str) else payload
    n = len(data)
    if n < 126:
        head = struct.pack("!BB", 0x81, n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x81, 126, n)
    else:
        head = struct.pack("!BBQ", 0x81, 127, n)
    sock.sendall(head + data)


def ws_recv(sock):
    def read(n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf
    head = read(2)
    if not head:
        return None
    op = head[0] & 0x0F
    ln = head[1] & 0x7F
    if ln == 126:
        ln = struct.unpack("!H", read(2))[0]
    elif ln == 127:
        ln = struct.unpack("!Q", read(8))[0]
    mask = read(4) if head[1] & 0x80 else None
    data = read(ln) if ln else b""
    if data is None:
        return None
    if mask:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return op, data


def broadcast(msg):
    payload = json.dumps(msg, ensure_ascii=False)
    with STATE["lock"]:
        dead = []
        for c in STATE["clients"]:
            try:
                ws_send(c, payload)
            except OSError:
                dead.append(c)
        for c in dead:
            STATE["clients"].remove(c)


class Handler(BaseHTTPRequestHandler):
    server_version = "rtsd/0.1"

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        ln = int(self.headers.get("Content-Length") or 0)
        if not ln:
            return {}
        try:
            return json.loads(self.rfile.read(ln))
        except Exception:
            return {}

    def _static(self, name):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "web")
        p = os.path.normpath(os.path.join(base, name))
        if not (p + os.sep).startswith(base + os.sep) and p != base:
            return None
        if not os.path.isfile(p):
            return None
        with open(p, "rb") as f:
            return f.read()

    _CTYPES = {".html": "text/html; charset=utf-8",
               ".js": "text/javascript; charset=utf-8",
               ".css": "text/css; charset=utf-8",
               ".json": "application/json; charset=utf-8",
               ".webmanifest": "application/manifest+json",
               ".png": "image/png", ".svg": "image/svg+xml",
               ".ico": "image/x-icon"}

    def _auth(self):
        """Non-loopback clients need the session token (query/header).
        Presenting the spectator token (from any client, loopback too)
        marks the connection read-only (#135); role lands on
        self._role for the POST gate and the snapshot's client_role."""
        ip = self.client_address[0]
        self._role = "admin"
        q = urllib.parse.parse_qs(
            urllib.parse.urlsplit(self.path).query)
        tok = (q.get("token", [None])[0]
               or self.headers.get("X-RTS-Token")
               or (self.headers.get("Authorization", "")
                   .removeprefix("Bearer ") or None))
        if tok and STATE["spectator_token"] and \
                secrets.compare_digest(tok, STATE["spectator_token"]):
            self._role = "spectator"
            if STATE["replay"] is None:
                append_event({"type": "auth.allow", "ip": ip,
                              "role": "spectator", "ts": time.time()})
            return True
        if ip in ("127.0.0.1", "::1", "localhost") or not STATE["token"]:
            return True
        if tok and secrets.compare_digest(tok, STATE["token"]):
            append_event({"type": "auth.allow", "ip": ip, "ts": time.time()})
            return True
        if STATE["replay"] is None:
            append_event({"type": "auth.deny", "ip": ip,
                          "path": self.path.split("?")[0],
                          "ts": time.time()})
        self._json(401, {"error": "auth required"})
        return False

    def do_GET(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]
        if path == "/ws" and "upgrade" in self.headers.get("Connection", "").lower():
            return self._ws()
        if path == "/health":
            return self._json(200, {"ok": True})
        if path == "/snapshot":
            snap = build_snapshot()
            snap["client_role"] = getattr(self, "_role", "admin")
            return self._json(200, snap)
        if path == "/score" and STATE.get("world") is not None:
            return self._json(200, STATE["world"].score())
        if path == "/sessions":
            return self._json(200, list_sessions())
        if path == "/weather":
            return self._json(200, weather_state(fetch_if_empty=True))
        if path == "/files":
            return self._json(200, list_project_files(STATE["root"]))
        if path == "/git":
            return self._json(200, git_codex_state(STATE["root"]))
        if path == "/loops":
            return self._json(200, loops_state())
        if path == "/trophies":
            tdir = os.path.join(state_dir(), "trophies")
            out = []
            if os.path.isdir(tdir):
                for fn in sorted(os.listdir(tdir)):
                    if fn.endswith(".md"):
                        aid = fn[:-3]
                        first = ""
                        try:
                            with open(os.path.join(tdir, fn),
                                      encoding="utf-8") as fh:
                                first = fh.readline().lstrip("# ").strip()
                        except OSError:
                            pass
                        out.append({"id": aid, "title": first,
                                    "svg": "/trophies/" + aid + ".svg"})
            mb2 = re.match(r"^/trophies$", path)
            return self._json(200, {"trophies": out})
        mb_t = re.match(r"^/trophies/([A-Za-z0-9_-]+\.svg)$", path)
        if mb_t:
            fp = os.path.join(state_dir(), "trophies", mb_t.group(1))
            if not os.path.isfile(fp):
                return self._json(404, {"error": "trophy not found"})
            try:
                with open(fp, "rb") as fh:
                    data = fh.read()
            except OSError:
                return self._json(404, {"error": "trophy unreadable"})
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/git/diff":
            q = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            rel = (q.get("path") or [""])[0]
            res = git_file_diff(STATE["root"], rel)
            return self._json(400 if res.get("error") else 200, res)
        if path == "/replay":
            if STATE["replay"] is None:
                return self._json(404, {"error": "not in replay mode"})
            return self._json(200, replay_status())
        if path == "/decisions":
            return self._json(200, build_snapshot()["decisions"])
        mb = re.match(r"^/buildings/([A-Za-z0-9_-]+)$", path)
        if mb and STATE.get("world") is not None:
            rts = state_dir()
            intents = [read_json(os.path.join(rts, "intents", fn), None)
                       for fn in os.listdir(os.path.join(rts, "intents"))]
            intents = [i for i in intents if i]
            decs = sum(1 for fn in os.listdir(
                os.path.join(rts, "decisions"))
                if (read_json(os.path.join(rts, "decisions", fn), {})
                    or {}).get("status") == "pending")
            det = STATE["world"].building_detail(
                mb.group(1), time.time(),
                {"intents": intents, "remote": STATE.get("remote"),
                 "decisions_pending": decs})
            if det is None:
                return self._json(404, {"error": "unknown building"})
            return self._json(200, det)
        name = "index.html" if path in ("/", "/index.html") else \
            path.lstrip("/")
        body = self._static(name)
        if body is not None:
            ext = os.path.splitext(name)[1].lower()
            ctype = self._CTYPES.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]
        # #135 fail-closed roles: spectators are read-only everywhere;
        # a replay daemon accepts only playback control, never new
        # events/intents/answers (the log is already immutable history)
        if getattr(self, "_role", "admin") == "spectator":
            return self._json(403, {"error": "spectator read-only"})
        if STATE["replay"] is not None:
            if path == "/replay":
                st = replay_control(self._body())
                if st is None:
                    return self._json(404, {"error": "not in replay mode"})
                return self._json(200, st)
            return self._json(403, {"error": "replay mode is read-only"})
        if path == "/event":
            ev = self._body()
            if not isinstance(ev, dict) or not ev:
                return self._json(400, {"error": "bad event"})
            append_event(ev)
            return self._json(200, {"ok": True})
        if path == "/weather":
            body = self._body() or {}
            mode = str(body.get("mode") or "live").lower()
            if mode not in ("live",) and mode not in _WX_PRESETS:
                return self._json(400, {"error": "bad weather mode"})
            STATE["weather_mode"] = mode
            if body.get("refresh"):
                fetch_weather(force=True)
            wx = weather_state(fetch_if_empty=True)
            broadcast({"type": "weather", "weather": wx})
            return self._json(200, wx)
        if path == "/git":
            res = git_action(STATE["root"], self._body() or {})
            return self._json(400 if res.get("error") else 200, res)
        if path == "/loops":
            res = loops_action(self._body() or {})
            return self._json(400 if res.get("error") else 200, res)
        if path == "/terminal":
            res = terminal_exec(STATE["root"], self._body() or {})
            return self._json(400 if res.get("error") else 200, res)
        if path == "/intent":
            it = self._body()
            kind = it.get("kind")
            if kind not in ("spawn", "message", "goal", "answer",
                            "order"):
                return self._json(400, {"error": "bad intent kind"})
            iid = str(it.setdefault("id", "i%d" % int(time.time() * 1000)))
            if not safe_name(iid):
                return self._json(400, {"error": "bad intent id"})
            it["status"] = "pending"
            p = os.path.join(state_dir(), "intents", iid + ".json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(it, f, ensure_ascii=False, indent=2)
            append_event({"type": "intent.created", "intent": it})
            return self._json(200, {"ok": True})
        m = re.match(r"^/decisions/([A-Za-z0-9_.-]+)/answer$", path)
        if m:
            dfile = os.path.join(state_dir(), "decisions", m.group(1) + ".json")
            d = read_json(dfile, None)
            if not d:
                return self._json(404, {"error": "unknown decision"})
            if d.get("status") == "answered":
                return self._json(409, {"error": "already answered"})
            ans = self._body()
            opts = d.get("options", [])
            choice = ans.get("choice")
            if opts and (not isinstance(choice, int)
                         or not 0 <= choice < len(opts)):
                return self._json(400, {"error": "choice out of range"})
            d["status"] = "answered"
            d["answer"] = ans
            d["answered_at"] = time.time()
            with open(dfile, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            with open(dfile + ".response", "w", encoding="utf-8") as f:
                json.dump(ans, f, ensure_ascii=False)
            append_event({"type": "decision.answered", "id": m.group(1)})
            return self._json(200, {"ok": True})
        self._json(404, {"error": "not found"})

    def _ws(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            return self._json(400, {"error": "no ws key"})
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", ws_accept(key))
        self.end_headers()
        sock = self.request
        sock.settimeout(60)
        with STATE["lock"]:
            STATE["clients"].append(sock)
        try:
            snap = build_snapshot()
            snap["client_role"] = getattr(self, "_role", "admin")
            ws_send(sock, json.dumps(
                {"type": "snapshot", "snapshot": snap},
                ensure_ascii=False))
            while True:
                try:
                    frame = ws_recv(sock)
                except (OSError, socket.timeout):
                    frame = None
                if frame is None:
                    break
                op, data = frame
                if op == 8:
                    break
                if op == 9:
                    try:
                        pong = struct.pack("!BB", 0x8A, len(data)) + data
                        sock.sendall(pong)
                    except OSError:
                        break
        finally:
            with STATE["lock"]:
                if sock in STATE["clients"]:
                    STATE["clients"].remove(sock)
        self.close_connection = True


class RtsServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR allows stealing a live listener; forbid it so a
    # second rtsd on the same port fails loudly instead of splitting traffic.
    allow_reuse_address = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--remote", type=float, default=0, metavar="MIN",
                    help="open a LAN listener on port+1 for MIN minutes "
                         "with a per-session token, then deny-safe close")
    ap.add_argument("--replay", metavar="EVENTS.JSONL",
                    help="replay a recorded session: deterministic rebuild "
                         "with play/pause/seek/speed controls over "
                         "GET+POST /replay; all other POSTs are denied")
    args = ap.parse_args()
    STATE["root"] = os.path.abspath(args.root)
    state_dir()
    if args.replay:
        events = load_events(os.path.abspath(args.replay))
        STATE["replay"] = {"path": os.path.abspath(args.replay),
                           "events": events, "idx": 0, "playing": False,
                           "speed": 1.0, "deadline": 0}
        STATE["world"] = worldmod.World(STATE["root"])
        threading.Thread(target=replay_loop, daemon=True).start()
    else:
        STATE["world"] = worldmod.World.replay_file(
            STATE["root"], os.path.join(state_dir(), "events.jsonl"))
    srv = RtsServer(("127.0.0.1", args.port), Handler)
    srv.daemon_threads = True
    print("rtsd on http://127.0.0.1:%d (root=%s%s)"
          % (args.port, STATE["root"],
             ", replay=%s" % args.replay if args.replay else ""))
    if args.remote > 0:
        STATE["token"] = secrets.token_urlsafe(16)
        STATE["spectator_token"] = secrets.token_urlsafe(16)
        rport = args.port + 1
        rsrv = RtsServer(("0.0.0.0", rport), Handler)
        rsrv.daemon_threads = True
        ttl = args.remote * 60
        STATE["remote"] = {"port": rport, "ttl_s": int(ttl),
                           "opened_at": time.time(),
                           "token": bool(STATE["token"]),
                           "spectator": bool(STATE["spectator_token"])}
        # operator-side copy of the share URLs (never served to clients)
        with open(os.path.join(state_dir(), "remote.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"port": rport, "token": STATE["token"],
                       "spectator_token": STATE["spectator_token"],
                       "expires_at": time.time() + ttl}, f, indent=2)

        def remote_serve():
            t = threading.Thread(target=rsrv.serve_forever, daemon=True)
            t.start()
            append_event({"type": "remote.open", "port": rport,
                          "ttl_s": ttl, "ts": time.time()})
            time.sleep(ttl)
            rsrv.shutdown()
            rsrv.server_close()
            STATE["token"] = None
            STATE["spectator_token"] = None
            try:
                os.remove(os.path.join(state_dir(), "remote.json"))
            except OSError:
                pass
            append_event({"type": "remote.expired", "port": rport,
                          "ts": time.time()})

        threading.Thread(target=remote_serve, daemon=True).start()
        print("remote: http://<lan-ip>:%d/?token=%s (ttl %ds)"
              % (rport, STATE["token"], int(ttl)))
        print("remote spectator (read-only): "
              "http://<lan-ip>:%d/?token=%s"
              % (rport, STATE["spectator_token"]))

    def poll_comms():
        """Turn out-of-band surfaces into real events (#128): new
        .devin/mailboxes/*/inbox/msg-*.json files -> mail.deposit (raven),
        changed agent status.json `note` -> agent.note (status report).
        Dedup keys live in the world (mail_seen/notes), so replay of
        events.jsonl keeps them quiet."""
        w = STATE["world"]
        root = STATE["root"]
        mroot = os.path.join(root, ".devin", "mailboxes")
        if os.path.isdir(mroot):
            for to in sorted(os.listdir(mroot)):
                ib = os.path.join(mroot, to, "inbox")
                if not os.path.isdir(ib):
                    continue
                for fn in sorted(os.listdir(ib)):
                    if not fn.endswith(".json"):
                        continue
                    d = read_json(os.path.join(ib, fn), None)
                    if not d or not d.get("id") \
                            or d["id"] in w.mail_seen:
                        continue
                    append_event({"type": "mail.deposit", "mail": {
                        "id": str(d["id"]),
                        "from": str(d.get("from") or "?"),
                        "to": str(d.get("to") or to),
                        "kind": str(d.get("type") or "task"),
                        "preview": str(d.get("content") or "")[:80]}})
        # pending decision files created out-of-band (rts-decision.py
        # --create, agents) ring the council bell exactly once (#129);
        # w.dec_seen is event-sourced so replay stays quiet
        ddir = os.path.join(root, ".devin", "rts", "decisions")
        if os.path.isdir(ddir):
            for fn in sorted(os.listdir(ddir)):
                if not fn.endswith(".json"):
                    continue
                d = read_json(os.path.join(ddir, fn), None)
                if not d or d.get("status") != "pending":
                    continue
                did = str(d.get("id") or fn[:-5])
                if did in w.dec_seen:
                    continue
                append_event({"type": "decision.created", "payload": {
                    "id": did, "kind": str(d.get("kind") or "decision"),
                    "prompt": str(d.get("prompt") or "")[:120],
                    "options": d.get("options") or [],
                    "requester": str(d.get("requester") or "")}})
        adir = os.path.join(root, ".devin", "rts", "agents")
        if os.path.isdir(adir):
            for key in sorted(os.listdir(adir)):
                hb = read_json(os.path.join(adir, key, "status.json"),
                               None)
                if not hb:
                    continue
                note = hb.get("note")
                if note and w.notes.get(key) != note:
                    append_event({"type": "agent.note", "agent": key,
                                  "note": str(note)[:120]})

    def tick_loop():
        while True:
            time.sleep(TICK_S)
            try:
                if STATE["replay"] is None:
                    poll_comms()      # live only: replay world is sealed
                deltas = STATE["world"].tick(time.time())
                if deltas:
                    broadcast({"type": "tick", "ts": time.time(),
                               "deltas": deltas})
            except Exception:
                pass  # fail-open: a bad tick never kills the daemon

    threading.Thread(target=lambda: fetch_weather(force=False),
                     daemon=True).start()
    threading.Thread(target=tick_loop, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
