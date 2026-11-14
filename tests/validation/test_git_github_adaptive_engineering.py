"""Contract tests for skills/git-github-adaptive-engineering (#612).

Agent-chosen validation tests (tests/validation/): pin the skill's
frontmatter and discovery contract, required coverage tokens, the
reference playbooks, the no-em/en-dash rule, and the phase-zero.py
envelope-v2 probe (offline-safe subprocess, modelled on
tests/test_envelope_contract_v2.py PROBES rows).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "git-github-adaptive-engineering"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE_DIR = SKILL_DIR / "reference"
REFERENCE_FILES = [
    "decision-flows.md",
    "gh-arsenal.md",
    "density-templates.md",
]
PHASE_ZERO = ROOT / "scripts" / "phase-zero.py"

# Task 2: executor skills that must point back at the orchestrator so
# agents discover the engine from whichever skill they already loaded.
WIRED_SKILLS = [
    "gh",
    "git-helper",
    "git-workflows",
    "github-actions",
    "pr",
    "debug-ci-failures",
    "deploy",
    "resolving-merge-conflicts",
    "using-git-worktrees",
    "finishing-a-development-branch",
]

REQUIRED_TOKENS = [
    "Fase Zero",
    "decision engine",
    "hotfix",
    "ADR",
    "ruleset",
    "gh secret",
    "gh variable",
    "gh workflow",
    "gh run view",
    "Closes #",
    "Refs:",
    "sub-issue",
    "git commit -F",
    "--body-file",
    "Mermaid",
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
        r"^name:\s*git-github-adaptive-engineering\s*$", block, re.M), \
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
    flows = _read(REFERENCE_DIR / "decision-flows.md")
    arsenal = _read(REFERENCE_DIR / "gh-arsenal.md")
    density = _read(REFERENCE_DIR / "density-templates.md")
    # Five flow patterns incl. hotfix fast-track + patch release.
    for token in ("hotfix", "patch release", "regression test",
                  "RFC", "ADR", "ruleset", "sub-issue"):
        assert token in flows, f"decision-flows.md missing: {token}"
    # Arsenal matrix: hierarchy, governance, CI, secrets, projects,
    # releases/attestations.
    for token in ("--add-sub-issue", "--parent", "--add-blocked-by",
                  "gh project", "rulesets", "environments",
                  "gh secret", "gh variable", "gh workflow", "gh run view",
                  "gh release", "gh attestation", "graphql"):
        assert token in arsenal, f"gh-arsenal.md missing: {token}"
    # Density templates: wiring keywords + Mermaid.
    for token in ("Refs: #", "Closes #", "git commit -F",
                  "--body-file", "mermaid"):
        assert token in density, f"density-templates.md missing: {token}"


def test_no_em_or_en_dashes_in_skill_files():
    for path in _skill_files():
        text = _read(path)
        assert EM_DASH not in text, \
            f"{path.relative_to(ROOT)} contains an em dash (U+2014)"
        assert EN_DASH not in text, \
            f"{path.relative_to(ROOT)} contains an en dash (U+2013)"


def test_phase_zero_help_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(PHASE_ZERO), "--help"],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=30, cwd=str(ROOT))
    assert proc.returncode == 0, \
        f"phase-zero.py --help exited {proc.returncode}: {proc.stderr}"
    assert "fase-zero" in proc.stdout.lower() or \
        "situational" in proc.stdout.lower()


def test_phase_zero_emits_envelope_v2_offline():
    """Subprocess probe modelled on tests/test_envelope_contract_v2.py:
    --timeout 5 bounds each gh/git probe so the run stays offline-fast
    even with no network or gh auth."""
    proc = subprocess.run(
        [sys.executable, str(PHASE_ZERO), "--timeout", "5"],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=120, cwd=str(ROOT))
    payload = json.loads(proc.stdout)
    assert payload.get("api_version") == 2, \
        f"api_version={payload.get('api_version')!r}"
    answered = payload.get("meta", {}).get("answered_by", {})
    assert answered.get("wrapper") == "phase-zero", \
        f"answered_by.wrapper={answered.get('wrapper')!r}"
    assert answered.get("bundle"), "answered_by.bundle must be non-empty"
    assert payload.get("battery") == "fase-zero"
    probes = payload.get("probes")
    assert isinstance(probes, list) and probes, "probes list missing"
    names = {p.get("probe") for p in probes}
    for expected in ("git_status", "git_branches", "git_remotes",
                     "git_log", "gh_auth", "gh_repo_view",
                     "github_tree", "gh_rulesets", "gh_workflows"):
        assert expected in names, f"probe missing: {expected}"
    for p in probes:
        assert "ok" in p, f"probe {p.get('probe')} lacks ok flag"
    summary = payload.get("summary", {})
    assert summary.get("total") == len(probes)


def test_wired_skills_reference_adaptive_engine():
    """Each executor skill carries a pointer to
    git-github-adaptive-engineering (cross-skills/cascade/see-also)."""
    for name in WIRED_SKILLS:
        path = ROOT / "skills" / name / "SKILL.md"
        assert path.is_file(), f"missing skill file: {path}"
        text = _read(path)
        assert "git-github-adaptive-engineering" in text, \
            f"{name}/SKILL.md does not reference the adaptive engine"
