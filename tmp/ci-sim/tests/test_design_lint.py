"""extensions/design-intelligence design_lint (M2_02)."""
import json
import os
import subprocess
import sys
import tempfile

EXT = os.path.join(os.path.dirname(__file__), "..", "extensions",
                   "design-intelligence")
FIX = os.path.join(EXT, "tests", "fixtures")
PY = sys.executable
sys.path.insert(0, EXT)
from rules_registry import ANTIPATTERNS  # noqa: E402
import checks  # noqa: E402


def run(script, *argv):
    return subprocess.run([PY, os.path.join(EXT, script), *argv],
                          capture_output=True, encoding="utf-8",
                          errors="replace")


def test_registry_counts():
    assert len(ANTIPATTERNS) == 62
    cats = {r["category"] for r in ANTIPATTERNS}
    assert cats == {"slop", "quality"}
    for r in ANTIPATTERNS:
        assert r["scope"] in ("static", "browser", "designsys")


def test_all_static_rules_implemented():
    missing = [r["id"] for r in ANTIPATTERNS
               if r["scope"] == "static" and r["id"] not in checks.CHECKS]
    assert missing == []


def test_list_rules():
    r = run("design_lint.py", ".", "--list-rules")
    assert r.returncode == 0
    assert "62 rules" in r.stdout
    assert "side-tab" in r.stdout


def test_fixtures_findings_exit2():
    r = run("design_lint.py", FIX, "--json")
    assert r.returncode == 2
    payload = json.loads(r.stdout[r.stdout.find("{"):])
    rules = {f["rule"] for f in payload["findings"]}
    assert {"side-tab", "marquee", "ai-color-palette",
            "low-contrast", "tiny-text"} <= rules
    assert payload["skipped"]["browser"] >= 10


def test_clean_files_exit0():
    r = run("design_lint.py", os.path.join(FIX, "clean.html"))
    assert r.returncode == 0
    r = run("design_lint.py", os.path.join(FIX, "clean.css"))
    assert r.returncode == 0


def test_seeded_rules_each_fire():
    cases = [
        ("<style>.x{border-left:6px solid #7c3aed}</style>", "side-tab"),
        ("<style>.a{font-family:'Inter',sans-serif}</style>",
         "overused-font"),
        ("<p>No clicks. No forms. Just results.</p>",
         "aphoristic-cadence"),
        ("<img src=''>", "broken-image"),
        ("<style>.b{text-align:justify}</style>", "justified-text"),
        ("<h1>A</h1><h3>B</h3>", "skipped-heading"),
        ("<p>delve into our seamless solution</p>",
         "marketing-buzzword"),
    ]
    for frag, rule in cases:
        found = checks.CHECKS[rule](frag,
                                    frag if "<style>" in frag else "",
                                    "t.html")
        assert found, rule


def test_ignore_file_rules(tmp_path):
    ig = tmp_path / "ig.json"
    ig.write_text(json.dumps({"files": [], "rules": ["side-tab"]}))
    r = run("design_lint.py", FIX, "--json", "--ignore", str(ig))
    payload = json.loads(r.stdout[r.stdout.find("{"):])
    assert "side-tab" not in {f["rule"] for f in payload["findings"]}


def test_look_ledger_reskin(tmp_path):
    a = tmp_path / "a.html"
    b = tmp_path / "b.html"
    skel = '<div class="wrap grid"><h1 class="t">X</h1></div>'
    a.write_text(skel + '<style>.t{font-family:Inter;color:#112233}'
                  '</style>')
    b.write_text(skel + '<style>.t{font-family:Roboto;color:#445566}'
                  '</style>')
    r = run("look_ledger.py", "compare", str(a), str(b))
    d = json.loads(r.stdout)
    assert d["same_skeleton"] and not d["same_fonts"]
    assert d["reskin"] is True
    led = tmp_path / "l.jsonl"
    r = run("look_ledger.py", "record", str(a), "--ledger", str(led))
    assert r.returncode == 0
    r = run("look_ledger.py", "check", str(b), "--ledger", str(led))
    assert r.returncode == 1  # same-skeleton family match


def test_no_finding_on_self():
    # lint the extension's own fixtures dir must not flag clean files
    r = run("design_lint.py", os.path.join(FIX, "clean.html"), "--json")
    d = json.loads(r.stdout[r.stdout.find("{"):])
    assert d["count"] == 0
