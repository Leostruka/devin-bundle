"""Agent model-pin contract: every model: pin in agents/*.md and
.devin/agents/*.md must resolve to a model_uid declared in
data/bundle-models.json, and must match the routing matrix:
  - judgment / deep exploration  -> swe-2-max
  - bounded technical execution  -> swe-2-flash-high
  - mechanical volume / triage   -> swe-2-flash-medium
"""
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AGENT_DIRS = [
    os.path.join(REPO_ROOT, 'agents'),
    os.path.join(REPO_ROOT, '.devin', 'agents'),
]

# Declared pin matrix: profile -> expected model pin.
EXPECTED_PINS = {
    # judgment / deep exploration stays on Max
    'architect': 'swe-2-max',
    'product-manager': 'swe-2-max',
    'red-team-lead': 'swe-2-max',
    'researcher': 'swe-2-max',
    'reviewer': 'swe-2-max',
    'scrum-master': 'swe-2-max',
    'security-auditor': 'swe-2-max',
    'sre': 'swe-2-max',
    'tech-lead': 'swe-2-max',
    'thermo-nuclear-code-quality-review-subagent': 'swe-2-max',
    'thermo-nuclear-review-subagent': 'swe-2-max',
    'ux-researcher': 'swe-2-max',
    'domain': 'swe-2-max',
    'repo-reviewer': 'swe-2-max',
    # bounded technical execution -> Flash High
    'art-director': 'swe-2-flash-high',
    'data-analyst': 'swe-2-flash-high',
    'debugger': 'swe-2-flash-high',
    'implementer': 'swe-2-flash-high',
    'performance-engineer': 'swe-2-flash-high',
    'qa-ci': 'swe-2-flash-high',
    # mechanical volume / triage -> Flash Medium
    'chief-of-staff': 'swe-2-flash-medium',
    'copywriter': 'swe-2-flash-medium',
    'issue-tracker': 'swe-2-flash-medium',
    'sentinel': 'swe-2-flash-medium',
    'triage-labels': 'swe-2-flash-medium',
}

MODEL_LINE = re.compile(r'^model:\s*(\S+)\s*$', re.MULTILINE)
NAME_LINE = re.compile(r'^name:\s*(\S+)\s*$', re.MULTILINE)


def load_registry_ids():
    path = os.path.join(REPO_ROOT, 'data', 'bundle-models.json')
    with open(path, encoding='utf-8-sig') as f:
        registry = json.load(f)
    return {m['id'] for m in registry['models']}


def iter_agent_pins():
    pins = {}
    for agents_dir in AGENT_DIRS:
        for fname in sorted(os.listdir(agents_dir)):
            if not fname.endswith('.md'):
                continue
            path = os.path.join(agents_dir, fname)
            with open(path, encoding='utf-8') as f:
                text = f.read()
            name_m = NAME_LINE.search(text)
            model_m = MODEL_LINE.search(text)
            if name_m and model_m:
                pins[name_m.group(1)] = model_m.group(1)
    return pins


def test_every_agent_pin_resolves_to_registry_id():
    ids = load_registry_ids()
    pins = iter_agent_pins()
    assert pins, 'no agent model pins found'
    for profile, model_id in pins.items():
        assert model_id in ids, f'{profile} pins unknown model {model_id}'


def test_agent_pins_match_declared_matrix():
    pins = iter_agent_pins()
    missing = set(EXPECTED_PINS) - set(pins)
    assert not missing, f'profiles without model pin: {sorted(missing)}'
    for profile, expected in EXPECTED_PINS.items():
        assert pins[profile] == expected, (
            f'{profile}: expected {expected}, found {pins[profile]}')


def test_no_agent_dispatch_targets_subagent_explore():
    # subagent_explore routes through the possibly-paid CLI default router;
    # agent profiles must never instruct dispatching it.
    offenders = []
    for agents_dir in AGENT_DIRS:
        for fname in sorted(os.listdir(agents_dir)):
            if not fname.endswith('.md'):
                continue
            path = os.path.join(agents_dir, fname)
            with open(path, encoding='utf-8') as f:
                text = f.read()
            for m in re.finditer(r'run_subagent[^\n]*subagent_explore', text):
                offenders.append(f'{fname}: {m.group(0).strip()}')
    assert not offenders, f'subagent_explore dispatch found: {offenders}'
