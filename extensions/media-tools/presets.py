"""Presets — grainrad's 6 built-ins + custom save/load (JSON file).
Site preset deltas (bundle `C4` over defaults `Ge`) mapped to our param space:
character.* -> ascii effect params; color.useOriginal -> mode original|mono;
image.* -> adjust; advanced.* -> process; postProcessing.* -> post dicts.
crtCurve/phosphor exist on-site but have no local stage yet."""
import copy
import json
from pathlib import Path

CUSTOM_FILE = Path(__file__).resolve().parent / "custom_presets.json"

BUILT_INS = {
    "classic-terminal": {
        "description": "Green monochrome with subtle glow",
        "effect": "ascii",
        "params": {"charset": "standard", "scale": 2, "spacing": 0,
                   "mode": "mono", "fg": "#00ff00", "intensity": 1},
        "post": {"bloom": {"threshold": .6, "soft": .5, "intensity": .8, "radius": 8},
                 "grain": {"intensity": 20, "size": 2},
                 "scanlines": {"opacity": .05, "spacing": 4}},
    },
    "matrix": {
        "description": "Bright green, high contrast, animated grain",
        "effect": "ascii",
        "params": {"charset": "standard", "scale": 2, "spacing": 1,
                   "mode": "mono", "fg": "#00ff00", "intensity": 1.2},
        "adjust": {"brightness": 10, "contrast": 30},
        "post": {"bloom": {"threshold": .5, "soft": .5, "intensity": 1, "radius": 10},
                 "grain": {"intensity": 40, "size": 1}},
    },
    "retro-crt": {
        "description": "Amber color, scanlines, chromatic aberration",
        "effect": "ascii",
        "params": {"mode": "mono", "fg": "#ffbf00", "intensity": 1},
        "post": {"bloom": {"threshold": .7, "soft": .5, "intensity": .6, "radius": 6},
                 "grain": {"intensity": 30, "size": 2},
                 "chromatic": {"offset": 3},
                 "scanlines": {"opacity": .15, "spacing": 3}},
    },
    "high-detail": {
        "description": "Small characters, extended character set",
        "effect": "ascii",
        "params": {"charset": "detailed", "scale": 1, "spacing": .8,
                   "mode": "original", "intensity": 1.1},
        "post": {},
    },
    "minimal": {
        "description": "Large characters, simple charset, bold look",
        "effect": "ascii",
        "params": {"charset": "minimal", "scale": 6, "spacing": 1.2,
                   "mode": "mono", "fg": "#00ff00", "intensity": 1},
        "adjust": {"contrast": 20},
        "post": {"bloom": {"threshold": .5, "soft": .5, "intensity": .9, "radius": 12},
                 "vignette": {"intensity": .3}},
    },
    "cyberpunk": {
        "description": "Cyan and magenta, heavy chromatic aberration",
        "effect": "ascii",
        "params": {"charset": "standard", "scale": 2, "spacing": 1,
                   "mode": "mono", "fg": "#00ffff", "intensity": 1.3},
        "post": {"bloom": {"threshold": .4, "soft": .5, "intensity": 1.2, "radius": 15},
                 "grain": {"intensity": 25, "size": 1},
                 "chromatic": {"offset": 6},
                 "scanlines": {"opacity": .08, "spacing": 2},
                 "vignette": {"intensity": .4}},
    },
}


def _load_custom():
    if CUSTOM_FILE.exists():
        return json.loads(CUSTOM_FILE.read_text(encoding="utf-8"))
    return {}


def list_presets():
    return {**{k: {"description": v["description"], "builtIn": True}
               for k, v in BUILT_INS.items()},
            **{k: {"description": v.get("description", ""), "builtIn": False}
               for k, v in _load_custom().items()}}


def get_preset(name):
    """Full spec: {effect, params, adjust, process, post} — missing sections empty."""
    src = BUILT_INS.get(name) or _load_custom().get(name)
    if not src:
        raise KeyError(f"unknown preset: {name}")
    spec = copy.deepcopy(src)
    for k in ("params", "adjust", "process", "post"):
        spec.setdefault(k, {})
    return spec


def save_preset(name, spec, description=""):
    """spec: same shape as get_preset output (effect/params/adjust/process/post)."""
    custom = _load_custom()
    custom[name] = {"description": description, **spec}
    CUSTOM_FILE.write_text(json.dumps(custom, indent=2), encoding="utf-8")


def delete_preset(name):
    custom = _load_custom()
    if name in custom:
        del custom[name]
        CUSTOM_FILE.write_text(json.dumps(custom, indent=2), encoding="utf-8")
        return True
    return False
