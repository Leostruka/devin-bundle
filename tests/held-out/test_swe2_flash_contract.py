"""Held-out gap checks for the SWE-2 Flash family integration.

Covers the contract the validation suite does not choose for itself:
  - exact free_until / free_tier_permanent values on all six swe-2/flash ids
  - role 'fast' resolution + BUNDLE_FAST_MODEL env override (isolated env)
  - alignment between agent pins, config.json, and MODEL-GUIDE.md windows
"""
import importlib.util
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_json(*parts):
    with open(os.path.join(REPO_ROOT, *parts), encoding='utf-8-sig') as f:
        return json.load(f)


def load_text(*parts):
    with open(os.path.join(REPO_ROOT, *parts), encoding='utf-8') as f:
        return f.read()


def load_context_pressure():
    spec = importlib.util.spec_from_file_location(
        'context_pressure',
        os.path.join(REPO_ROOT, 'scripts', 'context-pressure.py'),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_free_window_metadata_exact():
    registry = load_json('data', 'bundle-models.json')
    models = {m['id']: m for m in registry['models']}

    for mid in ('swe-2-medium', 'swe-2-high', 'swe-2-max'):
        m = models[mid]
        assert m['free_until'] == '2026-11-30', mid
        assert m['free_tier_permanent'] is False, mid

    for mid in ('swe-2-flash-medium', 'swe-2-flash-high', 'swe-2-flash-max'):
        m = models[mid]
        assert m['free_until'] == '2026-12-04T18:00:00Z', mid

    assert models['swe-2-flash-medium']['free_tier_permanent'] is True
    assert models['swe-2-flash-high']['free_tier_permanent'] is False
    assert models['swe-2-flash-max']['free_tier_permanent'] is False

    # Exactly one permanent-free model in the registry.
    permanent = [m['id'] for m in registry['models']
                 if m.get('free_tier_permanent') is True]
    assert permanent == ['swe-2-flash-medium']


def test_fast_role_resolution_and_env_override(monkeypatch):
    cp = load_context_pressure()
    for var in ('BUNDLE_RECIPE_X_MODEL', 'BUNDLE_FAST_MODEL',
                'BUNDLE_DEFAULT_MODEL', 'BUNDLE_MAX_MODEL',
                'BUNDLE_MEDIUM_MODEL', 'BUNDLE_DEFAULT_SUBAGENT_MODEL'):
        monkeypatch.delenv(var, raising=False)

    recipe = {'name': 'x', 'preferred_model_role': 'fast',
              'preferred_model': None}
    resolved = cp.resolve_preferred_model(recipe)
    assert resolved == 'swe-2-flash-high'

    monkeypatch.setenv('BUNDLE_FAST_MODEL', 'swe-2-flash-max')
    resolved = cp.resolve_preferred_model(recipe)
    assert resolved == 'swe-2-flash-max'

    monkeypatch.setenv('BUNDLE_RECIPE_X_MODEL', 'swe-2-medium')
    resolved = cp.resolve_preferred_model(recipe)
    assert resolved == 'swe-2-medium'


def test_registry_fast_role_model_points_at_flash():
    registry = load_json('data', 'bundle-models.json')
    assert registry['fast_role_model'] == 'swe-2-flash-high'
    ids = {m['id'] for m in registry['models']}
    assert registry['fast_role_model'] in ids
    fast_models = [m['id'] for m in registry['models']
                   if m.get('role') == 'fast']
    assert sorted(fast_models) == [
        'swe-2-flash-high', 'swe-2-flash-max', 'swe-2-flash-medium']


def test_config_flash_family_preference():
    config = load_json('config.json')
    preferred = config['agent']['preferred_family_models']
    assert preferred['swe-2-flash'] == 'swe-2-flash-high'
    assert preferred['swe-2'] == 'swe-2-max'
    assert config['agent']['model'] == 'swe-2-max'


def test_docs_carry_exact_window_dates():
    guide = load_text('.devin', 'docs', 'MODEL-GUIDE.md')
    tools_map = load_text('.devin', 'docs', 'TOOLS-MAP.md')
    for doc in (guide, tools_map):
        assert '2026-11-30' in doc, 'missing SWE-2 free cutoff date'
        assert '2026-12-04' in doc, 'missing Flash free cutoff date'
        assert 'swe-2-flash-medium' in doc
    # Flash cutoff must be documented at 18:00 UTC, not as a bare date or 11/30.
    assert ('2026-12-04T18:00:00Z' in guide
            or '2026-12-04 18:00 UTC' in guide)


def test_agent_pins_match_config_and_docs():
    guide = load_text('.devin', 'docs', 'MODEL-GUIDE.md')
    config = load_json('config.json')

    # config family preference is consistent with the bounded-execution pin.
    assert config['agent']['preferred_family_models']['swe-2-flash'] \
        == 'swe-2-flash-high'

    for profile, expected in (
            ('implementer', 'swe-2-flash-high'),
            ('debugger', 'swe-2-flash-high'),
            ('qa-ci', 'swe-2-flash-high'),
            ('researcher', 'swe-2-max'),
            ('reviewer', 'swe-2-max')):
        text = load_text('agents', f'{profile}.md')
        assert f'model: {expected}' in text, (
            f'{profile}: expected pin {expected}')
        # doc must mention the profile so the pin matrix is traceable
        assert profile in guide, f'{profile} missing from MODEL-GUIDE.md'

    for profile, expected in (
            ('issue-tracker', 'swe-2-flash-medium'),
            ('triage-labels', 'swe-2-flash-medium')):
        text = load_text('.devin', 'agents', f'{profile}.md')
        assert f'model: {expected}' in text, (
            f'{profile}: expected pin {expected}')
