"""image-forensics — residual, reference, PCE separation, verdict contract.

Synthetic fixtures only: a fake "camera" is a fixed spatial noise
pattern; "real" images carry it plus iid noise, "synthetic" images carry
iid noise only. PCE must separate the classes.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

IF_DIR = Path(__file__).resolve().parents[1] / \
    "extensions" / "image-forensics"
sys.path.insert(0, str(IF_DIR))

import prnu                    # noqa: E402
import metadata as md          # noqa: E402
import verdict as vd           # noqa: E402

rng = np.random.default_rng(42)
SIZE = (96, 96)


def _base():
    yy, xx = np.mgrid[0:SIZE[0], 0:SIZE[1]]
    return 0.5 + 0.3 * np.sin(xx / 9.0) * np.cos(yy / 11.0)


def make_set(n=6, stamp=True):
    ref_pattern = rng.normal(0, 0.02, SIZE)
    imgs = []
    for _ in range(n):
        img = _base() + rng.normal(0, 0.005, SIZE)
        if stamp:
            img = img + ref_pattern
        imgs.append(img)
    return imgs, ref_pattern


def _save(arr, path):
    from PIL import Image
    Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8)) \
        .save(path)


# --- residual / reference / pce ----------------------------------------------

def test_residual_is_zero_mean_and_deterministic():
    img = _base()
    r = prnu.residual(img)
    assert r.shape == img.shape
    assert abs(r.mean()) < 0.02
    assert np.allclose(r, prnu.residual(img))


def test_pce_separates_real_from_synthetic():
    reals, _ = make_set(6, stamp=True)
    ref = prnu.build_reference(reals[:4])
    real_pce = [prnu.pce(prnu.residual(i), ref) for i in reals[4:]]
    synths, _ = make_set(4, stamp=False)
    synth_pce = [prnu.pce(prnu.residual(i), ref) for i in synths]
    assert min(real_pce) > max(synth_pce) * 4, (
        f"no separation: real={real_pce} synth={synth_pce}")


def test_pce_shape_mismatch_raises():
    with pytest.raises(ValueError):
        prnu.pce(np.zeros((10, 10)), np.zeros((8, 8)))


def test_build_reference_empty_raises():
    with pytest.raises(ValueError):
        prnu.build_reference([])


# --- verdict ------------------------------------------------------------------

def test_verdict_real_capture(tmp_path):
    reals, _ = make_set(6, stamp=True)
    ref = prnu.build_reference(reals[:4])
    ref_path = tmp_path / "ref.npy"
    np.save(ref_path, ref)
    img_path = tmp_path / "real.png"
    _save(reals[5], img_path)
    out = vd.judge(str(img_path), str(ref_path), pce_real=1.0,
                   pce_synth=0.05)
    assert out["ok"] and out["verdict"] == "real_capture"
    assert out["pce"] and out["pce"] >= 1.0


def test_verdict_synthetic(tmp_path):
    reals, _ = make_set(4, stamp=True)
    ref = prnu.build_reference(reals)
    ref_path = tmp_path / "ref.npy"
    np.save(ref_path, ref)
    synth, _ = make_set(1, stamp=False)
    img_path = tmp_path / "synth.png"
    _save(synth[0], img_path)
    out = vd.judge(str(img_path), str(ref_path), pce_real=1e9,
                   pce_synth=1e8)
    assert out["verdict"] == "synthetic"


def test_verdict_no_reference_and_low_energy(tmp_path):
    img_path = tmp_path / "r.png"
    _save(make_set(1)[0][0], img_path)
    out = vd.judge(str(img_path))
    assert out["verdict"] == "no_reference"
    flat = tmp_path / "flat.png"
    _save(np.full(SIZE, 0.5), flat)
    out2 = vd.judge(str(flat))
    assert out2["verdict"] == "inconclusive"
    assert any("low_residual_energy" in n for n in out2["notes"])


def test_verdict_contract_keys(tmp_path):
    img_path = tmp_path / "x.png"
    _save(make_set(1)[0][0], img_path)
    out = vd.judge(str(img_path))
    assert set(out) == {"ok", "verdict", "pce", "metadata_flags",
                        "notes"}


# --- metadata -----------------------------------------------------------------

def test_metadata_no_exif_flag(tmp_path):
    img_path = tmp_path / "plain.png"
    _save(_base(), img_path)
    rep = md.report(img_path)
    assert rep["has_exif"] is False
    assert "no_exif" in rep["flags"]


def test_metadata_unreadable(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    rep = md.report(bad)
    assert any(f.startswith("unreadable") for f in rep["flags"])
