"""extensions/harness-tree - read/diff/apply/validate/ns fixture tests (M2_09)."""
import os
import subprocess
import sys

import pytest

EXT = os.path.join(os.path.dirname(__file__), "..", "extensions",
                   "harness-tree")
PY = sys.executable
sys.path.insert(0, EXT)
import specs  # noqa: E402
import tree  # noqa: E402


def run(script, *argv):
    return subprocess.run([PY, os.path.join(EXT, script), *argv],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


@pytest.fixture()
def root(tmp_path):
    r = tmp_path / "bundle"
    for rel, body in {
        "AGENTS.md": "# rules\n",
        ".devin/global_rules.md": "# project\n",
        ".devin/rules/foo.md": "rule\n",
        "hooks.v1.json": "{}\n",
        ".devin/memory/MOC.md": "mem\n",
        "skills/alpha/SKILL.md": "skill\n",
        "skills/skill-discovery/SKILL.md": "disc\n",
        "skills/ask-bundle/SKILL.md": "ask\n",
        ".devin/docs/SKILL-TIERS.md": "tiers\n",
        ".devin/agents/domain.md": "agent\n",
        "scripts/tool.py": "print(1)\n",
        "scripts/check-ai-signature.py": "reserved\n",
        "mcp_config.json": "{}\n",
        "manifest.json": "{}\n",
        "untracked.txt": "outside\n",
        "skills/x/__pycache__/y.pyc": "noise\n",
    }.items():
        p = r / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return str(r)


def test_read_scoped_and_deduped(root):
    t = tree.read(root)
    assert "untracked.txt" not in t
    assert "skills/x/__pycache__/y.pyc" not in t
    # c4 paths also under c6 skills/ must appear exactly once
    assert len(t) == len(set(t))
    assert specs.component_of(specs.DEVIN,
                            "skills/skill-discovery/SKILL.md") == (
        "c4_tool_guidance")


def test_roundtrip_diff_apply(root):
    a = tree.read(root)
    p = os.path.join(root, "skills/alpha/SKILL.md")
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("v2\n")
    b = tree.read(root)
    assert tree.apply(a, tree.diff(a, b)) == b


def test_apply_refuses_reserved_and_outside(root):
    a = tree.read(root)
    with pytest.raises(ValueError):
        tree.apply(a, {"scripts/check-ai-signature.py": "evil\n"})
    with pytest.raises(ValueError):
        tree.apply(a, {"untracked.txt": "x\n"})


def test_apply_delete(root):
    a = tree.read(root)
    out = tree.apply(a, {"skills/alpha/SKILL.md": None})
    assert "skills/alpha/SKILL.md" not in out


def test_validate_clean_fixture(root):
    r = run("tree.py", "validate", root)
    assert r.returncode == 0, r.stdout
    assert "OK: 0 problem(s)" in r.stdout


def test_validate_reports_missing(tmp_path):
    r = run("tree.py", "validate", str(tmp_path))
    assert r.returncode == 1
    assert "missing:" in r.stdout


def test_ns_create_resume(root, tmp_path):
    runs = str(tmp_path / "runs")
    r = run("ns.py", "create", root, "--seed", "s1", "--runs-dir", runs)
    assert r.returncode == 0, r.stderr
    rdir = r.stdout.strip()
    assert os.path.isfile(os.path.join(rdir, "tree.json"))
    assert os.path.isfile(os.path.join(rdir, "meta.json"))
    r = run("ns.py", "resume", rdir)
    assert r.returncode == 0
    assert '"files"' in r.stdout and '"sha"' in r.stdout
    # writes stay inside runs dir
    assert os.path.dirname(rdir) == runs


def test_diff_cli_roots(root):
    a = tree.read(root)
    a["skills/alpha/SKILL.md"] = "changed\n"
    d = tree.diff(tree.read(root), a)
    assert d == {"skills/alpha/SKILL.md": "changed\n"}


def test_real_bundle_validates():
    repo = os.path.join(os.path.dirname(__file__), "..")
    r = run("tree.py", "validate", repo)
    assert r.returncode == 0, r.stdout[-2000:]
