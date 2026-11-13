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
    assert context_pressure.get_model_window('swe-2-high') == 262144
    assert context_pressure.get_model_window('swe-2-max') == 262144


def test_get_model_window_fallback():
    # Unknown model returns a sensible default
    assert context_pressure.get_model_window('unknown-model') > 0


def test_get_thresholds():
    warn, critical, clear = context_pressure.get_thresholds()
    assert warn == 60
    assert critical == 75
    assert clear == 80


def test_get_model_window_flash_models():
    assert context_pressure.get_model_window('swe-2-flash-medium') == 262144
    assert context_pressure.get_model_window('swe-2-flash-high') == 262144
    assert context_pressure.get_model_window('swe-2-flash-max') == 262144


def test_resolve_preferred_model_fast_role(monkeypatch):
    for var in ('BUNDLE_RECIPE_IMPLEMENT_MODEL', 'BUNDLE_FAST_MODEL',
                'BUNDLE_DEFAULT_MODEL', 'BUNDLE_MAX_MODEL',
                'BUNDLE_MEDIUM_MODEL', 'BUNDLE_DEFAULT_SUBAGENT_MODEL'):
        monkeypatch.delenv(var, raising=False)
    recipe = {'name': 'implement', 'preferred_model_role': 'fast', 'preferred_model': None}
    assert context_pressure.resolve_preferred_model(recipe) == 'swe-2-flash-high'


def test_resolve_preferred_model_fast_env_override(monkeypatch):
    monkeypatch.setenv('BUNDLE_FAST_MODEL', 'swe-2-flash-medium')
    recipe = {'name': 'implement', 'preferred_model_role': 'fast', 'preferred_model': None}
    assert context_pressure.resolve_preferred_model(recipe) == 'swe-2-flash-medium'


def test_resolve_preferred_model_recipe_override_beats_role(monkeypatch):
    monkeypatch.setenv('BUNDLE_RECIPE_IMPLEMENT_MODEL', 'swe-2-max')
    monkeypatch.setenv('BUNDLE_FAST_MODEL', 'swe-2-flash-medium')
    recipe = {'name': 'implement', 'preferred_model_role': 'fast', 'preferred_model': None}
    assert context_pressure.resolve_preferred_model(recipe) == 'swe-2-max'
