from pathlib import Path


ROOT = Path(__file__).parents[2]
LEO = ROOT / "skills" / "leo" / "SKILL.md"


def leo_text():
    return LEO.read_text(encoding="utf-8")


def test_leo_is_universal_orchestrator():
    text = leo_text()
    assert "universal orchestration" in text.lower()
    assert "Route directly" in text
    assert "Return to Leo" in text
    assert "verified completion" in text


def test_leo_routes_wayfinder_without_ask_matt_detour():
    text = leo_text()
    assert "Large, foggy, multi-session effort | `wayfinder`" in text
    assert "Use `ask-matt` only" in text


def test_leo_covers_specialist_domains():
    text = leo_text()
    for skill in (
        "deploy",
        "security-audit",
        "data-analyst",
        "impeccable",
        "observability-quality",
        "wizard",
        "teach",
    ):
        assert f"`{skill}`" in text
