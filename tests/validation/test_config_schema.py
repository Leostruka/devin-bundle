import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_json(name):
    path = os.path.join(REPO_ROOT, name)
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def test_config_version_is_int():
    config = load_json('config.json')
    assert isinstance(config.get('version'), int)


def test_config_has_required_top_level_keys():
    config = load_json('config.json')
    for key in ['devin', 'agent', 'read_config_from', 'shell', 'hooks']:
        assert key in config, f'missing {key}'
        assert isinstance(config[key], (dict, list))


def test_attribution_is_boolean():
    config = load_json('config.json')
    assert 'attribution' in config
    assert isinstance(config['attribution'], bool)


def test_config_hooks_empty_single_source():
    # hooks.v1.json is the single authored source; config.json.hooks is rendered
    # at install time by scripts/render-user-hooks.py — a second copy would drift.
    config = load_json('config.json')
    assert config['hooks'] == {}, 'config.json.hooks must stay empty (single source: hooks.v1.json)'


def test_hooks_v1_entries_have_required_fields():
    hooks = load_json('hooks.v1.json')
    for event, entries in hooks.items():
        assert isinstance(entries, list)
        for entry in entries:
            assert isinstance(entry, dict)
            assert 'matcher' in entry
            assert 'hooks' in entry
            assert isinstance(entry['hooks'], list)
            for h in entry['hooks']:
                assert h.get('type') in ('command', 'prompt')
                assert h.get('command') or h.get('prompt')


def test_render_user_hooks_expands_paths():
    import subprocess
    import sys
    out = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, 'scripts', 'render-user-hooks.py'),
         'HOME_TOKEN'],
        capture_output=True, text=True)
    assert out.returncode == 0
    rendered = json.loads(out.stdout)
    assert len(rendered) == 8
    for entries in rendered.values():
        for entry in entries:
            for h in entry['hooks']:
                cmd = h.get('command', '')
                assert 'python scripts/' not in cmd
                if cmd:
                    assert 'HOME_TOKEN/scripts/' in cmd


def test_mcp_config_schema():
    mcp = load_json('mcp_config.json')
    assert 'mcpServers' in mcp
    assert isinstance(mcp['mcpServers'], dict)
    for name, cfg in mcp['mcpServers'].items():
        assert 'url' in cfg
        assert 'transport' in cfg
        assert cfg['url'].startswith('https://')
        assert cfg['transport'] in ('https', 'stdio')


def test_hooks_v1_json_has_known_events():
    hooks = load_json('hooks.v1.json')
    known = {'PreToolUse', 'PostToolUse', 'PreCompact', 'PostCompaction',
             'UserPromptSubmit', 'SessionStart', 'SessionEnd', 'Stop', 'PermissionRequest'}
    for event in hooks:
        assert event in known, f'unknown event {event} in hooks.v1.json'
