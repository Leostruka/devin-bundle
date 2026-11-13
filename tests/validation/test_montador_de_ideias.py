"""Contract tests for skills/montador-de-ideias and its /leo + ask-bundle routing."""
from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILL_DIR = ROOT / "skills" / "montador-de-ideias"
SKILL_MD = SKILL_DIR / "SKILL.md"

REFERENCES = [
    "journalistic-osint-protocol.md",
    "first-principles-justification.md",
    "atomic-modular-hardening.md",
    "contact-surfaces-excellence.md",
]

TEMPLATES = [
    "idea-dossier.md",
    "compiled-prompt.md",
]


def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_skill_frontmatter_and_core_pipeline():
    assert SKILL_MD.is_file(), "skills/montador-de-ideias/SKILL.md missing"
    text = skill_text()
    assert text.startswith("---\n"), "missing YAML frontmatter start"
    parts = text.split("---", 2)
    assert len(parts) >= 3, "unclosed YAML frontmatter"
    fm = parts[1]
    assert "name: montador-de-ideias" in fm
    desc_lines = [line for line in fm.splitlines() if line.startswith("description:")]
    assert len(desc_lines) == 1
    assert "Use when" in desc_lines[0]
    assert "triggers: [user, model]" in fm

    for required_token in (
        "original_prompt_sha256",
        "ask_user_question",
        "HARD-GATE",
        "journalistic-osint-protocol.md",
        "first-principles-justification.md",
        "atomic-modular-hardening.md",
        "contact-surfaces-excellence.md",
        "idea-dossier.md",
        "compiled-prompt.md",
        "Facilitar",
        "Resolver",
        "Impressionar",
        "Ser Intuitivo",
        "researcher",
    ):
        assert required_token in text, f"SKILL.md missing required token: {required_token}"
