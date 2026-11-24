"""Tests for scripts/log-refinement.py (C18).

Hand-appends produced a duplicate-id collision in the 2026-11-24 session
(audit c25 FAIL '1 duplicate IDs'); the helper must assign the next free
C<N> id and enforce the refine.md schema.
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'scripts', 'log-refinement.py')

spec = importlib.util.spec_from_file_location('log_refinement', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _seed(log, ids):
    with open(log, 'w', encoding='utf-8') as f:
        for i in ids:
            f.write(json.dumps({'id': i, 'timestamp': 't', 'type': 'hook',
                                'target': 'x', 'evidence': 'e',
                                'status': 'applied'}) + '\n')


def test_next_id_empty():
    assert mod._next_id([]) == 'C1'


def test_next_id_sequence():
    _seed_ids = [{'id': 'C1'}, {'id': 'C3'}, {'id': 'C13'}, {'id': 'ref-001'}]
    assert mod._next_id(_seed_ids) == 'C14'


def test_next_id_non_numeric_ignored():
    assert mod._next_id([{'id': 'C-1'}, {'id': 'C9x'}, {'id': 'C2'}]) == 'C3'


def test_append_creates_log_and_assigns_id(tmp_path):
    # Run in tmp cwd so LOG resolves to tmp .devin/ (never the repo log).
    rc = subprocess.run(
        [sys.executable, os.path.abspath(SCRIPT), '--type', 'hook',
         '--target', 'scripts/x.py', '--change', 'c', '--evidence', 'e'],
        capture_output=True, text=True, encoding='utf-8',
        cwd=str(tmp_path))
    assert rc.returncode == 0, rc.stderr
    out = json.loads(rc.stdout.strip().splitlines()[-1])
    assert out['ok'] is True and out['id'] == 'C1'
    assert out['api_version'] == 2
    assert out['meta']['answered_by']['wrapper'] == 'log-refinement'
    rows = [json.loads(l) for l in
            open(tmp_path / '.devin' / 'refinements.log.jsonl', encoding='utf-8')]
    assert all(k in rows[0] for k in
               ('id', 'timestamp', 'type', 'target', 'evidence', 'status'))


def test_append_continues_existing_sequence(tmp_path):
    log_dir = tmp_path / '.devin'
    log_dir.mkdir()
    _seed(log_dir / 'refinements.log.jsonl', ['C1', 'C5'])
    rc = subprocess.run(
        [sys.executable, os.path.abspath(SCRIPT), '--type', 'skill',
         '--target', 'skills/x', '--change', 'c', '--evidence', 'e'],
        capture_output=True, text=True, encoding='utf-8',
        cwd=str(tmp_path))
    assert rc.returncode == 0
    assert json.loads(rc.stdout.strip().splitlines()[-1])['id'] == 'C6'
    rows = [json.loads(l) for l in
            open(log_dir / 'refinements.log.jsonl', encoding='utf-8')]
    assert [r['id'] for r in rows] == ['C1', 'C5', 'C6']


def test_cli_missing_required_returns_2(tmp_path):
    rc = subprocess.run([sys.executable, os.path.abspath(SCRIPT)],
                        capture_output=True, text=True, cwd=str(tmp_path))
    assert rc.returncode == 2  # argparse exits 2 on missing required args
