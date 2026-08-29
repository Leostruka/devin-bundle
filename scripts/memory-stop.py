#!/usr/bin/env python3
"""Stop and SessionEnd hook for reporting .devin/memory/ state.

The hook only writes lifecycle and memory summaries to stderr; it never blocks.
"""
import json, os, sys
from datetime import date

BASE = '.devin/memory'


def count_md(path):
    if not os.path.isdir(path):
        return 0
    return sum(
        1 for root, _, files in os.walk(path)
        for f in files if f.endswith('.md')
    )


def log(msg):
    print(f'memory-stop: {msg}', file=sys.stderr)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    event = data.get('hookEventName') or data.get('hook_event_name')
    if event not in ('Stop', 'SessionEnd'):
        sys.exit(0)
    if event == 'SessionEnd':
        log(f"session ended: {data.get('reason', 'unknown')}")

    if not os.path.isdir(BASE):
        sys.exit(0)

    notes = count_md(os.path.join(BASE, 'notes'))
    decisions = count_md(os.path.join(BASE, 'decisions'))
    logbook = count_md(os.path.join(BASE, 'logbook'))
    total = notes + decisions + logbook

    if total == 0:
        log('memory directory exists but is empty; nothing to review')
        sys.exit(0)

    log(f'{total} memory page(s): {notes} note(s), {decisions} decision(s), {logbook} logbook entry(ies)')

    # Check for today's logbook entry
    today = date.today().isoformat()
    y, m, _ = today.split('-')
    today_path = os.path.join(BASE, 'logbook', y, m, f'{today}.md')
    if not os.path.exists(today_path):
        log(f'no logbook entry for {today}; consider capturing today\'s session')
    else:
        log(f'logbook entry for {today} exists')

    # Suggest next actions
    log('consider running: python .devin/memory/scripts/audit-memory.py')
    if notes:
        log('consider capturing any unanswered question/convention before stopping')

    sys.exit(0)


if __name__ == "__main__":
    main()
