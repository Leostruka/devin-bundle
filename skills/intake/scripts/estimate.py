#!/usr/bin/env python3
"""Estimate task size from a diff and warn if it exceeds reviewable limits."""
import argparse
import os
import re
import subprocess
import sys


def estimate_diff(diff_path=None, repo='.'):
    """Return added+modified lines in a diff or working tree."""
    if diff_path and os.path.exists(diff_path):
        with open(diff_path, encoding='utf-8') as f:
            diff = f.read()
    else:
        result = subprocess.run(
            ['git', 'diff', '--stat'],
            cwd=repo, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return 0, 0
        diff = result.stdout
    added = 0
    for line in diff.splitlines():
        m = re.search(r'\|\s*(\d+)\s*\+', line)
        if m:
            added += int(m.group(1))
    files = len([l for l in diff.splitlines() if '|' in l and 'Bin' not in l])
    return added, files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Estimate task size')
    parser.add_argument('--diff', default=None)
    parser.add_argument('--repo', default='.')
    args = parser.parse_args()
    added, files = estimate_diff(args.diff, args.repo)
    if added > 500:
        print(f'FAIL: {added} lines across {files} files; > 500 requires decomposition.')
        sys.exit(1)
    if added > 300:
        print(f'WARN: {added} lines across {files} files; consider splitting.')
        sys.exit(0)
    print(f'OK: {added} lines across {files} files.')
