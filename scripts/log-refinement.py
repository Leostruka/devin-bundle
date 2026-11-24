#!/usr/bin/env python3
"""Append a refinement entry to .devin/refinements.log.jsonl.

Guarantees a unique id (next free in the log's own C<N> scheme) and the
required keys per skills/self-improvement/modes/refine.md. Hand-appends
produced duplicate IDs in the 2026-11-24 session (audit c25 FAIL).

Usage:
    python scripts/log-refinement.py --type hook --target scripts/x.py \
        --action updated --change "what changed" \
        --evidence "repro command + observed output" \
        --vf "verification command -> result" \
        [--status applied] [--outcome helped] [--class INV] [--session "..."]
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_envelope import bind  # noqa: E402

_stamp, _dumps = bind("log-refinement")

LOG = os.path.join('.devin', 'refinements.log.jsonl')
REQUIRED = ('id', 'timestamp', 'type', 'target', 'evidence', 'status')


def _next_id(rows):
    hi = 0
    for r in rows:
        m = re.fullmatch(r'C(\d+)', str(r.get('id', '')))
        if m:
            hi = max(hi, int(m.group(1)))
    return f'C{hi + 1}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--type', required=True,
                    choices=('skill', 'rule', 'agent', 'hook', 'script', 'memory'))
    ap.add_argument('--target', required=True)
    ap.add_argument('--action', default='updated',
                    choices=('created', 'updated', 'deleted'))
    ap.add_argument('--change', required=True)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--vf', default='')
    ap.add_argument('--status', default='applied',
                    choices=('applied', 'rolled-back', 'pending-review'))
    ap.add_argument('--outcome', default=None,
                    choices=('helped', 'hurt', 'neutral', 'stagnation'))
    ap.add_argument('--cls', dest='cls', default='INV', choices=('INV', 'DOM'))
    ap.add_argument('--session', default='')
    ap.add_argument('--dry-run', action='store_true',
                    help='print the stamped record envelope without writing')
    a = ap.parse_args()

    rows = []
    if os.path.exists(LOG):
        with open(LOG, encoding='utf-8') as f:
            rows = [json.loads(l) for l in f if l.strip()]

    rec = {'id': _next_id(rows),
           'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
           'type': a.type, 'target': a.target, 'action': a.action,
           'change': a.change, 'evidence': a.evidence, 'vf': a.vf,
           'session': a.session, 'status': a.status,
           'outcome': a.outcome, 'class': a.cls}
    missing = [k for k in REQUIRED if not rec.get(k)]
    if missing:
        print(_dumps({'ok': False, 'error': 'missing ' + ','.join(missing)}))
        return 2

    if a.dry_run:
        print(_dumps({'ok': True, 'id': rec['id'], 'dry_run': True}))
        return 0

    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(_dumps({'ok': True, 'id': rec['id']}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
