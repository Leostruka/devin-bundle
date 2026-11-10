import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "rules-coverage.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_covered_and_uncovered_split(tmp_path):
    rules = tmp_path / "rules.md"
    rules.write_text(
        "- Never commit secrets or API keys.\n"
        "- Always re-check your own output twice.\n"
        "plain prose line without modal verbs\n",
        encoding="utf-8")
    r = run(str(rules))
    d = json.loads(r.stdout)
    assert d["ok"] and d["enforceable_clauses"] == 2
    covered = [x for x in d["rules"] if x["covered"]]
    assert any("destructive-gate" in c for c in covered[0]["controls"])
    assert d["uncovered"] == 1


def test_missing_file_typed_error(tmp_path):
    r = run(str(tmp_path / "nope.md"))
    d = json.loads(r.stdout)
    assert d["ok"] is False and r.returncode == 2


def test_default_scan_reports_real_repo_rules():
    r = run()
    d = json.loads(r.stdout)
    assert d["ok"] and d["enforceable_clauses"] > 10
    # secrets/signature/utf-8 classes must all be covered
    for rule in d["rules"]:
        t = rule["text"].lower()
        if "secret" in t or "signature" in t or "utf-8" in t:
            assert rule["covered"], rule
