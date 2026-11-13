"""scheduled-turns skill exists and passes format validation."""
import os, re


def test_skill_file_has_valid_frontmatter():
    p = os.path.join("skills", "scheduled-turns", "SKILL.md")
    assert os.path.isfile(p)
    text = open(p, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert m, "missing frontmatter"
    assert "name: scheduled-turns" in m.group(1)
    assert "description:" in m.group(1)
    assert re.search(r"description:\s*Use when", m.group(1))


def test_skill_has_required_sections():
    text = open(os.path.join("skills", "scheduled-turns",
                             "SKILL.md"), encoding="utf-8").read()
    for section in ("## When to Use", "## Recipe", "## Guards",
                    "## Disable"):
        assert section in text, "missing " + section
    assert "schtasks" in text or "Register-ScheduledTask" in text
    assert ".devin/ledgers/" in text
