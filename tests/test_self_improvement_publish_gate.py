"""self-improvement skill documents the human publish gate."""
import os


def test_publish_gate_section():
    p = os.path.join("skills", "self-improvement", "SKILL.md")
    text = open(p, encoding="utf-8").read().lower()
    assert "publish" in text
    assert "proposal" in text
    # the gate must bind publish to a human decision
    assert "human" in text or "user" in text
