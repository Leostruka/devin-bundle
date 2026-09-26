"""Test helper: load scrape-tools extension modules without installing the
extension venv. `scrapling` itself is imported lazily inside the scripts'
functions, so tests inject a fake `scrapling` module into sys.modules.
"""
import importlib.util
import sys
from pathlib import Path

EXT = Path(__file__).resolve().parents[1] / "extensions" / "scrape-tools"
if str(EXT) not in sys.path:
    sys.path.insert(0, str(EXT))


def load(name):
    """Load extensions/scrape-tools/<name>.py as a fresh module."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, EXT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
