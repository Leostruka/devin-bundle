"""Validation smoke test: validate-skill-format.py reports all skills passing.

Agent-chosen infrastructure test (tests/validation/), distinct from held-out
behavioral tests. Verifies the skill format validator works correctly.
"""
import subprocess
import sys
import os


def test_skill_format_all_pass():
    """validate-skill-format.py must report 0 failing skills."""
    bundle_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run(
        [sys.executable, "scripts/validate-skill-format.py"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=bundle_root,
        timeout=60,
    )
    assert result.returncode == 0, f"validate-skill-format.py exited {result.returncode}"
    output = (result.stdout or "") + (result.stderr or "")
    assert "Failing: 0" in output, \
        f"Skills failing format validation\n{output[-500:]}"


def test_skills_have_minimal_content():
    """Every SKILL.md must have frontmatter and at least one section after it."""
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'skills')
    for skill in os.listdir(skills_dir):
        path = os.path.join(skills_dir, skill, 'SKILL.md')
        if not os.path.exists(path):
            continue
        text = open(path, encoding='utf-8').read()
        assert text.startswith('---'), f"{skill} missing frontmatter"
        assert text.count('---') >= 2, f"{skill} frontmatter not closed"
        assert len(text.split('---')[-1].strip()) > 100, f"{skill} has too little content"


def _load_vsf():
    import importlib.util
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    spec = importlib.util.spec_from_file_location(
        "vsf", os.path.join(root, "scripts", "validate-skill-format.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_FM_RE = __import__('re').compile(r'^---\s*\n(.*?)\n---', __import__('re').S)


def test_skill_frontmatter_strict_yaml_sweep():
    """Every repo SKILL.md frontmatter passes the strict-YAML gate (#721)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    gate = _load_vsf().frontmatter_yaml_issues
    for skill in sorted(os.listdir(os.path.join(root, 'skills'))):
        path = os.path.join(root, 'skills', skill, 'SKILL.md')
        if not os.path.exists(path):
            continue
        m = _FM_RE.match(open(path, encoding='utf-8').read())
        assert m, f"{skill}: frontmatter block not found"
        issues = gate(m.group(1))
        assert not issues, f"{skill}: {issues}"


def test_frontmatter_yaml_gate_fixtures():
    """The gate flags scalars real YAML rejects/truncates, both copies (#721)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, root)
    from audit_checks.m_integrity import _frontmatter_yaml_issues as audit_gate
    script_gate = _load_vsf().frontmatter_yaml_issues
    cases = [
        ("name: x\ndescription: a: b", True),
        ("name: x\ndescription: foo #bar", True),
        ("name: x\ndescription: - foo", True),
        ("name: x\ndescription: \"a: b\"", False),
        ("name: x\ndescription: 'a: b'", False),
        ("name: x\ndescription: a:b", False),
        ("name: x\ndescription: >\n  folded: still fine", False),
        ("name: x\ntriggers:\n  - user\n  - model", False),
        ("name: x\nmetadata:\n  author: me\n  version: \"1.0\"", False),
    ]
    for gate in (script_gate, audit_gate):
        for text, expect_issues in cases:
            issues = gate(text)
            assert bool(issues) == expect_issues, f"{gate.__module__} {text!r} -> {issues}"
