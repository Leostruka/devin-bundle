"""ppisp-prep — photo_qc spread verdicts + runner doctor/entry contract."""
import sys
from pathlib import Path

import numpy as np

PP_DIR = Path(__file__).resolve().parents[1] / "extensions" / "ppisp-prep"
sys.path.insert(0, str(PP_DIR))

import photo_qc                  # noqa: E402
import ppisp_runner              # noqa: E402

rng = np.random.default_rng(7)
SIZE = (64, 64, 3)


def _img(exposure=0.5, wb=0.0, vign=0.0):
    arr = np.full(SIZE, exposure, dtype=np.float64)
    arr[..., 0] += wb / 2
    arr[..., 2] -= wb / 2
    yy, xx = np.mgrid[0:SIZE[0], 0:SIZE[1]]
    r = np.sqrt((yy - SIZE[0] / 2) ** 2 + (xx - SIZE[1] / 2) ** 2)
    arr -= (r / r.max())[:, :, None] * vign
    return np.clip(arr + rng.normal(0, 0.005, SIZE), 0, 1)


def _save(arr, path):
    from PIL import Image
    Image.fromarray((arr * 255).astype(np.uint8)).save(path)


def _set(tmp_path, specs):
    paths = []
    for i, s in enumerate(specs):
        p = tmp_path / f"img{i}.png"
        _save(_img(**s), p)
        paths.append(p)
    return paths


def test_consistent_set_goes(tmp_path):
    out = photo_qc.scan(_set(tmp_path, [{"exposure": 0.5}] * 4))
    assert out["ok"] and out["verdict"] == "go"
    assert out["spread"]["exposure"] < photo_qc.GO["exposure"]


def test_moderate_drift_corrects(tmp_path):
    specs = [{"exposure": e} for e in (0.3, 0.45, 0.6, 0.5)]
    out = photo_qc.scan(_set(tmp_path, specs))
    assert out["verdict"] == "correct"


def test_extreme_drift_recaptures(tmp_path):
    specs = [{"exposure": e} for e in (0.1, 0.9, 0.2, 0.85)]
    out = photo_qc.scan(_set(tmp_path, specs))
    assert out["verdict"] == "recapture"


def test_wb_spread_detected(tmp_path):
    specs = [{"wb": w} for w in (-0.3, 0.3, -0.25, 0.35)]
    out = photo_qc.scan(_set(tmp_path, specs))
    assert out["spread"]["wb"] > photo_qc.GO["wb"]
    assert out["verdict"] in ("correct", "recapture")


def test_single_image_inconclusive(tmp_path):
    out = photo_qc.scan(_set(tmp_path, [{"exposure": 0.5}]))
    assert out["ok"] is False and out["verdict"] == "inconclusive"


def test_runner_doctor_missing_upstream(tmp_path, monkeypatch):
    monkeypatch.setenv("PPISP_DIR", str(tmp_path / "nope"))
    d = ppisp_runner.doctor()
    assert d["present"] is False
    assert "clone" in d["hint"]


def test_runner_refuses_unverified_license(tmp_path, monkeypatch):
    up = tmp_path / "up"
    up.mkdir()
    (up / "README.md").write_text("ppisp")
    monkeypatch.setenv("PPISP_DIR", str(up))
    out = ppisp_runner.run(str(tmp_path), str(tmp_path / "out"))
    assert out["ok"] is False
    assert out["error"] == "license_unverified"
