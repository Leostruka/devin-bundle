#!/usr/bin/env python3
"""gcal: Google Calendar free/busy reader + event writer + .ics dev input.

Reads use `calendar.readonly`; writes (events.insert) require the
refresh token to carry `calendar.events` scope - doctor reports config
presence, scope failures surface as API errors. All writes go through
the wrapper's --confirm gate (real-world side effect).

Credential contract:
  - Env: BUNDLE_GCAL_CLIENT_ID, BUNDLE_GCAL_CLIENT_SECRET,
    BUNDLE_GCAL_REFRESH_TOKEN.
  - Or [gcal] section in %APPDATA%/devin/credentials.toml
    (~/.config/devin/credentials.toml on POSIX).
  - Secrets are never printed; absence -> status "missing", never fake.
  - --ics <file> works fully offline for dev/tests.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    import tomllib
except ImportError:  # python < 3.11
    tomllib = None

TOKEN_URL = "https://oauth2.googleapis.com/token"
EVENTS_URL = ("https://www.googleapis.com/calendar/v3/calendars/"
              "{calendar_id}/events")
CAL_LIST_URL = ("https://www.googleapis.com/calendar/v3/users/me/"
                "calendarList")
CAL_CREATE_URL = "https://www.googleapis.com/calendar/v3/calendars"
AGENT_CALENDAR = "AGdevin"
HTTP_TIMEOUT = 30


def _creds_paths():
    paths = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        paths.append(os.path.join(appdata, "devin", "credentials.toml"))
    paths.append(os.path.expanduser(
        os.path.join("~", ".config", "devin", "credentials.toml")))
    return paths


def load_credentials():
    """Return {client_id, client_secret, refresh_token} or None."""
    cid = os.environ.get("BUNDLE_GCAL_CLIENT_ID")
    sec = os.environ.get("BUNDLE_GCAL_CLIENT_SECRET")
    ref = os.environ.get("BUNDLE_GCAL_REFRESH_TOKEN")
    if cid and sec and ref:
        return {"client_id": cid, "client_secret": sec,
                "refresh_token": ref}
    if tomllib is None:
        return None
    for p in _creds_paths():
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                data = tomllib.loads(fh.read())
        except (OSError, ValueError):
            continue
        g = data.get("gcal", {})
        if g.get("client_id") and g.get("client_secret") \
                and g.get("refresh_token"):
            return {"client_id": g["client_id"],
                    "client_secret": g["client_secret"],
                    "refresh_token": g["refresh_token"]}
    return None


def _post_json(url, payload, headers=None, timeout=HTTP_TIMEOUT):
    body = json.dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=hdrs,
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url, headers=None, timeout=HTTP_TIMEOUT):
    req = urllib.request.Request(url, headers=headers or {},
                                 method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def access_token(creds):
    """Exchange refresh_token for an access token. Raises on failure."""
    data = _post_json(TOKEN_URL, {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    })
    return data["access_token"]


def free_busy(token, calendars, tmin, tmax):
    """-> {"busy": [{start,end}], "all_day": [{summary,start}]}.

    events.list per calendar (timed events only block slots; all-day
    events are informational - reminders/holidays must not zero out a
    planning day). Transparent + cancelled events excluded."""
    busy, all_day = [], []
    for cal in calendars:
        page_token = None
        for _ in range(5):  # pagination cap
            params = {
                "timeMin": tmin, "timeMax": tmax,
                "singleEvents": "true", "orderBy": "startTime",
                "maxResults": 250,
            }
            if page_token:
                params["pageToken"] = page_token
            url = ("https://www.googleapis.com/calendar/v3/calendars/"
                   + urllib.parse.quote(cal, safe="") + "/events?"
                   + urllib.parse.urlencode(params))
            data = _get_json(url,
                             headers={"Authorization": "Bearer " + token})
            for e in data.get("items", []):
                if e.get("status") == "cancelled" \
                        or e.get("transparency") == "transparent":
                    continue
                start, end = e.get("start", {}), e.get("end", {})
                if "dateTime" in start and "dateTime" in end:
                    busy.append({"start": start["dateTime"],
                                 "end": end["dateTime"]})
                elif "date" in start:
                    all_day.append({"summary": e.get("summary"),
                                    "start": start["date"]})
            page_token = data.get("nextPageToken")
            if not page_token:
                break
    return {"busy": busy, "all_day": all_day}


def _parse_dt(s):
    """ISO-8601 -> aware datetime (Z or offset; naive treated as UTC)."""
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def event_payload(summary, start, end, description=None, location=None,
                  tz=None):
    """Build a Calendar events.insert body. start/end are ISO-8601."""
    body = {
        "summary": summary,
        "start": {"dateTime": _parse_dt(start).isoformat()},
        "end": {"dateTime": _parse_dt(end).isoformat()},
    }
    if tz:
        body["start"]["timeZone"] = tz
        body["end"]["timeZone"] = tz
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    return body


def create_event(token, calendar_id, payload):
    """events.insert -> created event {id, htmlLink, status}. Raises."""
    url = EVENTS_URL.format(calendar_id=calendar_id)
    data = _post_json(url, payload,
                      headers={"Authorization": "Bearer " + token})
    return {"id": data.get("id"), "htmlLink": data.get("htmlLink"),
            "status": data.get("status", "confirmed")}


def list_calendars(token):
    """calendarList -> [{id, summary, primary}]."""
    data = _get_json(CAL_LIST_URL,
                     headers={"Authorization": "Bearer " + token})
    return [{"id": c.get("id"), "summary": c.get("summary"),
             "primary": bool(c.get("primary"))}
            for c in data.get("items", [])]


def find_calendar(token, name):
    """Return calendar id whose summary matches name, else None."""
    for c in list_calendars(token):
        if c["summary"] == name:
            return c["id"]
    return None


def create_calendar(token, name):
    """calendars.insert {summary} -> new calendar id."""
    data = _post_json(CAL_CREATE_URL, {"summary": name},
                      headers={"Authorization": "Bearer " + token})
    return data.get("id")


def ensure_calendar(token, name=AGENT_CALENDAR):
    """Find-or-create the agent calendar -> (id, created_bool)."""
    cid = find_calendar(token, name)
    if cid:
        return cid, False
    return create_calendar(token, name), True


def resolve_calendar(token, value):
    """Map a --calendar arg to an id: 'primary'/contains '@' -> id as-is,
    any other value is a summary name -> find-or-create."""
    if value in ("primary", None) or "@" in (value or ""):
        return value or "primary", False
    return ensure_calendar(token, value)


def free_slots(busy, tmin, tmax):
    """Sorted gaps between busy intervals inside [tmin, tmax]."""
    lo, hi = _parse_dt(tmin), _parse_dt(tmax)
    ivs = sorted((_parse_dt(b["start"]), _parse_dt(b["end"]))
                 for b in busy)
    out, cur = [], lo
    for s, e in ivs:
        if s > cur:
            out.append({"start": cur.isoformat(), "end": s.isoformat()})
        cur = max(cur, e)
    if cur < hi:
        out.append({"start": cur.isoformat(), "end": hi.isoformat()})
    return out


_ICS_DT = re.compile(
    r"^(?P<d>\d{8})(?:T(?P<t>\d{6})(?P<z>Z)?)?$")

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - py<3.9
    ZoneInfo = None
    ZoneInfoNotFoundError = KeyError

_tz_cache = {}


def _tz(name, warnings):
    if name in _tz_cache:
        return _tz_cache[name]
    try:
        tz = ZoneInfo(name) if ZoneInfo else None
        if tz is None:
            raise ZoneInfoNotFoundError(name)
    except Exception:
        warnings.append(f"TZID {name!r} unresolved; assumed UTC")
        tz = timezone.utc
    _tz_cache[name] = tz
    return tz


def _ics_dt(value, params, warnings):
    """Parse an ICS DATE/DATE-TIME property.

    params: raw ';'-separated parameter string (TZID=, VALUE=).
    Returns (all_day, dt) - all_day True for VALUE=DATE or bare
    YYYYMMDD; dt is an aware UTC datetime (floating times assumed UTC
    with a warning; TZID resolved via zoneinfo/tzdata when present).
    """
    m = _ICS_DT.match(value.strip())
    if not m:
        return False, None
    d, t, z = m.group("d"), m.group("t"), m.group("z")
    p = {}
    for seg in params.split(";"):
        k, _, v = seg.partition("=")
        if v:
            p[k.strip().upper()] = v.strip()
    if t is None or p.get("VALUE") == "DATE":
        return True, datetime.strptime(d, "%Y%m%d").replace(
            tzinfo=timezone.utc)
    dt = datetime.strptime(d + t, "%Y%m%d%H%M%S")
    if z:
        return False, dt.replace(tzinfo=timezone.utc)
    tzid = p.get("TZID")
    if tzid:
        return False, dt.replace(tzinfo=_tz(tzid, warnings)
                                 ).astimezone(timezone.utc)
    warnings.append("floating time (no Z/TZID) assumed UTC")
    return False, dt.replace(tzinfo=timezone.utc)


def _unfold(text):
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def ics_busy(text):
    """Parse VEVENTs from unfolded .ics text.

    Returns {"busy": [{start,end}], "all_day": [{summary,start,end}],
    "recurring": <RRULE count>, "warnings": [...]}.

    Semantics aligned with the api path (issue #397): all-day VEVENTs
    are informational, never full-day busy. TZID parameters convert via
    zoneinfo (#396). RRULE/EXDATE are NOT expanded (stdlib-only): each
    recurring VEVENT contributes only its DTSTART instance and is
    counted in "recurring" so callers can warn (#398).
    """
    busy, all_day, warnings = [], [], []
    recurring = 0
    cur = {}
    in_ev = False
    for line in _unfold(text):
        head, _, val = line.partition(":")
        parts = head.split(";")
        prop = parts[0].upper()
        params = ";".join(parts[1:])
        if prop == "BEGIN" and val.upper() == "VEVENT":
            in_ev, cur = True, {}
        elif prop == "END" and val.upper() == "VEVENT":
            if cur.get("transp") != "TRANSPARENT":
                if cur.get("all_day") and cur.get("start"):
                    end = cur.get("end") or (
                        cur["start"] + timedelta(days=1))
                    all_day.append({
                        "summary": cur.get("summary"),
                        "start": cur["start"].date().isoformat(),
                        "end": end.date().isoformat()})
                elif cur.get("start") and cur.get("end") \
                        and cur["end"] > cur["start"]:
                    busy.append({"start": cur["start"].isoformat(),
                                 "end": cur["end"].isoformat()})
            in_ev = False
        elif not in_ev:
            continue
        elif prop == "RRULE":
            recurring += 1
        elif prop == "TRANSP":
            cur["transp"] = val.upper()
        elif prop == "SUMMARY":
            cur["summary"] = val
        elif prop in ("DTSTART", "DTEND"):
            all_day_flag, dt = _ics_dt(val, params, warnings)
            if dt is not None:
                key = ("start" if prop == "DTSTART" else "end")
                cur[key] = dt
                if prop == "DTSTART":
                    cur["all_day"] = all_day_flag
    # de-duplicate identical floating-time warnings
    seen, uniq = set(), []
    for w in warnings:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return {"busy": busy, "all_day": all_day, "recurring": recurring,
            "warnings": uniq}
