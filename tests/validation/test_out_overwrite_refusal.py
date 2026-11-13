"""Validation: --out/-o/dst user-named output paths refuse to overwrite.

Pins the CLI contract convention (global_rules): every emitter that
writes a user-named output path must refuse an existing file with
stamped {"ok": false} + non-zero exit. Static assertions keep the
guards in place; one behavioral probe (eval_decisions, offline argv)
proves the shape end-to-end.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]

# file -> paths that gained the refusal guard
GUARDED = [
    "extensions/computer-use/cu_wgc.py",
    "extensions/computer-use/cu_bench.py",
    "extensions/computer-use/screenshot.py",
    "extensions/computer-use/record.py",
    "extensions/media-tools/ascii_mancer.py",
    "extensions/media-tools/grainrad.py",
    "extensions/media-tools/jxl.py",
    "extensions/media-tools/update_tooooools_db.py",
    "extensions/ai-tools/dory_sweep.py",
    "extensions/laya-tools/capture_eval.py",
    "extensions/laya-tools/eval_decisions.py",
    "extensions/laya-tools/fit_calibration.py",
    "extensions/laya-compactor/compact.py",
    "extensions/remotion-render/render.py",
    "extensions/image-forensics/verdict.py",
    "extensions/diagram-tools/plantuml_renderer.py",
    "extensions/ai-tools/heldout_batch.py",
    "skills/dma/tools/audit.py",
    "skills/dma/tools/mine.py",
    "skills/dma/tools/recon.py",
    "skills/brag/scripts/analyze_music_cues.py",
    "skills/dispatching-parallel-agents/scripts/review-package.py",
    "skills/dispatching-parallel-agents/scripts/task-brief.py",
]


def test_guarded_files_carry_refusal():
    missing = []
    for rel in GUARDED:
        src = (ROOT / rel).read_text(encoding="utf-8")
        if "refusing to overwrite" not in src and ".exists(" not in src:
            missing.append(rel)
    assert not missing, f"overwrite-refusal guard missing: {missing}"


def test_eval_decisions_refuses_existing_out(tmp_path):
    manifest = tmp_path / "frozen.json"
    manifest.write_text(
        json.dumps({"version": 1, "frozen": True, "cases": []}),
        encoding="utf-8")
    out = tmp_path / "report.json"
    out.write_text("{}", encoding="utf-8")
    p = subprocess.run(
        [sys.executable,
         str(ROOT / "extensions/laya-tools/eval_decisions.py"),
         "--manifest", str(manifest), "--mode", "evaluate",
         "--out", str(out)],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=ROOT)
    assert p.returncode != 0
    payload = json.loads(p.stdout)
    assert payload["ok"] is False
    assert "refusing to overwrite" in payload["error"]
    assert out.read_text(encoding="utf-8") == "{}"  # untouched


def test_eval_decisions_writes_fresh_out(tmp_path):
    manifest = tmp_path / "frozen.json"
    manifest.write_text(
        json.dumps({"version": 1, "frozen": True, "cases": []}),
        encoding="utf-8")
    out = tmp_path / "report.json"
    p = subprocess.run(
        [sys.executable,
         str(ROOT / "extensions/laya-tools/eval_decisions.py"),
         "--manifest", str(manifest), "--mode", "evaluate",
         "--out", str(out)],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=ROOT)
    assert p.returncode == 0
    assert out.exists()
