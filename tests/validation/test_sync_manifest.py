"""sync-manifest contract: drift detection, repair, newline-variant tolerance.

Reproduced failure 2026-11-26: 73 stale skill export_hash entries because
audit detection covered scripts/agents but not skills. These tests pin the
repair tool's behavior on an isolated fixture tree.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync-manifest.py"


def _fixture(tmp_path, hash_fn=None):
    """Minimal tree: manifest.json + one skill + one agent."""
    (tmp_path / "skills" / "alpha").mkdir(parents=True)
    (tmp_path / "agents").mkdir()
    skill_bytes = b"---\nname: alpha\n---\nbody\n"
    agent_bytes = b"---\nname: beta\n---\nbody\n"
    (tmp_path / "skills" / "alpha" / "SKILL.md").write_bytes(skill_bytes)
    (tmp_path / "agents" / "beta.md").write_bytes(agent_bytes)
    h = hash_fn or (lambda b: hashlib.sha256(b).hexdigest())
    manifest = {
        "name": "fixture", "version": "0.0.1",
        "skills": [{"name": "alpha", "export_hash": h(skill_bytes)}],
        "skill_count": 1,
        "agents": [{"name": "beta", "export_hash": h(agent_bytes)}],
        "agent_count": 1,
    }
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    return manifest


def _run(cwd, *argv):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + list(argv),
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=str(cwd), timeout=60)


def test_check_clean_tree_exits_zero(tmp_path):
    _fixture(tmp_path)
    proc = _run(tmp_path, "--check")
    payload = json.loads(proc.stdout)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert payload["ok"] is True and payload["drift"] == 0
    assert payload["api_version"] == 2
    assert payload["meta"]["answered_by"]["wrapper"] == "sync-manifest"


def test_corrupt_hash_detected_then_repaired(tmp_path):
    manifest = _fixture(tmp_path)
    manifest["skills"][0]["export_hash"] = "0" * 64
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    proc = _run(tmp_path, "--check")
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["drift"] == 1
    proc = _run(tmp_path)
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["count"] == 1
    proc = _run(tmp_path, "--check")
    assert proc.returncode == 0


def test_crlf_variant_hash_is_not_drift(tmp_path):
    """Entry hashed over CRLF bytes while the file is LF must pass -
    same tolerance as audit text_hash_matches."""
    def crlf_hash(b):
        return hashlib.sha256(b.replace(b"\n", b"\r\n")).hexdigest()
    _fixture(tmp_path, hash_fn=crlf_hash)
    proc = _run(tmp_path, "--check")
    assert proc.returncode == 0, proc.stdout
    assert json.loads(proc.stdout)["drift"] == 0


def test_unlisted_skill_reported_not_added(tmp_path):
    _fixture(tmp_path)
    (tmp_path / "skills" / "gamma").mkdir()
    (tmp_path / "skills" / "gamma" / "SKILL.md").write_bytes(b"x\n")
    proc = _run(tmp_path, "--check")
    payload = json.loads(proc.stdout)
    assert any("gamma" in p for p in payload["problems"])
    _run(tmp_path)
    manifest = json.loads(
        (tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert all(s["name"] != "gamma" for s in manifest["skills"])


def test_envelope_failure_exit_nonzero(tmp_path):
    """ok:false contract - missing manifest exits non-zero (rule: envelope
    v2 emitters exit non-zero on failure)."""
    proc = _run(tmp_path, "--check")
    assert proc.returncode != 0
    assert json.loads(proc.stdout)["ok"] is False
