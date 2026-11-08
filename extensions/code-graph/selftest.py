#!/usr/bin/env python3
"""selftest.py - index a fixture corpus, verify queries resolve."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, *argv, cwd=None):
    return subprocess.run([PY, os.path.join(HERE, script), *argv],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          cwd=cwd, timeout=60)


def main():
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "src"), exist_ok=True)
        with open(os.path.join(root, "src", "alpha.py"), "w") as fh:
            fh.write("import beta.gamma\n"
                     "def myCamelFunc():\n    pass\n"
                     "class Snake_case:\n    pass\n")
        with open(os.path.join(root, "src", "beta.py"), "w") as fh:
            fh.write("def helper():\n    pass\n")

        r = run("index.py", root)
        assert r.returncode == 0, r.stderr

        r = run("query.py", root, "symbols", "mycamel")
        assert "myCamelFunc" in r.stdout, r.stdout
        r = run("query.py", root, "symbols", "snake")
        assert "Snake_case" in r.stdout, r.stdout
        r = run("query.py", root, "outline", "src/alpha.py")
        assert "myCamelFunc" in r.stdout, r.stdout
        r = run("query.py", root, "refs", "beta")
        assert "alpha.py" in r.stdout, r.stdout
        r = run("query.py", root, "files", "alpha")
        assert "alpha.py" in r.stdout, r.stdout

        # change detection
        r = run("detect_changes.py", root)
        assert '"changed": []' in r.stdout, r.stdout
        with open(os.path.join(root, "src", "alpha.py"), "a") as fh:
            fh.write("\ndef added():\n    pass\n")
        r = run("detect_changes.py", root)
        assert "alpha.py" in r.stdout, r.stdout

        # incremental reindex resolves the new symbol
        r = run("index.py", root)
        r = run("query.py", root, "symbols", "added")
        assert "added" in r.stdout, r.stdout

    print("code-graph selftest: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
