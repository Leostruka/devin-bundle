import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import presets
from grainrad import run


def _src():
    return Image.fromarray((np.random.default_rng(0).random((32, 48, 3)) * 255).astype(np.uint8))


def test_six_builtins_present():
    names = set(presets.list_presets())
    assert {"classic-terminal", "matrix", "retro-crt",
            "high-detail", "minimal", "cyberpunk"} <= names
    assert all(v["builtIn"] for k, v in presets.list_presets().items()
               if k in presets.BUILT_INS)


def test_builtin_specs_have_site_params():
    m = presets.get_preset("matrix")
    assert m["params"]["mode"] == "mono" and m["params"]["fg"] == "#00ff00"
    assert m["adjust"] == {"brightness": 10, "contrast": 30}
    assert m["post"]["grain"]["intensity"] == 40
    c = presets.get_preset("cyberpunk")
    assert c["params"]["fg"] == "#00ffff"
    assert c["post"]["chromatic"]["offset"] == 6


def test_preset_runs_pipeline():
    spec = presets.get_preset("classic-terminal")
    out = run(_src(), spec["effect"], spec["params"], spec["adjust"],
              spec["process"], spec["post"])
    assert out.mode == "RGB"
    arr = np.asarray(out)
    # mono green terminal: green channel dominates
    assert arr[..., 1].mean() > arr[..., 0].mean()


def test_custom_preset_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(presets, "CUSTOM_FILE", tmp_path / "p.json")
    spec = {"effect": "threshold", "params": {"levels": 4},
            "adjust": {}, "process": {}, "post": {}}
    presets.save_preset("mine", spec, "test preset")
    assert "mine" in presets.list_presets()
    got = presets.get_preset("mine")
    assert got["effect"] == "threshold" and got["params"]["levels"] == 4
    assert presets.delete_preset("mine") is True
    assert "mine" not in presets.list_presets()


def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        presets.get_preset("nope")
