import os
import sys
import importlib.util

# Load scripts/context-pressure.py using importlib (filename has hyphen)
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location('context_pressure', os.path.join(repo_root, 'scripts', 'context-pressure.py'))
context_pressure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context_pressure)


def test_estimate_tokens_is_reasonable():
    text = "hello world"
    assert context_pressure.estimate_tokens(text) == len(text) // 4


def test_get_model_window_known_models():
    assert context_pressure.get_model_window('glm-5-2') == 200000
    assert context_pressure.get_model_window('swe-1.7') == 262000


def test_get_model_window_fallback():
    # Unknown model returns a sensible default
    assert context_pressure.get_model_window('unknown-model') > 0


def test_get_thresholds():
    warn, critical, clear = context_pressure.get_thresholds()
    assert warn == 60
    assert critical == 75
    assert clear == 80
