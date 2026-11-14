"""Contract tests for skills/adaptive-agenda-calendar-routine-engine (#613).

Agent-chosen validation tests (tests/validation/): pin the skill's
frontmatter and discovery contract, required coverage tokens, the
reference playbooks, and the no-em/en-dash rule.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "adaptive-agenda-calendar-routine-engine"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE_DIR = SKILL_DIR / "reference"
REFERENCE_FILES = [
    "temporal-architecture.md",
    "profiles.md",
    "five-stages.md",
]

# Task 2: executor skills that must point back at the orchestrator so
# agents discover the engine from whichever skill they already loaded.
WIRED_SKILLS = [
    "afk-loop",
    "scheduled-turns",
    "roteiro",
    "continuous-improvement",
    "self-improvement",
    "retro",
    "planning",
    "executing-plans",
    "gates",
    "autonomous-gates",
    "handoff",
    "task-sizer",
    "writing-plans",
    "planning-pipeline",
    "project-memory",
]

REQUIRED_TOKENS = [
    "HH:MM",
    "handoff",
    "workbench",
    "objetivo_primario",
    "objetivos_secundarios",
    "foco-novidades",
    "foco-qualidade-produto",
    "foco-interno",
    "foco-externo",
    "32",
    "Open-Minded Scrum",
    "Steve Jobs",
    "extensions/gcal/wrapper.py",
    "dossie",
    "radar",
]

# U+2014 em dash, U+2013 en dash - written as escapes so this file
# itself carries no literal dash characters.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def _read(path):
    return path.read_text(encoding="utf-8")


def _skill_files():
    return [SKILL_MD] + [REFERENCE_DIR / n for n in REFERENCE_FILES]


def test_skill_md_exists_with_valid_frontmatter():
    text = _read(SKILL_MD)
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert fm, "SKILL.md must start with a YAML frontmatter block"
    block = fm.group(1)
    assert re.search(
        r"^name:\s*adaptive-agenda-calendar-routine-engine\s*$",
        block, re.M), \
        "frontmatter name must match the skill directory"
    desc = re.search(r"^description:\s*(.+)$", block, re.M)
    assert desc, "frontmatter description missing"
    assert desc.group(1).strip().startswith("Use when"), \
        "description must start with 'Use when'"
    assert len(desc.group(1)) <= 1024, "description exceeds 1024 chars"
    assert "triggers: [user, model]" in block, \
        "triggers must be [user, model]"


def test_skill_md_covers_required_tokens():
    text = _read(SKILL_MD)
    missing = [t for t in REQUIRED_TOKENS if t not in text]
    assert not missing, f"SKILL.md missing required tokens: {missing}"


def test_reference_playbooks_exist_and_have_content():
    for name in REFERENCE_FILES:
        path = REFERENCE_DIR / name
        assert path.is_file(), f"missing reference file: {path}"
        body = _read(path).strip()
        assert len(body) > 500, f"{name} is too thin ({len(body)} chars)"


def test_reference_playbooks_cover_engine_surface():
    temporal = _read(REFERENCE_DIR / "temporal-architecture.md")
    profiles = _read(REFERENCE_DIR / "profiles.md")
    stages = _read(REFERENCE_DIR / "five-stages.md")
    # Temporal layer: HH:MM blocks, handoff rite, gcal wrapper commands.
    for token in ("HH:MM", "handoff", "free-busy", "plan", "apply",
                  "add", "--confirm", "confirm-required", "AGdevin"):
        assert token in temporal, \
            f"temporal-architecture.md missing: {token}"
    # Profiles: all four names + combination rules + Jobs/hardware axes.
    for token in ("foco-novidades", "foco-qualidade-produto",
                  "foco-interno", "foco-externo", "Steve Jobs",
                  "zero-trust", "hardware", "dominant"):
        assert token in profiles, \
            f"profiles.md missing: {token}"
    # Stages: workbench YAML schema keys, batteries, self-eval.
    for token in ("objetivo_primario", "objetivos_secundarios",
                  "ferramentas_na_bancada", "regras_e_decisoes",
                  "janela_horario", "perfil_ativo", "battery",
                  "Open-Minded Scrum", "dossie"):
        assert token in stages, \
            f"five-stages.md missing: {token}"


def test_no_em_or_en_dashes_in_skill_files():
    for path in _skill_files():
        text = _read(path)
        assert EM_DASH not in text, \
            f"{path.relative_to(ROOT)} contains an em dash (U+2014)"
        assert EN_DASH not in text, \
            f"{path.relative_to(ROOT)} contains an en dash (U+2013)"


def test_wired_skills_reference_adaptive_engine():
    """Each executor skill carries a pointer to
    adaptive-agenda-calendar-routine-engine (cross-skills/see-also)."""
    for name in WIRED_SKILLS:
        path = ROOT / "skills" / name / "SKILL.md"
        assert path.is_file(), f"missing skill file: {path}"
        text = _read(path)
        assert "adaptive-agenda-calendar-routine-engine" in text, \
            f"{name}/SKILL.md does not reference the adaptive engine"
