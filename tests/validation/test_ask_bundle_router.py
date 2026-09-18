from pathlib import Path


ROOT = Path(__file__).parents[2]
ROUTER = ROOT / "skills" / "ask-bundle" / "SKILL.md"


def router_text():
    return ROUTER.read_text(encoding="utf-8")


def test_router_is_universal_entry_point():
    text = router_text()
    assert "one entry point" in text.lower()
    assert "route" in text.lower()
    assert "verified completion" in text


def test_router_routes_foggy_effort_to_planning():
    text = router_text()
    assert "`planning` wayfinder" in text


def test_router_covers_specialist_domains():
    text = router_text()
    for skill in (
        "deploy",
        "security",
        "data-analyst",
        "impeccable",
        "observability-quality",
        "wizard",
        "teach",
    ):
        assert f"`{skill}`" in text


def test_router_references_merged_skill_names():
    text = router_text()
    for skill in (
        "grilling",
        "planning",
        "execution",
        "testing",
        "debugging",
        "intake",
        "gates",
        "code-review",
        "git-workflows",
        "architecture",
        "self-improvement",
        "devin-config",
        "skill-discovery",
        "context-hygiene",
        "project-bootstrap",
    ):
        assert f"`{skill}`" in text
