"""JEV runtime source contracts (tests/validation layer).

Behavioral checks against the shipped runtime — not doc-string claims:

- JEV-1: compact-gate assist floor is 0.25 (strict `>` trigger); the
  deterministic 0.70/0.80/0.40 bands stay unchanged.
- JEV-2: skill-picker emits at most 3 lexical read-hints, is stdlib-only
  and offline, and silently exits on non-prompt events / bad manifests.
- JEV-4: review_gate emits triage metadata only — it can never authorize.
- JEV-5: .devin/validation-contracts.json maps own-runtime docs to real
  test functions resolvable by doc_coverage (AST, inside tests/validation).
- JEV-6: a stale DOM snapshot always abstains — never a click suggestion.
- OpenUI: the line-DSL parser/streamer is bounded and the HTML renderer
  escapes all dynamic text (no handler injection).
"""
import ast
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import runpy

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))
sys.path.insert(0, str(ROOT / "extensions" / "computer-use"))
sys.path.insert(0, str(ROOT / "extensions" / "craft-bridge"))
sys.path.insert(0, str(ROOT / "extensions" / "scrape-tools"))

import doc_coverage as dco
import review_gate as rg
import cu_dom_picker as dp
import ui_dsl


def _load(name):
    return runpy.run_path(str(SCRIPTS / name))


def test_compact_gate_assist_floor_is_025():
    mod = _load("compact-gate.py")
    assert mod["DEFAULTS"]["eval_floor"] == 0.25
    profile = json.loads(
        (ROOT / ".devin" / "laya" / "profile.json").read_text("utf-8"))
    assert profile["compact_gate"]["eval_floor"] == 0.25


def test_compact_gate_deterministic_bands_unchanged():
    d = _load("compact-gate.py")["DEFAULTS"]
    assert d["compact_at"] == 0.70
    assert d["force_at"] == 0.80
    assert d["compact_to"] == 0.40


def test_skill_picker_lexical_hints_capped_at_3():
    mod = _load("skill-picker.py")
    skills = [{"name": f"skill-{i}", "purpose": "docker compose build"}
              for i in range(10)]
    hits = mod["pick_skills"]("docker compose build", skills)
    assert 0 < len(hits) <= 3
    assert mod["MAX_HINTS"] == 3
    assert len(mod["pick_skills"]("docker", skills, max_hints=99)) <= 3


def test_skill_picker_silent_on_non_prompt_and_bad_payload():
    mod = _load("skill-picker.py")
    out = io.StringIO()
    for payload in ({"hook_event_name": "PostToolUse"},
                    "not-json"):
        stdin = io.StringIO(
            payload if isinstance(payload, str) else json.dumps(payload))
        with patch.object(sys, "stdin", stdin), \
                patch.object(sys, "stdout", out), \
                pytest.raises(SystemExit) as e:
            mod["main"]()
        assert e.value.code == 0
    assert out.getvalue() == ""


def test_skill_picker_stdlib_only_and_offline():
    tree = ast.parse((SCRIPTS / "skill-picker.py").read_text("utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names)
    assert not imported & {"socket", "urllib", "http", "requests",
                           "subprocess", "ctypes"}


def _trivial_diff():
    return ("diff --git a/tests/test_x.py b/tests/test_x.py\n"
            "--- a/tests/test_x.py\n+++ b/tests/test_x.py\n"
            "@@ -1 +1 @@\n-x = 0\n+x = 1\n")


def test_review_gate_cannot_authorize():
    for diff, msg in (
        (_trivial_diff(), "fix: correct index because header row skipped"),
        ("diff --git a/hooks.v1.json b/hooks.v1.json\n"
         "--- a/hooks.v1.json\n+++ b/hooks.v1.json\n"
         "@@ -1 +1 @@\n-{}\n+{\"a\":1}\n", "x"),
    ):
        out = rg.triage_diff(diff, commit_msg=msg)
        assert out["ok"] is True
        assert out["risk"] in ("low", "medium", "high")
        assert isinstance(out["requires_deep_review"], bool)
        assert not ({"allow", "allowed", "approve", "approved",
                     "authorize", "authorized", "action", "execute",
                     "merge", "decision", "verdict"}
                    & set(out.keys()))


def test_dom_picker_stale_abstains():
    elements = [{"id": "b1", "role": "button", "name": "Save",
                 "enabled": True}]
    stale = dp.pick(None, {}, "Save", {"stale": True,
                                       "elements": elements})
    assert stale["outcome"] == "abstain"
    assert stale["reason"] == "stale_snapshot"
    assert stale["candidate_id"] == dp.dc.NONE_ID

    mismatch = dp.pick(None, {}, "Save",
                       {"observation_id": "obs-9",
                        "elements": elements},
                       expected_observation_id="obs-1")
    assert mismatch["outcome"] == "abstain"
    assert mismatch["reason"] == "stale_observation"
    fresh = dp.suggest_dom({"observation_id": "obs-1",
                            "elements": elements}, "Save",
                           mode="off")
    assert fresh["candidate_id"] in (dp.dc.NONE_ID, "b1")
    assert not ({"click", "dispatch", "coordinates", "x", "y"}
                & set(fresh.keys()))


def test_ui_dsl_stream_and_parser_bounded():
    too_many = "hud\nrow label=a value=1\nend\n" * (ui_dsl.MAX_LINES + 1)
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(too_many)
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse("x" * (ui_dsl.MAX_BYTES + 8))

    sp = ui_dsl.StreamParser()
    src = 'hud title="T" anchor=top\nrow label="L" value=1\nend\n'
    for ch in src.encode("utf-8"):
        sp.feed(bytes([ch]))
    doc = sp.finish()
    assert doc.blocks[0].type == "hud"
    with pytest.raises(ui_dsl.ParseError):
        sp.feed("row label=a value=1\n")

    sp2 = ui_dsl.StreamParser()
    sp2.feed("hud\n")
    with pytest.raises(ui_dsl.ParseError):
        sp2.finish()


def test_ui_dsl_render_has_no_handler_injection():
    src = ('form id=f title="t"\n'
           'q choice id=q1 text="<img onerror=x>" options=a|b\n'
           'btn action=submit label="<svg onload=y>"\nend\n')
    html = ui_dsl.render_html(ui_dsl.parse(src))
    assert "<img" not in html and "<svg" not in html
    assert "&lt;img" in html and "&lt;svg" in html
    assert "<script" not in html
    import re as _re
    assert not _re.search(r"\son\w+\s*=", html.replace("&lt;", "<") and
                          _re.sub(r"&lt;[^&]*?&gt;", "", html))
    assert 'method="dialog"' in html


MAP_PATH = ROOT / ".devin" / "validation-contracts.json"


def _map():
    return json.loads(MAP_PATH.read_text("utf-8"))


def test_doc_coverage_map_targets_are_real():
    mapping = _map()
    required = {
        ".devin/research/LAYA_MASTER_ARCHITECTURE.md",
        ".devin/rts/openui-lang.md",
        ".devin/sdd/goldfish-review.md",
    }
    assert required <= set(mapping), "core docs unmapped"
    for doc, targets in mapping.items():
        assert (ROOT / doc).is_file(), f"mapped doc missing: {doc}"
        assert isinstance(targets, list) and targets
        for t in targets:
            path = t.split("::", 1)[0]
            assert path.startswith("tests/validation/test_"), t
    out = dco.check_coverage(list(mapping), mapping,
                             tests_root=str(ROOT))
    assert out["ok"] is True
    assert out["findings"] == [], out["findings"]
    assert sorted(out["covered"]) == sorted(mapping)


def test_doc_coverage_rejects_non_validation_targets():
    bad = {"AGENTS.md": ["tests/test_jev_routing.py::test_x"],
           "README.md": ["tests/validation/test_jev_runtime_contracts.py"
                         "::test_does_not_exist"]}
    out = dco.check_coverage(list(bad), bad, tests_root=str(ROOT))
    assert out["ok"] is True
    reasons = {f["reason"] for f in out["findings"]}
    assert "target_out_of_scope" in reasons
    assert "missing_test_function" in reasons
    assert len(out["covered"]) == 0
