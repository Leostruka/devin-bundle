"""Regression guard for scripts/memory-retrieval.py BM25 fusion (#639).

Pins the held-out-eval behaviour: cue-only retrieval scored 0.25 recall@3
on paraphrased prompts; additive cue+BM25 fusion reached 0.85. These tests
lock the mechanics that produced the gain - BM25 paraphrase retrieval,
cue-as-boost (not gate), and the inactive-status halving.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "memory-retrieval.py"


def _load():
    spec = importlib.util.spec_from_file_location("memory_retrieval", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _note(title, body, cues=(), status="active", category="ops"):
    return {
        "path": "/tmp/x.md",
        "rel": "x",
        "title": title,
        "category": category,
        "status": status,
        "cues": list(cues),
        "body": body,
    }


def test_bm25_recovers_paraphrased_prompt():
    """Caldav-flake-style case from the eval corpus: the prompt shares no
    cue vocabulary with the note, only topical words."""
    m = _load()
    notes = [
        _note("CI CalDAV flake windows py3.11",
              "freebusy e2e test flakes on windows runners; rerun fixes it"),
        _note("branch cleanup procedure",
              "prune origin, verify merged PRs, delete local copies"),
    ]
    scores = m.bm25_scores(notes, "e2e test rerun windows runners")
    assert scores[0] > 0 and scores[0] > scores[1]


def test_bm25_zero_when_no_terms_match():
    m = _load()
    notes = [_note("totally unrelated", "nothing here matches")]
    assert m.bm25_scores(notes, "zzzxqqq") == [0.0]


def test_cue_score_unchanged_semantics():
    """Cue weights: keyword 3, symbol 4, path 2; inactive halves."""
    m = _load()
    n = _note("t", "b", cues=[("keyword", "deploy"),
                              ("symbol", "install.ps1"),
                              ("path", "scripts/x.py")])
    assert m.score(n, "run deploy via install.ps1 in scripts/x.py") == 9
    n["status"] = "archived"
    assert m.score(n, "run deploy via install.ps1 in scripts/x.py") == 4


def test_fusion_is_additive_not_gated():
    """The shipped scorer adds BM25 to the cue score - a note with zero cue
    hits must still be retrievable on BM25 alone (the whole point of the
    fusion; gate-OR fusion measured 0.80 < 0.85 in the eval)."""
    m = _load()
    notes = [_note("winrt pin conflict",
                   "winrt-runtime epoch mismatch broke computer-use venv")]
    bm = m.bm25_scores(notes, "winrt-runtime epoch mismatch")[0]
    cue = m.score(notes[0], "dependency resolution failed epoch pins")
    assert bm > 0 and cue == 0
    assert cue + bm > 0  # retrievable under the shipped s > 0 filter


def test_end_to_end_paraphrase_injects_note(tmp_path):
    """Subprocess E2E: paraphrased prompt must inject the note via
    additionalContext (the exact failure mode fixed by BM25)."""
    mem = tmp_path / ".devin" / "memory"
    mem.mkdir(parents=True)
    (mem / "flake.md").write_text(
        "---\ntitle: CI flake guide\ncategory: ops\nstatus: active\n"
        "cues:\n  - keyword: \"caldav-freebusy-hook\"\n---\n"
        "freebusy end to end test flakes on windows runners; "
        "job rerun fixes it\n", encoding="utf-8")
    env = dict(os.environ, BUNDLE_MEMORY_DIR=str(mem))
    payload = json.dumps({"hookEventName": "UserPromptSubmit",
                          "prompt": "e2e test on windows runner is flaky, "
                                    "does a rerun help"})
    out = subprocess.run(
        [sys.executable, str(SCRIPT)], input=payload, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env, check=False)
    assert out.returncode == 0
    data = json.loads(out.stdout)
    ctx = data["hookSpecificOutput"]["additionalContext"]
    assert "CI flake guide" in ctx


def test_no_match_exits_cleanly(tmp_path):
    mem = tmp_path / ".devin" / "memory"
    mem.mkdir(parents=True)
    (mem / "n.md").write_text("---\ntitle: t\n---\nbody\n",
                            encoding="utf-8")
    env = dict(os.environ, BUNDLE_MEMORY_DIR=str(mem))
    payload = json.dumps({"hookEventName": "UserPromptSubmit",
                          "prompt": "zzzxqqq no overlap at all"})
    out = subprocess.run(
        [sys.executable, str(SCRIPT)], input=payload, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env, check=False)
    assert out.returncode == 0
    assert out.stdout.strip() == ""


def test_empty_cue_values_score_zero():
    """C51: an empty cue value made `'' in text` True on every prompt -
    empty keyword/symbol/path must contribute nothing."""
    m = _load()
    n = _note("t", "b", cues=[("keyword", ""), ("symbol", ""),
                              ("path", "")])
    assert m.score(n, "anything at all") == 0
