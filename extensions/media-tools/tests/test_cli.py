import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "grainrad.py"


def run_cli(*argv):
    r = subprocess.run([sys.executable, str(CLI), *argv], capture_output=True, text=True)
    return json.loads(r.stdout.strip().splitlines()[-1]), r.returncode


def test_list_effects():
    out, code = run_cli("--list-effects")
    assert code == 0 and out["ok"] and "ascii" in out["effects"]


def test_self_test(tmp_path):
    out_path = tmp_path / "st.png"
    out, code = run_cli("--self-test", "--output", str(out_path))
    assert code == 0 and out["ok"] and out_path.exists()


def test_missing_args():
    out, code = run_cli()
    assert code == 2 and not out["ok"]


def test_param_parsing_effect(tmp_path):
    from grainrad import _parse_params
    eff, adj, proc, post = _parse_params(
        ["charset=blocks", "scale=3", "adjust.brightness=20",
         "process.blur=0.5", "bloom.threshold=0.6", "grain"])
    assert eff == {"charset": "blocks", "scale": 3}
    assert adj == {"brightness": 20}
    assert proc == {"blur": 0.5}
    assert post == {"bloom": {"threshold": 0.6}, "grain": {}}


def test_pipeline_on_file(tmp_path):
    from PIL import Image
    src = tmp_path / "in.png"
    Image.new("RGB", (64, 48), (120, 80, 40)).save(src)
    dst = tmp_path / "out.png"
    out, code = run_cli("--input", str(src), "--output", str(dst),
                        "--effect", "ascii", "--param", "charset=minimal",
                        "--param", "adjust.contrast=10", "--param", "vignette.intensity=0.5")
    assert code == 0 and out["ok"] and dst.exists()
