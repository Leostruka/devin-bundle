"""Test helper: load computer-use extension modules without installing the
extension venv. Heavy deps (pynput/mss/uiautomation/comtypes) are imported
lazily inside the scripts' functions, so pure-logic tests need only stdlib.
For paths that do reach them, tests inject fakes into sys.modules first.
"""
import importlib.util
import sys
from pathlib import Path

EXT = Path(__file__).resolve().parents[1] / "extensions" / "computer-use"
if str(EXT) not in sys.path:
    sys.path.insert(0, str(EXT))


def load(name):
    """Load extensions/computer-use/<name>.py as a fresh module."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, EXT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # before exec: `import cu_hints` etc. resolve
    spec.loader.exec_module(mod)
    return mod
