"""JEV-4/5/6 — review gate, doc coverage, DOM action picker.

JEV-4: seven deterministic boolean questions over a diff; any yes in
Q1-Q3 (secrets, protected paths, dependency changes) is immediate high
risk; missing tests / missing rationale / egress / large diff escalate
from low. A low-risk result can never authorize anything — the gate
only emits risk + requires_deep_review, never an action.

JEV-5: doc-to-test coverage uses an EXPLICIT mapping from changed
rules/docs to real test files/functions; unmapped or broken targets
are Important findings. No heuristic counts as coverage.

JEV-6: DOM snapshots become a deterministic shortlist of <=8
candidates feeding the existing cu_decision contract; output is a
typed suggestion or abstain — never a click. Stale, disabled, unsafe
or missing candidates abstain; daemon unavailable keeps the
deterministic policy.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "laya-tools"))
sys.path.insert(0, str(ROOT / "extensions" / "computer-use"))
sys.path.insert(0, str(ROOT / "extensions" / "scrape-tools"))

import decision_contract as dc
import review_gate as rg
import doc_coverage as dco
import cu_dom_picker as dp
import dom_elements as de


def _diff(path="src/app.py", added=None, removed=None):
    added = added or ["+x = 1"]
    removed = removed or ["-x = 0"]
    body = "\n".join(removed + added)
    return (f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n+++ b/{path}\n"
            f"@@ -1 +1 @@\n{body}\n")


def _delete_diff(path):
    return (f"diff --git a/{path} b/{path}\n"
            f"deleted file mode 100644\n"
            f"--- a/{path}\n+++ /dev/null\n"
            f"@@ -1 +0,0 @@\n-x = 1\n")


def _rename_diff(old, new):
    return (f"diff --git a/{old} b/{new}\n"
            f"similarity index 98%\n"
            f"rename from {old}\nrename to {new}\n")


def _binary_diff(path):
    return (f"diff --git a/{path} b/{path}\n"
            f"index 000..111 100644\n"
            f"Binary files a/{path} and b/{path} differ\n")




def test_clean_diff_is_low_and_never_deep():
    out = rg.triage_diff(
        _diff("tests/test_app.py", added=["+def test_x(): pass"]),
        commit_msg="fix: correct off-by-one because the index "
                   "skipped the header row")
    q = out["questions"]
    assert out["risk"] == "low"
    assert out["requires_deep_review"] is False
    assert q["q1_secret_indication"]["answer"] is False
    assert q["q2_protected_paths"]["answer"] is False
    assert q["q3_dependency_changes"]["answer"] is False
    assert q["q4_has_tests"]["answer"] is True
    assert q["q5_egress"]["answer"] is False
    assert q["q6_large_diff"]["answer"] is False
    assert q["q7_commit_rationale"]["answer"] is True


def test_docs_only_diff_does_not_demand_tests():
    out = rg.triage_diff(_diff("docs/guide.md"),
                         commit_msg="docs: clarify export flow because "
                                    "users conflated it with install")
    assert out["questions"]["q4_has_tests"]["answer"] is True
    assert out["risk"] == "low"


def test_secret_positive_is_high_and_redacted():
    secret = "AKIAIOSFODNN7EXAMPLE"
    d = _diff("src/conf.py", added=[f'+AWS_KEY = "{secret}"'])
    out = rg.triage_diff(d, commit_msg="chore: config")
    assert out["questions"]["q1_secret_indication"]["answer"] is True
    assert out["risk"] == "high"
    assert out["requires_deep_review"] is True
    blob = json.dumps(out)
    assert secret not in blob
    assert "conf.py" in blob


def test_protected_path_positive_is_high():
    for p in ("hooks.v1.json", "scripts/pre-exec-guard.py"):
        out = rg.triage_diff(_diff(p), commit_msg="x")
        assert out["questions"]["q2_protected_paths"]["answer"] is True
        assert out["risk"] == "high"


def test_dependency_change_positive_is_high():
    out = rg.triage_diff(_diff("requirements.txt",
                               added=["+scrapling>=1.0"]),
                         commit_msg="deps")
    assert out["questions"]["q3_dependency_changes"]["answer"] is True
    assert out["risk"] == "high"


def test_missing_tests_escalates_when_source_changes():
    out = rg.triage_diff(_diff("src/core.py"),
                         commit_msg="fix: real rationale text here")
    assert out["questions"]["q4_has_tests"]["answer"] is False
    assert out["risk"] in ("medium", "high")
    assert out["requires_deep_review"] is True


def test_tests_present_does_not_escalate():
    d = _diff("tests/test_core.py", added=["+def test_ok(): pass"])
    out = rg.triage_diff(d,
                         commit_msg="test: add coverage for parser "
                                    "because the case was untested")
    assert out["questions"]["q4_has_tests"]["answer"] is True
    assert out["risk"] == "low"


def test_egress_positive_escalates():
    d = _diff("src/net.py", added=["+import requests",
                                   "+r = requests.get(url)"])
    out = rg.triage_diff(d, commit_msg="feat: fetch remote data "
                                       "because cache misses")
    assert out["questions"]["q5_egress"]["answer"] is True
    assert out["risk"] != "low"


def test_large_diff_positive():
    added = [f"+line{i} = {i}" for i in range(401)]
    out = rg.triage_diff(_diff("src/big.py", added=added),
                         commit_msg="big change because reasons")
    assert out["questions"]["q6_large_diff"]["answer"] is True
    assert out["questions"]["q6_large_diff"]["lines"] > 400
    assert out["risk"] != "low"


def test_missing_rationale_escalates():
    out = rg.triage_diff(_diff(), commit_msg="")
    assert out["questions"]["q7_commit_rationale"]["answer"] is False
    assert out["risk"] != "low"
    out2 = rg.triage_diff(_diff("tests/test_a.py",
                                added=["+def test_a(): pass"]),
                          commit_msg="wip")
    assert out2["questions"]["q7_commit_rationale"]["answer"] is False
    assert out2["risk"] != "low"


def test_low_risk_never_authorizes():
    out = rg.triage_diff(_diff("tests/test_b.py",
                               added=["+def test_b(): pass"]),
                         commit_msg="test: cover branch because gap")
    assert out["risk"] == "low"
    for key, val in out.items():
        assert key not in ("allow", "approve", "merge", "execute")
    assert json.dumps(out).count('"abstain"') >= 0


def test_laya_off_gives_typed_abstention(tmp_path):
    cfg = tmp_path / "profile.json"
    cfg.write_text(json.dumps({"version": 1, "mode": "off"}))
    out = rg.triage_diff(_diff(), commit_msg="fix: why",
                         config=str(cfg))
    assert out["laya"]["outcome"] == "abstain"
    assert out["laya"]["reason"] in ("feature_off", "daemon_unavailable")


def test_deleted_guard_file_is_high():
    out = rg.triage_diff(_delete_diff("scripts/pre-exec-guard.py"),
                         commit_msg="chore: remove old script because "
                                    "it was superseded upstream")
    assert "scripts/pre-exec-guard.py" in out["files_changed"]
    assert out["questions"]["q2_protected_paths"]["answer"] is True
    assert out["risk"] == "high"


def test_deleted_dependency_file_is_high():
    out = rg.triage_diff(_delete_diff("requirements.txt"),
                         commit_msg="chore: drop pins because vendored")
    assert out["questions"]["q3_dependency_changes"]["answer"] is True
    assert out["risk"] == "high"


def test_rename_only_protected_path_is_high():
    out = rg.triage_diff(_rename_diff("hooks.v1.json",
                                      "hooks.legacy.json"),
                         commit_msg="chore: rename because reorganize")
    assert out["questions"]["q2_protected_paths"]["answer"] is True
    assert out["risk"] == "high"


def test_binary_change_to_guard_is_high():
    out = rg.triage_diff(_binary_diff("scripts/run-guard.py"),
                         commit_msg="chore: binary update because "
                                    "upstream blob changed")
    assert "scripts/run-guard.py" in out["files_changed"]
    assert out["questions"]["q2_protected_paths"]["answer"] is True
    assert out["risk"] == "high"


def _gnu_diff(path, added=None, ts="2026-01-02 10:00:00 +0000"):
    added = added or ["+x = 1"]
    body = "\n".join(added)
    return (f"--- {path}\t{ts}\n+++ {path}\t{ts}\n"
            f"@@ -1 +1 @@\n{body}\n")


def test_gnu_diff_timestamps_keep_paths():
    out = rg.triage_diff(_gnu_diff("scripts/run-guard.py"),
                         commit_msg="chore: touch guard because sync")
    assert "scripts/run-guard.py" in out["files_changed"]
    assert out["questions"]["q2_protected_paths"]["answer"] is True
    assert out["risk"] == "high"


def test_gnu_diff_synthetic_secret_detected():
    fake = 'token = "ZZZZZZZZZZZZZZZZ"'
    out = rg.triage_diff(
        _gnu_diff("src/conf.py", added=[f"+{fake}"]),
        commit_msg="chore: config because reasons")
    assert out["questions"]["q1_secret_indication"]["answer"] is True
    assert fake not in json.dumps(out)
    assert out["risk"] == "high"


def test_malformed_header_escalates_not_low():
    d = "diff --git a/src/x.py b/src/x.py\n" \
        "--- \t\n+++ \x01garbage\n@@ -1 +1 @@\n+y = 1\n"
    out = rg.triage_diff(d, commit_msg="fix: real reason text here")
    assert out["parse_anomalies"] >= 1
    assert out["risk"] != "low"


def test_testbed_testament_dirs_are_not_tests():
    for p in ("src/testament/x.py", "src/testbed/y.py"):
        out = rg.triage_diff(_diff(p),
                             commit_msg="fix: real reason why here ok")
        assert out["questions"]["q4_has_tests"]["answer"] is False
        assert out["risk"] != "low"


def test_test_dir_segment_and_name_conventions():
    for p in ("tests/foo.py", "test/foo.py", "src/test_foo.py",
              "src/foo_test.py", "conftest.py"):
        d = _diff(p, added=["+def test_x(): pass"])
        out = rg.triage_diff(d,
                             commit_msg="fix: real reason why here ok")
        assert out["questions"]["q4_has_tests"]["answer"] is True, p


def test_diff_git_quoted_space_paths():
    d = ('diff --git "a/my file.py" "b/my file.py"\n'
         '--- "a/my file.py"\n+++ "b/my file.py"\n'
         '@@ -1 +1 @@\n+x = 1\n')
    out = rg.triage_diff(d, commit_msg="fix: real reason why here ok")
    assert out["files_changed"] == ["my file.py"]


def test_diff_git_quoted_guard_space_path_still_protected():
    d = ('diff --git "a/scripts/my guard.py" "b/scripts/my guard.py"\n'
         '--- "a/scripts/my guard.py"\n+++ "b/scripts/my guard.py"\n'
         '@@ -1 +1 @@\n+x = 1\n')
    out = rg.triage_diff(d, commit_msg="chore: because reasons ok")
    assert out["files_changed"] == ["scripts/my guard.py"]
    assert out["questions"]["q2_protected_paths"]["answer"] is True
    assert out["risk"] == "high"


def test_deleted_test_files_do_not_count_for_q4():
    d = _diff("src/core.py") + _delete_diff("tests/test_core.py")
    out = rg.triage_diff(d,
                         commit_msg="chore: cleanup because obsolete")
    assert "tests/test_core.py" in out["files_changed"]
    assert out["questions"]["q4_has_tests"]["answer"] is False
    assert out["risk"] != "low"


def test_deleted_source_does_not_demand_tests():
    out = rg.triage_diff(_delete_diff("src/dead.py"),
                         commit_msg="chore: remove dead code because "
                                    "nothing referenced it")
    assert out["questions"]["q4_has_tests"]["answer"] is True
    assert out["risk"] == "low"




def test_coverage_hit_file_and_function(tmp_path):
    tdir = tmp_path / "tests" / "validation"
    tdir.mkdir(parents=True)
    (tdir / "test_rules.py").write_text(
        "def test_rule_contract():\n    assert True\n")
    mapping = {"AGENTS.md": ["tests/validation/test_rules.py::"
                             "test_rule_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["findings"] == []
    assert out["covered"] == ["AGENTS.md"]


def test_unmapped_changed_doc_is_important(tmp_path):
    out = dco.check_coverage([".devin/rules/new-rule.md"], {},
                             tests_root=str(tmp_path))
    assert out["findings"][0]["severity"] == "Important"
    assert out["findings"][0]["reason"] == "no_contract_mapping"


def test_missing_test_file_is_important(tmp_path):
    mapping = {"AGENTS.md": ["tests/validation/nope.py::test_x"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    kinds = {f["reason"] for f in out["findings"]}
    assert "missing_test_file" in kinds
    assert all(f["severity"] == "Important" for f in out["findings"])


def test_missing_test_function_is_important(tmp_path):
    tdir = tmp_path / "tests" / "validation"
    tdir.mkdir(parents=True)
    (tdir / "test_rules.py").write_text("def test_other(): pass\n")
    mapping = {"AGENTS.md": ["tests/validation/test_rules.py::"
                             "test_rule_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert any(f["reason"] == "missing_test_function"
               for f in out["findings"])


def _mk_test(tmp_path, rel="tests/validation/test_rules.py",
             body="def test_contract():\n    assert True\n"):
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body)
    return f


def test_traversal_target_rejected(tmp_path):
    real = _mk_test(tmp_path)
    mapping = {"AGENTS.md": ["../outside.py::test_x",
                             "tests/../../x/test_rules.py"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["covered"] == []
    assert all(f["severity"] == "Important" for f in out["findings"])


def test_target_outside_validation_dir_rejected(tmp_path):
    (tmp_path / "tests" / "test_top.py").parent.mkdir(parents=True,
                                                    exist_ok=True)
    (tmp_path / "tests" / "test_top.py").write_text(
        "def test_x(): pass\n")
    mapping = {"AGENTS.md": ["tests/test_top.py::test_x"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["covered"] == []
    assert out["findings"]


def test_symlink_target_rejected(tmp_path):
    real = _mk_test(tmp_path)
    link = tmp_path / "tests" / "validation" / "test_link.py"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        import pytest as _pt
        _pt.skip("symlinks unsupported")
    mapping = {"AGENTS.md": ["tests/validation/test_link.py::"
                             "test_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["covered"] == []
    assert out["findings"]


def test_non_test_file_rejected(tmp_path):
    f = tmp_path / "tests" / "validation" / "helper.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("def test_contract(): pass\n")
    mapping = {"AGENTS.md": ["tests/validation/helper.py::"
                             "test_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["covered"] == []
    assert out["findings"]


def test_docstring_fake_def_not_accepted(tmp_path):
    _mk_test(tmp_path,
             body='"""docstring\ndef test_contract(): pass\n"""\n'
                  'x = 1\n')
    mapping = {"AGENTS.md": ["tests/validation/test_rules.py::"
                             "test_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert any(f["reason"] == "missing_test_function"
               for f in out["findings"])


def test_syntax_error_target_rejected(tmp_path):
    _mk_test(tmp_path, body="def test_contract(:\n")
    mapping = {"AGENTS.md": ["tests/validation/test_rules.py::"
                             "test_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["covered"] == []
    assert out["findings"]


def test_class_method_counts(tmp_path):
    _mk_test(tmp_path,
             body="class TestRules:\n"
                  "    def test_contract(self):\n"
                  "        assert True\n")
    mapping = {"AGENTS.md": ["tests/validation/test_rules.py::"
                             "test_contract"]}
    out = dco.check_coverage(["AGENTS.md"], mapping,
                             tests_root=str(tmp_path))
    assert out["findings"] == []
    assert out["covered"] == ["AGENTS.md"]


def test_malformed_mapping_rejected(tmp_path):
    _mk_test(tmp_path)
    out = dco.check_coverage(["AGENTS.md"], ["not", "a", "dict"],
                             tests_root=str(tmp_path))
    assert out["ok"] is False or out["findings"]
    out2 = dco.check_coverage(
        ["AGENTS.md"], {"AGENTS.md": "tests/validation/test_rules.py"},
        tests_root=str(tmp_path))
    assert out2["covered"] == []
    assert out2["findings"]


def test_changed_docs_iterator_materialized(tmp_path):
    _mk_test(tmp_path)
    mapping = {"AGENTS.md": ["tests/validation/test_rules.py::"
                             "test_contract"]}
    docs = (d for d in ["AGENTS.md", "docs/x.md"])
    out = dco.check_coverage(docs, mapping, tests_root=str(tmp_path))
    assert out["stats"]["changed"] == 2
    assert out["stats"]["covered"] == 1
    assert out["stats"]["findings"] == 1




def _snapshot(n=12, obs="obs-1"):
    els = [{"id": f"e{i}", "role": "button", "name": f"item {i}",
            "enabled": True} for i in range(n)]
    return {"observation_id": obs, "elements": els}


def test_shortlist_caps_at_eight_deterministic():
    a = dp.shortlist(_snapshot(20)["elements"])
    b = dp.shortlist(_snapshot(20)["elements"])
    assert len(a) == 8
    assert [c["id"] for c in a] == [c["id"] for c in b]


def test_shortlist_limit_clamped():
    els = [{"id": f"e{i}", "role": "button", "enabled": True}
           for i in range(20)]
    assert len(dp.shortlist(els, limit=100)) <= 8
    assert dp.shortlist(els, limit=-3) == []


def test_duplicate_ids_deduped():
    els = [{"id": "same", "role": "button", "enabled": True},
           {"id": "same", "role": "button", "enabled": True},
           {"id": "other", "role": "button", "enabled": True}]
    ids = [c["id"] for c in dp.shortlist(els)]
    assert ids == ["same", "other"]


def test_hidden_elements_filtered():
    els = [{"id": "h1", "role": "button", "enabled": True,
            "hidden": True},
           {"id": "h2", "role": "button", "enabled": True,
            "aria_hidden": True},
           {"id": "h3", "role": "button", "enabled": True,
            "style": "display:none"},
           {"id": "v1", "role": "button", "enabled": True}]
    assert [c["id"] for c in dp.shortlist(els)] == ["v1"]


def test_malformed_actionable_filtered():
    els = [{"id": "m1", "role": "button", "enabled": True,
            "actionable": "yes"},
           {"id": "ok", "role": "button", "enabled": True}]
    assert [c["id"] for c in dp.shortlist(els)] == ["ok"]


def test_unknown_role_requires_explicit_actionable():
    els = [{"id": "u1", "role": "weird-widget", "enabled": True},
           {"id": "u2", "role": "weird-widget", "enabled": True,
            "actionable": True}]
    assert [c["id"] for c in dp.shortlist(els)] == ["u2"]


def test_disabled_and_unsafe_never_candidates():
    els = [{"id": "ok", "role": "button", "name": "go", "enabled": True},
           {"id": "d1", "role": "button", "name": "off",
            "enabled": False},
           {"id": "u1", "role": "button", "name": "x", "enabled": True,
            "unsafe": True}]
    ids = [c["id"] for c in dp.shortlist(els)]
    assert ids == ["ok"]


def test_stale_snapshot_abstains():
    snap = _snapshot(obs="obs-old")
    rec = dp.pick(None, {}, "item 1", snap,
                  expected_observation_id="obs-new")
    assert rec["outcome"] == "abstain"
    assert "stale" in rec["reason"]


def test_explicitly_marked_stale_abstains():
    snap = _snapshot()
    snap["stale"] = True
    rec = dp.pick(None, {}, "item 1", snap)
    assert rec["outcome"] == "abstain"


def test_empty_after_filtering_abstains():
    snap = {"observation_id": "o", "elements": [
        {"id": "d", "role": "button", "enabled": False}]}
    rec = dp.pick(None, {}, "goal", snap)
    assert rec["outcome"] == "abstain"


def test_daemon_unavailable_is_typed_abstain(tmp_path, monkeypatch):
    monkeypatch.setenv("LAYA_NO_DAEMON", "1")
    cfg = tmp_path / "profile.json"
    cfg.write_text(json.dumps({"version": 1, "mode": "shadow",
                               "profiles": ["ui-target-v1"]}))
    rec = dp.suggest_dom(_snapshot(3), goal="item 1", context={},
                         config=str(cfg))
    if rec["outcome"] == "suggestion":
        assert rec["reason"] == "exact_match"
        assert rec["candidate_id"] == "e1"
    else:
        assert rec["reason"] in ("daemon_unavailable",
                                 "daemon_unreachable", "feature_off")


def test_mode_off_with_assist_override_never_raises(tmp_path,
                                                    monkeypatch):
    monkeypatch.setenv("LAYA_NO_DAEMON", "1")
    cfg = tmp_path / "profile.json"
    cfg.write_text(json.dumps({"version": 1, "mode": "off",
                               "profiles": ["ui-target-v1"]}))
    called = []
    monkeypatch.setattr(dp.lc, "ensure_daemon",
                        lambda *a, **k: called.append(1) or None)
    rec = dp.suggest_dom(_snapshot(3), goal="item 1", context={},
                         config=str(cfg), mode="assist")
    assert called == []
    assert rec["outcome"] == "abstain"
    assert rec["mode"] == "off"


def test_uncalibrated_assist_override_degrades(tmp_path, monkeypatch):
    monkeypatch.setenv("LAYA_NO_DAEMON", "1")
    cfg = tmp_path / "profile.json"
    cfg.write_text(json.dumps({"version": 1, "mode": "assist",
                               "calibration": None,
                               "profiles": ["ui-target-v1"]}))
    rec = dp.suggest_dom(_snapshot(3), goal="zzznomatch", context={},
                         config=str(cfg), mode="assist")
    assert rec["outcome"] == "abstain"
    assert rec["mode"] != "assist"


def test_exact_match_shortcircuits_before_daemon(tmp_path,
                                                 monkeypatch):
    cfg = tmp_path / "profile.json"
    cfg.write_text(json.dumps({"version": 1, "mode": "shadow",
                               "profiles": ["ui-target-v1"]}))
    called = []
    monkeypatch.setattr(dp.lc, "ensure_daemon",
                        lambda *a, **k: called.append(1) or None)
    rec = dp.suggest_dom(_snapshot(4), goal="item 2", context={},
                         config=str(cfg), mode="shadow")
    assert called == []
    assert rec["outcome"] == "suggestion"
    assert rec["candidate_id"] == "e2"


def test_non_list_elements_abstains_not_raises():
    for bad in ("bogus", {"e": {}}, 42):
        rec = dp.pick(None, {}, "goal", {"elements": bad})
        assert rec["outcome"] == "abstain"
        rec2 = dp.suggest_dom({"elements": bad}, "goal", {},
                              config=None)
        assert rec2["outcome"] == "abstain"


def test_suggestion_is_only_typed_never_action():
    rec = dp.pick(None, {}, "nope", _snapshot(3),
                  expected_observation_id="obs-1")
    assert rec["outcome"] in ("suggestion", "abstain")
    assert not hasattr(dp, "click") and not hasattr(dp, "dispatch")


def test_exact_match_suggests_without_client():
    rec = dp.pick(None, {}, "item 2", _snapshot(4),
                  expected_observation_id="obs-1")
    assert rec["outcome"] == "suggestion"
    assert rec["candidate_id"] == "e2"




def test_nodes_to_elements_canonical_parity_and_stable_ids():
    nodes = [{"tag": "a", "text": "Home",
              "attrib": {"id": "nav-home", "href": "/"}},
             {"tag": "button", "text": "Save",
              "attrib": {"disabled": "disabled"}},
             {"tag": "input", "text": "",
              "attrib": {"type": "password", "id": "pw"}},
             {"tag": "div", "text": "", "attrib": {"hidden": ""}},
             {"tag": "script", "text": "x()", "attrib": {}}]
    els = de.nodes_to_elements(nodes)
    assert els == dp.nodes_to_elements(nodes)
    assert els == de.nodes_to_elements(nodes)
    by_id = {e["id"]: e for e in els}
    assert "nav-home" in by_id
    assert by_id["nav-home"]["enabled"] is True
    assert "pw" in by_id and by_id["pw"]["unsafe"] is True
    assert any(e["enabled"] is False for e in els)
    assert any(e["hidden"] is True for e in els)
    ids = [c["id"] for c in dp.shortlist(els)]
    assert "nav-home" in ids
    assert "pw" not in ids
    assert all(e["enabled"] for e in dp.shortlist(els))




def test_review_gate_cli(tmp_path):
    diff = tmp_path / "d.diff"
    diff.write_text(_diff("requirements.txt", added=["+requests"]))
    msg = tmp_path / "m.txt"
    msg.write_text("deps: add requests because scraping")
    out = subprocess.run(
        [sys.executable,
         str(ROOT / "extensions" / "laya-tools" / "review_gate.py"),
         "--diff", str(diff), "--commit-msg-file", str(msg)],
        capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["ok"] is True and data["risk"] == "high"


def test_dom_picker_cli(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps(_snapshot(5)))
    out = subprocess.run(
        [sys.executable,
         str(ROOT / "extensions" / "computer-use" / "cu_dom_picker.py"),
         "--snapshot", str(snap), "--goal", "item 3",
         "--observation-id", "obs-1"],
        capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["ok"] is True
    assert data["outcome"] in ("suggestion", "abstain")


class _CountingStdin:
    def __init__(self, payload):
        self._payload = payload
        self.sizes = []

    def read(self, n=-1):
        self.sizes.append(n)
        return self._payload if n is None or n < 0 else self._payload[:n]


def test_picker_stdin_read_is_bounded(monkeypatch):
    fake = _CountingStdin(json.dumps(_snapshot(3)))
    monkeypatch.setattr(sys, "stdin", fake)
    assert dp.main(["--snapshot", "-", "--goal", "x"]) == 0
    assert fake.sizes == [dp.MAX_SNAPSHOT_BYTES + 1]


def test_picker_stdin_oversize_rejected_before_parse(monkeypatch):
    fake = _CountingStdin("x" * (dp.MAX_SNAPSHOT_BYTES + 10))
    monkeypatch.setattr(sys, "stdin", fake)
    assert dp.main(["--snapshot", "-", "--goal", "x"]) == 2
    assert fake.sizes == [dp.MAX_SNAPSHOT_BYTES + 1]


def test_dom_elements_stdin_read_is_bounded(monkeypatch):
    fake = _CountingStdin('{"nodes": []}')
    monkeypatch.setattr(sys, "stdin", fake)
    assert de.main(["-"]) == 0
    assert fake.sizes == [de.MAX_INPUT_BYTES + 1]


def test_dom_elements_stdin_oversize_rejected(monkeypatch):
    fake = _CountingStdin("x" * (de.MAX_INPUT_BYTES + 10))
    monkeypatch.setattr(sys, "stdin", fake)
    assert de.main(["-"]) == 2
    assert fake.sizes == [de.MAX_INPUT_BYTES + 1]


def test_read_bounded_counts_bytes_not_chars(tmp_path):
    f = tmp_path / "s.json"
    f.write_text("é" * 10, encoding="utf-8")
    assert dp.read_bounded(str(f), 10) is None
    assert dp.read_bounded(str(f), 20) == "é" * 10


def test_read_bounded_file_oversize(tmp_path):
    f = tmp_path / "big.json"
    f.write_bytes(b"x" * 100)
    assert dp.read_bounded(str(f), 50) is None
