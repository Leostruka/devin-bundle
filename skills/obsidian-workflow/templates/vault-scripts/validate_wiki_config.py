#!/usr/bin/env python3
"""Validate wiki-config.json against the steering schema.

Usage:
    python validate_wiki_config.py

Checks:
    - Valid JSON
    - Max 30 pages (80 if --enterprise flag)
    - Max 100 total notes (repo_notes + all page_notes)
    - Max 10000 chars per note
    - Page titles unique and non-empty
    - Each page has title and purpose
    - parent references resolve to existing page titles
    - mode and language are valid values
"""
import argparse
import json
from pathlib import Path

VALID_MODES = {"comprehensive", "concise"}
VALID_LANGS = {"en", "pt", "es", "ja", "zh", "ko", "vi", "he"}
MAX_PAGES_DEFAULT = 30
MAX_PAGES_ENTERPRISE = 80
MAX_NOTES = 100
MAX_NOTE_CHARS = 10000


def count_notes(config):
    repo_notes = len(config.get("repo_notes", []))
    page_notes = sum(len(p.get("page_notes", [])) for p in config.get("pages", []))
    return repo_notes + page_notes


def validate(config, enterprise=False):
    errors = []
    warnings = []
    max_pages = MAX_PAGES_ENTERPRISE if enterprise else MAX_PAGES_DEFAULT

    mode = config.get("mode", "comprehensive")
    if mode not in VALID_MODES:
        errors.append(f"Invalid mode '{mode}'. Must be one of {VALID_MODES}.")

    lang = config.get("language", "en")
    if lang not in VALID_LANGS:
        errors.append(f"Invalid language '{lang}'. Must be one of {VALID_LANGS}.")

    repo_notes = config.get("repo_notes", [])
    if not isinstance(repo_notes, list):
        errors.append("repo_notes must be an array.")
    else:
        for i, note in enumerate(repo_notes):
            content = note.get("content", "")
            if len(content) > MAX_NOTE_CHARS:
                errors.append(f"repo_notes[{i}] exceeds {MAX_NOTE_CHARS} chars ({len(content)}).")

    pages = config.get("pages", [])
    if not isinstance(pages, list):
        errors.append("pages must be an array.")
        return errors, warnings

    if len(pages) > max_pages:
        errors.append(f"Too many pages: {len(pages)} (max {max_pages}).")

    titles = []
    for i, page in enumerate(pages):
        title = page.get("title", "")
        if not title or not title.strip():
            errors.append(f"pages[{i}] has empty or missing title.")
        titles.append(title)
        purpose = page.get("purpose", "")
        if not purpose or not purpose.strip():
            errors.append(f"pages[{i}] '{title}' has empty or missing purpose.")
        importance = page.get("importance", "medium")
        if importance not in {"high", "medium", "low"}:
            warnings.append(f"pages[{i}] '{title}' has invalid importance '{importance}' (expected high/medium/low).")
        for j, pn in enumerate(page.get("page_notes", [])):
            content = pn.get("content", "")
            if len(content) > MAX_NOTE_CHARS:
                errors.append(f"pages[{i}] '{title}' page_notes[{j}] exceeds {MAX_NOTE_CHARS} chars.")

    # Check unique titles
    seen = set()
    for t in titles:
        if t in seen:
            errors.append(f"Duplicate page title: '{t}'.")
        seen.add(t)

    # Check parent references
    title_set = set(titles)
    for i, page in enumerate(pages):
        parent = page.get("parent")
        if parent is not None and parent not in title_set:
            errors.append(f"pages[{i}] '{page.get('title','')}' has parent '{parent}' that does not match any page title.")

    total_notes = count_notes(config)
    if total_notes > MAX_NOTES:
        errors.append(f"Too many notes: {total_notes} (max {MAX_NOTES}).")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate wiki-config.json steering config.")
    parser.add_argument("--enterprise", action="store_true", help="Use enterprise page limit (80 instead of 30)")
    args = parser.parse_args()

    config_path = Path(__file__).parent / "wiki-config.json"
    if not config_path.exists():
        print(f"ERROR: wiki-config.json not found at {config_path}")
        return 1

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return 1

    errors, warnings = validate(config, enterprise=args.enterprise)

    if warnings:
        for w in warnings:
            print(f"  [WARN] {w}")
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        print(f"\nValidation FAILED with {len(errors)} error(s).")
        return 1

    print(f"Validation PASSED. {len(config.get('pages', []))} pages, {count_notes(config)} notes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
