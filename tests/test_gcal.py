"""gcal extension: ics parsing, free slots, roteiro packing, CLI."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "extensions", "gcal"))
import gcal  # noqa: E402
import plan  # noqa: E402

WRAPPER = os.path.join(ROOT, "extensions", "gcal", "wrapper.py")

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


def test_ics_busy_parses_utc_tzid_folded_allday():
    busy = gcal.ics_busy(ICS)
    assert len(busy) == 4
    starts = sorted(b["start"] for b in busy)
    assert starts[0] == "2026-11-06T09:00:00+00:00"
    assert starts[3] == "2026-11-07T00:00:00+00:00"


def test_ics_busy_skips_malformed_and_inverted():
    bad = "BEGIN:VEVENT\nDTSTART:20261106T100000Z\n" \
          "DTEND:20261106T090000Z\nEND:VEVENT\n"
    assert gcal.ics_busy(bad) == []


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
        capture_output=True, text=True)
    out = json.loads(p.stdout)
    assert p.returncode == 0 and out["status"] == "ok"
    assert out["source"] == "ics" and len(out["busy"]) == 4
    assert out["free_slots"]


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
                       capture_output=True, text=True, env=env)
    out = json.loads(p.stdout)
    assert p.returncode == 1 and out["status"] == "missing"


def test_wrapper_plan(tmp_path):
    ics = tmp_path / "cal.ics"
    ics.write_text(ICS, encoding="utf-8")
    tasks = tmp_path / "t.json"
    tasks.write_text(json.dumps(
        [{"name": "deep work", "minutes": 120, "priority": 1},
         {"name": "email", "minutes": 30, "priority": 3}]))
    p = subprocess.run(
        [sys.executable, WRAPPER, "plan", "--tasks", str(tasks),
         "--ics", str(ics),
         "--from", "2026-11-06T08:00:00Z", "--to", "2026-11-06T18:00:00Z"],
        capture_output=True, text=True)
    out = json.loads(p.stdout)
    assert p.returncode == 0
    r = out["roteiro"]
    assert [s["task"] for s in r["schedule"]][0] == "deep work"
