#!/usr/bin/env python3
"""Validate a JSON object against a local knowledge.json ontology."""
import json
import os
import sys


def load_knowledge():
    """Load knowledge.json if present, otherwise empty list."""
    path = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~/.config')), 'devin', '.devin', 'notes', 'structured-knowledge-extraction', 'knowledge.json')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def validate(entity_type, status=None):
    """Check entity type and status against known ontology."""
    knowledge = load_knowledge()
    valid_types = {k.get('entity') for k in knowledge if 'entity' in k}
    valid_statuses = {'pending', 'in_progress', 'completed', 'archived'}
    errors = []
    if valid_types and entity_type not in valid_types:
        errors.append(f"Unknown entity type: {entity_type}")
    if status is not None and status not in valid_statuses:
        errors.append(f"Invalid status: {status}")
    return errors


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Validate against ontology')
    parser.add_argument('--entity-type', required=True)
    parser.add_argument('--status', default=None)
    args = parser.parse_args()
    errors = validate(args.entity_type, args.status)
    if errors:
        for e in errors:
            print(e)
        sys.exit(1)
    print('OK')
