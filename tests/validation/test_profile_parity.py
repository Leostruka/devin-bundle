"""Every agents/*.md profile must be dispatchable through run_subagent.

validate-tool-args.py rejects unknown profiles, so a new agent file that
ships without a VALID_PROFILES entry is undispatchable. This drift bit
twice (chief-of-staff, sentinel); pin the parity.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _valid_profiles():
    src = open(os.path.join(ROOT, "scripts", "validate-tool-args.py"),
               encoding="utf-8").read()
    m = re.search(r"VALID_PROFILES = frozenset\(\{([^}]*)\}", src, re.S)
    assert m, "VALID_PROFILES set not found in validate-tool-args.py"
    return {p.strip().strip("\"'") for p in m.group(1).split(",") if p.strip()}


def _disk_profiles():
    names = set()
    for adir in (os.path.join(ROOT, "agents"),
                 os.path.join(ROOT, ".devin", "agents")):
        for f in os.listdir(adir):
            if f.endswith(".md") and f != "README.md":
                names.add(f[:-3])
    return names


def test_every_disk_profile_is_dispatchable():
    missing = _disk_profiles() - _valid_profiles()
    assert not missing, (
        f"agents/ profiles missing from VALID_PROFILES: {sorted(missing)}"
    )


def test_project_agents_have_frontmatter():
    for name in sorted(_disk_profiles()):
        path = next(
            p for p in (os.path.join(ROOT, "agents", name + ".md"),
                        os.path.join(ROOT, ".devin", "agents", name + ".md"))
            if os.path.exists(p))
        head = open(path, encoding="utf-8").read(400)
        assert head.startswith("---"), f"{name}: missing frontmatter"
        assert re.search(r"^name:\s*" + re.escape(name) + r"\s*$", head, re.M), \
            f"{name}: frontmatter name mismatch"


def _profile_deny():
    src = open(os.path.join(ROOT, "scripts", "validate-tool-args.py"),
               encoding="utf-8").read()
    m = re.search(r"PROFILE_DENY = \{(.*?)\n\}", src, re.S)
    assert m, "PROFILE_DENY map not found in validate-tool-args.py"
    return set(re.findall(r'"([^"]+)":\s*frozenset', m.group(1)))


def _exec_free_profiles():
    """agents/*.md profiles whose allowed-tools do not grant exec."""
    out = set()
    for name in _disk_profiles():
        path = next(
            (p for p in (os.path.join(ROOT, "agents", name + ".md"),
                         os.path.join(ROOT, ".devin", "agents", name + ".md"))
             if os.path.exists(p)), None)
        if not path:
            continue
        head = open(path, encoding="utf-8").read(4000)
        m = re.search(r"allowed-tools:\n((?:\s+-[^\n]+\n)+)", head)
        tools = set(re.findall(r"-\s*(\w+)", m.group(1))) if m else set()
        if "exec" not in tools:
            out.add(name)
    return out


def test_exec_free_profiles_are_in_profile_deny():
    """A read-only (no exec) profile missing from PROFILE_DENY leaves its
    sandbox unenforced on the hook path - drift parity, same class as
    VALID_PROFILES coverage."""
    missing = _exec_free_profiles() - _profile_deny()
    assert not missing, (
        f"exec-free profiles not in PROFILE_DENY: {sorted(missing)}")


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
