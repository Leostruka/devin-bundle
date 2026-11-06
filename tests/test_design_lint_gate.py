"""M2_05: scripts/design-lint-gate.py hook contract."""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "design-lint-gate.py")
PY = sys.executable


def run_hook(path=None, raw=None):
    payload = raw if raw is not None else json.dumps(
        {"tool_input": {"file_path": path}})
    return subprocess.run([PY, HOOK], input=payload,
                          capture_output=True, text=True)


def write(tmpdir, name, text):
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def test_registered_in_hooks_v1():
    v1 = json.load(open(os.path.join(os.path.dirname(__file__), "..",
                                     "hooks.v1.json"), encoding="utf-8"))
    cmds = [h["command"] for m in v1["PostToolUse"]
            for h in m.get("hooks", [])]
    assert any("design-lint-gate" in c for c in cmds)


def test_slop_warns(tmp_path):
    p = write(tmp_path, "a.css",
              ".h{background:linear-gradient(90deg,#8b5cf6,#06b6d4)}"
              ".c{border-left:6px solid #7c3aed;font-family:'Inter'}")
    r = run_hook(path=p)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "[DESIGN-LINT]" in ctx
    assert "ai-color-palette" in ctx


def test_clean_silent(tmp_path):
    p = write(tmp_path, "ok.css",
              ".b{background:#1a56db;color:#fff;padding:12px}")
    r = run_hook(path=p)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_non_ui_silent(tmp_path):
    p = write(tmp_path, "x.py", "print('inter roboto #8b5cf6')")
    r = run_hook(path=p)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_fail_open_on_garbage():
    assert run_hook(raw="not json at all").returncode == 0
    assert run_hook(raw="{}").returncode == 0
    assert run_hook(path=r"C:\nonexistent\ghost.css").returncode == 0


def test_fixture_skipped(tmp_path):
    # files under fixtures/ or extensions/ are never linted by the hook
    d = os.path.join(tmp_path, "extensions")
    os.makedirs(d)
    p = write(d, "f.css",
              ".h{background:linear-gradient(90deg,#8b5cf6,#06b6d4)}")
    r = run_hook(path=p)
    assert r.stdout.strip() == ""


def test_em_dash_and_marquee(tmp_path):
    p = write(tmp_path, "m.html",
              "<p>a\u2014b\u2014c\u2014d\u2014e\u2014f</p>"
              '<div class="animate-marquee">x</div>')
    r = run_hook(path=p)
    out = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "em-dash-overuse" in out or "marquee" in out
