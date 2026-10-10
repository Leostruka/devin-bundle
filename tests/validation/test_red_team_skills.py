"""Red-team capability gate: skills contract, wrappers, manifest sync,
and safety boundaries for the offensive-skill tree."""
import json
import os
import py_compile
import re

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

RED_TEAM_SKILLS = [
    "red-team", "re-binary", "web-probe", "net-probe",
    "wireless-probe", "firmware-probe", "mobile-probe",
]


def _read(rel):
    with open(os.path.join(repo_root, rel), encoding="utf-8") as fh:
        return fh.read()


def test_red_team_skills_exist_with_valid_frontmatter():
    for name in RED_TEAM_SKILLS:
        text = _read("skills/%s/SKILL.md" % name)
        fm = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert fm, "%s: SKILL.md must start with YAML frontmatter" % name
        assert re.search(r"^name:\s*%s\s*$" % name, fm.group(1), re.M), name
        desc = re.search(r"^description:\s*(.+)$", fm.group(1), re.M)
        assert desc and desc.group(1).startswith("Use when"), name
        assert "triggers: [user, model]" in fm.group(1), name
        assert len(text.splitlines()) >= 20, "%s: body too thin" % name


def test_red_team_skills_declare_engagement_contract():
    for name in RED_TEAM_SKILLS:
        text = _read("skills/%s/SKILL.md" % name).lower()
        for field in ("target", "window", "roe"):
            assert field in text, "%s: missing contract field %s" % (
                name, field)


def test_red_team_skills_keep_safety_boundaries():
    text = _read("skills/red-team/SKILL.md").lower()
    assert "credential" in text  # no-credential-harvesting boundary stated
    assert "unknown" in text     # missing tool must report unknown
    for name in RED_TEAM_SKILLS:
        body = _read("skills/%s/SKILL.md" % name).lower()
        assert "boundaries" in body, "%s: missing Boundaries section" % name


def test_wrappers_exist_and_compile():
    for rel in ("extensions/rea-ops/wrapper.py",
                "extensions/offsec-tools/wrapper.py"):
        path = os.path.join(repo_root, rel)
        assert os.path.isfile(path), rel
        py_compile.compile(path, doraise=True)


def test_offsec_wrapper_enforces_contract_and_modes():
    src = _read("extensions/offsec-tools/wrapper.py")
    for field in ("target", "window", "roe"):
        assert '"%s"' % field in src or "'%s'" % field in src
    assert "requires_confirmation" in src
    assert "unsupported_platform" in src
    assert '"wsl"' in src and '"docker"' in src and '"native"' in src
    assert "credential" in src.lower()  # no credential-harvesting note


def test_rea_wrapper_whitelists_subcommands():
    src = _read("extensions/rea-ops/wrapper.py")
    assert "EXEC_SUBCOMMANDS" in src
    for sub in ("analyze", "inspect", "search", "xrefs", "compare"):
        assert '"%s"' % sub in src
    assert "rea-agents" in src and "npx" in src


def test_no_shell_dispatch_in_wrappers():
    for rel in ("extensions/rea-ops/wrapper.py",
                "extensions/offsec-tools/wrapper.py"):
        src = _read(rel)
        assert "shell=True" not in src, rel
        assert "os.system" not in src, rel
        assert "subprocess.run" in src, rel


def test_red_team_lead_agent_registered():
    text = _read("agents/red-team-lead.md")
    fm = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert fm and "name: red-team-lead" in fm.group(1)
    assert "description:" in fm.group(1)
    assert "roe" in text.lower()


def test_manifest_covers_red_team_components():
    manifest = json.loads(_read("manifest.json"))
    names = {s["name"] for s in manifest["skills"]}
    for name in RED_TEAM_SKILLS:
        assert name in names, "manifest missing skill %s" % name
        entry = next(s for s in manifest["skills"] if s["name"] == name)
        assert entry.get("purpose", "").startswith("Use when"), name
    agent_names = {a["name"] for a in manifest.get("agents", [])}
    assert "red-team-lead" in agent_names
    disk_skills = {d for d in os.listdir(os.path.join(repo_root, "skills"))
                   if os.path.isdir(os.path.join(repo_root, "skills", d))}
    assert manifest.get("skill_count") == len(disk_skills)


def test_installer_enumerates_new_dirs_generically():
    """install.ps1 loops skills/*/extensions/*/ -- new components need no
    special-casing; pin the generic enumeration."""
    ps1 = _read("install.ps1")
    assert "Get-ChildItem" in ps1
    assert "skills" in ps1 and "extensions" in ps1
