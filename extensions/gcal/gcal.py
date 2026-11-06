#!/usr/bin/env python3
"""gcal: Google Calendar free/busy reader + local .ics dev input.

Read-only by design (issue #345): `calendar.readonly` scope equivalent -
the extension only fetches free/busy, never writes events.

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
import urllib.request
from datetime import datetime, timezone

try:
    import tomllib
except ImportError:  # python < 3.11
    tomllib = None

TOKEN_URL = "https://oauth2.googleapis.com/token"
FREEBUSY_URL = "https://www.googleapis.com/calendar/v3/freeBusy"
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
    """Return merged busy [{start,end}] across calendars (ISO strs)."""
    data = _post_json(FREEBUSY_URL, {
        "timeMin": tmin,
        "timeMax": tmax,
        "items": [{"id": c} for c in calendars],
    }, headers={"Authorization": "Bearer " + token})
    busy = []
    for cal in data.get("calendars", {}).values():
        busy.extend(cal.get("busy", []))
    return busy


def _parse_dt(s):
    """ISO-8601 -> aware datetime (Z or offset; naive treated as UTC)."""
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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


def _ics_dt(value):
    """Return aware datetime or None for DATE/all-day start."""
    m = _ICS_DT.match(value.strip())
    if not m:
        return None
    d, t = m.group("d"), m.group("t")
    if t is None:
        return datetime.strptime(d, "%Y%m%d").replace(
            tzinfo=timezone.utc)  # all-day -> date at 00:00Z
    dt = datetime.strptime(d + t, "%Y%m%d%H%M%S")
    return dt.replace(tzinfo=timezone.utc)


def ics_busy(text):
    """Parse VEVENT DTSTART/DTEND pairs from unfolded .ics text."""
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    busy, cur = [], {}
    in_ev = False
    for line in lines:
        name, _, val = line.partition(":")
        prop = name.split(";", 1)[0].upper()
        if prop == "BEGIN" and val.upper() == "VEVENT":
            in_ev, cur = True, {}
        elif prop == "END" and val.upper() == "VEVENT":
            if cur.get("start") and cur.get("end") \
                    and cur["end"] > cur["start"]:
                busy.append({"start": cur["start"].isoformat(),
                             "end": cur["end"].isoformat()})
            in_ev = False
        elif in_ev and prop in ("DTSTART", "DTEND"):
            dt = _ics_dt(val)
            if dt is not None:
                cur["start" if prop == "DTSTART" else "end"] = dt
    return busy
