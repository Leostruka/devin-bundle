"""reminder record schema in refine-review-prompt.py (C21).

The Stop-hook reminder writer previously emitted pre-ADR-011 keys
(repro_command/expected/actual/verdict) which audit c25 rejected after
the schema alignment. Lock the canonical record shape.
"""
import importlib.util
import json
import os

import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'scripts', 'refine-review-prompt.py')
spec = importlib.util.spec_from_file_location('rrp', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REQUIRED = ('id', 'timestamp', 'type', 'target', 'evidence', 'status')


def test_record_has_canonical_keys():
    rec = mod._reminder_record(1700000000, 'complex session')
    for k in REQUIRED:
        assert rec.get(k), f'missing required key {k}'
    assert rec['id'] == 'refine-reminder-1700000000'
    assert rec['type'] == 'hook'
    assert rec['status'] == 'applied'
    assert 'complex session' in rec['evidence']


def test_record_no_legacy_keys():
    rec = mod._reminder_record(1, 'x')
    for legacy in ('repro_command', 'expected', 'actual', 'verdict'):
        assert legacy not in rec


def test_append_writes_jsonl(tmp_path):
    mod._append_reminder_record(str(tmp_path), 42, 'd')
    log = tmp_path / '.devin' / 'refinements.log.jsonl'
    rows = [json.loads(l) for l in open(log, encoding='utf-8')]
    assert len(rows) == 1
    assert rows[0]['id'] == 'refine-reminder-42'
    assert all(k in rows[0] for k in REQUIRED)


def test_audit_c25_accepts_reminder_record(tmp_path):
    # Mirror audit_checks/m_scripts.py c25: required keys + unique ids.
    mod._append_reminder_record(str(tmp_path), 1, 'a')
    mod._append_reminder_record(str(tmp_path), 2, 'b')
    required = ['id', 'timestamp', 'type', 'target', 'evidence', 'status']
    ids = []
    for line in open(tmp_path / '.devin' / 'refinements.log.jsonl',
                     encoding='utf-8'):
        e = json.loads(line)
        ids.append(e['id'])
        assert not [k for k in required if k not in e or not e[k]]
    assert len(ids) == len(set(ids))
