"""scripts/file-size-guard.py hook contract."""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "file-size-guard.py")
PY = sys.executable


def run_hook(raw):
    return subprocess.run([PY, HOOK], input=raw,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def test_fail_open_on_garbage():
    assert run_hook("not json at all").returncode == 0
    assert run_hook("{}").returncode == 0


def test_fail_open_on_non_dict_payload():
    for raw in ('[1,2]', '"x"', '42', 'null'):
        r = run_hook(raw)
        assert r.returncode == 0 and 'Traceback' not in r.stderr


def test_fail_open_on_non_dict_tool_input():
    # tool_input as string/list must not AttributeError on .get
    for raw in ('{"tool_input":"x"}', '{"tool_input":[1]}',
                '{"tool_input":42}'):
        r = run_hook(raw)
        assert r.returncode == 0 and 'Traceback' not in r.stderr


def test_small_file_silent(tmp_path):
    p = tmp_path / "small.py"
    p.write_text("print('hi')\n", encoding="utf-8")
    r = run_hook(json.dumps({"tool_input": {"file_path": str(p)}}))
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_large_code_file_warns(tmp_path):
    p = tmp_path / "big.py"
    p.write_text("x = 1\n" * 900, encoding="utf-8")
    r = run_hook(json.dumps({"tool_input": {"file_path": str(p)}}))
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "file-size-guard" in out["hookSpecificOutput"]["additionalContext"]
