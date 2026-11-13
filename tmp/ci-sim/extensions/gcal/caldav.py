#!/usr/bin/env python3
"""CalDAV backend for the calendar extension (app-password CalDAV).

Alternative to Google OAuth for users whose calendar lives on iCloud,
Fastmail, Nextcloud, Radicale, or an Odysseus-style CalDAV setup.
Stdlib only: PROPFIND discovery (RFC 6764 well-known then base),
calendar-home-set, calendar-query REPORT for busy windows, MKCALENDAR
+ PUT .ics for writes. Credentials never printed; absence -> None.

Credential contract:
  - Env: BUNDLE_CALDAV_URL, BUNDLE_CALDAV_USER, BUNDLE_CALDAV_PASSWORD.
  - Or [caldav] section in credentials.toml (url, username, password).
  - Server URL may be the CalDAV root (https://caldav.fastmail.com/dav)
    or a provider base (https://caldav.icloud.com); discovery resolves
    the principal either way.
"""
import base64
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, urljoin, urlsplit
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

try:
    import tomllib
except ImportError:  # python < 3.11
    tomllib = None

import gcal  # noqa: E402  (reuse _parse_dt, _creds_paths, ics_busy)

DAV = "DAV:"
CAL = "urn:ietf:params:xml:ns:caldav"
HTTP_TIMEOUT = 30
_MAX_REDIRECTS = 3


class CalDAVError(Exception):
    pass


def _check_url(url):
    """CalDAV endpoints must be https - credentials ride Basic auth.
    Loopback (127.0.0.1/localhost/::1) is exempt: private test/dev
    servers never leave the host (project rule: private endpoints)."""
    u = url.lower()
    if u.startswith("https://"):
        return
    host = urlsplit(url).hostname or ""
    if host in ("127.0.0.1", "localhost", "::1"):
        return
    raise CalDAVError(f"caldav url must be https: {url!r}")


def load_credentials():
    """Return {url, username, password} or None."""
    url = os.environ.get("BUNDLE_CALDAV_URL")
    user = os.environ.get("BUNDLE_CALDAV_USER")
    pw = os.environ.get("BUNDLE_CALDAV_PASSWORD")
    if url and user and pw:
        _check_url(url)
        return {"url": url, "username": user, "password": pw}
    if tomllib is None:
        return None
    for p in gcal._creds_paths():
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                data = tomllib.loads(fh.read())
        except (OSError, ValueError):
            continue
        c = data.get("caldav", {})
        if c.get("url") and c.get("username") and c.get("password"):
            _check_url(c["url"])
            return {"url": c["url"], "username": c["username"],
                    "password": c["password"]}
    return None


def _auth(creds):
    tok = base64.b64encode(
        f"{creds['username']}:{creds['password']}".encode()).decode()
    return "Basic " + tok


def _request(creds, method, url, body=None, content_type=None,
             depth=None, extra_headers=None):
    """HTTP call returning (status, headers, text). Manual redirect
    follow for non-GET (urllib would drop the body)."""
    for _ in range(_MAX_REDIRECTS + 1):
        hdrs = {"User-Agent": "devin-bundle-caldav/1.0",
                "Authorization": _auth(creds)}
        if depth is not None:
            hdrs["Depth"] = str(depth)
        hdrs.update(extra_headers or {})
        data = None
        if body is not None:
            data = body.encode("utf-8") if isinstance(body, str) else body
            hdrs["Content-Type"] = \
                content_type or "text/xml; charset=utf-8"
            hdrs["Content-Length"] = str(len(data))
        req = urllib.request.Request(url, data=data, headers=hdrs,
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return (resp.status, dict(resp.headers),
                        resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) \
                    and e.headers.get("Location"):
                nxt = urljoin(url, e.headers["Location"])
                # never forward Basic auth off-origin or to plaintext
                if urlsplit(nxt).netloc != urlsplit(url).netloc \
                        or not nxt.lower().startswith("https://"):
                    raise CalDAVError(
                        f"refusing cross-origin/insecure redirect: {nxt}")
                url = nxt
                continue
            text = ""
            try:
                text = e.read().decode("utf-8", "replace")
            except Exception:
                pass  # fail-soft: cleanup; preserve primary error
            return e.code, dict(e.headers or {}), text
    raise CalDAVError(f"too many redirects for {url}")


def _propfind(creds, url, props_xml, depth):
    body = ('<?xml version="1.0" encoding="utf-8"?>'
            f'<D:propfind xmlns:D="{DAV}" xmlns:C="{CAL}">'
            f"<D:prop>{props_xml}</D:prop></D:propfind>")
    return _request(creds, "PROPFIND", url, body=body, depth=depth)


def _parse_multistatus(xml_text):
    """-> [{href, props}]; props maps local-name -> text (or list for
    resourcetype). Only propstats with status 200 contribute."""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for resp in root.iter(f"{{{DAV}}}response"):
        href_el = resp.find(f"{{{DAV}}}href")
        href = href_el.text.strip() \
            if href_el is not None and href_el.text else ""
        props = {}
        for propstat in resp.iter(f"{{{DAV}}}propstat"):
            status = propstat.find(f"{{{DAV}}}status")
            if status is not None and status.text \
                    and " 200" not in status.text:
                continue
            prop = propstat.find(f"{{{DAV}}}prop")
            if prop is None:
                continue
            for child in prop:
                tag = child.tag.rsplit("}", 1)[-1]
                if tag == "resourcetype":
                    props[tag] = [c.tag.rsplit("}", 1)[-1]
                                  for c in child]
                elif tag in ("current-user-principal",
                             "calendar-home-set"):
                    inner = child.find(f"{{{DAV}}}href")
                    props[tag] = inner.text.strip() \
                        if inner is not None and inner.text else ""
                else:
                    props[tag] = (child.text or "").strip()
        out.append({"href": href, "props": props})
    return out


def _base(creds):
    return creds["url"].rstrip("/") + "/"


def _resolve(base, href):
    return urljoin(base, href)


def discover(creds):
    """Principal URL: well-known first, base fallback. Raises.
    RFC 6764: .well-known lives at the host root, not under the base
    path (review: path-bearing bases probed a wrong URL first)."""
    base = _base(creds)
    parts = urlsplit(base)
    origin = f"{parts.scheme}://{parts.netloc}"
    for url in (origin + "/.well-known/caldav", base):
        code, _, text = _propfind(
            creds, url, "<D:current-user-principal/>", depth=0)
        if code == 207:
            for r in _parse_multistatus(text):
                principal = r["props"].get("current-user-principal")
                if principal:
                    return _resolve(base, principal)
    raise CalDAVError("current-user-principal not found")


def calendar_home(creds, principal_url=None):
    """calendar-home-set href resolved to absolute URL."""
    base = _base(creds)
    principal = principal_url or discover(creds)
    code, _, text = _propfind(
        creds, principal, "<D:calendar-home-set/>", depth=0)
    if code != 207:
        raise CalDAVError(f"calendar-home-set PROPFIND -> {code}")
    for r in _parse_multistatus(text):
        home = r["props"].get("calendar-home-set")
        if home:
            return _resolve(base, home)
    raise CalDAVError("calendar-home-set empty")


def _calendars(creds):
    """-> (home_url, [{href, name}]) calendar collections only."""
    base = _base(creds)
    home = calendar_home(creds)
    code, _, text = _propfind(
        creds, home, "<D:displayname/><D:resourcetype/>", depth=1)
    if code != 207:
        raise CalDAVError(f"calendar list PROPFIND -> {code}")
    cals = []
    for r in _parse_multistatus(text):
        if "calendar" not in (r["props"].get("resourcetype") or []):
            continue
        cals.append({"href": _resolve(base, r["href"]),
                     "name": r["props"].get("displayname")
                     or r["href"]})
    return home, cals


def list_calendars(creds):
    """-> [{href, name}] for calendar collections."""
    return _calendars(creds)[1]


def find_calendar(creds, name):
    """Calendar href whose display-name or href tail matches name
    (case-insensitive, stripped)."""
    want = (name or "").strip().lower()
    for c in list_calendars(creds):
        cname = (c["name"] or "").strip().lower()
        if cname == want or c["href"].rstrip("/").lower() \
                .endswith("/" + want):
            return c["href"]
    return None


def ensure_calendar(creds, name):
    """Find-or-create calendar collection -> (href, created_bool)."""
    href = find_calendar(creds, name)
    if href:
        return href, False
    home, _ = _calendars(creds)
    target = _resolve(home, quote(name, safe="") + "/")
    body = ('<?xml version="1.0" encoding="utf-8"?>'
            f'<C:mkcalendar xmlns:D="{DAV}" xmlns:C="{CAL}">'
            "<D:set><D:prop>"
            f"<D:displayname>{escape(name)}</D:displayname>"
            "</D:prop></D:set></C:mkcalendar>")
    code, _, _ = _request(creds, "MKCALENDAR", target, body=body,
                          depth=0)
    if code not in (200, 201, 204):
        raise CalDAVError(f"MKCALENDAR {name} -> {code}")
    return target, True


def _ical_time(iso_or_dt):
    dt = gcal._parse_dt(iso_or_dt) \
        if isinstance(iso_or_dt, str) else iso_or_dt
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def free_busy(creds, calendars=None, tmin=None, tmax=None):
    """Merged busy [{start,end}] (ISO) across calendars via
    calendar-query REPORT + local VEVENT parse. calendars: display
    names or hrefs; None/empty -> all."""
    _, cals = _calendars(creds)
    if calendars:
        wanted = {c.strip().lower() for c in calendars}

        def _match(c):
            cn = (c["name"] or "").strip().lower()
            href = c["href"].rstrip("/").lower()
            return (cn in wanted or href in wanted
                    or any(href.endswith("/" + w) for w in wanted))

        matched = [c for c in cals if _match(c)]
        if not matched:
            avail = ", ".join(c["name"] for c in cals) or "(none)"
            raise CalDAVError(
                f"calendar(s) not found: {sorted(wanted)}; "
                f"available: {avail}")
        cals = matched
    body_t = ('<?xml version="1.0" encoding="utf-8"?>'
              f'<C:calendar-query xmlns:D="{DAV}" xmlns:C="{CAL}">'
              "<D:prop><D:getetag/><C:calendar-data/></D:prop>"
              '<C:filter><C:comp-filter name="VCALENDAR">'
              '<C:comp-filter name="VEVENT">'
              f'<C:time-range start="{_ical_time(tmin)}" '
              f'end="{_ical_time(tmax)}"/>'
              "</C:comp-filter></C:comp-filter></C:filter>"
              "</C:calendar-query>")
    busy = []
    for c in cals:
        code, _, text = _request(
            creds, "REPORT", c["href"], body=body_t,
            content_type="application/xml; charset=utf-8")
        if code != 207:
            raise CalDAVError(f"calendar-query {c['name']} -> {code}")
        for r in _parse_multistatus(text):
            data = r["props"].get("calendar-data")
            if data:
                busy.extend(gcal.ics_busy(data)["busy"])
    return busy


def _ics_escape(s):
    return str(s).replace("\\", "\\\\").replace("\n", "\\n") \
        .replace(",", "\\,").replace(";", "\\;")


def _fold_ics_line(line):
    """RFC 5545 3.1: content lines <=75 octets; folds insert CRLF+space.
    Continuation lines carry the leading space inside the 75 budget."""
    chunks, cur, curlen = [], "", 0
    for ch in line:
        clen = len(ch.encode("utf-8"))
        cap = 75 if not chunks else 74
        if curlen + clen > cap:
            chunks.append(cur)
            cur, curlen = "", 0
        cur += ch
        curlen += clen
    chunks.append(cur)
    return "\r\n ".join(chunks) if len(chunks) > 1 else line


def event_ics(summary, start, end, description=None, location=None,
              uid=None):
    """VCALENDAR/VEVENT text. start/end ISO-8601 (any tz -> UTC)."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//devin-bundle//caldav//EN",
             "BEGIN:VEVENT",
             f"UID:{uid or uuid.uuid4().hex + '@devin-bundle'}",
             "DTSTAMP:" + datetime.now(timezone.utc).strftime(
                 "%Y%m%dT%H%M%SZ"),
             "DTSTART:" + _ical_time(start),
             "DTEND:" + _ical_time(end),
             "SUMMARY:" + _ics_escape(summary)]
    if description:
        lines.append("DESCRIPTION:" + _ics_escape(description))
    if location:
        lines.append("LOCATION:" + _ics_escape(location))
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(_fold_ics_line(l) for l in lines) + "\r\n"


def create_event(creds, calendar_href, ics_text):
    """PUT new .ics resource into a calendar collection.
    -> {href, etag, status}. Raises CalDAVError on non-2xx."""
    base = calendar_href if calendar_href.endswith("/") \
        else calendar_href + "/"
    url = _resolve(base, uuid.uuid4().hex + ".ics")
    code, headers, _ = _request(
        creds, "PUT", url, body=ics_text,
        content_type="text/calendar; charset=utf-8",
        extra_headers={"If-None-Match": "*"})
    if code not in (200, 201, 204):
        raise CalDAVError(f"PUT event -> {code}")
    etag = next((v for k, v in headers.items()
                 if k.lower() == "etag"), None)
    return {"href": url, "etag": etag,
            "status": code}
