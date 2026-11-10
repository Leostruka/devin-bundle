import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "pulse.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def mk_intent(d, name, when, auto):
    (d / f"{name}.json").write_text(
        json.dumps({"kind": "resume_at", "when": when, "auto": auto}),
        encoding="utf-8")


def mk_issue(d, name, status, blocked_by=""):
    p = d / f"{name}.md"
    p.write_text(f"# {name}\nStatus: {status}\nBlocked by: {blocked_by}\n",
                 encoding="utf-8")
    return p


def test_auto_false_refused(tmp_path):
    intents = tmp_path / "intents"
    intents.mkdir()
    mk_intent(intents, "i1", int(time.time()) - 100, False)
    r = run("--intents-dir", str(intents),
            "--issues-glob", str(tmp_path / "none" / "*.md"))
    d = json.loads(r.stdout)
    assert d["ok"] and not d["due"] and len(d["refused"]) == 1


def test_due_auto_emits_next_issue_and_consumes(tmp_path):
    intents = tmp_path / "intents"
    issues = tmp_path / "proj" / "issues"
    intents.mkdir()
    issues.mkdir(parents=True)
    mk_intent(intents, "i1", int(time.time()) - 100, True)
    mk_issue(issues, "02-second", "open", blocked_by="01-first")
    mk_issue(issues, "01-first", "open")
    r = run("--intents-dir", str(intents),
            "--issues-glob", str(issues / "*.md"))
    d = json.loads(r.stdout)
    assert d["ok"] and d["due"] == ["i1.json"]
    assert d["next_issue"] == "01-first"
    # consumed marker written
    data = json.loads((intents / "i1.json").read_text())
    assert data["consumed"] is True


def test_dry_run_does_not_consume(tmp_path):
    intents = tmp_path / "intents"
    intents.mkdir()
    mk_intent(intents, "i1", int(time.time()) - 100, True)
    r = run("--dry-run", "--intents-dir", str(intents),
            "--issues-glob", str(tmp_path / "none" / "*.md"))
    d = json.loads(r.stdout)
    assert d["dry_run"] and d["due"] == ["i1.json"]
    assert "consumed" not in (intents / "i1.json").read_text()


def test_blocked_frontier_skips_blocked(tmp_path):
    issues = tmp_path / "issues"
    issues.mkdir()
    mk_issue(issues, "01-b", "open", blocked_by="09-z")
    mk_issue(issues, "02-a", "open")
    mk_issue(issues, "09-z", "open")
    intents = tmp_path / "intents"
    intents.mkdir()
    mk_intent(intents, "i1", int(time.time()) - 100, True)
    r = run("--intents-dir", str(intents),
            "--issues-glob", str(issues / "*.md"))
    d = json.loads(r.stdout)
    assert d["next_issue"] == "02-a"


def test_bold_colon_status_and_blockers(tmp_path):
    issues = tmp_path / "issues"
    issues.mkdir()
    (issues / "01-done.md").write_text(
        "# done\n**Status:** resolved\n", encoding="utf-8")
    (issues / "02-blocked.md").write_text(
        "# blocked\n**Status:** open\n**Blocked by:** 03-gate\n",
        encoding="utf-8")
    (issues / "03-gate.md").write_text(
        "# gate\n**Status:** open\n", encoding="utf-8")
    (issues / "04-ready.md").write_text(
        "# ready\n**Status:** open\n", encoding="utf-8")
    intents = tmp_path / "intents"
    intents.mkdir()
    mk_intent(intents, "i1", int(time.time()) - 100, True)
    r = run("--dry-run", "--intents-dir", str(intents),
            "--issues-glob", str(issues / "*.md"))
    d = json.loads(r.stdout)
    # resolved 01 excluded, 02 blocked by open 03 -> next ready is 03
    assert d["next_issue"] == "03-gate"
