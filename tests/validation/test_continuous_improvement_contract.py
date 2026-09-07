"""Validation tests for the continuous-improvement execution contract."""
from pathlib import Path


BUNDLE_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = BUNDLE_ROOT / "skills" / "continuous-improvement" / "SKILL.md"


def skill_text():
    return SKILL_PATH.read_text(encoding="utf-8")


def frontmatter():
    text = skill_text()
    return text.split("---", 2)[1]


def test_continuous_improvement_runs_inline_by_default():
    metadata = frontmatter()
    assert "subagent:" not in metadata
    assert "agent:" not in metadata


def test_contract_preserves_inputs_sources_and_verification():
    text = skill_text()
    for marker in ("DELEGATION", "INPUT_REGISTER", "SOURCE_REGISTER", "VFS", "SCOPE"):
        assert marker in text
    for marker in ("OUTCOME", "CHECK", "EXPECT", "EVIDENCE"):
        assert marker in text
    assert "INPUT_COVERAGE" in text
    assert "`MELHOROU` exige held-out" in text


def test_contract_protects_install_and_unrelated_changes():
    text = skill_text()
    assert "dry-run" in text
    assert "DELEGATION=disabled" in text
    assert "git checkout` amplo" in text
    assert "patch próprio" in text


def test_contract_requires_change_classification():
    assert "CHANGE_CLASS" in skill_text()
