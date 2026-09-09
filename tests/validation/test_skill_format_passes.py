"""Validation smoke test: validate-skill-format.py reports all skills passing.

Agent-chosen infrastructure test (tests/validation/), distinct from held-out
behavioral tests. Verifies the skill format validator works correctly.
"""
import subprocess
import os


def test_skill_format_all_pass():
    """validate-skill-format.py must report 0 failing skills."""
    bundle_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run(
        ["python", "scripts/validate-skill-format.py"],
        capture_output=True,
        text=True,
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
