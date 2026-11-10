import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "simplify-scan.py"


def run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def make_fixture(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "used.py").write_text(
        "# TODO: fix me\n"
        "def used_helper():\n"
        "    return 1\n"
        "used_helper()\n",
        encoding="utf-8")
    (tmp_path / "pkg" / "rot.py").write_text(
        "def dead_func():\n"
        "    pass\n"
        "\n"
        "def swallow():\n"
        "    try:\n"
        "        pass\n"
        "    except Exception:\n"
        "        pass\n",
        encoding="utf-8")
    big = tmp_path / "pkg" / "big.py"
    big.write_text("\n".join("# line %d" % i for i in range(805)),
                   encoding="utf-8")


def test_report_shape_and_signals(tmp_path):
    make_fixture(tmp_path)
    r = run(["--root", str(tmp_path)])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["ok"] is True
    types = {(it["type"], it["file"]) for it in data["items"]}
    assert ("marker", os_path("pkg/used.py")) in types
    assert ("oversized_file", os_path("pkg/big.py")) in types
    assert ("except_pass", os_path("pkg/rot.py")) in types
    dead = [it for it in data["items"] if it["type"] == "unreferenced_def"]
    names = {it["name"] for it in dead}
    assert "dead_func" in names
    assert "used_helper" not in names  # called in used.py
    assert data["totals"]["files_scanned"] == 3


def os_path(p):
    return str(Path(p))


def test_swallow_detects_bare_except(tmp_path):
    (tmp_path / "a.py").write_text(
        "try:\n    pass\nexcept:\n    pass\n", encoding="utf-8")
    r = run(["--root", str(tmp_path)])
    data = json.loads(r.stdout)
    kinds = [it for it in data["items"] if it["type"] == "except_pass"]
    assert len(kinds) == 1 and kinds[0]["kind"] == "bare"


def test_swallow_sibling_reraise_is_intentional(tmp_path):
    (tmp_path / "gate.py").write_text(
        "try:\n    risky()\nexcept SystemExit:\n    raise\n"
        "except Exception:\n    pass\n", encoding="utf-8")
    (tmp_path / "still.py").write_text(
        "try:\n    risky()\nexcept Exception:\n    pass\n", encoding="utf-8")
    r = run(["--root", str(tmp_path)])
    data = json.loads(r.stdout)
    kinds = [it["file"] for it in data["items"]
             if it["type"] == "except_pass"]
    assert kinds == [os_path("still.py")]


def test_bad_root_exits_nonzero(tmp_path):
    r = run(["--root", str(tmp_path / "nope")])
    assert r.returncode != 0
    assert json.loads(r.stdout)["ok"] is False


def test_missing_root_arg_exits_2():
    r = run(["--root"])
    assert r.returncode == 2
    assert json.loads(r.stdout)["ok"] is False


def test_clean_fixture_no_items(tmp_path):
    (tmp_path / "ok.py").write_text(
        "def f():\n    return 1\nprint(f())\n", encoding="utf-8")
    r = run(["--root", str(tmp_path)])
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["items"] == []
