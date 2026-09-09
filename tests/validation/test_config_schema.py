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


def test_hooks_events_are_known():
    config = load_json('config.json')
    known = {'PreToolUse', 'PostToolUse', 'PreCompact', 'PostCompaction',
             'UserPromptSubmit', 'SessionStart', 'SessionEnd', 'Stop', 'PermissionRequest'}
    for event in config['hooks']:
        assert event in known, f'unknown event {event}'


def test_hooks_entries_have_required_fields():
    config = load_json('config.json')
    for event, entries in config['hooks'].items():
        assert isinstance(entries, list)
        for entry in entries:
            assert isinstance(entry, dict)
            assert 'matcher' in entry
            assert 'hooks' in entry
            assert isinstance(entry['hooks'], list)
            for h in entry['hooks']:
                assert h.get('type') == 'command'
                assert h.get('command')


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
