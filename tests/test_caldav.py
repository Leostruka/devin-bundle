"""caldav backend: discovery, multistatus parse, free/busy, writes, CLI."""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "extensions", "gcal"))
import caldav  # noqa: E402

WRAPPER = os.path.join(ROOT, "extensions", "gcal", "wrapper.py")

DAV = 'xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav"'

PRINCIPAL_MS = f"""<?xml version="1.0"?>
<D:multistatus {DAV}>
<D:response><D:href>/dav/.well-known/caldav</D:href>
<D:propstat><D:prop><D:current-user-principal>
<D:href>/dav/principal/user/</D:href>
</D:current-user-principal></D:prop>
<D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
</D:multistatus>"""

HOME_MS = f"""<?xml version="1.0"?>
<D:multistatus {DAV}>
<D:response><D:href>/dav/principal/user/</D:href>
<D:propstat><D:prop><D:calendar-home-set>
<D:href>/dav/calendars/user/</D:href>
</D:calendar-home-set></D:prop>
<D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
</D:multistatus>"""

CALS_MS = f"""<?xml version="1.0"?>
<D:multistatus {DAV}>
<D:response><D:href>/dav/calendars/user/</D:href>
<D:propstat><D:prop><D:displayname>root</D:displayname>
<D:resourcetype><D:collection/></D:resourcetype></D:prop>
<D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
<D:response><D:href>/dav/calendars/user/personal/</D:href>
<D:propstat><D:prop><D:displayname>Personal</D:displayname>
<D:resourcetype><D:collection/><C:calendar/></D:resourcetype>
</D:prop><D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
<D:response><D:href>/dav/calendars/user/work/</D:href>
<D:propstat><D:prop><D:displayname>Work</D:displayname>
<D:resourcetype><D:collection/><C:calendar/></D:resourcetype>
</D:prop><D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
</D:multistatus>"""

BUSY_ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20261108T120000Z
DTEND:20261108T130000Z
SUMMARY:dentist
END:VEVENT
BEGIN:VEVENT
DTSTART:20261108T140000Z
DTEND:20261108T150000Z
SUMMARY:tentative
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR"""

REPORT_MS = f"""<?xml version="1.0"?>
<D:multistatus {DAV}>
<D:response><D:href>/dav/calendars/user/personal/</D:href>
<D:propstat><D:prop><C:calendar-data>{BUSY_ICS}</C:calendar-data>
</D:prop><D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
</D:multistatus>"""

EMPTY_MS = f"""<?xml version="1.0"?>
<D:multistatus {DAV}>
<D:response><D:href>/dav/calendars/user/work/</D:href>
<D:propstat><D:prop><D:getetag>"e1"</D:getetag></D:prop>
<D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>
</D:multistatus>"""

CREDS = {"url": "http://127.0.0.1:1/dav",
         "username": "u", "password": "p"}


def test_load_credentials_env(monkeypatch):
    monkeypatch.setenv("BUNDLE_CALDAV_URL", "https://x/dav")
    monkeypatch.setenv("BUNDLE_CALDAV_USER", "me")
    monkeypatch.setenv("BUNDLE_CALDAV_PASSWORD", "pw")
    c = caldav.load_credentials()
    assert c["url"] == "https://x/dav" and c["password"] == "pw"


def test_parse_multistatus_props():
    rows = caldav._parse_multistatus(CALS_MS)
    assert len(rows) == 3
    personal = rows[1]
    assert personal["href"] == "/dav/calendars/user/personal/"
    assert personal["props"]["displayname"] == "Personal"
    assert "calendar" in personal["props"]["resourcetype"]
    assert "collection" in rows[0]["props"]["resourcetype"]


def test_discover_and_home(monkeypatch):
    calls = []

    def fake(creds, method, url, **kw):
        calls.append(url)
        if url.endswith("/.well-known/caldav"):
            return 207, {}, PRINCIPAL_MS
        if url.endswith("/dav/principal/user/"):
            return 207, {}, HOME_MS
        raise AssertionError(url)
    monkeypatch.setattr(caldav, "_request", fake)
    assert caldav.discover(CREDS) == "http://127.0.0.1:1/dav/principal/user/"
    assert caldav.calendar_home(CREDS) == \
        "http://127.0.0.1:1/dav/calendars/user/"


def test_list_calendars_filters_collections(monkeypatch):
    def fake(creds, method, url, **kw):
        if url.endswith("/.well-known/caldav"):
            return 207, {}, PRINCIPAL_MS
        if url.endswith("/dav/principal/user/"):
            return 207, {}, HOME_MS
        if url.endswith("/dav/calendars/user/"):
            return 207, {}, CALS_MS
        raise AssertionError(url)
    monkeypatch.setattr(caldav, "_request", fake)
    cals = caldav.list_calendars(CREDS)
    assert [c["name"] for c in cals] == ["Personal", "Work"]
    assert cals[0]["href"].endswith("/dav/calendars/user/personal/")


def test_ensure_calendar_found_and_created(monkeypatch):
    state = {"mk": 0}

    def fake(creds, method, url, **kw):
        if method == "MKCALENDAR":
            state["mk"] += 1
            return 201, {}, ""
        if url.endswith("/.well-known/caldav"):
            return 207, {}, PRINCIPAL_MS
        if url.endswith("/dav/principal/user/"):
            return 207, {}, HOME_MS
        if url.endswith("/dav/calendars/user/"):
            return 207, {}, CALS_MS
        raise AssertionError(url)
    monkeypatch.setattr(caldav, "_request", fake)
    href, created = caldav.ensure_calendar(CREDS, "Personal")
    assert href.endswith("/personal/") and created is False
    assert state["mk"] == 0
    href, created = caldav.ensure_calendar(CREDS, "AGdevin")
    assert href.endswith("/AGdevin/") and created is True
    assert state["mk"] == 1


def test_free_busy_merges_and_skips_transparent(monkeypatch):
    reports = []

    def fake(creds, method, url, **kw):
        if method == "REPORT":
            reports.append(url)
            if url.endswith("/personal/"):
                return 207, {}, REPORT_MS
            return 207, {}, EMPTY_MS
        if url.endswith("/.well-known/caldav"):
            return 207, {}, PRINCIPAL_MS
        if url.endswith("/dav/principal/user/"):
            return 207, {}, HOME_MS
        if url.endswith("/dav/calendars/user/"):
            return 207, {}, CALS_MS
        raise AssertionError(url)
    monkeypatch.setattr(caldav, "_request", fake)
    busy = caldav.free_busy(CREDS,
                            tmin="2026-11-08T00:00:00Z",
                            tmax="2026-11-09T00:00:00Z")
    assert len(reports) == 2
    assert busy == [{"start": "2026-11-08T12:00:00+00:00",
                     "end": "2026-11-08T13:00:00+00:00"}]


def test_free_busy_calendar_filter(monkeypatch):
    reports = []

    def fake(creds, method, url, **kw):
        if method == "REPORT":
            reports.append(url)
            return 207, {}, EMPTY_MS
        if url.endswith("/.well-known/caldav"):
            return 207, {}, PRINCIPAL_MS
        if url.endswith("/dav/principal/user/"):
            return 207, {}, HOME_MS
        if url.endswith("/dav/calendars/user/"):
            return 207, {}, CALS_MS
        raise AssertionError(url)
    monkeypatch.setattr(caldav, "_request", fake)
    caldav.free_busy(CREDS, calendars=["Work"],
                     tmin="2026-11-08T00:00:00Z",
                     tmax="2026-11-09T00:00:00Z")
    assert reports == ["http://127.0.0.1:1/dav/calendars/user/work/"]


def test_event_ics_shape_and_escape():
    ics = caldav.event_ics("dentist, molar; ok", "2026-11-08T09:00:00-03:00",
                           "2026-11-08T10:00:00-03:00",
                           description="line1\nline2", location="home",
                           uid="fixed")
    assert "UID:fixed" in ics
    assert "DTSTART:20261108T120000Z" in ics
    assert "DTEND:20261108T130000Z" in ics
    assert "SUMMARY:dentist\\, molar\\; ok" in ics
    assert "DESCRIPTION:line1\\nline2" in ics
    assert "LOCATION:home" in ics
    assert ics.endswith("END:VCALENDAR\r\n")


def test_create_event_put_and_error(monkeypatch):
    seen = {}

    def fake(creds, method, url, **kw):
        seen["method"] = method
        seen["url"] = url
        seen["headers"] = kw.get("extra_headers")
        seen["ctype"] = kw.get("content_type")
        return 201, {"ETag": '"abc"'}, ""
    monkeypatch.setattr(caldav, "_request", fake)
    out = caldav.create_event(CREDS, "http://h/cal/",
                              caldav.event_ics("x", "2026-11-08T09:00:00Z",
                                               "2026-11-08T10:00:00Z"))
    assert seen["method"] == "PUT" and seen["ctype"].startswith(
        "text/calendar")
    assert seen["headers"] == {"If-None-Match": "*"}
    assert out["etag"] == '"abc"' and out["status"] == 201

    monkeypatch.setattr(caldav, "_request",
                        lambda *a, **k: (403, {}, "forbidden"))
    try:
        caldav.create_event(CREDS, "http://h/cal/", "x")
        assert False, "expected CalDAVError"
    except caldav.CalDAVError:
        pass


# --- wrapper-level: hermetic missing creds + local fake server e2e ---


def _scrubbed_env(**extra):
    import tempfile
    empty = tempfile.mkdtemp(prefix="caldav-test-")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("BUNDLE_CALDAV_")
           and not k.startswith("BUNDLE_GCAL_")}
    env.update({"APPDATA": empty, "USERPROFILE": empty, "HOME": empty})
    env.update(extra)
    return env


def test_wrapper_caldav_missing_creds():
    p = subprocess.run(
        [sys.executable, WRAPPER, "free-busy", "--caldav",
         "--from", "2026-11-08T00:00:00Z", "--to", "2026-11-09T00:00:00Z"],
        capture_output=True, text=True, env=_scrubbed_env())
    out = json.loads(p.stdout)
    assert p.returncode == 1 and out["status"] == "missing"


def test_wrapper_caldav_add_preview():
    p = subprocess.run(
        [sys.executable, WRAPPER, "add", "--caldav", "--summary", "x",
         "--start", "2026-11-08T09:00:00Z",
         "--end", "2026-11-08T10:00:00Z"],
        capture_output=True, text=True, env=_scrubbed_env())
    out = json.loads(p.stdout)
    assert p.returncode == 0 and out["status"] == "confirm-required"
    assert out["backend"] == "caldav" and out["calendar"] == "AGdevin"
    assert "BEGIN:VCALENDAR" in out["events"][0]["ics"]


class _FakeCalDAV(BaseHTTPRequestHandler):
    puts = []

    def _send(self, code, body="", ctype="text/xml", headers=None):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _ms(self, body):
        self._send(207, body)

    def do_PROPFIND(self):
        path = self.path.split("?")[0]
        if path.endswith("/.well-known/caldav"):
            return self._ms(PRINCIPAL_MS)
        if path.endswith("/dav/principal/user/"):
            return self._ms(HOME_MS)
        if path.endswith("/dav/calendars/user/"):
            return self._ms(CALS_MS)
        self._send(404, "not found", "text/plain")

    def do_REPORT(self):
        path = self.path.split("?")[0]
        if path.endswith("/personal/"):
            return self._ms(REPORT_MS)
        if path.endswith("/work/"):
            return self._ms(EMPTY_MS)
        self._send(404, "not found", "text/plain")

    def do_MKCALENDAR(self):
        self._send(201, "")

    def do_PUT(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        _FakeCalDAV.puts.append((self.path, body))
        self._send(201, "", "text/calendar", {"ETag": '"e1"'})

    def log_message(self, *a):
        pass


def _serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _FakeCalDAV)
    _FakeCalDAV.puts = []
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_wrapper_caldav_e2e_freebusy_add_apply():
    srv = _serve()
    port = srv.server_address[1]
    env = _scrubbed_env(
        BUNDLE_CALDAV_URL=f"http://127.0.0.1:{port}/dav",
        BUNDLE_CALDAV_USER="u", BUNDLE_CALDAV_PASSWORD="p")
    try:
        p = subprocess.run(
            [sys.executable, WRAPPER, "free-busy", "--caldav",
             "--from", "2026-11-08T00:00:00Z",
             "--to", "2026-11-09T00:00:00Z"],
            capture_output=True, text=True, env=env)
        out = json.loads(p.stdout)
        assert p.returncode == 0 and out["status"] == "ok"
        assert out["source"] == "caldav"
        assert out["busy"] == [
            {"start": "2026-11-08T12:00:00+00:00",
             "end": "2026-11-08T13:00:00+00:00"}]

        p = subprocess.run(
            [sys.executable, WRAPPER, "add", "--caldav", "--confirm",
             "--calendar", "Personal", "--summary", "focus",
             "--start", "2026-11-08T14:00:00Z",
             "--end", "2026-11-08T15:00:00Z"],
            capture_output=True, text=True, env=env)
        out = json.loads(p.stdout)
        assert p.returncode == 0 and out["status"] == "ok"
        assert out["backend"] == "caldav"
        assert out["event"]["etag"] == '"e1"'
        assert any(path.endswith(".ics") and "focus" in body
                   for path, body in _FakeCalDAV.puts)

        import tempfile
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as f:
            json.dump({"schedule": [
                {"task": "block1",
                 "start": "2026-11-08T16:00:00Z",
                 "end": "2026-11-08T17:00:00Z"}]}, f)
            rfile = f.name
        p = subprocess.run(
            [sys.executable, WRAPPER, "apply", "--caldav", "--confirm",
             "--roteiro", rfile],
            capture_output=True, text=True, env=env)
        out = json.loads(p.stdout)
        assert p.returncode == 0 and out["status"] == "ok"
        assert out["calendar_created"] is True
        assert len(out["created"]) == 1
        assert any("block1" in body for _, body in _FakeCalDAV.puts)
        os.unlink(rfile)
    finally:
        srv.shutdown()
