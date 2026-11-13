"""gcal extension: ics parsing, free slots, roteiro packing, CLI."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "extensions", "gcal"))
import gcal  # noqa: E402
import plan  # noqa: E402

WRAPPER = os.path.join(ROOT, "extensions", "gcal", "wrapper.py")


def _tz_available():
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo("America/Sao_Paulo")
        return True
    except Exception:
        return False


needs_tzdata = pytest.mark.skipif(
    not _tz_available(), reason="zoneinfo tzdata unavailable")

ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20261106T090000Z
DTEND:20261106T100000Z
SUMMARY:standup
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=America/Sao_Paulo:20261106T140000
DTEND;TZID=America/Sao_Paulo:20261106T153000
SUMMARY:focus
END:VEVENT
BEGIN:VEVENT
DTSTART:20261106T110000Z
DTEND:20261106T113000Z
SUMMARY:a very long event summary that keeps
 going on a folded continuation line
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261107
DTEND;VALUE=DATE:20261108
SUMMARY:all day
END:VEVENT
END:VCALENDAR
"""


@needs_tzdata
def test_ics_busy_parses_utc_tzid_folded_allday():
    res = gcal.ics_busy(ICS)
    busy = res["busy"]
    assert len(busy) == 3  # 2 timed + all-day moved out of busy
    starts = sorted(b["start"] for b in busy)
    assert starts[0] == "2026-11-06T09:00:00+00:00"
    # TZID America/Sao_Paulo 14:00-03:00 -> 17:00Z
    assert any(b["start"] == "2026-11-06T17:00:00+00:00"
               for b in busy)
    assert res["all_day"] == [
        {"summary": "all day", "start": "2026-11-07",
         "end": "2026-11-08"}]
    assert res["recurring"] == 0


@needs_tzdata
def test_ics_busy_tzid_sao_paulo_issue396():
    ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\n"
           "DTSTART;TZID=America/Sao_Paulo:20261108T090000\n"
           "DTEND;TZID=America/Sao_Paulo:20261108T100000\n"
           "END:VEVENT\nEND:VCALENDAR")
    res = gcal.ics_busy(ics)
    assert res["busy"] == [
        {"start": "2026-11-08T12:00:00+00:00",
         "end": "2026-11-08T13:00:00+00:00"}]


def test_ics_busy_all_day_not_full_day_busy_issue397():
    ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\n"
           "DTSTART;VALUE=DATE:20261108\nDTEND;VALUE=DATE:20261109\n"
           "SUMMARY:holiday\nEND:VEVENT\nEND:VCALENDAR")
    res = gcal.ics_busy(ics)
    assert res["busy"] == []
    assert res["all_day"][0]["start"] == "2026-11-08"


def test_ics_busy_rrule_counted_not_expanded_issue398():
    ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\n"
           "DTSTART:20261109T130000Z\nDTEND:20261109T133000Z\n"
           "RRULE:FREQ=WEEKLY;BYDAY=MO\nEND:VEVENT\nEND:VCALENDAR")
    res = gcal.ics_busy(ics)
    assert len(res["busy"]) == 1
    assert res["recurring"] == 1


def test_ics_busy_unknown_tzid_warns_assumes_utc():
    ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\n"
           "DTSTART;TZID=Mars/Olympus:20261108T090000\n"
           "DTEND;TZID=Mars/Olympus:20261108T100000\n"
           "END:VEVENT\nEND:VCALENDAR")
    res = gcal.ics_busy(ics)
    assert res["busy"][0]["start"] == "2026-11-08T09:00:00+00:00"
    assert any("TZID" in w for w in res["warnings"])


def test_ics_busy_skips_malformed_and_inverted():
    bad = "BEGIN:VEVENT\nDTSTART:20261106T100000Z\n" \
          "DTEND:20261106T090000Z\nEND:VEVENT\n"
    assert gcal.ics_busy(bad)["busy"] == []


def test_ics_busy_skips_transparent_events():
    ics = "BEGIN:VCALENDAR\n" \
          "BEGIN:VEVENT\nDTSTART:20261106T090000Z\n" \
          "DTEND:20261106T100000Z\nSUMMARY:busy\nEND:VEVENT\n" \
          "BEGIN:VEVENT\nDTSTART:20261106T110000Z\n" \
          "DTEND:20261106T120000Z\nSUMMARY:free-marked\n" \
          "TRANSP:TRANSPARENT\nEND:VEVENT\nEND:VCALENDAR\n"
    busy = gcal.ics_busy(ics)["busy"]
    assert len(busy) == 1 and busy[0]["start"].startswith("2026-11-06T09")


def test_find_calendar_case_insensitive(monkeypatch):
    monkeypatch.setattr(gcal, "list_calendars",
                        lambda token: [{"id": "cal1", "summary": "AGdevin",
                                        "primary": False}])
    assert gcal.find_calendar("t", "agdevin") == "cal1"
    assert gcal.find_calendar("t", "  AGDEVIN ") == "cal1"
    assert gcal.find_calendar("t", "other") is None


def test_event_dedupe_key_stable_and_stamped():
    k1 = gcal.event_dedupe_key("sum", "2026-11-09T09:00:00-03:00",
                             "2026-11-09T10:00:00-03:00")
    k2 = gcal.event_dedupe_key("sum", "2026-11-09T09:00:00-03:00",
                             "2026-11-09T10:00:00-03:00")
    k3 = gcal.event_dedupe_key("sum", "2026-11-09T09:00:00-03:00",
                             "2026-11-09T11:00:00-03:00")
    assert k1 == k2 and k1 != k3 and len(k1) == 24
    p = gcal.stamp_event({"summary": "x"}, k1)
    assert p["extendedProperties"]["private"]["bundle_key"] == k1


def test_free_busy_requests_fields_and_paginates(monkeypatch):
    urls = []

    def fake_get(url, headers=None, timeout=None):
        urls.append(url)
        if "pageToken" not in url:
            return {"items": [{"status": "confirmed",
                               "start": {"dateTime": "2026-11-06T09:00:00Z"},
                               "end": {"dateTime": "2026-11-06T10:00:00Z"}}],
                    "nextPageToken": "p2"}
        return {"items": []}
    monkeypatch.setattr(gcal, "_get_json", fake_get)
    res = gcal.free_busy("tok", ["primary"],
                         "2026-11-06T00:00:00Z", "2026-11-07T00:00:00Z")
    assert len(urls) == 2
    assert "fields=" in urls[0] and "pageToken=p2" in urls[1]
    assert len(res["busy"]) == 1


def test_free_slots_gaps_and_edges():
    busy = [{"start": "2026-11-06T10:00:00+00:00",
             "end": "2026-11-06T11:00:00+00:00"},
            {"start": "2026-11-06T13:00:00+00:00",
             "end": "2026-11-06T14:00:00+00:00"}]
    slots = gcal.free_slots(busy, "2026-11-06T08:00:00+00:00",
                            "2026-11-06T18:00:00+00:00")
    assert [(s["start"], s["end"]) for s in slots] == [
        ("2026-11-06T08:00:00+00:00", "2026-11-06T10:00:00+00:00"),
        ("2026-11-06T11:00:00+00:00", "2026-11-06T13:00:00+00:00"),
        ("2026-11-06T14:00:00+00:00", "2026-11-06T18:00:00+00:00")]


def test_free_slots_overlapping_and_empty():
    busy = [{"start": "2026-11-06T09:00:00+00:00",
             "end": "2026-11-06T12:00:00+00:00"},
            {"start": "2026-11-06T10:00:00+00:00",
             "end": "2026-11-06T11:00:00+00:00"}]
    slots = gcal.free_slots(busy, "2026-11-06T08:00:00+00:00",
                            "2026-11-06T13:00:00+00:00")
    assert len(slots) == 2
    assert gcal.free_slots([], "2026-11-06T08:00:00+00:00",
                           "2026-11-06T10:00:00+00:00") == \
        [{"start": "2026-11-06T08:00:00+00:00",
          "end": "2026-11-06T10:00:00+00:00"}]


def test_pack_priority_order_and_fit():
    tasks = [{"name": "low", "minutes": 60, "priority": 5},
             {"name": "high", "minutes": 60, "priority": 1}]
    slots = [{"start": "2026-11-06T08:00:00+00:00",
              "end": "2026-11-06T10:00:00+00:00"}]
    r = plan.pack(tasks, slots)
    assert [s["task"] for s in r["schedule"]] == ["high", "low"]
    assert r["schedule"][0]["start"] == "2026-11-06T08:00:00+00:00"
    assert r["schedule"][1]["start"] == "2026-11-06T09:00:00+00:00"
    assert not r["unscheduled"] and not r["overcommit"]


def test_pack_overcommit_flags_unscheduled():
    tasks = [{"name": "a", "minutes": 90, "priority": 1},
             {"name": "b", "minutes": 90, "priority": 2}]
    slots = [{"start": "2026-11-06T08:00:00+00:00",
              "end": "2026-11-06T10:00:00+00:00"}]
    r = plan.pack(tasks, slots)
    assert r["unscheduled"] == ["b"] and r["overcommit"]
    assert r["slack_min"] == 30


def test_pack_empty_slots():
    r = plan.pack([{"name": "x", "minutes": 30}], [])
    assert r["unscheduled"] == ["x"]


def test_wrapper_ics_free_busy(tmp_path):
    ics = tmp_path / "cal.ics"
    ics.write_text(ICS, encoding="utf-8")
    p = subprocess.run(
        [sys.executable, WRAPPER, "free-busy", "--ics", str(ics),
         "--from", "2026-11-06T08:00:00Z", "--to", "2026-11-06T18:00:00Z"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert p.returncode == 0 and out["status"] == "ok"
    assert out["source"] == "ics" and len(out["busy"]) == 3
    assert out["all_day"] and out["free_slots"]


def test_wrapper_ics_url_free_busy():
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            body = ICS.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        port = srv.server_address[1]
        p = subprocess.run(
            [sys.executable, WRAPPER, "free-busy",
             "--ics-url", f"http://127.0.0.1:{port}/cal.ics",
             "--from", "2026-11-06T08:00:00Z",
             "--to", "2026-11-06T18:00:00Z"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = json.loads(p.stdout)
        assert p.returncode == 0 and out["status"] == "ok"
        assert out["source"] == "ics-url" and len(out["busy"]) == 3
    finally:
        srv.shutdown()


def test_wrapper_missing_creds_graceful(tmp_path):
    # hermetic: blank BUNDLE_GCAL_* + point creds paths at tmp so a real
    # credentials.toml on the host can never leak into this test
    env = {**os.environ,
           "BUNDLE_GCAL_CLIENT_ID": "",
           "BUNDLE_GCAL_CLIENT_SECRET": "",
           "BUNDLE_GCAL_REFRESH_TOKEN": "",
           "APPDATA": str(tmp_path),
           "USERPROFILE": str(tmp_path),
           "HOME": str(tmp_path)}
    p = subprocess.run([sys.executable, WRAPPER, "free-busy"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = json.loads(p.stdout)
    assert p.returncode == 1 and out["status"] == "missing"


def test_wrapper_plan(tmp_path):
    ics = tmp_path / "cal.ics"
    ics.write_text(ICS, encoding="utf-8")
    tasks = tmp_path / "t.json"
    tasks.write_text(json.dumps(
        [{"name": "deep work", "minutes": 120, "priority": 1},
         {"name": "email", "minutes": 30, "priority": 3}]), encoding="utf-8")
    p = subprocess.run(
        [sys.executable, WRAPPER, "plan", "--tasks", str(tasks),
         "--ics", str(ics),
         "--from", "2026-11-06T08:00:00Z", "--to", "2026-11-06T18:00:00Z"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert p.returncode == 0
    r = out["roteiro"]
    assert [s["task"] for s in r["schedule"]][0] == "deep work"


def test_event_payload_shape_and_tz():
    p = gcal.event_payload(
        "deep work", "2026-11-07T09:00:00Z", "2026-11-07T11:00:00Z",
        description="roteiro", location="home", tz="America/Sao_Paulo")
    assert p["summary"] == "deep work"
    assert p["start"]["timeZone"] == "America/Sao_Paulo"
    assert p["end"]["dateTime"].endswith("+00:00")
    assert p["description"] == "roteiro" and p["location"] == "home"


def test_add_needs_confirm_before_any_write(tmp_path):
    env = dict(os.environ)
    p = subprocess.run(
        [sys.executable, WRAPPER, "add", "--summary", "x",
         "--start", "2026-11-07T09:00:00Z",
         "--end", "2026-11-07T10:00:00Z"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = json.loads(p.stdout)
    assert p.returncode == 0 and out["status"] == "confirm-required"
    assert out["payload"]["summary"] == "x"


def test_add_missing_args_is_usage_error():
    p = subprocess.run([sys.executable, WRAPPER, "add", "--summary", "x"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert p.returncode == 2 and out["status"] == "error"


def test_apply_previews_roteiro_without_confirm(tmp_path):
    roteiro = tmp_path / "r.json"
    roteiro.write_text(json.dumps({"schedule": [
        {"task": "deep work", "start": "2026-11-07T09:00:00Z",
         "end": "2026-11-07T11:00:00Z"},
        {"task": "email", "start": "2026-11-07T11:30:00Z",
         "end": "2026-11-07T12:00:00Z"}]}), encoding="utf-8")
    p = subprocess.run(
        [sys.executable, WRAPPER, "apply", "--roteiro", str(roteiro),
         "--prefix", "[r] "],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert p.returncode == 0 and out["status"] == "confirm-required"
    assert len(out["events"]) == 2
    assert out["events"][0]["summary"] == "[r] deep work"


def test_apply_missing_file_is_error():
    p = subprocess.run([sys.executable, WRAPPER, "apply",
                        "--roteiro", "nope.json"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert p.returncode == 2 and out["status"] == "error"


def test_resolve_existing_calendar_reuses_id(monkeypatch):
    monkeypatch.setattr(gcal, "_get_json", lambda *a, **k: {
        "items": [{"id": "cal-ag-1", "summary": "AGdevin"},
                  {"id": "p", "summary": "Agenda", "primary": True}]})
    cid, created = gcal.resolve_calendar("tok", "AGdevin")
    assert cid == "cal-ag-1" and created is False


def test_resolve_missing_calendar_creates_once(monkeypatch):
    calls = {"post": 0}
    monkeypatch.setattr(gcal, "_get_json",
                        lambda *a, **k: {"items": []})
    def fake_post(url, payload, **k):
        calls["post"] += 1
        assert url == gcal.CAL_CREATE_URL
        assert payload == {"summary": "AGdevin"}
        return {"id": "cal-new"}
    monkeypatch.setattr(gcal, "_post_json", fake_post)
    cid, created = gcal.resolve_calendar("tok", "AGdevin")
    assert cid == "cal-new" and created is True and calls["post"] == 1


def test_resolve_primary_and_raw_id_passthrough(monkeypatch):
    monkeypatch.setattr(gcal, "_get_json",
                        lambda *a, **k: {"items": []})
    monkeypatch.setattr(gcal, "_post_json",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("must not create")))
    assert gcal.resolve_calendar("tok", "primary") == ("primary", False)
    cid, created = gcal.resolve_calendar("tok", "x@group.calendar.google.com")
    assert cid == "x@group.calendar.google.com" and created is False


def test_add_preview_names_agdevin_default():
    p = subprocess.run(
        [sys.executable, WRAPPER, "add", "--summary", "x",
         "--start", "2026-11-07T09:00:00Z",
         "--end", "2026-11-07T10:00:00Z"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert out["status"] == "confirm-required"
    assert out["calendar"] == "AGdevin"


def test_bool_flag_rejects_value_assignment(tmp_path):
    """Review regression: --confirm=false must error, not silently apply."""
    p = subprocess.run(
        [sys.executable, WRAPPER, "add", "--summary", "x",
         "--start", "2026-11-07T09:00:00Z",
         "--end", "2026-11-07T10:00:00Z",
         "--confirm=false"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = json.loads(p.stdout)
    assert p.returncode == 2 and out["status"] == "error"
    assert "takes no value" in out["stderr"]


def test_calendar_id_quoted_in_events_url(monkeypatch):
    """Review regression: ids with # ? @ must be percent-encoded so the
    fragment/query chars can't truncate or split the path."""
    calls = []
    monkeypatch.setattr(
        gcal, "_post_json",
        lambda url, *a, **k: calls.append(url) or {"id": "e1", "status": "confirmed"})
    gcal.create_event("tok", "weird#id@group.calendar.google.com",
                      {"summary": "t", "start": "2026-11-07T09:00:00Z",
                       "end": "2026-11-07T10:00:00Z"})
    assert calls, "expected a POST"
    url = calls[0]
    assert "weird%23id%40group.calendar.google.com" in url
    assert "#" not in url.split("calendars/")[-1]

    get_calls = []
    monkeypatch.setattr(
        gcal, "_get_json",
        lambda url, *a, **k: get_calls.append(url) or {"items": []})
    gcal.find_events_by_key("tok", "weird#id@group.calendar.google.com",
                            "k1")
    assert "weird%23id%40group.calendar.google.com" in get_calls[0]
