#!/usr/bin/env python3
"""selftest.py - round-trip read -> diff -> apply == identity; validate
catches outside-spec writes; reserved paths refuse mutation."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, *argv, cwd=None):
    return subprocess.run([PY, os.path.join(HERE, script), *argv],
                          capture_output=True, text=True, cwd=cwd,
                          encoding="utf-8", errors="replace", timeout=60)


def make_root(tmp):
    root = os.path.join(tmp, "bundle")
    for rel, body in {
        "AGENTS.md": "# rules\n",
        ".devin/global_rules.md": "# project\n",
        ".devin/rules/foo.md": "rule\n",
        "hooks.v1.json": "{}\n",
        ".devin/memory/MOC.md": "mem\n",
        "skills/alpha/SKILL.md": "skill\n",
        ".devin/agents/domain.md": "agent\n",
        "scripts/tool.py": "print(1)\n",
        "scripts/check-ai-signature.py": "reserved\n",
        "mcp_config.json": "{}\n",
        "manifest.json": "{}\n",
        "untracked.txt": "outside spec\n",
    }.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
    return root


def main():
    sys.path.insert(0, HERE)
    import tree as t

    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(tmp)

        a = t.read(root)
        assert "untracked.txt" not in a, "outside-spec file leaked"
        assert "scripts/check-ai-signature.py" in a

        snap = os.path.join(tmp, "snap.json")
        r = run("tree.py", "snapshot", root, "--out", snap)
        assert r.returncode == 0, r.stderr

        # mutate one file, diff, apply -> identity with live tree
        with open(os.path.join(root, "skills/alpha/SKILL.md"), "a",
                  encoding="utf-8") as fh:
            fh.write("v2\n")
        b = t.read(root)
        d = t.diff(a, b)
        assert d == {"skills/alpha/SKILL.md": "skill\nv2\n"}, d
        merged = t.apply(a, d)
        assert merged == b
        assert t.tree_hash(merged) == t.tree_hash(b)

        # reserved + outside-spec refusals
        for bad in ({"scripts/check-ai-signature.py": "evil\n"},
                    {"untracked.txt": "x\n"}):
            try:
                t.apply(a, bad)
            except ValueError:
                pass
            else:
                raise AssertionError(f"apply should refuse {bad}")

        # delete propagation
        gone = t.apply(a, {"skills/alpha/SKILL.md": None})
        assert "skills/alpha/SKILL.md" not in gone

        # validate: clean root reports only the missing c4 dirs we skipped
        r = run("tree.py", "validate", root)
        assert "outside-spec" not in r.stdout, r.stdout
        assert "duplicate" not in r.stdout, r.stdout
        assert "missing: c4_tool_guidance" in r.stdout, r.stdout

        # ns create + resume
        runs = os.path.join(tmp, "runs")
        r = run("ns.py", "create", root, "--seed", "s1", "--runs-dir", runs)
        assert r.returncode == 0, r.stderr
        rdir = r.stdout.strip()
        assert os.path.isfile(os.path.join(rdir, "tree.json"))
        r = run("ns.py", "resume", rdir)
        assert '"files"' in r.stdout and '"sha"' in r.stdout, r.stdout

    print("selftest: PASS")


if __name__ == "__main__":
    main()
