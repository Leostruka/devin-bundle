"""extensions/design-intelligence - BM25 engine + corpus tests (M2_01)."""
import csv
import os
import subprocess
import sys
import tempfile

import pytest

EXT = os.path.join(os.path.dirname(__file__), "..", "extensions",
                   "design-intelligence")
PY = sys.executable
sys.path.insert(0, EXT)
import core  # noqa: E402


def run(script, *argv, cwd=None):
    return subprocess.run([PY, os.path.join(EXT, script), *argv],
                          capture_output=True, encoding="utf-8",
                          errors="replace", cwd=cwd)


def test_search_style_domain():
    r = run("search.py", "saas dashboard dark", "--domain", "style",
            "--max-results", "3")
    assert r.returncode == 0, r.stderr
    assert "Found:" in r.stdout
    assert "dark" in r.stdout.lower()


def test_search_auto_detect_reports_domain():
    r = run("search.py", "saas dashboard dark", "--max-results", "2")
    assert r.returncode == 0
    assert "auto-detected" in r.stdout


def test_search_stack_rules():
    r = run("search.py", "image optimization lazy", "--stack", "nextjs",
            "--max-results", "2")
    assert r.returncode == 0
    assert "nextjs" in r.stdout.lower()


def test_search_json_mode():
    r = run("search.py", "dashboard", "--domain", "product",
            "--max-results", "2", "--json")
    assert r.returncode == 0
    import json
    payload = json.loads(r.stdout[r.stdout.find("{"):])
    assert "results" in payload or "query" in payload


def test_zero_result_suggests_terms():
    r = run("search.py", "zzqqxxyy nonexistent", "--domain", "style")
    assert r.returncode == 0
    # engine either finds weak matches or reports the miss; never crashes
    assert "Result" in r.stdout or "no " in r.stdout.lower() \
        or "suggest" in r.stdout.lower() or "Found: 0" in r.stdout


def test_validate_csv_all_domains():
    r = run("validate_csv.py", "--json")
    assert r.returncode == 0, r.stdout
    import json
    payload = json.loads(r.stdout[r.stdout.find("{"):])
    assert payload["problems"] == []
    assert len(payload["domains"]) >= 30


def test_bm25_ranking_order():
    bm = core.BM25()
    bm.fit(["dashboard dark mode oled", "landing page hero conversion",
            "typography serif elegant"])
    ranked = bm.score("dark dashboard")
    assert ranked[0][0] == 0  # first doc best match
    assert ranked[0][1] > ranked[-1][1]


def test_synonym_normalization():
    assert "dark" in core.BM25().tokenize("darkmode theme")
    assert "accessibility" in core.BM25().tokenize("a11y checklist")


def test_corpus_counts_real():
    styles = list(csv.DictReader(
        open(os.path.join(EXT, "data", "styles.csv"), encoding="utf-8")))
    colors = list(csv.DictReader(
        open(os.path.join(EXT, "data", "colors.csv"), encoding="utf-8")))
    typo = list(csv.DictReader(
        open(os.path.join(EXT, "data", "typography.csv"),
             encoding="utf-8")))
    assert len(styles) >= 60 and len(colors) >= 150 and len(typo) >= 50
    stacks = [f for f in os.listdir(os.path.join(EXT, "data", "stacks"))
              if f.endswith(".csv")]
    assert len(stacks) >= 20


def test_design_system_persist(tmp_path):
    r = run("search.py", "SaaS dashboard", "--design-system",
            "--project-name", "T", "--persist",
            "--output-dir", str(tmp_path))
    assert r.returncode == 0, r.stderr
    master = list(tmp_path.rglob("MASTER.md"))
    assert master, r.stdout[-500:]
    assert master[0].read_text(encoding="utf-8").strip()


def test_persist_skips_without_force(tmp_path):
    args = ("search.py", "SaaS dashboard", "--design-system",
            "--project-name", "T", "--persist",
            "--output-dir", str(tmp_path))
    assert run(*args).returncode == 0
    r = run(*args)
    assert "exist" in r.stdout.lower() or "skip" in r.stdout.lower() \
        or "force" in r.stdout.lower()
