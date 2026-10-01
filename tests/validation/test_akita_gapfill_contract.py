"""Contract tests for the akita my-skills gap-fill.

Asserts the structural markers each merged mode and new skill must carry,
so the gap-fill cannot silently regress. Mirrors the style of
test_continuous_improvement_contract.py.
"""
from pathlib import Path


BUNDLE = Path(__file__).resolve().parents[2]
CR = BUNDLE / "skills" / "code-review"


def read(p):
    return p.read_text(encoding="utf-8")


def test_code_review_registers_three_new_modes():
    text = read(CR / "SKILL.md")
    for mode in ("pr-audit.md", "post-merge-audit.md", "dependency-bumps.md"):
        assert f"modes/{mode}" in text


def test_pr_audit_mode_carries_trust_and_supply_chain():
    text = read(CR / "modes" / "pr-audit.md")
    for marker in (
        "Trust Boundary",
        "untrusted",
        "claim ledger",
        "Hostile-change gate",
        "pull_request_target",
        "typosquatting",
        "[CRITICAL]",
        "[BLOCKING]",
        "[UNCERTAIN]",
        "defaultBranchRef",
    ):
        assert marker in text


def test_post_merge_audit_mode_carries_composition_checks():
    text = read(CR / "modes" / "post-merge-audit.md")
    for marker in (
        "first-parent",
        "provenance",
        "Cross-PR",
        "Test masking",
        "frozen",
        "|||||||",
        "exact",
    ):
        assert marker in text


def test_dependency_bumps_mode_carries_batch_and_disposition():
    text = read(CR / "modes" / "dependency-bumps.md")
    for marker in (
        "newest compatible",
        "default public registry",
        "Closes #",
        "tracking issue",
        "defaultBranchRef",
    ):
        assert marker in text


def test_fact_check_skill_contract():
    text = read(BUNDLE / "skills" / "fact-check" / "SKILL.md")
    for marker in (
        "claims.json",
        "run_subagent",
        "checker-prompt.md",
        "deal breaker",
        "Primary sources",
        "S1",
    ):
        assert marker in text


def test_fact_check_checker_prompt_contract():
    text = read(
        BUNDLE / "skills" / "fact-check" / "references" / "checker-prompt.md"
    )
    for marker in (
        "{{TITLE}}",
        "{{CLAIMS}}",
        "Tier 0",
        "unsupported",
        "affects_argument",
        "DISCUSS WITH AUTHOR",
    ):
        assert marker in text


def test_humanizer_skill_and_patterns():
    text = read(BUNDLE / "skills" / "humanizer" / "SKILL.md")
    assert "reference/patterns.md" in text
    patterns = read(BUNDLE / "skills" / "humanizer" / "reference" / "patterns.md")
    count = sum(
        1 for line in patterns.splitlines() if line.startswith("### ")
    )
    assert count == 25


def test_git_workflows_lane_orchestration():
    text = read(BUNDLE / "skills" / "git-workflows" / "SKILL.md")
    for marker in ("lane", "ownership", "worktrees.json"):
        assert marker in text


def test_dispatching_background_discipline():
    text = read(
        BUNDLE / "skills" / "dispatching-parallel-agents" / "SKILL.md"
    )
    assert "is_background" in text
    assert "unreconciled" in text
