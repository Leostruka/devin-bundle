"""Task 12 gate: system-control distribution — thin skill router,
USAGE contract, manifest sync, installer enumeration."""
import json
import os
import re

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _read(rel):
    with open(os.path.join(repo_root, rel), encoding="utf-8") as fh:
        return fh.read()


def test_system_control_skill_is_thin_router():
    text = _read("skills/system-control/SKILL.md")
    assert "extensions/system-control/USAGE.md" in text
    assert len(text.splitlines()) <= 80


def test_system_control_skill_frontmatter_triggers():
    text = _read("skills/system-control/SKILL.md")
    fm = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert fm, "SKILL.md must start with YAML frontmatter"
    assert "triggers: [user, model]" in fm.group(1)
    assert re.search(r"^name:\s*system-control\s*$", fm.group(1), re.M)
    assert "description:" in fm.group(1)


def test_system_control_workflow_declares_safe_defaults():
    usage = _read("extensions/system-control/USAGE.md")
    for phrase in ["no privileged daemon by default",
                   "one-shot confirmation", "dropped"]:
        assert phrase in usage


def test_manifest_has_system_control_entry():
    manifest = json.loads(_read("manifest.json"))
    names = {s["name"] for s in manifest["skills"]}
    assert "system-control" in names
    entry = next(s for s in manifest["skills"]
                 if s["name"] == "system-control")
    assert entry.get("purpose", "").startswith("Use when")


def test_installer_enumerates_extensions_dirs_generically():
    """install.sh loops over extensions/*/ — system-control needs no
    special-casing; pin the generic enumeration, not the name."""
    install = _read("install.sh")
    assert 'for ext_dir in "$ext_src"/*/' in install
    # PowerShell installer enumerates Get-ChildItem over extensions.
    ps1 = _read("install.ps1")
    assert "extensions" in ps1 and "Get-ChildItem" in ps1
