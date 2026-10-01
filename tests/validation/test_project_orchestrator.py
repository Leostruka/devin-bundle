"""Contract tests for skills/project-orchestrator (string presence + files).

Spec: .devin/plans/2026-09-28-project-orchestrator.prompt.md acceptance
criteria 1-14. Asserts structure and required vocabulary only.
AI-signature absence is enforced by check-ai-signature.py and
validate-skill-format.py (see test_skill_format_passes.py), not re-asserted
here to keep signature literals out of the test file.
"""
from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILL_DIR = ROOT / "skills" / "project-orchestrator"
SKILL_MD = SKILL_DIR / "SKILL.md"

TEMPLATES = [
    "intake-vision.md",
    "development-case.md",
    "role-matrix.md",
    "delegation-contract.md",
    "handoff-doc.md",
    "ledger.md",
    "raid-register.md",
    "adr.md",
    "worker-role.md",
    "advisor-charter.md",
    "team-pack.md",
]

REFERENCE = [
    "methodology-selection.md",
    "research-protocol.md",
    "quality-gates.md",
    "advisor-protocol.md",
]


def skill_text():
    return SKILL_MD.read_text(encoding="utf-8")


def all_text():
    parts = [skill_text()]
    for sub in ("templates", "reference"):
        for f in (SKILL_DIR / sub).glob("*.md"):
            parts.append(f.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_skill_frontmatter_valid():
    text = skill_text()
    assert text.startswith("---"), "missing frontmatter"
    fm = text.split("---")[1]
    assert "name: project-orchestrator" in fm
    desc = [l for l in fm.splitlines() if l.startswith("description:")][0]
    assert "Use when" in desc


def test_all_templates_exist():
    for name in TEMPLATES:
        assert (SKILL_DIR / "templates" / name).is_file(), f"missing template {name}"


def test_all_reference_docs_exist():
    for name in REFERENCE:
        assert (SKILL_DIR / "reference" / name).is_file(), f"missing reference {name}"
    assert (SKILL_DIR / "USAGE.pt.md").is_file(), "missing PT usage doc"


def test_phase_route_present():
    text = skill_text()
    for token in (
        "Analyst",
        "Inception",
        "Methodology",
        "walking skeleton",
        "INVEST",
        "MoSCoW",
        "RICE",
        "semver",
        "CI/CD",
        "DORA",
        "golden signals",
    ):
        assert token in text, f"phase route missing {token}"


def test_methodology_and_research_codified():
    text = all_text()
    for token in ("Cynefin", "RUP", "Scrum", "hybrid", "PRISMA",
                  "lateral reading", "entailment"):
        assert token in text, f"missing {token}"


def test_orchestration_mechanics_present():
    text = all_text()
    for token in (
        "run_subagent",
        "delegation-contract",
        "handoff-doc",
        "Task Ledger",
        "Progress Ledger",
        "RAID",
        "workers/",
        ".devin/ledgers/",
        ".devin/adr/",
        ".devin/handoffs/",
        "qa-ci",
        "grilling",
        "ask_user_question",
        "termination",
    ):
        assert token in text, f"missing {token}"


def test_quality_and_excellence_bar():
    text = all_text()
    for token in (
        "Nielsen",
        "LCP",
        "INP",
        "CLS",
        "record.py",
        "computer-use",
        "time-to-value",
    ):
        assert token in text, f"missing {token}"


def test_subconscious_advisor_codified():
    text = all_text()
    for token in (
        "advisor",
        "terminal.py",
        "send-to",
        "HYGIENE",
        "RESET_ORCHESTRATOR",
        "MEMORY DELTA",
        "onboarding.md",
        ".devin/advisor/",
        "resume",
        "devin acp",
        "consultative",
    ):
        assert token in text, f"missing {token}"


def test_maestri_improvements_codified():
    text = all_text()
    for token in (
        "ESCALATE",
        "## Status",
        "Frozen inputs",
        "sha256",
        "handle:",
        "reassign",
        "spent:",
        "consumed",
        "trigger",
        "Lane setup",
        "Lane teardown",
        "$LANE_PATH",
        "Peer consults",
        "CONSULT:",
        "Readable refs",
        "team-pack",
    ):
        assert token in text, f"missing {token}"


def test_no_em_dashes():
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)
    for f in SKILL_DIR.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        assert em_dash not in text and en_dash not in text, f"dash in {f.name}"
